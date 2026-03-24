from astro.agents.trader.signal_generator import extract_signal_from_text


def test_extract_signal():
    assert extract_signal_from_text("FINAL TRANSACTION PROPOSAL: **BUY**") == "BUY"
    assert extract_signal_from_text("We recommend HOLD for now") == "HOLD"
