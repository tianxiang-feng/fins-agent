"""Create report-ready baseline Part B figures from precomputed CSV outputs."""
from __future__ import annotations

import pathlib

import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import matplotlib.ticker as mtick
import pandas as pd


ROOT = pathlib.Path(__file__).resolve().parent.parent
FIGURE_DIR = ROOT / "results" / "figures"
RETURNS_PATH = ROOT / "results" / "data" / "fund_returns.csv"
WEIGHTS_PATH = ROOT / "results" / "data" / "fund_weights.csv"
METRICS_PATH = ROOT / "results" / "tables" / "performance_metrics.csv"
SENTIMENT_PATH = ROOT / "results" / "data" / "sector_sentiment_index.csv"

COLORS = {"equal_weight": "#0B6E99", "min_variance": "#E07A2D"}
DISPLAY = {"equal_weight": "Equal weight", "min_variance": "Minimum variance"}


def _style_axis(ax: plt.Axes) -> None:
    ax.spines[["top", "right"]].set_visible(False)
    ax.grid(axis="y", color="#D9D9D9", linewidth=0.7, alpha=0.75)
    ax.set_axisbelow(True)


def _add_note(fig: plt.Figure, sample: str, detail: str) -> None:
    fig.text(
        0.08, 0.025,
        f"Note: {detail}  Sample: {sample}.  Source: authors' calculations from Project B outputs.",
        ha="left", va="bottom", fontsize=8, color="#555555",
    )


def _save(fig: plt.Figure, filename: str) -> pathlib.Path:
    FIGURE_DIR.mkdir(parents=True, exist_ok=True)
    path = FIGURE_DIR / filename
    fig.savefig(path, dpi=300, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    return path


def _date_axis(ax: plt.Axes) -> None:
    ax.xaxis.set_major_locator(mdates.YearLocator())
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))


def create_figures() -> list[pathlib.Path]:
    """Load existing result CSVs and create the four required PNG figures."""
    fund_returns = pd.read_csv(RETURNS_PATH, parse_dates=["date"])
    fund_weights = pd.read_csv(WEIGHTS_PATH, parse_dates=["date"])
    metrics = pd.read_csv(METRICS_PATH, parse_dates=["start_date", "end_date"])
    # Preserve the original combined-fund figures as a like-for-like comparison;
    # native-calendar crypto funds have their own dedicated chart below.
    fund_returns = fund_returns.loc[
        fund_returns["fund"].isin(["equal_weight", "min_variance"])
    ]
    metrics = metrics.loc[metrics["fund"].isin(["equal_weight", "min_variance"])]
    sample = (
        f"{fund_returns['date'].min():%d %b %Y}–"
        f"{fund_returns['date'].max():%d %b %Y}"
    )
    paths: list[pathlib.Path] = []

    fig, ax = plt.subplots(figsize=(8.2, 4.8))
    for fund, group in fund_returns.groupby("fund", sort=False):
        ax.plot(group["date"], group["growth_1"], label=DISPLAY.get(fund, fund),
                color=COLORS.get(fund), linewidth=2.0)
    ax.set_title("Growth of $1: baseline combined funds", loc="left", weight="bold")
    ax.set_xlabel("Date")
    ax.set_ylabel("Portfolio value ($, log scale)")
    ax.set_yscale("log")
    growth_min = fund_returns["growth_1"].min()
    growth_max = fund_returns["growth_1"].max()
    dollar_ticks = [value / 10 for value in range(9, 18)
                    if growth_min <= value / 10 <= growth_max]
    ax.yaxis.set_major_locator(mtick.FixedLocator(dollar_ticks))
    ax.yaxis.set_major_formatter(mtick.StrMethodFormatter("${x:,.2f}"))
    ax.yaxis.set_minor_locator(mtick.NullLocator())
    _date_axis(ax)
    _style_axis(ax)
    ax.legend(frameon=False, ncol=2, loc="upper left")
    _add_note(fig, sample, "Growth is compounded from daily net returns; log scale.")
    fig.subplots_adjust(bottom=0.18)
    paths.append(_save(fig, "fund_growth_1.png"))

    fig, ax = plt.subplots(figsize=(8.2, 4.8))
    for fund, group in fund_returns.groupby("fund", sort=False):
        wealth = group.set_index("date")["growth_1"]
        drawdown = wealth / wealth.cummax() - 1.0
        ax.plot(drawdown.index, drawdown, label=DISPLAY.get(fund, fund),
                color=COLORS.get(fund), linewidth=1.7, alpha=0.9)
    ax.axhline(0, color="#555555", linewidth=0.8)
    ax.set_title("Drawdowns of baseline combined funds", loc="left", weight="bold")
    ax.set_xlabel("Date")
    ax.set_ylabel("Drawdown from prior peak")
    ax.yaxis.set_major_formatter(mtick.PercentFormatter(1.0))
    _date_axis(ax)
    _style_axis(ax)
    ax.legend(frameon=False, ncol=2, loc="lower left")
    _add_note(fig, sample, "Drawdown is the percentage decline from each fund's prior peak.")
    fig.subplots_adjust(bottom=0.18)
    paths.append(_save(fig, "fund_drawdown.png"))

    min_var = fund_weights.loc[fund_weights["fund"] == "min_variance"].copy()
    importance = min_var.groupby("asset")["weight"].apply(lambda x: x.abs().mean())
    top_assets = importance.nlargest(10).index
    top_weights = min_var.loc[min_var["asset"].isin(top_assets)]
    fig, ax = plt.subplots(figsize=(8.2, 5.3))
    palette = plt.get_cmap("tab10")
    for position, (asset, group) in enumerate(top_weights.groupby("asset")):
        ax.plot(group["date"], group["weight"], drawstyle="steps-post",
                label=asset, color=palette(position), linewidth=1.35)
    ax.set_title("Minimum-variance weights: ten largest average allocations",
                 loc="left", weight="bold")
    ax.set_xlabel("Rebalance date")
    ax.set_ylabel("Portfolio weight")
    ax.yaxis.set_major_formatter(mtick.PercentFormatter(1.0))
    _date_axis(ax)
    _style_axis(ax)
    ax.legend(frameon=False, ncol=5, loc="upper center", bbox_to_anchor=(0.5, -0.14),
              fontsize=8)
    _add_note(fig, sample, "Assets ranked by average absolute weight; weights are long-only.")
    fig.subplots_adjust(bottom=0.29)
    paths.append(_save(fig, "fund_weights_over_time.png"))

    fig, ax = plt.subplots(figsize=(7.2, 4.8))
    for _, row in metrics.iterrows():
        fund = row["fund"]
        ax.scatter(row["annualised_volatility"], row["annualised_return"], s=100,
                   color=COLORS.get(fund), edgecolor="white", linewidth=0.8, zorder=3)
        ax.annotate(
            f"{DISPLAY.get(fund, fund)}\nSharpe {row['sharpe_ratio']:.2f}",
            (row["annualised_volatility"], row["annualised_return"]),
            xytext=(8, 7), textcoords="offset points", fontsize=9,
        )
    ax.set_title("Annualised risk and return", loc="left", weight="bold")
    ax.set_xlabel("Annualised volatility")
    ax.set_ylabel("Annualised return")
    ax.xaxis.set_major_formatter(mtick.PercentFormatter(1.0))
    ax.yaxis.set_major_formatter(mtick.PercentFormatter(1.0))
    _style_axis(ax)
    _add_note(fig, sample, "Annualisation uses 252 observations; Sharpe assumes a zero risk-free rate.")
    fig.subplots_adjust(bottom=0.18)
    paths.append(_save(fig, "fund_risk_return.png"))

    return paths


