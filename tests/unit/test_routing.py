from astro.decision_engine.routing import should_continue_debate, should_continue_risk_analysis


def test_debate_routes():
    st = {
        "investment_debate_state": {
            "count": 0,
            "current_response": "",
        }
    }
    assert should_continue_debate(st, max_debate_rounds=1) == "Bull Researcher"
    st["investment_debate_state"]["current_response"] = "Bull Analyst: x"
    assert should_continue_debate(st, max_debate_rounds=1) == "Bear Researcher"
    st["investment_debate_state"]["count"] = 2
    assert should_continue_debate(st, max_debate_rounds=1) == "Research Manager"


def test_risk_routes():
    st = {"risk_debate_state": {"count": 0, "latest_speaker": ""}}
    assert should_continue_risk_analysis(st, max_risk_discuss_rounds=1) == "Aggressive Analyst"
    st["risk_debate_state"]["latest_speaker"] = "Aggressive"
    assert should_continue_risk_analysis(st, max_risk_discuss_rounds=1) == "Conservative Analyst"
    st["risk_debate_state"]["latest_speaker"] = "Conservative"
    assert should_continue_risk_analysis(st, max_risk_discuss_rounds=1) == "Neutral Analyst"
    st["risk_debate_state"]["latest_speaker"] = "Neutral"
    assert should_continue_risk_analysis(st, max_risk_discuss_rounds=1) == "Aggressive Analyst"
    st["risk_debate_state"]["count"] = 3
    assert should_continue_risk_analysis(st, max_risk_discuss_rounds=1) == "Risk Judge"
