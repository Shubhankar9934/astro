import pandas as pd

from astro.features.validation import validate_fused_frame


def test_validate_fused_ok():
    df = pd.DataFrame(
        {
            "Date": pd.date_range("2020-01-01", periods=3),
            "open": [1, 2, 3],
            "high": [1, 2, 3],
            "low": [1, 2, 3],
            "close": [1, 2, 3],
            "volume": [1, 2, 3],
            "ret_1": [0, 0, 0],
            "rsi_14": [50, 50, 50],
            "macd": [0, 0, 0],
            "macds": [0, 0, 0],
            "news_event_count": [0.0, 0.0, 0.0],
            "sentiment_score": [0.0, 0.0, 0.0],
        }
    )
    rep = validate_fused_frame(df, "fused_v1")
    assert rep.ok
    assert not rep.errors


def test_validate_fused_missing_column():
    df = pd.DataFrame({"Date": [1], "close": [1]})
    rep = validate_fused_frame(df, "fused_v1")
    assert not rep.ok
    assert rep.errors
