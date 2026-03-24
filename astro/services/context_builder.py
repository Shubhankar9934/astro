from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any, Dict, Optional

import pandas as pd

from astro.decision_engine.state_manager import DecisionContext, ModelPrediction
from astro.features.validation import validate_fused_frame
from astro.models.transformer.inference import load_inference_optional
from astro.services.feature_service import FeatureService
from astro.utils.config_loader import AstroConfig

_DEGENERATE_P_EPS = 1e-3
_DEGENERATE_UNC_MIN = 0.95


def _tail_has_signal(series: pd.Series, n: int = 20) -> bool:
    if series is None or len(series) == 0:
        return False
    t = series.tail(n).astype(float)
    if not t.notna().any():
        return False
    t = t.fillna(0.0)
    return bool((t.abs() > 1e-12).any())


def _structured_market_facts_row(df: pd.DataFrame) -> Dict[str, float]:
    """Numeric last-bar facts for audit / structured analyst prompts."""
    if df is None or len(df) == 0:
        return {}
    row = df.iloc[-1]
    keys = (
        "open",
        "high",
        "low",
        "close",
        "volume",
        "ret_1",
        "rsi_14",
        "macd",
        "macds",
        "atr",
        "sentiment_score",
        "news_event_count",
        "sentiment_proxy_momentum",
        "news_intensity_proxy",
    )
    out: Dict[str, float] = {}
    for k in keys:
        if k not in row.index:
            continue
        try:
            fv = float(row[k])
            if pd.notna(fv) and math.isfinite(fv):
                out[k] = fv
        except (TypeError, ValueError):
            pass
    return out


def _summarize_ohlcv_tail(df: pd.DataFrame, n: int = 5) -> str:
    tail = df.tail(n)
    lines = []
    for _, row in tail.iterrows():
        d = row.get("Date", row.get("date", ""))
        c = row.get("close", row.get("Close", ""))
        lines.append(f"{d}: close={c}")
    return "\n".join(lines)


