from __future__ import annotations

"""Sentiment pipeline: produce coarse daily scores / trends for fusion, not token-level feeds."""

from pathlib import Path

import pandas as pd

from astro.ingestion.sentiment.sentiment_parser import lexical_sentiment_score


def daily_sentiment_from_text_rows(
    rows: list[tuple[pd.Timestamp, str]], feature_dates: pd.Series
) -> pd.DataFrame:
    """rows: (timestamp, text) pairs aggregated to mean score per day."""
    if not rows:
        return pd.DataFrame(
            {
                "Date": pd.to_datetime(feature_dates).dt.normalize(),
                "sentiment_score": 0.0,
            }
        )
    df = pd.DataFrame(rows, columns=["ts", "text"])
    df["Date"] = pd.to_datetime(df["ts"]).dt.normalize()
    df["sentiment_score"] = df["text"].map(lexical_sentiment_score)
    g = df.groupby("Date", as_index=False)["sentiment_score"].mean()
    full = pd.DataFrame({"Date": pd.to_datetime(feature_dates).dt.normalize()})
    return full.merge(g, on="Date", how="left").assign(
        sentiment_score=lambda x: x["sentiment_score"].fillna(0.0)
    )
