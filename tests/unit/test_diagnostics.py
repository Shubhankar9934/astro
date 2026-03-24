import pandas as pd

from astro.features.diagnostics import correlation_report


def test_correlation_report_flags_high_corr():
    df = pd.DataFrame({"a": [1, 2, 3, 4, 5], "b": [1.01, 2.01, 3.01, 4.01, 5.01]})
    rep = correlation_report(df, ["a", "b"], max_corr=0.95)
    assert rep["ok"] is False
    assert len(rep["pairs"]) >= 1


def test_correlation_report_ok_on_low_corr():
    df = pd.DataFrame(
        {
            "a": [1.0, 0.2, 0.8, 0.1, 0.9, 0.3, 0.7, 0.4, 0.6, 0.5],
            "b": [0.5, 0.9, 0.1, 0.7, 0.2, 0.8, 0.3, 0.6, 0.4, 0.55],
        }
    )
    rep = correlation_report(df, ["a", "b"], max_corr=0.95)
    assert rep["ok"] is True
