from __future__ import annotations

from dataclasses import dataclass, field, replace
from typing import Any, Dict, List, Optional

# InvestDebateState / RiskDebateState kept for typing docs; runtime uses dicts on AstroState


@dataclass
class ModelPrediction:
    p_up: float = 0.5
    expected_return: float = 0.0
    uncertainty: float = 0.0
    raw: Dict[str, Any] = field(default_factory=dict)


@dataclass
class DecisionContext:
    """Typed snapshot passed to agents (built by ingestion + pipelines)."""

    symbol: str
    as_of: str
    market_summary: str = ""
    sentiment_summary: str = ""
    news_summary: str = ""
    fundamentals_summary: str = ""
    feature_version: str = ""
    bar_timestamp: str = ""
    model: Optional[ModelPrediction] = None
    extra: Dict[str, Any] = field(default_factory=dict)


@dataclass
class InvestDebateState:
    bull_history: str = ""
    bear_history: str = ""
    history: str = ""
    current_response: str = ""
    judge_decision: str = ""
    count: int = 0


@dataclass
class RiskDebateState:
    aggressive_history: str = ""
    conservative_history: str = ""
    neutral_history: str = ""
    history: str = ""
    latest_speaker: str = ""
    current_aggressive_response: str = ""
    current_conservative_response: str = ""
    current_neutral_response: str = ""
    judge_decision: str = ""
    count: int = 0


@dataclass
class AstroState:
    company_of_interest: str
    trade_date: str
    context: DecisionContext
    messages: List[Any] = field(default_factory=list)
    sender: str = ""
    market_report: str = ""
    sentiment_report: str = ""
    news_report: str = ""
    fundamentals_report: str = ""
    macro_report: str = ""
    # Mutable dicts mirror LangGraph AgentState for agent node compatibility
    investment_debate_state: Dict[str, Any] = field(default_factory=dict)
    investment_plan: str = ""
    trader_investment_plan: str = ""
    risk_debate_state: Dict[str, Any] = field(default_factory=dict)
    final_trade_decision: str = ""

    def with_updates(self, **kwargs: Any) -> "AstroState":
        return replace(self, **kwargs)

    def as_dict(self) -> Dict[str, Any]:
        from dataclasses import asdict

        d = asdict(self)
        return d


def initial_invest_debate() -> Dict[str, Any]:
    return {
        "bull_history": "",
        "bear_history": "",
        "history": "",
        "current_response": "",
        "judge_decision": "",
        "count": 0,
    }


def initial_risk_debate() -> Dict[str, Any]:
    return {
        "aggressive_history": "",
        "conservative_history": "",
        "neutral_history": "",
        "history": "",
        "latest_speaker": "",
        "current_aggressive_response": "",
        "current_conservative_response": "",
        "current_neutral_response": "",
        "judge_decision": "",
        "count": 0,
    }
