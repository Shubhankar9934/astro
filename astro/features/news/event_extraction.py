"""Event extraction from headlines (stub for NER / LLM)."""


def headline_keywords(headline: str) -> list[str]:
    return [w for w in headline.split() if len(w) > 4][:5]
