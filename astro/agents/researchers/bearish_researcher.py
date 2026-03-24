from __future__ import annotations

from typing import Any, Dict

from astro.agents.shared.memory import FinancialSituationMemory


def create_bearish_researcher(llm, memory: FinancialSituationMemory):
    def bear_node(state: Dict[str, Any]) -> Dict[str, Any]:
        investment_debate_state = state["investment_debate_state"]
        history = investment_debate_state.get("history", "")
        bear_history = investment_debate_state.get("bear_history", "")
        current_response = investment_debate_state.get("current_response", "")
        market_research_report = state["market_report"]
        sentiment_report = state["sentiment_report"]
        news_report = state["news_report"]
        fundamentals_report = state["fundamentals_report"]
        macro_report = state.get("macro_report", "")
        mx = f"\n\nMacro (external knowledge allowed): {macro_report}" if macro_report else ""
        curr_situation = f"{market_research_report}\n\n{sentiment_report}\n\n{news_report}\n\n{fundamentals_report}{mx}"
        past_memories = memory.get_memories(curr_situation, n_matches=2)
        past_memory_str = "\n\n".join(rec["recommendation"] for rec in past_memories)
        prompt = f"""You are a Bear Analyst arguing against investing. Emphasize risks and weaknesses.
Resources:
Market: {market_research_report}
Sentiment: {sentiment_report}
News: {news_report}
Fundamentals: {fundamentals_report}
Macro: {macro_report or "(none)"}
Debate history: {history}
Last bull argument: {current_response}
Past reflections: {past_memory_str}
"""
        response = llm.invoke(prompt)
        argument = f"Bear Analyst: {response.content}"
        new_state = {
            "history": history + "\n" + argument,
            "bear_history": bear_history + "\n" + argument,
            "bull_history": investment_debate_state.get("bull_history", ""),
            "current_response": argument,
            "judge_decision": investment_debate_state.get("judge_decision", ""),
            "count": investment_debate_state["count"] + 1,
        }
        return {"investment_debate_state": new_state}

    return bear_node
