from __future__ import annotations

from typing import Any, Dict

from astro.decision_engine.state_manager import DecisionContext


def create_macro_analyst(llm):
    """Optional analyst: may use general macro knowledge; not grounded in fused features."""

    def node(state: Dict[str, Any]) -> Dict[str, Any]:
        ticker = state["company_of_interest"]
        current_date = state["trade_date"]
        ctx: DecisionContext | None = state.get("astro_context")
        sym_ctx = f"Symbol: {ticker}, as_of: {current_date}."
        if ctx and ctx.market_summary:
            sym_ctx += "\n\nFused feature digest (for context only; you may discuss broader macro not in this list):\n" + ctx.market_summary[
                :4000
            ]
        prompt = f"""You are a macro / cross-asset analyst. External knowledge and current macro narratives are ALLOWED here.
Clearly label opinions vs facts. Do not claim specific numbers for {ticker} unless sourced from the digest below.
Write a short macro backdrop for traders. End with a Markdown table.

{sym_ctx}
"""
        response = llm.invoke(prompt)
        return {"macro_report": response.content}

    return node