def create_sentiment_figure() -> pathlib.Path:
    """Create small multiples from the precomputed sector sentiment CSV."""
    sentiment = pd.read_csv(SENTIMENT_PATH, parse_dates=["date"])
    sectors = sorted(sentiment["sector"].unique())
    ncols = 2
    nrows = (len(sectors) + ncols - 1) // ncols
    fig, axes = plt.subplots(nrows, ncols, figsize=(8.2, 1.9 * nrows),
                             sharex=True, sharey=True, squeeze=False)
    for ax, sector in zip(axes.flat, sectors):
        group = sentiment.loc[sentiment["sector"] == sector].sort_values("date")
        smooth = group["sentiment_index"].rolling(21, min_periods=5).mean()
        ax.plot(group["date"], group["sentiment_index"], color="#9CBED0",
                linewidth=0.45, alpha=0.45)
        ax.plot(group["date"], smooth, color="#0B6E99", linewidth=1.25)
        ax.axhline(0, color="#777777", linewidth=0.55)
        ax.set_title(str(sector), loc="left", fontsize=9, weight="bold")
        _date_axis(ax)
        _style_axis(ax)
        ax.tick_params(labelsize=7)
    for ax in axes.flat[len(sectors):]:
        ax.set_visible(False)

    fig.suptitle("Sector news sentiment", x=0.08, ha="left", weight="bold")
    fig.supxlabel("Signal availability date", y=0.105, fontsize=9)
    fig.supylabel("VADER compound score", x=0.02, fontsize=9)
    sample = f"{sentiment['date'].min():%d %b %Y}–{sentiment['date'].max():%d %b %Y}"
    _add_note(
        fig, sample,
        "Faint lines are daily equal-weight ticker sentiment; dark lines are 21-observation means. Signals are lagged one trading day.",
    )
    fig.subplots_adjust(left=0.08, right=0.98, top=0.91, bottom=0.17,
                        hspace=0.42, wspace=0.18)
    return _save(fig, "sector_sentiment_index.png")


