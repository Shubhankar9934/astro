from __future__ import annotations

import re
from typing import Literal, Optional

Signal = Literal["BUY", "SELL", "HOLD"]


def extract_signal_from_text(text: str) -> Signal:
    t = text.upper()
    m = re.search(
        r"FINAL\s+TRANSACTION\s+PROPOSAL:\s*\*\*(BUY|SELL|HOLD)\*\*",
        t,
        re.I,
    )
    if m:
        return m.group(1).upper()  # type: ignore[return-value]
    if re.search(r"\bSELL\b", t) and not re.search(r"\b(BUY|HOLD)\b", t):
        return "SELL"
    if re.search(r"\bBUY\b", t) and not re.search(r"\b(SELL|HOLD)\b", t):
        return "BUY"
    if re.search(r"\bHOLD\b", t):
        return "HOLD"
    return "HOLD"


def refine_signal_with_llm(llm, full_signal: str) -> str:
    messages = [
        (
            "system",
            "Extract only BUY, SELL, or HOLD from the text. Output a single word.",
        ),
        ("human", full_signal),
    ]
    return llm.invoke(messages).content.strip().upper()
