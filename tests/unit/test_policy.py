from astro.decision_engine.policy import (
    apply_model_governance,
    apply_model_governance_detailed,
    should_skip_research_debate,
    should_upgrade_fast_to_full,
)
from astro.decision_engine.state_manager import ModelPrediction


def test_governance_hold_when_low_edge():
    m = ModelPrediction(p_up=0.52, uncertainty=0.1)
    cfg = {
        "enabled": True,
        "min_edge_for_directional": 0.08,
        "allow_llm_only_without_model": False,
        "agents_can_override_direction": False,
    }
    assert apply_model_governance("BUY", m, cfg) == "HOLD"
    _, meta = apply_model_governance_detailed("BUY", m, cfg)
    assert meta["reason"] == "below_min_edge_weak_hold"
    assert meta["edge_achieved"] == abs(0.52 - 0.5)


def test_governance_model_wins_when_no_override():
    m = ModelPrediction(p_up=0.85, uncertainty=0.1)
    cfg = {
        "enabled": True,
        "min_edge_for_directional": 0.08,
        "allow_llm_only_without_model": False,
        "agents_can_override_direction": False,
    }
    assert apply_model_governance("SELL", m, cfg) == "BUY"
    _, meta = apply_model_governance_detailed("SELL", m, cfg)
    assert meta["reason"] == "model_primary_no_override"


def test_governance_weak_band_uses_llm_when_enabled():
    m = ModelPrediction(p_up=0.55, uncertainty=0.1)
    cfg = {
        "enabled": True,
        "min_edge_for_directional": 0.08,
        "min_edge_weak": 0.03,
        "allow_llm_in_weak_band": True,
        "allow_llm_only_without_model": False,
        "agents_can_override_direction": False,
    }
    sig, meta = apply_model_governance_detailed("SELL", m, cfg)
    assert meta["edge_band"] == "weak"
    assert sig == "SELL"
    assert meta["reason"] == "weak_band_llm_direction"


def test_governance_detailed_no_model():
    cfg = {
        "enabled": True,
        "min_edge_for_directional": 0.08,
        "allow_llm_only_without_model": False,
        "agents_can_override_direction": False,
    }
    sig, meta = apply_model_governance_detailed("BUY", None, cfg)
    assert sig == "HOLD"
    assert meta["reason"] == "no_model_forced_hold"


def test_upgrade_fast_to_full_on_uncertainty():
    agents = {"uncertainty_debate_threshold": 0.1}
    m = ModelPrediction(p_up=0.6, uncertainty=0.5)
    assert should_upgrade_fast_to_full(m, agents) is True
    assert should_upgrade_fast_to_full(None, agents) is False


def test_skip_debate_when_certain():
    agents = {"skip_debate_if_certain": True, "uncertainty_certainty_max": 0.1}
    m = ModelPrediction(p_up=0.9, uncertainty=0.01)
    assert should_skip_research_debate(m, agents) is True
