from __future__ import annotations

from typing import Any, Dict


def create_conservative_debator(llm):
    def conservative_node(state: Dict[str, Any]) -> Dict[str, Any]:
        risk_debate_state = state["risk_debate_state"]
        history = risk_debate_state.get("history", "")
        conservative_history = risk_debate_state.get("conservative_history", "")
        current_aggressive_response = risk_debate_state.get("current_aggressive_response", "")
        current_neutral_response = risk_debate_state.get("current_neutral_response", "")
        trader_decision = state["trader_investment_plan"]
        prompt = f"""Conservative Risk Analyst: prioritize capital preservation; counter aggressive/neutral.
Trader plan: {trader_decision}
Market: {state['market_report']}
Sentiment: {state['sentiment_report']}
News: {state['news_report']}
Fundamentals: {state['fundamentals_report']}
Macro: {state.get('macro_report', '') or '(none)'}
History: {history}
Aggressive last: {current_aggressive_response}
Neutral last: {current_neutral_response}
"""
        response = llm.invoke(prompt)
        argument = f"Conservative Analyst: {response.content}"
        new_risk_debate_state = {
            "history": history + "\n" + argument,
            "aggressive_history": risk_debate_state.get("aggressive_history", ""),
            "conservative_history": conservative_history + "\n" + argument,
            "neutral_history": risk_debate_state.get("neutral_history", ""),
            "latest_speaker": "Conservative",
            "current_aggressive_response": risk_debate_state.get("current_aggressive_response", ""),
            "current_conservative_response": argument,
            "current_neutral_response": risk_debate_state.get("current_neutral_response", ""),
            "count": risk_debate_state["count"] + 1,
        }
        return {"risk_debate_state": new_risk_debate_state}

    return conservative_node
