from __future__ import annotations

import functools
from typing import Any, Dict

from astro.agents.shared.memory import FinancialSituationMemory


def create_trader_agent(llm, memory: FinancialSituationMemory):
    def trader_node(state: Dict[str, Any], name: str) -> Dict[str, Any]:
        company_name = state["company_of_interest"]
        investment_plan = state["investment_plan"]
        market_research_report = state["market_report"]
        sentiment_report = state["sentiment_report"]
        news_report = state["news_report"]
        fundamentals_report = state["fundamentals_report"]
        macro_report = state.get("macro_report", "")
        mx = f"\n\nMacro (external knowledge allowed): {macro_report}" if macro_report else ""
        curr_situation = f"{market_research_report}\n\n{sentiment_report}\n\n{news_report}\n\n{fundamentals_report}{mx}"
        past_memories = memory.get_memories(curr_situation, n_matches=2)
        past_memory_str = (
            "\n\n".join(rec["recommendation"] for rec in past_memories)
            if past_memories
            else "No past memories found."
        )
        model_hint = ""
        ctx = state.get("astro_context")
        if ctx and ctx.model:
            model_hint = f"Transformer p(up)={ctx.model.p_up:.4f}. "
        messages = [
            {
                "role": "system",
                "content": f"""You are a trading agent. {model_hint}Use past lessons: {past_memory_str}
Conclude with FINAL TRANSACTION PROPOSAL: **BUY/HOLD/SELL**.""",
            },
            {
                "role": "user",
                "content": f"Investment plan for {company_name}:\n{investment_plan}",
            },
        ]
        result = llm.invoke(messages)
        return {
            "trader_investment_plan": result.content,
            "sender": name,
        }

    return functools.partial(trader_node, name="Trader")
