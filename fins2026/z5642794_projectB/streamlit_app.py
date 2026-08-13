"""Wealth Radar: investor dashboard built only from precomputed results."""
from __future__ import annotations

import pathlib

import numpy as np
import pandas as pd
import streamlit as st


ROOT = pathlib.Path(__file__).resolve().parent
RESULTS = ROOT / "results"
CSV_PATHS = {
    "fund returns": RESULTS / "data" / "fund_returns.csv",
    "fund weights": RESULTS / "data" / "fund_weights.csv",
    "sector sentiment": RESULTS / "data" / "sector_sentiment_index.csv",
    "performance metrics": RESULTS / "tables" / "performance_metrics.csv",
    "sentiment fusion metrics": RESULTS / "tables" / "sentiment_fusion_metrics.csv",
}
FIGURE_PATHS = {
    "growth": RESULTS / "figures" / "fund_growth_1.png",
    "drawdown": RESULTS / "figures" / "fund_drawdown.png",
    "risk return": RESULTS / "figures" / "fund_risk_return.png",
    "weights": RESULTS / "figures" / "fund_weights_over_time.png",
    "sentiment": RESULTS / "figures" / "sector_sentiment_index.png",
    "fusion growth": RESULTS / "figures" / "sentiment_fusion_growth.png",
    "fusion risk return": RESULTS / "figures" / "sentiment_fusion_risk_return.png",
    "crypto growth": RESULTS / "figures" / "crypto_only_growth.png",
}
FUND_LABELS = {
    "equal_weight": "Equal Weight",
    "min_variance": "Minimum Variance",
    "base_equity": "Base Equity",
    "sentiment_equity": "Sentiment Equity",
    "crypto_equal_weight": "Crypto Equal Weight",
    "crypto_min_variance": "Crypto Minimum Variance",
}

st.set_page_config(page_title="Wealth Radar", page_icon="📡", layout="wide")


@st.cache_data(show_spinner=False)
def load_results() -> dict[str, pd.DataFrame]:
    """Load committed outputs only; no raw data, models, or network calls."""
    return {
        "returns": pd.read_csv(CSV_PATHS["fund returns"], parse_dates=["date"]),
        "weights": pd.read_csv(CSV_PATHS["fund weights"], parse_dates=["date"]),
        "sentiment": pd.read_csv(CSV_PATHS["sector sentiment"], parse_dates=["date"]),
        "metrics": pd.read_csv(CSV_PATHS["performance metrics"]),
        "fusion_metrics": pd.read_csv(CSV_PATHS["sentiment fusion metrics"]),
    }


def format_metrics(frame: pd.DataFrame) -> pd.DataFrame:
    """Return a client-facing copy of a performance table."""
    display = frame.copy()
    display["fund"] = display["fund"].map(FUND_LABELS).fillna(display["fund"])
    return display.rename(columns={
        "fund": "Fund",
        "annualised_return": "Annualised return",
        "annualised_volatility": "Annualised volatility",
        "sharpe_ratio": "Sharpe ratio",
        "max_drawdown": "Maximum drawdown",
        "observations": "Observations",
        "start_date": "Start date",
        "end_date": "End date",
    })


def show_metrics_table(frame: pd.DataFrame) -> None:
    st.dataframe(
        format_metrics(frame).style.format({
            "Annualised return": "{:.2%}",
            "Annualised volatility": "{:.2%}",
            "Sharpe ratio": "{:.2f}",
            "Maximum drawdown": "{:.2%}",
        }),
        width="stretch", hide_index=True,
    )


def allocation_metrics(
    daily_returns: pd.Series, periods_per_year: int
) -> dict[str, float]:
    wealth = (1.0 + daily_returns).cumprod()
    volatility = daily_returns.std(ddof=1) * np.sqrt(periods_per_year)
    return {
        "Annualised return": wealth.iloc[-1] ** (periods_per_year / len(daily_returns)) - 1,
        "Annualised volatility": volatility,
        "Sharpe ratio": (daily_returns.mean() / daily_returns.std(ddof=1)
                         * np.sqrt(periods_per_year) if volatility > 0 else np.nan),
        "Maximum drawdown": (wealth / wealth.cummax() - 1).min(),
    }


