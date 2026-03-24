"""Map social text to coarse scores (-1..1)."""


def lexical_sentiment_score(text: str) -> float:
    t = text.lower()
    pos = sum(1 for w in ("great", "beat", "bull", "up", "buy", "growth") if w in t)
    neg = sum(1 for w in ("bad", "miss", "bear", "down", "sell", "lawsuit") if w in t)
    if pos + neg == 0:
        return 0.0
    return (pos - neg) / (pos + neg)
