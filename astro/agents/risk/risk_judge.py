from __future__ import annotations

from typing import Any, Dict

from astro.agents.shared.memory import FinancialSituationMemory


def create_risk_judge(llm, memory: FinancialSituationMemory):
    def risk_manager_node(state: Dict[str, Any]) -> Dict[str, Any]:
        history = state["risk_debate_state"]["history"]
        risk_debate_state = state["risk_debate_state"]
        trader_plan = state["investment_plan"]
        mr = state.get("macro_report", "")
        mx = f"\n\nMacro (external knowledge allowed): {mr}" if mr else ""
        curr_situation = f"{state['market_report']}\n\n{state['sentiment_report']}\n\n{state['news_report']}\n\n{state['fundamentals_report']}{mx}"
        past_memories = memory.get_memories(curr_situation, n_matches=2)
        past_memory_str = "\n\n".join(rec["recommendation"] for rec in past_memories)
        prompt = f"""Risk Management Judge: decide Buy, Sell, or Hold with clear rationale.
Trader original plan: {trader_plan}
Past reflections: {past_memory_str}
Risk debate:
{history}
"""
        response = llm.invoke(prompt)
        new_risk_debate_state = {
            "judge_decision": response.content,
            "history": risk_debate_state["history"],
            "aggressive_history": risk_debate_state["aggressive_history"],
            "conservative_history": risk_debate_state["conservative_history"],
            "neutral_history": risk_debate_state["neutral_history"],
            "latest_speaker": "Judge",
            "current_aggressive_response": risk_debate_state["current_aggressive_response"],
            "current_conservative_response": risk_debate_state["current_conservative_response"],
            "current_neutral_response": risk_debate_state["current_neutral_response"],
            "count": risk_debate_state["count"],
        }
        return {
            "risk_debate_state": new_risk_debate_state,
            "final_trade_decision": response.content,
        }

    return risk_manager_node
