from __future__ import annotations

from typing import Any, Dict

from astro.agents.shared.grounding import GROUNDING_PREFIX
from astro.decision_engine.state_manager import DecisionContext


def create_technical_analyst(llm, *, structured_json: bool = False):
    def node(state: Dict[str, Any]) -> Dict[str, Any]:
        ticker = state["company_of_interest"]
        current_date = state["trade_date"]
        ctx: DecisionContext | None = state.get("astro_context")
        base = ""
        if ctx:
            base = ctx.market_summary
            if ctx.model:
                base += f"\n\nStructured model signal: p(up)={ctx.model.p_up:.4f}"
        struct = ""
        if structured_json:
            struct = """
Output format (mandatory):
1) First, a single fenced JSON code block named structured_technical with ONLY numeric fields that appear in DATA / STRUCTURED_FACTS (no invented keys).
2) Then your Markdown narrative must not introduce numbers absent from that JSON.
"""
        prompt = f"""{GROUNDING_PREFIX}
{struct}You are a trading assistant analyzing technical market conditions for {ticker} as of {current_date}.
Use ONLY the data below (pre-computed from the data pipeline). Write a detailed report on trends, momentum, volatility, and key levels. End with a Markdown table summarizing main points.

DATA:
{base or "(No market feature summary available.)"}
"""
        response = llm.invoke(prompt)
        return {"market_report": response.content}

    return node