def build_decision_context(
    symbol: str,
    trade_date: str,
    fused_parquet: Optional[Path],
    *,
    config: Optional[AstroConfig] = None,
    feature_version: str = "1",
    checkpoint: Optional[Path] = None,
    scaler_path: Optional[Path] = None,
    seq_len: int = 32,
    schema_id: Optional[str] = None,
    validate_schema: bool = True,
    risk: Optional[Dict[str, Any]] = None,
) -> DecisionContext:
    market_summary = ""
    sentiment_summary = "(No sentiment pipeline run.)"
    news_summary = "(No news pipeline run.)"
    fundamentals_summary = "(Fundamentals: plug FundamentalSource.)"
    bar_ts = trade_date
    model_pred: Optional[ModelPrediction] = None
    extra: dict = {}
    manifest_path: Optional[Path] = None
    risk_cfg = dict(risk or {})

    if config is not None:
        fs = FeatureService(config)
        if fused_parquet is None:
            fused_parquet = fs.fused_path(symbol)
    else:
        fs = None

    if fused_parquet and fused_parquet.exists():
        df = pd.read_parquet(fused_parquet)
        if validate_schema:
            rep = validate_fused_frame(df, schema_id)
            extra["schema_validation_ok"] = rep.ok
            extra["schema_id"] = rep.schema_id
            if not rep.ok:
                extra["schema_validation_errors"] = rep.errors
        elif schema_id:
            extra["schema_id"] = schema_id
        manifest_path = fused_parquet.with_suffix(".manifest.json")
        if manifest_path.exists():
            extra["feature_manifest_path"] = str(manifest_path)
        facts = _structured_market_facts_row(df)
        if facts:
            extra["structured_market_facts"] = facts
            extra["structured_market_facts_json"] = json.dumps(facts, sort_keys=True)
        market_summary = (
            "Recent OHLCV (tail):\n"
            + _summarize_ohlcv_tail(df)
            + "\nTechnical columns available: "
            + ", ".join(c for c in df.columns if str(c).lower() not in ("date",))
        )
        if facts:
            market_summary += "\n\nSTRUCTURED_FACTS_JSON (last bar, numeric):\n" + extra[
                "structured_market_facts_json"
            ]
        if "Date" in df.columns and len(df):
            bar_ts = str(df["Date"].iloc[-1])
        if "sentiment_score" in df.columns:
            v = float(df["sentiment_score"].iloc[-1])
            sentiment_summary = f"Real fused sentiment aggregate (news/social pipeline): {v}"
            extra["sentiment_has_evidence"] = _tail_has_signal(df["sentiment_score"])
        else:
            extra["sentiment_has_evidence"] = False
        if "sentiment_proxy_momentum" in df.columns:
            pv = float(df["sentiment_proxy_momentum"].iloc[-1])
            extra["sentiment_proxy_has_evidence"] = _tail_has_signal(df["sentiment_proxy_momentum"])
            extra["sentiment_proxy_momentum_latest"] = pv
            proxy_note = (
                f"\nTechnical momentum proxy only (NOT social sentiment): sentiment_proxy_momentum latest={pv}"
            )
            if extra["sentiment_has_evidence"]:
                sentiment_summary += proxy_note
            elif extra["sentiment_proxy_has_evidence"]:
                sentiment_summary = (
                    "(No real sentiment aggregates in fused features.)" + proxy_note.strip()
                )
        else:
            extra["sentiment_proxy_has_evidence"] = False
        if "news_event_count" in df.columns:
            n = float(df["news_event_count"].iloc[-1])
            news_summary = f"Real fused news event count (headline aggregates): {n}"
            extra["news_has_evidence"] = _tail_has_signal(df["news_event_count"])
        else:
            extra["news_has_evidence"] = False
        if "news_intensity_proxy" in df.columns:
            ni = float(df["news_intensity_proxy"].iloc[-1])
            extra["news_proxy_has_evidence"] = _tail_has_signal(df["news_intensity_proxy"])
            extra["news_intensity_proxy_latest"] = ni
            nproxy = (
                f"\nVolatility/ATR spike proxy only (NOT headline count): news_intensity_proxy latest={ni}"
            )
            if extra["news_has_evidence"]:
                news_summary += nproxy
            elif extra["news_proxy_has_evidence"]:
                news_summary = "(No real news counts in fused features.)" + nproxy.strip()
        else:
            extra["news_proxy_has_evidence"] = False
        close_col = None
        for c in ("Close", "close"):
            if c in df.columns:
                close_col = c
                break
        if close_col is not None and len(df):
            try:
                px = float(df[close_col].iloc[-1])
                if pd.notna(px) and math.isfinite(px):
                    extra["sizing_price"] = px
                    extra["sizing_price_source"] = "fused_bar"
            except (TypeError, ValueError):
                pass
        atr_col = "atr" if "atr" in df.columns else None
        if atr_col and len(df):
            try:
                av = float(df[atr_col].iloc[-1])
                if pd.notna(av) and math.isfinite(av) and av > 0:
                    extra["sizing_atr"] = av
                    extra["sizing_atr_source"] = "fused_bar"
            except (TypeError, ValueError):
                pass
        if extra.get("sizing_atr_source") is None and "ret_1" in df.columns and len(df) >= 3:
            tail = pd.to_numeric(df["ret_1"], errors="coerce").tail(20)
            rv = float(tail.std(ddof=0))
            px = extra.get("sizing_price")
            if px is not None and rv > 0 and math.isfinite(rv) and math.isfinite(float(px)):
                extra["sizing_atr"] = rv * float(px)
                extra["sizing_atr_source"] = "realized_vol_times_price"
        if extra.get("sizing_atr_source") is None:
            frac = float(risk_cfg.get("default_atr_fraction", 0.02))
            px = float(extra.get("sizing_price") or 100.0)
            extra["sizing_atr"] = frac * px
            extra["sizing_atr_source"] = "config_default_atr_fraction"
        obs = extra.get("sizing_atr_source") in ("fused_bar", "realized_vol_times_price")
        if bool(risk_cfg.get("require_vol_for_sizing", False)) and not obs:
            extra["sizing_rejected_reason"] = "require_vol_for_sizing_no_observed_vol"

    reg_schema_version = feature_version
    if checkpoint and scaler_path:
        extra["checkpoint_path"] = str(checkpoint)
        inf = load_inference_optional(checkpoint, scaler_path)
        if inf is not None:
            extra["schema_id"] = inf.schema_id
            extra["feature_schema_version"] = inf.feature_schema_version
            reg_schema_version = inf.feature_schema_version
            if fused_parquet and fused_parquet.exists():
                try:
                    model_pred = inf.predict_latest_from_parquet(fused_parquet, seq_len)
                except Exception as e:
                    extra["model_predict_error"] = f"{type(e).__name__}: {e}"
                    model_pred = None
                if model_pred is not None:
                    if (
                        abs(model_pred.p_up - 0.5) < _DEGENERATE_P_EPS
                        and model_pred.uncertainty >= _DEGENERATE_UNC_MIN
                    ):
                        extra["model_degenerate"] = True

    return DecisionContext(
        symbol=symbol,
        as_of=trade_date,
        market_summary=market_summary,
        sentiment_summary=sentiment_summary,
        news_summary=news_summary,
        fundamentals_summary=fundamentals_summary,
        feature_version=reg_schema_version,
        bar_timestamp=bar_ts,
        model=model_pred,
        extra=extra,
    )
