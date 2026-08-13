"""Reproduce your Part B results. Run from the project root:

    python scripts/run_part_b.py
"""
import sys
import pathlib

import pandas as pd

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))

from src import data_access, features, fusion, portfolios, sentiment  # noqa: E402
from scripts.make_part_b_figures import (  # noqa: E402
    create_crypto_figure, create_figures, create_fusion_figures,
    create_sentiment_figure,
)


ROOT = pathlib.Path(__file__).resolve().parent.parent
END_DATE = pd.Timestamp("2023-12-31")


def _wide_returns(prices: pd.DataFrame) -> pd.DataFrame:
    long_returns = features.daily_returns(prices)
    return long_returns.pivot(index="date", columns="ticker", values="return").sort_index()


def _align_crypto_to_equity_calendar(
    crypto_returns: pd.DataFrame, equity_calendar: pd.DatetimeIndex
) -> pd.DataFrame:
    """Compound crypto returns between consecutive equity trading dates.

    Sampling raw crypto returns on weekdays would silently discard weekends.
    Sampling the crypto wealth index instead rolls weekend performance into the
    next equity observation while retaining an equity-frequency combined fund.
    """
    crypto_wealth = (1.0 + crypto_returns).cumprod()
    sampled_wealth = crypto_wealth.reindex(equity_calendar, method="ffill")
    return sampled_wealth.pct_change(fill_method=None)


