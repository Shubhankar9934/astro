from __future__ import annotations

import hashlib
import json
from dataclasses import asdict
from pathlib import Path
from typing import Any, Dict, List, Literal, Optional, Tuple

from astro.agents import (
    create_aggressive_debator,
    create_bearish_researcher,
    create_bullish_researcher,
    create_conservative_debator,
    create_fundamentals_analyst,
    create_macro_analyst,
    create_neutral_debator,
    create_news_analyst,
    create_research_synthesizer,
    create_risk_judge,
    create_sentiment_analyst,
    create_technical_analyst,
    create_trader_agent,
)
from astro.agents.shared.memory import FinancialSituationMemory
from astro.agents.risk.exposure_manager import ExposureManager
from astro.agents.risk.portfolio_constraints import apply_post_decision_risk
from astro.agents.trader.signal_generator import extract_signal_from_text
from astro.decision_engine.policy import (
    apply_model_governance_detailed,
    should_skip_research_debate,
    should_upgrade_fast_to_full,
)
from astro.decision_engine.routing import should_continue_debate, should_continue_risk_analysis
from astro.decision_engine.state_manager import AstroState, DecisionContext, initial_invest_debate, initial_risk_debate
from astro.decision_engine.workflow import build_analyst_chain
from astro.utils.config_loader import AstroConfig, load_all_configs
from astro.utils.llm.factory import create_llm_client
from astro.storage.database import MetadataDB
from astro.utils.logger import get_logger

LOG = get_logger("astro.executor")

DecisionMode = Literal["fast", "full"]


def _file_sha256(path: Optional[Path]) -> Optional[str]:
    if path is None or not path.exists():
        return None
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def _apply_patch(state: AstroState, patch: Dict[str, Any]) -> None:
    for k, v in patch.items():
        if k == "messages" and v:
            state.messages.extend(v)
        elif hasattr(state, k):
            setattr(state, k, v)


def _state_dict(state: AstroState) -> Dict[str, Any]:
    return {
        "company_of_interest": state.company_of_interest,
        "trade_date": state.trade_date,
        "market_report": state.market_report,
        "sentiment_report": state.sentiment_report,
        "news_report": state.news_report,
        "fundamentals_report": state.fundamentals_report,
        "macro_report": state.macro_report,
        "investment_debate_state": dict(state.investment_debate_state),
        "investment_plan": state.investment_plan,
        "trader_investment_plan": state.trader_investment_plan,
        "risk_debate_state": dict(state.risk_debate_state),
        "final_trade_decision": state.final_trade_decision,
        "messages": state.messages,
        "sender": state.sender,
        "astro_context": state.context,
    }


