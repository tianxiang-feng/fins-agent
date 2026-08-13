"""Station 3 - baseline funds and walk-forward out-of-sample backtests.

Build at least a combined equity-plus-crypto fund with two optimisation methods.
Backtest rules: walk-forward, no look-ahead, weights from past data only, annualise
with 252 (equity) or 365 (crypto). See the brief, Part B.
"""
from __future__ import annotations

import numpy as np
import pandas as pd


ESTIMATION_WINDOW = 252


def _equal_weights(n_assets: int) -> np.ndarray:
    return np.full(n_assets, 1.0 / n_assets)


def _min_variance_weights(estimation_returns: pd.DataFrame) -> np.ndarray:
    """Long-only minimum-variance weights, with an equal-weight fallback."""
    fallback = _equal_weights(estimation_returns.shape[1])
    try:
        from scipy.optimize import minimize

        covariance = estimation_returns.cov().to_numpy()
        if not np.isfinite(covariance).all():
            return fallback

        result = minimize(
            lambda weights: float(weights @ covariance @ weights),
            fallback,
            method="SLSQP",
            bounds=[(0.0, 1.0)] * len(fallback),
            constraints={"type": "eq", "fun": lambda weights: weights.sum() - 1.0},
            options={"maxiter": 500, "ftol": 1e-12},
        )
        if not result.success or not np.isfinite(result.x).all():
            return fallback

        weights = np.clip(result.x, 0.0, 1.0)
        return weights / weights.sum()
    except (ImportError, ValueError, ArithmeticError):
        return fallback


def oos_backtest(
    returns: pd.DataFrame,
    method: str = "min_variance",
    estimation_window: int = ESTIMATION_WINDOW,
) -> dict:
    """Run a monthly walk-forward backtest on a wide return panel.

    The first ``estimation_window`` complete observations form the initial
    estimation window (252 by default; callers may use 365 for daily crypto).
    Thereafter, weights are refreshed on the last available observation of each
    month. Crucially, the window for date ``t`` ends at ``t - 1``; the return on
    the rebalance date is therefore genuinely out of sample.
    """
    if method not in {"equal_weight", "min_variance"}:
        raise ValueError("method must be 'equal_weight' or 'min_variance'")
    if not isinstance(returns.index, pd.DatetimeIndex):
        raise ValueError("returns must have a DatetimeIndex")
    if returns.columns.empty:
        raise ValueError("returns must contain at least one asset")
    if estimation_window <= 1:
        raise ValueError("estimation_window must be greater than one")

    panel = (returns.sort_index().astype(float)
                    .replace([np.inf, -np.inf], np.nan)
                    .dropna(how="any"))
    if panel.index.has_duplicates:
        raise ValueError("returns index must not contain duplicate dates")
    if len(panel) <= estimation_window:
        raise ValueError(
            f"returns needs more than {estimation_window} complete observations"
        )

    # Each selected date is the final date actually present in that month.
    index_series = pd.Series(panel.index, index=panel.index)
    rebalance_dates = set(index_series.groupby(panel.index.to_period("M")).max())

    current_weights = None
    portfolio_returns: list[tuple[pd.Timestamp, float]] = []
    weight_records: list[dict] = []

    for position in range(estimation_window, len(panel)):
        date = panel.index[position]
        if date in rebalance_dates:
            # iloc excludes `position`: no return from the holding period is
            # used to choose its own weight, avoiding look-ahead bias.
            history = panel.iloc[position - estimation_window:position]
            if method == "equal_weight":
                current_weights = _equal_weights(panel.shape[1])
            else:
                current_weights = _min_variance_weights(history)

            weight_records.extend(
                {"date": date, "asset": asset, "weight": float(weight)}
                for asset, weight in zip(panel.columns, current_weights)
            )

        # The backtest starts at the first eligible month-end rebalance.
        if current_weights is not None:
            realised = float(panel.iloc[position].to_numpy() @ current_weights)
            portfolio_returns.append((date, realised))

    daily = pd.Series(
        dict(portfolio_returns), name="daily_return", dtype=float
    ).sort_index()
    daily.index.name = "date"
    growth = (1.0 + daily).cumprod().rename("growth_1")
    weights = pd.DataFrame(weight_records, columns=["date", "asset", "weight"])
    return {"daily_returns": daily, "growth_1": growth, "weights": weights}


def performance_metrics(daily_returns: pd.Series, periods_per_year: int = 252) -> dict:
    """Calculate standard performance statistics from periodic simple returns."""
    if periods_per_year <= 0:
        raise ValueError("periods_per_year must be positive")

    series = pd.Series(daily_returns, dtype=float).replace([np.inf, -np.inf], np.nan).dropna()
    if series.empty:
        raise ValueError("daily_returns contains no finite observations")
    if (series <= -1.0).any():
        raise ValueError("simple returns must be greater than -100%")

    observations = len(series)
    wealth = (1.0 + series).cumprod()
    annualised_return = float(wealth.iloc[-1] ** (periods_per_year / observations) - 1.0)
    annualised_volatility = float(series.std(ddof=1) * np.sqrt(periods_per_year))
    sharpe_ratio = (
        float(series.mean() / series.std(ddof=1) * np.sqrt(periods_per_year))
        if series.std(ddof=1) > 0 else np.nan
    )
    max_drawdown = float((wealth / wealth.cummax() - 1.0).min())

    def _format_date(value) -> str:
        try:
            return pd.Timestamp(value).strftime("%Y-%m-%d")
        except (TypeError, ValueError):
            return str(value)

    return {
        "annualised_return": annualised_return,
        "annualised_volatility": annualised_volatility,
        "sharpe_ratio": sharpe_ratio,
        "max_drawdown": max_drawdown,
        "observations": observations,
        "start_date": _format_date(series.index[0]),
        "end_date": _format_date(series.index[-1]),
    }