def main():
    equity_prices = data_access.load_equity_prices()
    crypto_prices = data_access.load_crypto_prices()
    news_headlines = data_access.load_news_headlines()
    equity_prices = equity_prices.loc[equity_prices["date"] <= END_DATE].copy()
    crypto_prices = crypto_prices.loc[crypto_prices["date"] <= END_DATE].copy()

    # Returns are computed on each market's native calendar before alignment.
    equity_returns = _wide_returns(equity_prices)
    crypto_returns = _wide_returns(crypto_prices)
    aligned_crypto = _align_crypto_to_equity_calendar(
        crypto_returns, equity_returns.index
    )

    # Prefixes make asset identifiers unambiguous if tickers overlap.
    combined_equity_returns = equity_returns.add_prefix("EQ_")
    aligned_crypto = aligned_crypto.add_prefix("CR_")
    combined_returns = pd.concat([combined_equity_returns, aligned_crypto], axis=1).dropna(how="any")

    fund_return_frames = []
    fund_weight_frames = []
    metric_rows = []
    for method in ("equal_weight", "min_variance"):
        result = portfolios.oos_backtest(combined_returns, method=method)
        fund_returns = pd.concat(
            [result["daily_returns"], result["growth_1"]], axis=1
        ).reset_index()
        fund_returns.insert(1, "fund", method)
        fund_return_frames.append(fund_returns)

        fund_weights = result["weights"].copy()
        fund_weights.insert(1, "fund", method)
        fund_weight_frames.append(fund_weights)

        metrics = portfolios.performance_metrics(
            result["daily_returns"], periods_per_year=252
        )
        metric_rows.append({"fund": method, **metrics})

    # Crypto-only funds remain on the native seven-day calendar. A 365-day
    # window and 365-day annualisation match their observation frequency. As in
    # the baseline engine, each month-end weight uses returns ending at t-1.
    crypto_panel = crypto_returns.dropna(how="any").add_prefix("CR_")
    crypto_results = {}
    for method in ("equal_weight", "min_variance"):
        fund_name = f"crypto_{method}"
        result = portfolios.oos_backtest(
            crypto_panel, method=method, estimation_window=365
        )
        crypto_results[fund_name] = result
        fund_returns = pd.concat(
            [result["daily_returns"], result["growth_1"]], axis=1
        ).reset_index()
        fund_returns.insert(1, "fund", fund_name)
        fund_return_frames.append(fund_returns)
        fund_weights = result["weights"].copy()
        fund_weights.insert(1, "fund", fund_name)
        fund_weight_frames.append(fund_weights)
        metric_rows.append({
            "fund": fund_name,
            **portfolios.performance_metrics(result["daily_returns"], periods_per_year=365),
        })

    all_fund_returns = pd.concat(fund_return_frames, ignore_index=True)
    all_fund_weights = pd.concat(fund_weight_frames, ignore_index=True)
    all_metrics = pd.DataFrame(metric_rows)

    # Extension validation: complete returns and fully invested monthly weights.
    crypto_output_returns = pd.concat(
        [result["daily_returns"] for result in crypto_results.values()]
    )
    if crypto_output_returns.isna().any():
        raise ValueError("crypto-only fund returns contain missing values")
    for fund_name, result in crypto_results.items():
        sums = result["weights"].groupby("date")["weight"].sum()
        if not sums.sub(1.0).abs().lt(1e-10).all():
            raise ValueError(f"{fund_name} weights do not sum to one")

    data_dir = ROOT / "results" / "data"
    table_dir = ROOT / "results" / "tables"
    data_dir.mkdir(parents=True, exist_ok=True)
    table_dir.mkdir(parents=True, exist_ok=True)
    output_paths = {
        "fund returns": data_dir / "fund_returns.csv",
        "fund weights": data_dir / "fund_weights.csv",
        "performance metrics": table_dir / "performance_metrics.csv",
    }
    all_fund_returns.to_csv(output_paths["fund returns"], index=False)
    all_fund_weights.to_csv(output_paths["fund weights"], index=False)
    all_metrics.to_csv(output_paths["performance metrics"], index=False)

    # Sentiment covers equities only. Its output date is already shifted one
    # equity trading day beyond the calendar-aligned headline date.
    equity_calendar = pd.DatetimeIndex(equity_prices["date"].drop_duplicates())
    sector_index = sentiment.build_sector_sentiment_index(
        news_headlines, equity_calendar
    )
    sentiment_path = data_dir / "sector_sentiment_index.csv"
    sector_index.to_csv(sentiment_path, index=False)

    # Equity-only fusion comparison. The base follows the same 252-day,
    # month-end OOS design as the combined baseline funds.
    equity_panel = equity_returns.dropna(how="any")
    ticker_sector = (equity_prices[["ticker", "sector"]].drop_duplicates()
                     .set_index("ticker")["sector"])
    base_equity = portfolios.oos_backtest(equity_panel, method="equal_weight")
    sentiment_equity = fusion.oos_sentiment_backtest(
        equity_panel, sector_index, ticker_sector
    )
    fusion_frames = []
    fusion_metric_rows = []
    for fund_name, result in (
        ("base_equity", base_equity),
        ("sentiment_equity", sentiment_equity),
    ):
        frame = pd.concat([result["daily_returns"], result["growth_1"]], axis=1).reset_index()
        frame.insert(1, "fund", fund_name)
        fusion_frames.append(frame)
        fusion_metric_rows.append({
            "fund": fund_name,
            **portfolios.performance_metrics(result["daily_returns"], 252),
        })
    fusion_returns = pd.concat(fusion_frames, ignore_index=True)
    fusion_metrics = pd.DataFrame(fusion_metric_rows)

    # Fail loudly if the fusion becomes invalid or uses a same/future-dated signal.
    if fusion_returns.isna().any().any() or fusion_metrics.isna().any().any():
        raise ValueError("fusion outputs contain missing values")
    weight_sums = sentiment_equity["weights"].groupby("date")["weight"].sum()
    if not weight_sums.sub(1.0).abs().lt(1e-10).all():
        raise ValueError("sentiment-augmented weights do not sum to one")
    audit = sentiment_equity["audit"]
    if not (audit["max_sentiment_date"] < audit["date"]).all():
        raise ValueError("fusion used sentiment that was not available before return date")

    fusion_metrics_path = table_dir / "sentiment_fusion_metrics.csv"
    fusion_metrics.to_csv(fusion_metrics_path, index=False)

    print("equity prices:", equity_prices.shape, "crypto prices:", crypto_prices.shape)
    print("combined complete return panel:", combined_returns.shape)
    print("fund returns:", all_fund_returns.shape, "->", output_paths["fund returns"])
    print("fund weights:", all_fund_weights.shape, "->", output_paths["fund weights"])
    print("performance metrics:", all_metrics.shape, "->", output_paths["performance metrics"])
    print("sector sentiment index:", sector_index.shape, "->", sentiment_path)
    print("sentiment fusion metrics:", fusion_metrics.shape, "->", fusion_metrics_path)
    # Figure creation reads the saved CSVs; it does not recompute the backtest.
    for figure_path in create_figures():
        print("figure:", figure_path)
    print("figure:", create_crypto_figure(all_fund_returns))
    print("figure:", create_sentiment_figure())
    for figure_path in create_fusion_figures(fusion_returns, fusion_metrics):
        print("figure:", figure_path)


if __name__ == "__main__":
    main()