class DecisionExecutor:
    def __init__(
        self,
        config: AstroConfig,
        *,
        quick_llm: Any,
        deep_llm: Any,
        bull_memory: FinancialSituationMemory,
        bear_memory: FinancialSituationMemory,
        trader_memory: FinancialSituationMemory,
        invest_judge_memory: FinancialSituationMemory,
        risk_manager_memory: FinancialSituationMemory,
        log_dir: Optional[Path] = None,
    ):
        self.config = config
        self.quick_llm = quick_llm
        self.deep_llm = deep_llm
        self.bull_memory = bull_memory
        self.bear_memory = bear_memory
        self.trader_memory = trader_memory
        self.invest_judge_memory = invest_judge_memory
        self.risk_manager_memory = risk_manager_memory
        self.log_dir = log_dir
        agents_cfg = config.agents
        self.selected_analysts: List[str] = list(
            agents_cfg.get(
                "selected_analysts",
                ["market", "social", "news", "fundamentals"],
            )
        )
        if bool(agents_cfg.get("macro_analyst", {}).get("enabled", False)):
            if "macro" not in self.selected_analysts:
                self.selected_analysts = list(self.selected_analysts) + ["macro"]
        self.technical_structured_json: bool = bool(
            agents_cfg.get("technical_structured_json", False)
        )
        self.fast_mode_analysts: List[str] = list(
            agents_cfg.get("fast_mode_analysts", ["market"])
        )
        self.max_debate_rounds = int(agents_cfg.get("max_debate_rounds", 1))
        self.max_risk_discuss_rounds = int(agents_cfg.get("max_risk_discuss_rounds", 1))

    @classmethod
    def from_config(cls, config: Optional[AstroConfig] = None, log_dir: Optional[Path] = None):
        cfg = config or load_all_configs()
        agents = cfg.agents
        q = agents["quick_think"]
        d = agents["deep_think"]
        quick = create_llm_client(
            q["provider"], q["model"], temperature=q.get("temperature", 0.3)
        ).get_llm()
        deep = create_llm_client(
            d["provider"], d["model"], temperature=d.get("temperature", 0.2)
        ).get_llm()
        return cls(
            cfg,
            quick_llm=quick,
            deep_llm=deep,
            bull_memory=FinancialSituationMemory("bull"),
            bear_memory=FinancialSituationMemory("bear"),
            trader_memory=FinancialSituationMemory("trader"),
            invest_judge_memory=FinancialSituationMemory("invest_judge"),
            risk_manager_memory=FinancialSituationMemory("risk_manager"),
            log_dir=log_dir,
        )

    def _analyst_factories(self) -> Dict[str, Any]:
        return {
            "market": create_technical_analyst(
                self.quick_llm, structured_json=self.technical_structured_json
            ),
            "social": create_sentiment_analyst(self.quick_llm),
            "news": create_news_analyst(self.quick_llm),
            "fundamentals": create_fundamentals_analyst(self.quick_llm),
            "macro": create_macro_analyst(self.quick_llm),
        }

    def _run_analysts(self, state: AstroState, keys: List[str]) -> None:
        sd = _state_dict(state)
        chain = build_analyst_chain(keys, self._analyst_factories())
        for step in chain:
            patch = step(sd)
            _apply_patch(state, patch)
            sd = _state_dict(state)

    def _research_debate(self, state: AstroState, skip: bool) -> None:
        sd = _state_dict(state)
        mgr = create_research_synthesizer(self.deep_llm, self.invest_judge_memory)
        if skip:
            state.investment_debate_state = {
                **initial_invest_debate(),
                "history": "Research debate skipped: model uncertainty below threshold.",
                "count": 0,
            }
            sd = _state_dict(state)
            patch = mgr(sd)
            _apply_patch(state, patch)
            return
        bull = create_bullish_researcher(self.quick_llm, self.bull_memory)
        bear = create_bearish_researcher(self.quick_llm, self.bear_memory)
        while True:
            nxt = should_continue_debate(sd, self.max_debate_rounds)
            if nxt == "Research Manager":
                patch = mgr(sd)
                _apply_patch(state, patch)
                return
            if nxt == "Bear Researcher":
                patch = bear(sd)
            else:
                patch = bull(sd)
            _apply_patch(state, patch)
            sd = _state_dict(state)

    def _risk_cycle(self, state: AstroState, fast: bool) -> None:
        sd = _state_dict(state)
        judge = create_risk_judge(self.deep_llm, self.risk_manager_memory)
        if fast:
            state.risk_debate_state = {
                **initial_risk_debate(),
                "history": "Fast mode: single risk judge review (no 3-way debate).",
            }
            sd = _state_dict(state)
            patch = judge(sd)
            _apply_patch(state, patch)
            return
        aggressive = create_aggressive_debator(self.quick_llm)
        conservative = create_conservative_debator(self.quick_llm)
        neutral = create_neutral_debator(self.quick_llm)
        while True:
            nxt = should_continue_risk_analysis(sd, self.max_risk_discuss_rounds)
            if nxt == "Risk Judge":
                patch = judge(sd)
                _apply_patch(state, patch)
                return
            if nxt == "Conservative Analyst":
                patch = conservative(sd)
            elif nxt == "Neutral Analyst":
                patch = neutral(sd)
            else:
                patch = aggressive(sd)
            _apply_patch(state, patch)
            sd = _state_dict(state)

    def _run_full_pipeline(
        self,
        state: AstroState,
        *,
        skip_research_debate: bool,
    ) -> None:
        self._run_analysts(state, self.selected_analysts)
        self._research_debate(state, skip=skip_research_debate)
        sd = _state_dict(state)
        trader = create_trader_agent(self.quick_llm, self.trader_memory)
        patch = trader(sd)
        _apply_patch(state, patch)
        self._risk_cycle(state, fast=False)

    def run_analysts_only(
        self,
        symbol: str,
        trade_date: str,
        context: DecisionContext,
        keys: Optional[List[str]] = None,
    ) -> Dict[str, str]:
        state = AstroState(
            company_of_interest=symbol,
            trade_date=trade_date,
            context=context,
            investment_debate_state=initial_invest_debate(),
            risk_debate_state=initial_risk_debate(),
        )
        self._run_analysts(state, keys or self.selected_analysts)
        return {
            "technical": state.market_report,
            "sentiment": state.sentiment_report,
            "news": state.news_report,
            "fundamentals": state.fundamentals_report,
            "macro": state.macro_report,
        }

    def run_research_only(
        self,
        symbol: str,
        trade_date: str,
        context: DecisionContext,
    ) -> Dict[str, Any]:
        state = AstroState(
            company_of_interest=symbol,
            trade_date=trade_date,
            context=context,
            investment_debate_state=initial_invest_debate(),
            risk_debate_state=initial_risk_debate(),
        )
        self._run_analysts(state, self.selected_analysts)
        self._research_debate(state, skip=False)
        ids = state.investment_debate_state
        return {
            "bull_history": ids.get("bull_history", ""),
            "bear_history": ids.get("bear_history", ""),
            "final_summary": state.investment_plan,
        }

    def run_risk_only(self, state_dict: Dict[str, Any]) -> Dict[str, str]:
        """Expects keys like market_report, trader_investment_plan, investment_plan."""
        ac = state_dict.get("astro_context")
        if isinstance(ac, DecisionContext):
            context = ac
        elif isinstance(ac, dict):
            context = DecisionContext(
                symbol=ac.get("symbol", state_dict.get("company_of_interest", "")),
                as_of=ac.get("as_of", state_dict.get("trade_date", "")),
            )
        else:
            context = DecisionContext(
                symbol=state_dict.get("company_of_interest", ""),
                as_of=state_dict.get("trade_date", ""),
            )
        state = AstroState(
            company_of_interest=state_dict.get("company_of_interest", ""),
            trade_date=state_dict.get("trade_date", ""),
            context=context,
            market_report=state_dict.get("market_report", ""),
            sentiment_report=state_dict.get("sentiment_report", ""),
            news_report=state_dict.get("news_report", ""),
            fundamentals_report=state_dict.get("fundamentals_report", ""),
            macro_report=state_dict.get("macro_report", ""),
            investment_plan=state_dict.get("investment_plan", ""),
            trader_investment_plan=state_dict.get("trader_investment_plan", ""),
            investment_debate_state=state_dict.get("investment_debate_state")
            or initial_invest_debate(),
            risk_debate_state=initial_risk_debate(),
        )
        self._risk_cycle(state, fast=False)
        return {
            "risk_summary": state.final_trade_decision,
            "raw": state.risk_debate_state.get("history", ""),
        }

    def _run_fast_pipeline(self, state: AstroState) -> None:
        self._run_analysts(state, self.fast_mode_analysts)
        parts = [
            state.market_report,
            state.sentiment_report,
            state.news_report,
            state.fundamentals_report,
            state.macro_report,
        ]
        mp = state.context.model
        model_line = ""
        if mp:
            model_line = f"\nTransformer: p_up={mp.p_up:.4f} uncertainty={mp.uncertainty:.4f}\n"
        state.investment_plan = (
            "(Fast mode) Compressed analyst output:\n"
            + model_line
            + "\n---\n".join(p for p in parts if p)
        )[:12000]
        state.investment_debate_state = {**initial_invest_debate(), "count": 0}
        sd = _state_dict(state)
        trader = create_trader_agent(self.quick_llm, self.trader_memory)
        patch = trader(sd)
        _apply_patch(state, patch)
        self._risk_cycle(state, fast=True)

    def run(
        self,
        symbol: str,
        trade_date: str,
        context: DecisionContext,
        *,
        mode: Optional[DecisionMode] = None,
    ) -> Tuple[AstroState, str, Dict[str, Any]]:
        agents_cfg = self.config.agents
        requested: DecisionMode = mode or agents_cfg.get("decision_mode_default", "full")  # type: ignore[assignment]
        eff_mode: DecisionMode = requested
        if requested == "fast" and should_upgrade_fast_to_full(context.model, agents_cfg):
            eff_mode = "full"
            LOG.info("Upgrading fast->full due to model uncertainty")

        state = AstroState(
            company_of_interest=symbol,
            trade_date=trade_date,
            context=context,
            investment_debate_state=initial_invest_debate(),
            risk_debate_state=initial_risk_debate(),
        )
        skip_debate = should_skip_research_debate(context.model, agents_cfg)
        if eff_mode == "full":
            self._run_full_pipeline(state, skip_research_debate=skip_debate)
        else:
            self._run_fast_pipeline(state)

        raw_signal = extract_signal_from_text(state.final_trade_decision)
        gov = dict(agents_cfg.get("model_governance", {}))
        final_signal, governance_meta = apply_model_governance_detailed(
            raw_signal, context.model, gov
        )

        suggested_size = 0.0
        nav = float(self.config.risk.get("portfolio_nav", 1_000_000))
        p_up = context.model.p_up if context.model else 0.5
        ctx_ex = context.extra
        atr = float(ctx_ex.get("sizing_atr", 0.02))
        price = float(ctx_ex.get("sizing_price", 100.0))
        if atr <= 0 or not (atr == atr):  # NaN check
            atr = 0.02
        if price <= 0 or not (price == price):
            price = 100.0
        db_path = self.config.data_root_path(Path.cwd()) / "cache" / "astro_meta.sqlite"
        db_path.parent.mkdir(parents=True, exist_ok=True)
        db = MetadataDB(db_path)
        em = ExposureManager(db)
        final_signal, suggested_size = apply_post_decision_risk(
            final_signal,
            em,
            dict(self.config.risk),
            nav=nav,
            p_up=p_up,
            atr=atr,
            price=price,
        )
        if context.extra.get("sizing_rejected_reason"):
            suggested_size = 0.0
        db.close()

        ckpt_path = context.extra.get("checkpoint_path")
        if ckpt_path:
            ckpt_path = Path(ckpt_path)
        manifest_path = context.extra.get("feature_manifest_path")

        if self.log_dir:
            self.log_dir.mkdir(parents=True, exist_ok=True)
            log_path = self.log_dir / f"decision_{symbol}_{trade_date}.json"
            payload = {
                "symbol": symbol,
                "trade_date": trade_date,
                "mode_requested": requested,
                "mode_effective": eff_mode,
                "signal_raw": raw_signal,
                "signal_final": final_signal,
                "governance": governance_meta,
                "sizing": {
                    "atr": atr,
                    "price": price,
                    "atr_source": context.extra.get("sizing_atr_source", "default"),
                    "price_source": context.extra.get("sizing_price_source", "default"),
                },
                "suggested_size_usd": suggested_size,
                "schema_id": context.extra.get("schema_id"),
                "feature_schema_version": context.extra.get("feature_schema_version"),
                "checkpoint_sha256": _file_sha256(ckpt_path),
                "feature_manifest_path": str(manifest_path) if manifest_path else None,
                "model": asdict(context.model) if context.model else None,
                "model_degenerate": context.extra.get("model_degenerate"),
                "model_predict_error": context.extra.get("model_predict_error"),
                "structured_market_facts": context.extra.get("structured_market_facts"),
                "state": asdict(state),
            }
            with open(log_path, "w", encoding="utf-8") as f:
                json.dump(payload, f, default=str, indent=2)
            LOG.info("Wrote decision log %s", log_path)
        run_meta: Dict[str, Any] = {
            "suggested_size_usd": suggested_size,
            "governance": governance_meta,
            "sizing": {
                "atr": atr,
                "price": price,
                "atr_source": context.extra.get("sizing_atr_source", "default"),
                "price_source": context.extra.get("sizing_price_source", "default"),
                "rejected_reason": context.extra.get("sizing_rejected_reason"),
            },
        }
        return state, final_signal, run_meta

    def run_once(
        self,
        symbol: str,
        trade_date: str,
        context: DecisionContext,
    ) -> Tuple[AstroState, str, Dict[str, Any]]:
        return self.run(symbol, trade_date, context, mode="full")
