from __future__ import annotations

from typing import Any, Dict

from astro.agents.shared.memory import FinancialSituationMemory


def create_research_synthesizer(llm, memory: FinancialSituationMemory):
    """Portfolio manager / research judge (final research memo)."""

    def research_manager_node(state: Dict[str, Any]) -> Dict[str, Any]:
        history = state["investment_debate_state"].get("history", "")
        market_research_report = state["market_report"]
        sentiment_report = state["sentiment_report"]
        news_report = state["news_report"]
        fundamentals_report = state["fundamentals_report"]
        investment_debate_state = state["investment_debate_state"]
        macro_report = state.get("macro_report", "")
        mx = f"\n\nMacro (external knowledge allowed): {macro_report}" if macro_report else ""
        curr_situation = f"{market_research_report}\n\n{sentiment_report}\n\n{news_report}\n\n{fundamentals_report}{mx}"
        past_memories = memory.get_memories(curr_situation, n_matches=2)
        past_memory_str = "\n\n".join(rec["recommendation"] for rec in past_memories)
        prompt = f"""As portfolio manager, synthesize the bull/bear debate and commit to Buy, Sell, or Hold with rationale and strategic actions.
Past reflections: {past_memory_str}
Debate:
{history}
"""
        response = llm.invoke(prompt)
        new_investment_debate_state = {
            "judge_decision": response.content,
            "history": investment_debate_state.get("history", ""),
            "bear_history": investment_debate_state.get("bear_history", ""),
            "bull_history": investment_debate_state.get("bull_history", ""),
            "current_response": response.content,
            "count": investment_debate_state["count"],
        }
        return {
            "investment_debate_state": new_investment_debate_state,
            "investment_plan": response.content,
        }

    return research_manager_node
