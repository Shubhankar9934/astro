from __future__ import annotations

from typing import Any, Dict, Literal, Optional

from pydantic import BaseModel, Field


class DecisionRequest(BaseModel):
    symbol: str
    trade_date: str
    mode: Optional[Literal["fast", "full"]] = None


class SymbolDateRequest(BaseModel):
    symbol: str
    trade_date: str


class PredictRequest(BaseModel):
    symbol: str


class BacktestRequest(BaseModel):
    fused_path: str
    signal_col: str = "sentiment_score"
    symbol: str = "TEST"


class ExecutionOrderRequest(BaseModel):
    symbol: str
    action: Literal["BUY", "SELL"]
    quantity: float
    idempotency_key: str = Field(..., min_length=4)


class RiskRequest(BaseModel):
    company_of_interest: str
    trade_date: str
    market_report: str = ""
    sentiment_report: str = ""
    news_report: str = ""
    fundamentals_report: str = ""
    investment_plan: str = ""
    trader_investment_plan: str = ""
    astro_context: Optional[Dict[str, Any]] = None


class ExperimentLogRequest(BaseModel):
    model_version: str
    schema_id: str = "fused_v1"
    payload: Dict[str, Any] = Field(default_factory=dict)
