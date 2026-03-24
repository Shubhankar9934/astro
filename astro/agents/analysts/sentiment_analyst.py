from __future__ import annotations

from typing import Any, Dict

from astro.agents.shared.grounding import GROUNDING_PREFIX, STUB_NO_SENTIMENT_EVIDENCE
from astro.decision_engine.state_manager import DecisionContext


def create_sentiment_analyst(llm):
    def node(state: Dict[str, Any]) -> Dict[str, Any]:
        ticker = state["company_of_interest"]
        current_date = state["trade_date"]
        ctx: DecisionContext | None = state.get("astro_context")
        if ctx is None:
            return {"sentiment_report": STUB_NO_SENTIMENT_EVIDENCE}
        real_ev = ctx.extra.get("sentiment_has_evidence")
        proxy_ev = ctx.extra.get("sentiment_proxy_has_evidence")
        if ctx.sentiment_summary.startswith("(No sentiment pipeline run.)") and not proxy_ev:
            return {"sentiment_report": STUB_NO_SENTIMENT_EVIDENCE}
        if real_ev is False and not proxy_ev:
            return {"sentiment_report": STUB_NO_SENTIMENT_EVIDENCE}
        data = ctx.sentiment_summary
        proxy_only = ""
        if real_ev is False and proxy_ev:
            proxy_only = "IMPORTANT: No real sentiment aggregates — only technical momentum proxy fields. Do NOT infer social/retail sentiment.\n"
        prompt = f"""{GROUNDING_PREFIX}
{proxy_only}You are a social/sentiment analyst for {ticker} as of {current_date}.
Using ONLY the pipeline summary below (fused feature aggregates), write a concise report. If the signal is neutral or near zero, say so explicitly. End with a Markdown table.

PIPELINE SUMMARY:
{data}
"""
        response = llm.invoke(prompt)
        return {"sentiment_report": response.content}

    return node
