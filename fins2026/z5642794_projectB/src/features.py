"""Station 2 - your features: return features and text assembly.

Build your return features here, and assemble the headlines into a daily text
panel. Scoring the text is the Station 3 sentiment model (see src/sentiment.py).
"""
import pandas as pd


def daily_returns(prices: pd.DataFrame, price_col: str = "adjClose") -> pd.DataFrame:
    """Simple daily returns per ticker. Use adjClose.

    Returns a long panel with one simple return per date and ticker. The first
    observation for each ticker is omitted because it has no preceding price.
    """
    required = {"date", "ticker", price_col}
    missing = required.difference(prices.columns)
    if missing:
        raise ValueError(f"prices is missing required columns: {sorted(missing)}")

    panel = prices.loc[:, ["date", "ticker", price_col]].copy()
    panel["date"] = pd.to_datetime(panel["date"])
    panel = panel.sort_values(["ticker", "date"])
    panel["return"] = panel.groupby("ticker", sort=False)[price_col].pct_change()
    return (panel.loc[panel["return"].notna(), ["date", "ticker", "return"]]
                 .reset_index(drop=True))


def assemble_headline_panel(headlines: pd.DataFrame) -> pd.DataFrame:
    """Assemble the headlines into a daily panel per ticker and sector.

    Station 2 is assembly only: structure the text and date-align it to the
    trading calendar. Scoring the text - and lagging the signal - is the
    Station 3 model.
    """
    raise NotImplementedError
