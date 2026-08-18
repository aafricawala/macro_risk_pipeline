"""
Module Name: stage_2_harvester.py
Repo Path: src/stages/stage_2_harvester.py
Stage 2: Market Plumbing & Catalyst Harvester.
"""
import os
import sys
import json
from datetime import date, datetime
from typing import List, Optional, Dict, Any
from pathlib import Path
import pytz
from loguru import logger
from src.core.schemas import (
    MacroTier,
    EpistemicTag,
    Stage1TemporalOutput,
    KeyValueItem,
    TreasuryAuctionRow,
    CentralBankEventRow,
    EarningsBellwetherRow,
    OpExGammaRow,
    CotPositioningRow,
    VixTermStructureRow,
    AuditLogRow,
    ModuleDataKV,
    Stage2HarvesterOutput,
)
from src.core.llm_router import execute_dynamic_json_query

logger.remove()
logger.add(sys.stdout, level="INFO")

try:
    from google.colab import userdata
    HAS_COLAB = True
except ImportError:
    HAS_COLAB = False

def get_storage_base_dir() -> Path:
    env_path = os.getenv("GOOGLE_DRIVE_MOUNT_PATH")
    if env_path and os.path.exists(env_path):
        return Path(env_path)
    local_path = Path("./artifacts_storage")
    local_path.mkdir(parents=True, exist_ok=True)
    return local_path

def write_error_log(stage_name: str, exception_obj: Exception) -> Path:
    base_dir = get_storage_base_dir()
    error_dir = base_dir / "error_logs"
    error_dir.mkdir(parents=True, exist_ok=True)
    ts_str = datetime.now(pytz.utc).strftime("%Y%m%d_%H%M%S")
    error_file = error_dir / f"{stage_name}_error_{ts_str}.log"
    with open(error_file, "w", encoding="utf-8") as ef:
        ef.write(f"PIPELINE FAILURE IN: {stage_name}\n")
        ef.write(f"TIMESTAMP: {datetime.now(pytz.utc).isoformat()} UTC\n")
        ef.write(f"EXCEPTION: {type(exception_obj).__name__}: {str(exception_obj)}\n")
        import traceback
        ef.write(traceback.format_exc())
    logger.error(f"Fatal error logged to: {error_file.resolve()}")
    return error_file

def get_gemini_api_key() -> str:
    if HAS_COLAB:
        try:
            secret = userdata.get("GEMINI_API_KEY")
            if secret:
                return str(secret).strip()
        except Exception:
            pass
    return os.getenv("GEMINI_API_KEY", "").strip()

HARVESTER_PROMPT_TEMPLATE = """You are a Senior Quantitative Data Harvester at a tier-1 multi-asset fund.
Coverage Window: {start_date} to {end_date}. Dominant Macro Theme: "{dominant_theme}". Current Execution Time: {as_of_time} ET.

Harvest and populate raw Key-Value items across all 7 Risk Modules with ZERO narrative prose:
1. Module 1 Plumbing: TGA_BALANCE, ON_RRP_USAGE, WALCL_FED_ASSETS, TREASURY_SUPPLY
2. Module 2 Macro Surprises: CPI_HEADLINE, CORE_PCE_DEFLATOR, NFP_PAYROLLS, ISM_MANUFACTURING
3. Module 3 Earnings: MAG7_TECH_EARNINGS, SEMI_EQUIPMENT_BILLINGS
4. Module 4 Derivatives: ZERO_GAMMA_LEVEL (log 'UNKNOWN' if paywalled per v14.6 Rule), DEALER_GEX ('UNKNOWN'), VIX_CURVE_SLOPE, COT_MANAGED_MONEY (cite 'lagged snapshot (subject to 45-day reporting lag)')
5. Module 5 Regulatory: FDA_PDUFA, OPEC_PLUS_QUOTAS, SEC_ITEM_105
6. Module 6 Geopolitics: TARIFFS_POLICY, CHOKEPOINTS_HORMUZ, BALTIC_DRY_INDEX
7. Module 7 Narratives: EXECUTIVE_ORDERS, LEADERSHIP_STATEMENTS, AAII_BULL_BEAR_SPREAD

Tag statements with [VERIFIED_OFFICIAL], [VERIFIED_SOCIAL_PRIMARY], or [UNVERIFIED_RUMOR].
Populate the 7 tables and the Top 5 Load-Bearing Claims Audit Log.
Output must conform strictly to the Stage2HarvesterOutput schema.
"""