def create_fusion_figures(
    fusion_returns: pd.DataFrame, fusion_metrics: pd.DataFrame
) -> list[pathlib.Path]:
    """Create growth and risk-return comparisons from computed fusion results."""
    data = fusion_returns.copy()
    data["date"] = pd.to_datetime(data["date"])
    sample = f"{data['date'].min():%d %b %Y}–{data['date'].max():%d %b %Y}"
    labels = {"base_equity": "Base equity", "sentiment_equity": "Sentiment equity"}
    colors = {"base_equity": "#777777", "sentiment_equity": "#0B6E99"}
    paths = []

    fig, ax = plt.subplots(figsize=(8.2, 4.8))
    for fund, group in data.groupby("fund", sort=False):
        ax.plot(group["date"], group["growth_1"], label=labels[fund],
                color=colors[fund], linewidth=1.9)
    ax.set_title("Equity fund growth with a sentiment tilt", loc="left", weight="bold")
    ax.set_xlabel("Date")
    ax.set_ylabel("Portfolio value ($, log scale)")
    ax.set_yscale("log")
    low, high = data["growth_1"].min(), data["growth_1"].max()
    ticks = [value / 20 for value in range(15, 41) if low <= value / 20 <= high]
    ax.yaxis.set_major_locator(mtick.FixedLocator(ticks[::2]))
    ax.yaxis.set_major_formatter(mtick.StrMethodFormatter("${x:,.2f}"))
    ax.yaxis.set_minor_locator(mtick.NullLocator())
    _date_axis(ax)
    _style_axis(ax)
    ax.legend(frameon=False, ncol=2, loc="upper left")
    _add_note(fig, sample, "Both funds are equity-only; the tilt uses lagged sector sentiment.")
    fig.subplots_adjust(bottom=0.18)
    paths.append(_save(fig, "sentiment_fusion_growth.png"))

    fig, ax = plt.subplots(figsize=(7.2, 4.8))
    for _, row in fusion_metrics.iterrows():
        fund = row["fund"]
        ax.scatter(row["annualised_volatility"], row["annualised_return"],
                   s=105, color=colors[fund], edgecolor="white", linewidth=0.8)
        ax.annotate(f"{labels[fund]}\nSharpe {row['sharpe_ratio']:.2f}",
                    (row["annualised_volatility"], row["annualised_return"]),
                    xytext=(8, 7), textcoords="offset points", fontsize=9)
    ax.set_title("Risk and return before and after sentiment tilt", loc="left", weight="bold")
    ax.set_xlabel("Annualised volatility")
    ax.set_ylabel("Annualised return")
    ax.xaxis.set_major_formatter(mtick.PercentFormatter(1.0))
    ax.yaxis.set_major_formatter(mtick.PercentFormatter(1.0))
    _style_axis(ax)
    _add_note(fig, sample, "Annualisation uses 252 observations; Sharpe assumes a zero risk-free rate.")
    fig.subplots_adjust(bottom=0.18)
    paths.append(_save(fig, "sentiment_fusion_risk_return.png"))
    return paths


def create_crypto_figure(fund_returns: pd.DataFrame) -> pathlib.Path:
    """Create a focused growth comparison for the two crypto-only funds."""
    crypto = fund_returns.loc[
        fund_returns["fund"].isin(["crypto_equal_weight", "crypto_min_variance"])
    ].copy()
    crypto["date"] = pd.to_datetime(crypto["date"])
    labels = {
        "crypto_equal_weight": "Crypto equal weight",
        "crypto_min_variance": "Crypto minimum variance",
    }
    colors = {"crypto_equal_weight": "#0B6E99", "crypto_min_variance": "#E07A2D"}
    fig, ax = plt.subplots(figsize=(8.2, 4.8))
    for fund, group in crypto.groupby("fund", sort=False):
        ax.plot(group["date"], group["growth_1"], label=labels[fund],
                color=colors[fund], linewidth=1.9)
    ax.set_title("Growth of $1: crypto-only funds", loc="left", weight="bold")
    ax.set_xlabel("Date")
    ax.set_ylabel("Portfolio value ($, log scale)")
    ax.set_yscale("log")
    ax.yaxis.set_major_locator(mtick.FixedLocator([0.5, 0.75, 1.0, 1.5, 2.0, 3.0, 4.0]))
    ax.yaxis.set_major_formatter(mtick.StrMethodFormatter("${x:,.2f}"))
    ax.yaxis.set_minor_locator(mtick.NullLocator())
    _date_axis(ax)
    _style_axis(ax)
    ax.legend(frameon=False, ncol=2, loc="best")
    sample = f"{crypto['date'].min():%d %b %Y}–{crypto['date'].max():%d %b %Y}"
    _add_note(fig, sample, "Crypto trades daily; estimation and annualisation use 365 observations.")
    fig.subplots_adjust(bottom=0.18)
    return _save(fig, "crypto_only_growth.png")


if __name__ == "__main__":
    for output in create_figures():
        print("figure:", output)
