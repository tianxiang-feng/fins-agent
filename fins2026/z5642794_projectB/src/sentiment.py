"""Station 3 - your sentiment model and index from news headlines.

This is the model step: score each headline, aggregate to a daily per-ticker score,
then to an equal-weight sector index. Headlines are a noisy proxy, so lag to avoid
look-ahead.
"""
import pandas as pd


def score_headlines(panel: pd.DataFrame) -> pd.DataFrame:
    """Return a copy of the headline panel with VADER compound scores.

    Headline strings are passed directly to VADER because casing, punctuation,
    negation, and emphasis all carry information for that model.
    """
    if "title" not in panel.columns:
        raise ValueError("panel must contain a title column")

    from nltk.sentiment import SentimentIntensityAnalyzer

    try:
        analyser = SentimentIntensityAnalyzer()
    except LookupError:
        # This is a one-time reproduction/build dependency. The deployed app
        # reads the precomputed CSV and never downloads or runs NLTK.
        import nltk

        if not nltk.download("vader_lexicon", quiet=True):
            raise RuntimeError("could not download the NLTK VADER lexicon")
        analyser = SentimentIntensityAnalyzer()

    scored = panel.copy()
    scored["sentiment_score"] = scored["title"].map(
        lambda title: analyser.polarity_scores(title)["compound"]
    )
    return scored


def sector_sentiment_index(
    scores: pd.DataFrame, trading_calendar: pd.DatetimeIndex
) -> pd.DataFrame:
    """Build a lagged sector-day index that equal-weights ticker-day scores.

    Calendar dates first map to the next available equity trading day. The
    mapped signal is then moved forward by one *additional* trading day. Thus,
    headlines associated with day t are first usable on t+1 and cannot affect
    a portfolio return on the day they became observable.
    """
    required = {"date", "ticker", "sector", "sentiment_score"}
    missing = required.difference(scores.columns)
    if missing:
        raise ValueError(f"scores is missing required columns: {sorted(missing)}")

    calendar = pd.DatetimeIndex(
        pd.to_datetime(trading_calendar, utc=True).tz_convert(None).normalize()
    ).drop_duplicates().sort_values()
    if calendar.empty:
        raise ValueError("trading_calendar must contain at least one date")

    aligned = scores.copy()
    aligned["date"] = (
        pd.to_datetime(aligned["date"], utc=True).dt.tz_convert(None).dt.normalize()
    )
    positions = calendar.searchsorted(aligned["date"], side="left")
    valid = positions < len(calendar)
    aligned = aligned.loc[valid].copy()
    positions = positions[valid]

    # `positions + 1` is the explicit one-trading-day availability lag.
    has_lagged_day = positions + 1 < len(calendar)
    aligned = aligned.loc[has_lagged_day].copy()
    aligned["date"] = calendar.take(positions[has_lagged_day] + 1).to_numpy()

    ticker_day = (
        aligned.groupby(["date", "sector", "ticker"], as_index=False)
        .agg(sentiment_score=("sentiment_score", "mean"),
             headline_count=("sentiment_score", "size"))
    )
    sector_day = (
        ticker_day.groupby(["date", "sector"], as_index=False)
        .agg(sentiment_index=("sentiment_score", "mean"),
             headline_count=("headline_count", "sum"),
             ticker_count=("ticker", "nunique"))
        .sort_values(["date", "sector"])
        .reset_index(drop=True)
    )
    return sector_day


def build_sector_sentiment_index(
    headlines: pd.DataFrame, trading_calendar: pd.DatetimeIndex
) -> pd.DataFrame:
    """Clean, score, calendar-align, lag, and aggregate raw headlines."""
    required = {"ticker", "date", "title", "sector"}
    missing = required.difference(headlines.columns)
    if missing:
        raise ValueError(f"headlines is missing required columns: {sorted(missing)}")

    clean = headlines.loc[:, ["ticker", "date", "title", "sector"]].copy()
    clean["date"] = pd.to_datetime(clean["date"], utc=True)
    clean = clean.dropna(subset=["ticker", "date", "title", "sector"])
    clean = clean.loc[clean["title"].astype(str).str.strip().ne("")]
    # Preserve title text; only exact duplicates under the required key vanish.
    clean = clean.drop_duplicates(subset=["ticker", "date", "title"])
    return sector_sentiment_index(score_headlines(clean), trading_calendar)