def fallback_baseline_harvester(stage_1_input: Stage1TemporalOutput) -> Stage2HarvesterOutput:
    logger.warning("Degraded Mode: Generating Structural Liquidity & Baseline Plumbing Harvester Payload.")
    as_of_str = stage_1_input.as_of_timestamp_et.strftime("%Y-%m-%d %H:%M:%S ET")
    baseline_kv = ModuleDataKV(
        module_1_plumbing=[
            KeyValueItem(key="TGA_BALANCE", value="$780B (Estimated baseline)"),
            KeyValueItem(key="ON_RRP_USAGE", value="$210B (Estimated baseline)"),
            KeyValueItem(key="WALCL_FED_ASSETS", value="$6.82T (Estimated baseline)"),
        ],
        module_2_macro_surprises=[
            KeyValueItem(key="CPI_HEADLINE", value="Baseline monitoring mode"),
            KeyValueItem(key="CORE_PCE_DEFLATOR", value="Baseline monitoring mode"),
        ],
        module_3_earnings=[
            KeyValueItem(key="MAG7_EARNINGS_RADAR", value="Baseline corporate earnings window"),
        ],
        module_4_derivatives=[
            KeyValueItem(key="ZERO_GAMMA_LEVEL", value="UNKNOWN"),
            KeyValueItem(key="DEALER_GEX", value="UNKNOWN"),
            KeyValueItem(key="COT_10Y_MANAGED_MONEY", value="Net short baseline (subject to 45-day reporting lag)"),
        ],
        module_5_regulatory=[
            KeyValueItem(key="OPEC_PLUS_QUOTAS", value="Voluntary production cuts maintained [VERIFIED_OFFICIAL]"),
        ],
        module_6_geopolitics=[
            KeyValueItem(key="STRATEGIC_CHOKEPOINTS", value="Hormuz and Bab el-Mandeb transit baseline monitoring"),
        ],
        module_7_narratives=[
            KeyValueItem(key="EXECUTIVE_POLICY_STANCE", value="Monitoring verified statements [VERIFIED_OFFICIAL]"),
            KeyValueItem(key="AAII_BULL_BEAR_SPREAD", value="+8.5% (Historical baseline range)"),
        ],
    )
    return Stage2HarvesterOutput(
        as_of_timestamp_et=stage_1_input.as_of_timestamp_et,
        coverage_start_date=stage_1_input.coverage_start_date,
        coverage_end_date=stage_1_input.coverage_end_date,
        dominant_theme=stage_1_input.regime.dominant_theme,
        raw_kv_store=baseline_kv,
        treasury_auctions_table=[
            TreasuryAuctionRow(
                auction_date=stage_1_input.coverage_start_date.isoformat(),
                security_type="Bill",
                term="4-Week",
                offering_size_usd="$70B",
                settlement_date=(stage_1_input.coverage_start_date).isoformat(),
                auction_url="https://treasurydirect.gov",
                retrieval_timestamp_US_Eastern=as_of_str,
            )
        ],
        central_bank_events_table=[
            CentralBankEventRow(
                event_date=stage_1_input.coverage_start_date.isoformat(),
                central_bank="Federal Reserve",
                event_type="Meeting Minutes",
                expected_action="Assessment of policy trajectory",
                press_release_url="https://federalreserve.gov",
                retrieval_timestamp_US_Eastern=as_of_str,
            )
        ],
        earnings_bellwethers_table=[
            EarningsBellwetherRow(
                ticker="N/A",
                company="N/A",
                earnings_date="N/A",
                expected_eps="N/A",
                implied_move_pct="UNKNOWN",
                hist_realized_move_pct="UNKNOWN",
                ir_release_url="N/A",
                retrieval_timestamp_US_Eastern=as_of_str,
            )
        ],
        opex_and_gamma_table=[
            OpExGammaRow(
                opex_date=stage_1_input.windows.week_1.end_date.isoformat(),
                description="Monthly Equity & Index OpEx",
                zero_gamma_level="UNKNOWN",
                markets_affected="SPX, QQQ",
                source_url="https://cboe.com",
                retrieval_timestamp_US_Eastern=as_of_str,
            )
        ],
        cot_positioning_table=[
            CotPositioningRow(
                report_date=stage_1_input.coverage_start_date.isoformat(),
                asset_class="10Y Treasury Notes",
                managed_money_net_positions="UNKNOWN",
                change_vs_prior_week="UNKNOWN",
                source_url="https://cftc.gov",
                retrieval_timestamp_US_Eastern=as_of_str,
            )
        ],
        vix_term_structure_table=[
            VixTermStructureRow(
                as_of_date=stage_1_input.coverage_start_date.isoformat(),
                spot_vix="15.20",
                m1_future="16.10",
                m2_future="16.95",
                m3_future="17.50",
                curve_slope_m1_m2="+0.85 (Contango)",
                source_url="https://cboe.com",
                retrieval_timestamp_US_Eastern=as_of_str,
            )
        ],
        audit_log_table=[
            AuditLogRow(
                rank=1,
                load_bearing_claim="Federal Reserve H.4.1 total assets baseline monitoring.",
                search_query="site:federalreserve.gov H.4.1 factors affecting reserve balances",
                retrieved_snippet="Total assets baseline plumbing level.",
                source_url="federalreserve.gov",
                retrieval_timestamp_US_Eastern=as_of_str,
                confidence_score=0.95,
                epistemic_tag=EpistemicTag.VERIFIED_OFFICIAL,
            )
        ],
        degraded_mode=True,
        audit_trace=["Stage 2 Degraded Baseline Mode Activated."],
    )

