from __future__ import annotations

import asyncio
import logging
import os
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple


def _restore_attr_patches(stack: List[Tuple[Any, str, Any]]) -> None:
    while stack:
        mod, attr, old = stack.pop()
        setattr(mod, attr, old)


def _push_attr_patch(
    stack: List[Tuple[Any, str, Any]], mod: Any, attr: str, value: Any
) -> None:
    stack.append((mod, attr, getattr(mod, attr)))
    setattr(mod, attr, value)


def describe_ibkr_connect_failure(
    exc: BaseException, *, host: str, port: int, timeout_s: float
) -> str:
    """Human-readable message; TimeoutError often has an empty str() in Python 3."""
    if isinstance(exc, TimeoutError):
        detail = str(exc).strip()
        if detail:
            return f"{detail} (API timeout budget {timeout_s:g}s, {host}:{port})"
        return (
            f"Timed out after {timeout_s:g}s connecting to {host}:{port}. "
            "Start IB Gateway (or TWS), enable API sockets, and match the port "
            "(IB Gateway: paper 4002, live 4001; TWS: paper 7497, live 7496)."
        )
    text = str(exc).strip()
    return text if text else repr(exc)


class IBKRNotInstalledError(ImportError):
    pass


def _require_ib():
    try:
        from ib_async import IB  # type: ignore
    except ImportError as e:
        raise IBKRNotInstalledError(
            "ib_async is required for IBKR. Install with: pip install astro-trading[ibkr]"
        ) from e
    return IB


@dataclass
class IBKRConnectionConfig:
    host: str = "127.0.0.1"
    port: int = 7497
    client_id: int = 1
    paper: bool = True
    read_only: bool = False
    # Seconds for TCP + API handshake; 0 = no limit (ib_async default).
    connect_timeout: float = 45.0

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "IBKRConnectionConfig":
        return cls(
            host=str(d.get("host", "127.0.0.1")),
            port=int(d.get("port", 7497)),
            client_id=int(d.get("client_id", 1)),
            paper=bool(d.get("paper", True)),
            read_only=bool(d.get("read_only", False)),
            connect_timeout=float(d.get("connect_timeout", 45.0)),
        )


def _bind_eventkit_to_running_loop(
    running: asyncio.AbstractEventLoop, stack: List[Tuple[Any, str, Any]]
) -> None:
    """eventkit.event binds get_event_loop at import time to the policy loop, not uvicorn's."""
    import eventkit.event as ev_event
    import eventkit.util as ev_util

    def ev_get_loop() -> asyncio.AbstractEventLoop:
        try:
            return asyncio.get_running_loop()
        except RuntimeError:
            return running

    _push_attr_patch(stack, ev_util, "get_event_loop", ev_get_loop)
    _push_attr_patch(stack, ev_event, "get_event_loop", ev_get_loop)


class IBKRClient:
    """Connection manager for TWS / IB Gateway (ib_async)."""

    def __init__(self, cfg: IBKRConnectionConfig):
        self.cfg = cfg
        self._ib: Any = None
        self._eventkit_patch_stack: Optional[List[Tuple[Any, str, Any]]] = None

    def connect(self) -> Any:
        IB = _require_ib()
        if self._ib is None:
            self._ib = IB()
        if not self._ib.isConnected():
            self._ib.connect(
                self.cfg.host,
                self.cfg.port,
                clientId=self.cfg.client_id,
                timeout=self.cfg.connect_timeout or 0,
                readonly=self.cfg.read_only,
            )
        return self._ib

    async def connect_async(self) -> Any:
        """Connect on uvicorn's loop; sync ib.connect() cannot run inside a running loop."""
        IB = _require_ib()
        if self._ib is None:
            self._ib = IB()
        if not self._ib.isConnected():
            if os.environ.get("ASTRO_IBKR_DEBUG", "").lower() in ("1", "true", "yes"):
                from ib_async import util as ib_util

                ib_util.logToConsole(logging.DEBUG)

            running = asyncio.get_running_loop()
            stack: List[Tuple[Any, str, Any]] = []
            _bind_eventkit_to_running_loop(running, stack)

            try:
                await self._ib.connectAsync(
                    self.cfg.host,
                    self.cfg.port,
                    clientId=self.cfg.client_id,
                    timeout=self.cfg.connect_timeout or None,
                    readonly=self.cfg.read_only,
                )
            except BaseException:
                _restore_attr_patches(stack)
                raise
            self._eventkit_patch_stack = stack
        return self._ib

    def disconnect(self) -> None:
        if self._ib and self._ib.isConnected():
            self._ib.disconnect()
        if self._eventkit_patch_stack:
            _restore_attr_patches(self._eventkit_patch_stack)
            self._eventkit_patch_stack = None

    @property
    def ib(self) -> Any:
        if self._ib is None:
            return self.connect()
        return self._ib
