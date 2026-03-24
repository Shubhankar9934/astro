from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query

from astro.api.dependencies import get_feature_service

router = APIRouter(prefix="/data", tags=["data"])


@router.get("/features")
def get_features(symbol: str = Query(...), timeframe: str = Query("1d")):
    fs = get_feature_service()
    try:
        row = fs.latest_feature_row(symbol)
    except FileNotFoundError as e:
        raise HTTPException(404, str(e)) from e
    return {"symbol": symbol, "timeframe": timeframe, "features": row}


@router.get("/market")
def get_market(symbol: str = Query(...)):
    fs = get_feature_service()
    try:
        df = fs.load_fused(symbol)
    except FileNotFoundError as e:
        raise HTTPException(404, str(e)) from e
    tail = df.tail(20)
    records = tail.to_dict(orient="records")
    for r in records:
        for k, v in list(r.items()):
            if hasattr(v, "isoformat"):
                r[k] = v.isoformat()
    return {"symbol": symbol, "bars": records}
