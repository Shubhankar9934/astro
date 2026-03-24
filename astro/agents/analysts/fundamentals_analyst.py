from __future__ import annotations

from typing import Any, Dict

from astro.agents.shared.grounding import GROUNDING_PREFIX
from astro.decision_engine.state_manager import DecisionContext

STUB_NO_FUNDAMENTALS = """## Fundamentals (fused features only)

Fundamental ratios and filings are not present in fused features for this run. Do not infer P/E, growth, or balance-sheet metrics from general knowledge.

**Action:** Treat fundamentals as unknown for decision purposes.
"""


def create_fundamentals_analyst(llm):
    def node(state: Dict[str, Any]) -> Dict[str, Any]:
        ticker = state["company_of_interest"]
        current_date = state["trade_date"]
        ctx: DecisionContext | None = state.get("astro_context")
        data = (
            ctx.fundamentals_summary
            if ctx
            else "(No fundamental data wired; state assumptions explicitly.)"
        )
        if data.startswith("(Fundamentals:") or data.startswith("(No fundamental"):
            return {"fundamentals_report": STUB_NO_FUNDAMENTALS}
        if ctx and ctx.extra.get("fundamentals_has_evidence") is False:
            return {"fundamentals_report": STUB_NO_FUNDAMENTALS}
        prompt = f"""{GROUNDING_PREFIX}
You are a fundamentals analyst for {ticker} as of {current_date}.
Using ONLY the summary below, write a fundamentals report. End with a Markdown table.

DATA:
{data}
"""
        response = llm.invoke(prompt)
        return {"fundamentals_report": response.content}

    return node