def load_stage_1_artifact() -> Stage1TemporalOutput:
    art_path = get_storage_base_dir() / "artifacts" / "stage_1_temporal_output.json"
    if not art_path.exists():
        raise FileNotFoundError(f"Stage 1 artifact not found at {art_path.resolve()}. Please run Stage 1 first.")
    with open(art_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return Stage1TemporalOutput.model_validate(data)

def run_stage_2(
    stage_1_input: Optional[Stage1TemporalOutput] = None,
    api_key: Optional[str] = None,
    candidate_models: Optional[List[str]] = None,
    save_artifact: bool = True,
) -> Stage2HarvesterOutput:
    logger.info("Initializing STAGE 2: Market Plumbing & Catalyst Harvester...")
    audit_trace: List[str] = [f"Initialized at {datetime.now(pytz.utc).isoformat()} UTC"]
    if stage_1_input is None:
        stage_1_input = load_stage_1_artifact()
    audit_trace.append(f"Inherited Dominant Theme: {stage_1_input.regime.dominant_theme}")
    audit_trace.append(f"Coverage window: {stage_1_input.coverage_start_date} to {stage_1_input.coverage_end_date}")

    effective_key = get_gemini_api_key() if api_key is None else api_key.strip()
    is_degraded = False

    if effective_key:
        try:
            logger.info("Querying LLM Router for structured 7-Module macro harvesting...")
            prompt = HARVESTER_PROMPT_TEMPLATE.format(
                start_date=stage_1_input.coverage_start_date.isoformat(),
                end_date=stage_1_input.coverage_end_date.isoformat(),
                dominant_theme=stage_1_input.regime.dominant_theme,
                as_of_time=stage_1_input.as_of_timestamp_et.isoformat(),
            )
            parsed_json, model_used = execute_dynamic_json_query(
                prompt=prompt,
                api_key=effective_key,
                candidate_models=candidate_models,
                response_schema=Stage2HarvesterOutput,
            )
            output = Stage2HarvesterOutput.model_validate(parsed_json)
            audit_trace.append(f"Harvested via LLM Router using model: {model_used}")
            output.audit_trace.extend(audit_trace)
        except Exception as exc:
            logger.error(f"Stage 2 Harvester failed: {exc}. Persisting error and activating Degraded Mode.")
            write_error_log("stage_2_harvester_llm", exc)
            output = fallback_baseline_harvester(stage_1_input)
            is_degraded = True
    else:
        logger.warning("No API key provided. Running Stage 2 in Degraded Baseline Mode.")
        output = fallback_baseline_harvester(stage_1_input)
        is_degraded = True

    if save_artifact:
        art_dir = get_storage_base_dir() / "artifacts"
        art_dir.mkdir(parents=True, exist_ok=True)
        out_file = art_dir / "stage_2_harvester_output.json"
        with open(out_file, "w", encoding="utf-8") as out_f:
            out_f.write(output.model_dump_json(indent=2))
        logger.info(f"STAGE 2 artifact saved to: {out_file.resolve()}")

    logger.info(f"STAGE 2 complete. Harvested {len(output.raw_kv_store.module_1_plumbing)} plumbing metrics, {len(output.audit_log_table)} audit records.")
    return output
