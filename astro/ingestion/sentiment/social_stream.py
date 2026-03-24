from __future__ import annotations

import asyncio
from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class SocialPost:
    posted_at: datetime
    text: str
    symbol: Optional[str] = None


class SocialStream:
    def __init__(self, queue: Optional[asyncio.Queue] = None):
        self.queue = queue or asyncio.Queue(maxsize=2000)

    async def publish(self, post: SocialPost) -> None:
        await self.queue.put(post)
