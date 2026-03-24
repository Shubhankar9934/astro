from __future__ import annotations

from typing import Any, Dict


def create_aggressive_debator(llm):
    def aggressive_node(state: Dict[str, Any]) -> Dict[str, Any]:
        risk_debate_state = state["risk_debate_state"]
        history = risk_debate_state.get("history", "")
        aggressive_history = risk_debate_state.get("aggressive_history", "")
        current_conservative_response = risk_debate_state.get("current_conservative_response", "")
        current_neutral_response = risk_debate_state.get("current_neutral_response", "")
        trader_decision = state["trader_investment_plan"]
        prompt = f"""Aggressive Risk Analyst: champion upside; critique conservative/neutral views.
Trader plan: {trader_decision}
Market: {state['market_report']}
Sentiment: {state['sentiment_report']}
News: {state['news_report']}
Fundamentals: {state['fundamentals_report']}
Macro: {state.get('macro_report', '') or '(none)'}
History: {history}
Conservative last: {current_conservative_response}
Neutral last: {current_neutral_response}
"""
        response = llm.invoke(prompt)
        argument = f"Aggressive Analyst: {response.content}"
        new_risk_debate_state = {
            "history": history + "\n" + argument,
            "aggressive_history": aggressive_history + "\n" + argument,
            "conservative_history": risk_debate_state.get("conservative_history", ""),
            "neutral_history": risk_debate_state.get("neutral_history", ""),
            "latest_speaker": "Aggressive",
            "current_aggressive_response": argument,
            "current_conservative_response": risk_debate_state.get("current_conservative_response", ""),
            "current_neutral_response": risk_debate_state.get("current_neutral_response", ""),
            "count": risk_debate_state["count"] + 1,
        }
        return {"risk_debate_state": new_risk_debate_state}

    return aggressive_node
