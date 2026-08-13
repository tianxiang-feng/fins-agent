"""Station 3 (extension) - fuse sentiment into the funds.

Tilt or factor: combine your sentiment signal with the portfolio weights,
look-ahead safe, then test whether it adds value. An honest negative result,
explained, is good work.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from src.portfolios import ESTIMATION_WINDOW


MAX_WEIGHT_CHANGE = 0.005
SENTIMENT_LOOKBACK = 21


def apply_sentiment(
    weights: pd.Series,
    sector_scores: pd.Series,
    ticker_sector: pd.Series,
    max_weight_change: float = MAX_WEIGHT_CHANGE,
) -> pd.Series:
    """Apply a bounded, zero-sum sector-sentiment tilt to equity weights.

    Sector scores are mapped to tickers, demeaned across the eligible stocks,
    and scaled to [-1, 1]. Each equal weight then changes by no more than 0.5
    percentage points by default. The zero-sum adjustment preserves full
    investment; clipping is a final numerical guard for long-only weights.
    """
    if max_weight_change < 0:
        raise ValueError("max_weight_change must be non-negative")
    mapped_scores = ticker_sector.reindex(weights.index).map(sector_scores).fillna(0.0)
    centred = mapped_scores - mapped_scores.mean()
    scale = float(centred.abs().max())
    adjustment = (
        centred / scale * max_weight_change if scale > 0
        else pd.Series(0.0, index=weights.index)
    )
    tilted = (weights + adjustment).clip(lower=0.0)
    return tilted / tilted.sum()


def oos_sentiment_backtest(
    returns: pd.DataFrame,
    sentiment: pd.DataFrame,
    ticker_sector: pd.Series,
) -> dict:
    """Run an equity-only monthly sentiment-tilted OOS backtest.

    The initial 252 observations and month-end schedule match the baseline
    portfolio backtest. For a rebalance on date t, sentiment is restricted to
    output dates strictly earlier than t. Since the sentiment index itself is
    already lagged one trading day, this is an additional conservative guard
    against same-day information leakage.
    """
    panel = (returns.sort_index().astype(float)
                    .replace([np.inf, -np.inf], np.nan).dropna(how="any"))
    if not isinstance(panel.index, pd.DatetimeIndex):
        raise ValueError("returns must have a DatetimeIndex")
    if len(panel) <= ESTIMATION_WINDOW:
        raise ValueError(f"returns needs more than {ESTIMATION_WINDOW} observations")
    if not panel.columns.isin(ticker_sector.index).all():
        raise ValueError("every return ticker must have a sector mapping")

    signals = sentiment.copy()
    signals["date"] = pd.to_datetime(signals["date"])
    signals = signals.sort_values(["sector", "date"])
    index_series = pd.Series(panel.index, index=panel.index)
    rebalance_dates = set(index_series.groupby(panel.index.to_period("M")).max())

    base_weights = pd.Series(1.0 / panel.shape[1], index=panel.columns)
    current_weights = None
    returns_records = []
    weight_records = []
    audit_records = []

    for position in range(ESTIMATION_WINDOW, len(panel)):
        date = panel.index[position]
        if date in rebalance_dates:
            available = signals.loc[signals["date"] < date]
            recent = available.groupby("sector", group_keys=False).tail(SENTIMENT_LOOKBACK)
            sector_scores = recent.groupby("sector")["sentiment_index"].mean()
            current_weights = apply_sentiment(
                base_weights, sector_scores, ticker_sector
            )
            max_signal_date = available["date"].max()
            audit_records.append({"date": date, "max_sentiment_date": max_signal_date})
            weight_records.extend(
                {"date": date, "asset": asset, "weight": float(weight)}
                for asset, weight in current_weights.items()
            )

        if current_weights is not None:
            realised = float(panel.iloc[position].dot(current_weights))
            returns_records.append((date, realised))

    daily = pd.Series(dict(returns_records), name="daily_return").sort_index()
    daily.index.name = "date"
    return {
        "daily_returns": daily,
        "growth_1": (1.0 + daily).cumprod().rename("growth_1"),
        "weights": pd.DataFrame(weight_records),
        "audit": pd.DataFrame(audit_records),
    }