missing = [str(path.relative_to(ROOT)) for path in [*CSV_PATHS.values(), *FIGURE_PATHS.values()]
           if not path.is_file()]
if missing:
    st.title("Wealth Radar")
    st.error("Some precomputed result files are unavailable. Reproduce the project outputs first.")
    st.code("\n".join(missing))
    st.info("From the project root, run: python scripts/run_part_b.py")
    st.stop()

try:
    data = load_results()
except Exception as exc:
    st.title("Wealth Radar")
    st.error("The precomputed results could not be loaded.")
    st.exception(exc)
    st.stop()

st.title("Wealth Radar")
st.caption("Systematic multi-asset funds and lagged equity-sector news sentiment analytics")

page = st.sidebar.radio(
    "Explore",
    ["Overview", "Fund comparison", "Fund fact sheets", "Allocation simulator",
     "Sentiment analytics", "Sentiment fusion"],
)
st.sidebar.caption("Research prototype · Results through 29 December 2023")

if page == "Overview":
    st.header("A clearer view of systematic investing")
    st.write(
        "Wealth Radar compares rules-based equity-and-crypto funds and tracks "
        "news sentiment across US equity sectors. All results are historical, "
        "out-of-sample simulations—not forecasts or investment advice."
    )
    metrics = data["metrics"]
    best = metrics.loc[metrics["sharpe_ratio"].idxmax()]
    cols = st.columns(3)
    cols[0].metric("Available funds", metrics["fund"].nunique())
    cols[1].metric("Highest historical Sharpe", f"{best['sharpe_ratio']:.2f}",
                   FUND_LABELS.get(best["fund"], best["fund"]))
    cols[2].metric("Out-of-sample observations", f"{int(best['observations']):,}")
    st.subheader("Baseline fund snapshot")
    show_metrics_table(metrics)
    st.info("Crypto trades every day; combined-fund results are aligned to the equity trading calendar.")
    st.image(str(FIGURE_PATHS["crypto growth"]), width="stretch")

elif page == "Fund comparison":
    st.header("Compare baseline funds")
    st.image(str(FIGURE_PATHS["growth"]), width="stretch")
    st.subheader("Crypto-only comparison")
    st.image(str(FIGURE_PATHS["crypto growth"]), width="stretch")
    left, right = st.columns(2)
    with left:
        st.image(str(FIGURE_PATHS["drawdown"]), width="stretch")
    with right:
        st.image(str(FIGURE_PATHS["risk return"]), width="stretch")
    show_metrics_table(data["metrics"])

elif page == "Fund fact sheets":
    st.header("Fund fact sheets")
    metrics = data["metrics"]
    choices = metrics["fund"].tolist()
    selected = st.selectbox("Select a fund", choices,
                            format_func=lambda value: FUND_LABELS.get(value, value))
    row = metrics.loc[metrics["fund"] == selected].iloc[0]
    cols = st.columns(4)
    cols[0].metric("Annualised return", f"{row['annualised_return']:.2%}")
    cols[1].metric("Annualised volatility", f"{row['annualised_volatility']:.2%}")
    cols[2].metric("Sharpe ratio", f"{row['sharpe_ratio']:.2f}")
    cols[3].metric("Maximum drawdown", f"{row['max_drawdown']:.2%}")
    st.caption(
        f"{int(row['observations']):,} daily observations · "
        f"{row['start_date']} to {row['end_date']} · zero risk-free rate"
    )
    weights = data["weights"]
    selected_weights = weights.loc[weights["fund"] == selected]
    latest_date = selected_weights["date"].max()
    latest = (selected_weights.loc[selected_weights["date"] == latest_date, ["asset", "weight"]]
              .sort_values("weight", ascending=False))
    st.subheader(f"Latest holdings · {latest_date:%d %B %Y}")
    st.dataframe(latest.rename(columns={"asset": "Asset", "weight": "Weight"})
                 .style.format({"Weight": "{:.2%}"}), width="stretch", hide_index=True)
    if selected == "min_variance":
        st.image(str(FIGURE_PATHS["weights"]), width="stretch")

