from __future__ import annotations

from typing import Any, Dict, Literal

RiskNext = Literal[
    "Aggressive Analyst",
    "Conservative Analyst",
    "Neutral Analyst",
    "Risk Judge",
]
DebateNext = Literal["Bull Researcher", "Bear Researcher", "Research Manager"]


def should_continue_debate(
    state: Dict[str, Any], max_debate_rounds: int
) -> DebateNext:
    d = state["investment_debate_state"]
    if d["count"] >= 2 * max_debate_rounds:
        return "Research Manager"
    if d.get("current_response", "").startswith("Bull"):
        return "Bear Researcher"
    return "Bull Researcher"


def should_continue_risk_analysis(
    state: Dict[str, Any], max_risk_discuss_rounds: int
) -> RiskNext:
    d = state["risk_debate_state"]
    if d["count"] >= 3 * max_risk_discuss_rounds:
        return "Risk Judge"
    sp = d.get("latest_speaker", "")
    if sp.startswith("Aggressive"):
        return "Conservative Analyst"
    if sp.startswith("Conservative"):
        return "Neutral Analyst"
    return "Aggressive Analyst"
