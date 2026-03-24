from __future__ import annotations

"""Shared LLM grounding rules for analyst prompts (quant / auditability)."""

GROUNDING_PREFIX = """Grounding rules (mandatory):
- Use ONLY facts that appear in the DATA section below. Do not cite P/E, EPS, revenue, macro indicators, or news headlines unless they appear verbatim or as explicit numeric fields in DATA.
- If a metric is not listed in DATA, write exactly: "Not in fused features."
- Do not fill gaps with general financial knowledge or assumed current events.
"""

STUB_NO_SENTIMENT_EVIDENCE = """## Sentiment (fused features only)

No usable sentiment aggregate in fused features for this as-of date (missing pipeline output or zero/neutral tail). Do not infer social or retail sentiment from general knowledge.

**Action:** Treat sentiment as unknown for decision purposes.
"""

STUB_NO_NEWS_EVIDENCE = """## News intensity (fused features only)

No usable news-event aggregate in fused features (missing pipeline output or zero tail). Do not cite specific headlines or macro events unless provided in DATA.

**Action:** Treat news flow as unknown for decision purposes.
"""