elif page == "Allocation simulator":
    st.header("Allocation simulator")
    st.write("Set target allocations across the two baseline funds. Inputs are normalized to 100%.")
    funds = data["returns"]["fund"].drop_duplicates().tolist()
    raw = {}
    columns = st.columns(len(funds))
    for column, fund in zip(columns, funds):
        raw[fund] = column.number_input(
            FUND_LABELS.get(fund, fund) + " (%)", min_value=0.0, max_value=100.0,
            value=100.0 / len(funds), step=5.0,
        )
    total = sum(raw.values())
    if total <= 0:
        st.warning("Enter a positive allocation for at least one fund.")
    else:
        normalized = {fund: value / total for fund, value in raw.items()}
        if not np.isclose(total, 100.0):
            st.info(f"The entered total is {total:.1f}%; allocations have been normalized to 100%.")
        active_funds = [fund for fund, weight in normalized.items() if weight > 0]
        return_panel = (data["returns"].pivot(index="date", columns="fund", values="daily_return")
                        .sort_index()[active_funds].dropna(how="any"))
        active_weights = pd.Series({fund: normalized[fund] for fund in active_funds})
        active_weights = active_weights / active_weights.sum()
        portfolio_return = return_panel.mul(active_weights).sum(axis=1)
        growth = (1.0 + portfolio_return).cumprod().rename("Growth of $1")
        crypto_only = all(fund.startswith("crypto_") for fund in active_funds)
        periods_per_year = 365 if crypto_only else 252
        stats = allocation_metrics(portfolio_return, periods_per_year)
        cols = st.columns(4)
        cols[0].metric("Annualised return", f"{stats['Annualised return']:.2%}")
        cols[1].metric("Annualised volatility", f"{stats['Annualised volatility']:.2%}")
        cols[2].metric("Sharpe ratio", f"{stats['Sharpe ratio']:.2f}")
        cols[3].metric("Maximum drawdown", f"{stats['Maximum drawdown']:.2%}")
        st.line_chart(growth, y_label="Portfolio value ($)")
        st.caption(
            f"Historical simulation using precomputed fund returns and {periods_per_year}-day "
            "annualisation; no rebalancing costs included."
        )

elif page == "Sentiment analytics":
    st.header("Equity-sector sentiment")
    st.image(str(FIGURE_PATHS["sentiment"]), width="stretch")
    st.info(
        "Sentiment applies only to equity sectors. Headline dates are mapped to the equity "
        "calendar and lagged one trading day before appearing in this dataset."
    )
    sentiment = data["sentiment"]
    sector = st.selectbox("Preview sector", sorted(sentiment["sector"].unique()))
    preview = (sentiment.loc[sentiment["sector"] == sector]
               .sort_values("date", ascending=False).head(20))
    st.dataframe(preview.rename(columns={
        "date": "Signal date", "sector": "Sector", "sentiment_index": "Sentiment index",
        "headline_count": "Headlines", "ticker_count": "Tickers",
    }).style.format({"Sentiment index": "{:.3f}"}), width="stretch", hide_index=True)

elif page == "Sentiment fusion":
    st.header("Does sentiment improve the equity fund?")
    fusion = data["fusion_metrics"]
    base = fusion.set_index("fund").loc["base_equity"]
    tilted = fusion.set_index("fund").loc["sentiment_equity"]
    return_difference = tilted["annualised_return"] - base["annualised_return"]
    sharpe_difference = tilted["sharpe_ratio"] - base["sharpe_ratio"]
    if return_difference > 0 and sharpe_difference > 0:
        st.success(
            f"The sentiment fund improved annualised return by {return_difference:.2%} "
            f"and Sharpe by {sharpe_difference:.2f} over this sample."
        )
    else:
        st.warning(
            f"The sentiment fund underperformed: annualised return changed by "
            f"{return_difference:.2%} and Sharpe by {sharpe_difference:.2f}. "
            "The result is retained without performance-driven retuning."
        )
    st.image(str(FIGURE_PATHS["fusion growth"]), width="stretch")
    st.image(str(FIGURE_PATHS["fusion risk return"]), width="stretch")
    show_metrics_table(fusion)
    st.caption(
        "The equity-only extension applies a bounded sector tilt using sentiment available "
        "strictly before each monthly rebalance. Crypto is excluded because it has no headline data."
    )
