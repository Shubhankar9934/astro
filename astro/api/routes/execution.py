from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request

from astro.api.dependencies import ROOT, get_config, require_api_key
from astro.api.schemas.requests import ExecutionOrderRequest
from astro.execution.order_manager import OrderManager
from astro.execution.trade_executor import TradeExecutor
from astro.ingestion.ibkr.client import IBKRClient, IBKRConnectionConfig

router = APIRouter(prefix="/execution", tags=["execution"])


@router.post("/order")
def place_order(
    req: ExecutionOrderRequest,
    request: Request,
    _: None = Depends(require_api_key),
):
    cfg = get_config()
    if not cfg.ibkr.get("paper", True):
        raise HTTPException(403, "Live trading disabled via API in this build; use paper=true in ibkr.yaml")
    try:
        client = getattr(request.app.state, "ibkr_client", None)
        if client is None:
            ic = IBKRConnectionConfig.from_dict(cfg.ibkr)
            client = IBKRClient(ic)
            client.connect()
        ex = TradeExecutor(client)
        db_path = cfg.data_root_path(ROOT) / "cache" / "astro_meta.sqlite"
        db_path.parent.mkdir(parents=True, exist_ok=True)
        from astro.storage.database import MetadataDB

        om = OrderManager(ex, db_path)
        trade = om.submit_market(
            req.idempotency_key, req.symbol, req.action, req.quantity
        )
        if trade is None:
            return {"status": "duplicate", "idempotency_key": req.idempotency_key}
        return {"status": "submitted", "trade": str(trade)}
    except Exception as e:
        raise HTTPException(503, f"Execution failed: {e}") from e
