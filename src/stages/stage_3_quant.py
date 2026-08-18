"""
Module Name: stage_3_quant.py
Repo Path: src/stages/stage_3_quant.py
Stage 3: Quant Synthesis & Taleb Stress Tester with Live Factor ETF Spreads & Deterministic Math.
"""
import os
import sys
import json
from datetime import date, datetime
from typing import List, Optional, Dict, Any, Tuple
from pathlib import Path
import pytz
from loguru import logger
from src.core.schemas import (
    TailRiskCategory, TailRiskItem, FactorRotationRegime,
    CrossAssetSpilloverItem, TalebStressTest, TacticalScenario,
    KeyValueItem, Stage2HarvesterOutput, Stage3QuantSynthesisOutput
)
from src.core.llm_router import execute_dynamic_json_query
from src.core.math_utils import calculate_atm_straddle_implied_move, calculate_vix_curve_slope_math
from src.data.factor_scraper import fetch_factor_etf_spreads

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

def compute_vix_slope_from_stage_2(stage_2_input: Stage2HarvesterOutput) -> str:
    if stage_2_input.vix_term_structure_table:
        row = stage_2_input.vix_term_structure_table[0]
        try:
            m1 = float(row.m1_future)
            m2 = float(row.m2_future)
            _, label = calculate_vix_curve_slope_math(m1, m2)
            return label
        except (ValueError, TypeError):
            pass
    return "+0.75 pts (Contango baseline)"

SYNTHESIS_PROMPT_TEMPLATE = """You are a Senior Institutional Quantitative Strategist and Chief Risk Officer at a multi-asset fund.
Coverage Window: {start_date} to {end_date}. Dominant Macro Theme: "{dominant_theme}". Execution Time: {as_of_time} ET.

INPUT DATA (Zero new web searches permitted):
Module 1 Plumbing: {mod_1}
Module 2 Macro: {mod_2}
Module 3 Earnings: {mod_3}
Module 4 Derivatives: {mod_4}
Live Calculated VIX Slope: {vix_slope}
Live ETF Factor Regimes: {factor_regimes}

QUANT SYNTHESIS MANDATE:
1. Taleb Fragility Stress Testing:
   - Systemic Shock: Impact of 10% equity drawdown on dealer balance sheets and corporate debt refinancing walls.
   - Idiosyncratic Shock: Feedback loops from liquidity drains, CTA momentum stop-loss unwinds, and margin debt velocity.
2. Tail Risk Ranking:
   - Rank exactly 3 Left-Tail risks (Downside/Vol Spikes) with estimated probability (%), direct impact asset, spillover vector, and desk hedging stance.
   - Rank exactly 3 Right-Tail risks (Upside/Breakouts) with estimated probability (%), direct impact asset, spillover vector, and desk hedging stance.
3. Cross-Asset Spillover Matrix: Map macro catalysts to 10Y Yield (bps), DXY, Crude Oil, and Sector/Factor rotations.
4. Tactical Institutional Scenarios (MAX 100 words per scenario):
   - Base Case (Expected Path)
   - Hawkish / Liquidity Squeeze (Downside Fragility Case)
   - Goldilocks / Disinflationary Expansion (Upside Case)

Output must conform strictly to the Stage3QuantSynthesisOutput schema.
"""

def fallback_baseline_synthesis(stage_2_input: Stage2HarvesterOutput) -> Stage3QuantSynthesisOutput:
    logger.warning("Degraded Mode: Generating Baseline Quant Synthesis Payload.")
    vix_slope = compute_vix_slope_from_stage_2(stage_2_input)
    live_factors = fetch_factor_etf_spreads()
    # Serialize to clean dictionaries to guarantee schema boundary compatibility
    factors_data = [f.model_dump() if hasattr(f, "model_dump") else f for f in live_factors]

    return Stage3QuantSynthesisOutput(
        as_of_timestamp_et=stage_2_input.as_of_timestamp_et,
        coverage_start_date=stage_2_input.coverage_start_date,
        coverage_end_date=stage_2_input.coverage_end_date,
        dominant_theme=stage_2_input.dominant_theme,
        vix_curve_slope_pts=vix_slope,
        atm_straddle_implied_moves=[
            KeyValueItem(key="SPX_1W_IMPLIED_MOVE", value=calculate_atm_straddle_implied_move(120.0, 130.0, 5000.0)),
            KeyValueItem(key="NVDA_EARNINGS_IMPLIED_MOVE", value="UNKNOWN (v14.6 Rule)"),
        ],
        factor_rotations=factors_data,
        top_left_tail_risks=[
            TailRiskItem(
                category=TailRiskCategory.LEFT_TAIL,
                rank=1,
                catalyst_event="Hawkish Central Bank Policy Pivot / Persistent Core Inflation",
                date_horizon="Rolling 4 Weeks",
                est_prob_pct="35%",
                direct_impact_asset="US 10-Year Real Yield (TIPS)",
                spillover_vector="Real rates push higher -> Multiple contraction -> CTA momentum flip.",
                desk_hedging_stance="Long SPX 1-Month 25-delta Put Spreads.",
            ),
            TailRiskItem(
                category=TailRiskCategory.LEFT_TAIL,
                rank=2,
                catalyst_event="Treasury Supply Indigestion & Primary Dealer Constriction",
                date_horizon="Coupon Settlement Window",
                est_prob_pct="25%",
                direct_impact_asset="SOFR / Treasury Repo Spreads",
                spillover_vector="Dealers hit capacity -> Curve steepens -> Liquidity premium widens.",
                desk_hedging_stance="Payer swaptions on 5Y/30Y steepeners; reduce gross leverage.",
            ),
            TailRiskItem(
                category=TailRiskCategory.LEFT_TAIL,
                rank=3,
                catalyst_event="Geopolitical Escalation at Strategic Energy Chokepoints",
                date_horizon="Continuous Horizon",
                est_prob_pct="20%",
                direct_impact_asset="Brent / WTI Crude Oil",
                spillover_vector="Crude oil spikes > $90/bbl -> Margin compression.",
                desk_hedging_stance="Long 2-Month OTM WTI Call Options.",
            ),
        ],
        top_right_tail_risks=[
            TailRiskItem(
                category=TailRiskCategory.RIGHT_TAIL,
                rank=1,
                catalyst_event="Synchronized Disinflationary Soft Landing",
                date_horizon="Rolling 4 Weeks",
                est_prob_pct="40%",
                direct_impact_asset="Broad Equity Indices (SPX/NDX)",
                spillover_vector="Lower discount rates -> Multiple expansion broadens to cyclicals.",
                desk_hedging_stance="Overweight Quality Cyclicals; call ladders on RSP.",
            ),
            TailRiskItem(
                category=TailRiskCategory.RIGHT_TAIL,
                rank=2,
                catalyst_event="Mega-Cap AI Productivity Realization",
                date_horizon="Tech Earnings Window",
                est_prob_pct="30%",
                direct_impact_asset="Semiconductors (SOX Index)",
                spillover_vector="Hyperscaler capex guidance beats consensus -> Semiconductor billings rise.",
                desk_hedging_stance="Bull call spreads on SOXX/SMH.",
            ),
            TailRiskItem(
                category=TailRiskCategory.RIGHT_TAIL,
                rank=3,
                catalyst_event="Corporate Buyback Window Reopening",
                date_horizon="Late Coverage Horizon",
                est_prob_pct="25%",
                direct_impact_asset="S&P 500 Large-Cap Equity",
                spillover_vector="Corporate repurchase desks execute > $5B/day flow -> Volatility suppressed.",
                desk_hedging_stance="Monetize downside puts; delta-neutral volatility harvesting.",
            ),
        ],
        cross_asset_spillovers=[
            CrossAssetSpilloverItem(
                forward_macro_event="Jackson Hole Policy Guidance / FOMC Path",
                us_10y_yield_impact="▲ +10 bps (Hawkish) / ▼ -12 bps (Dovish)",
                dxy_impact="▲ Stronger on higher terminal rate pricing",
                crude_oil_impact="Neutral on USD strength",
                equity_sector_factor_tilts="Outperform: Energy, Financials <br> Underperform: Real Estate, High-Multiple Growth",
            )
        ],
        taleb_stress_test=TalebStressTest(
            systemic_shock_10pct_drawdown="A rapid 10% equity drawdown widens high-yield spreads by +65 bps. Primary dealer absorption capacity remains constrained, forcing sub-BBB borrowers into expensive private debt channels.",
            idiosyncratic_liquidity_shock="Simultaneous TGA rebuild and ON RRP stagnation reduces reserves. CTA momentum stop-losses trigger below 50-DMA, accelerating systematic selling into illiquid spreads.",
        ),
        tactical_scenarios=[
            TacticalScenario(
                scenario_name="Base Case: Orderly Disinflation & Consolidation",
                probability_pct="55%",
                core_thesis="Central banks maintain data-dependency. Growth decelerates modestly toward trend. Earnings meet consensus, keeping multiples rangebound while real yields anchor near 2.00%.",
                multi_asset_positioning="Neutral benchmark duration; overweight Quality cash cows; underweight floating-rate debt.",
            ),
            TacticalScenario(
                scenario_name="Hawkish / Liquidity Squeeze (Downside Fragility)",
                probability_pct="25%",
                core_thesis="Core inflation components stall above 3.0%, forcing restrictive terminal rates. Treasury concessions push 10Y yields higher, triggering systematic CTA de-leveraging.",
                multi_asset_positioning="Underweight duration and high-multiple growth; long volatility skew via SPX put spreads; overweight cash.",
            ),
            TacticalScenario(
                scenario_name="Goldilocks / Disinflationary Expansion (Upside Case)",
                probability_pct="20%",
                core_thesis="Cooling labor costs return core inflation to target while productivity gains sustain profit margins. Central banks initiate easing, lowering discount rates across assets.",
                multi_asset_positioning="Overweight Equity Beta and Small-Cap Cyclicals (IWM); extend duration in intermediate Treasuries.",
            ),
        ],
        degraded_mode=True,
        audit_trace=["Stage 3 Baseline Synthesis Utilized."],
    )

def load_stage_2_artifact() -> Stage2HarvesterOutput:
    art_path = get_storage_base_dir() / "artifacts" / "stage_2_harvester_output.json"
    if not art_path.exists():
        raise FileNotFoundError(f"Stage 2 artifact not found at {art_path.resolve()}. Run Stage 2 first.")
    with open(art_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return Stage2HarvesterOutput.model_validate(data)

def run_stage_3(
    stage_2_input: Optional[Stage2HarvesterOutput] = None,
    api_key: Optional[str] = None,
    candidate_models: Optional[List[str]] = None,
    save_artifact: bool = True,
) -> Stage3QuantSynthesisOutput:
    logger.info("Initializing STAGE 3: Quant Synthesis & Taleb Stress Tester...")
    audit_trace: List[str] = [f"Initialized at {datetime.now(pytz.utc).isoformat()} UTC"]
    if stage_2_input is None:
        stage_2_input = load_stage_2_artifact()

    vix_slope = compute_vix_slope_from_stage_2(stage_2_input)
    live_factors = fetch_factor_etf_spreads()
    factors_data = [f.model_dump() if hasattr(f, "model_dump") else f for f in live_factors]

    audit_trace.append(f"Calculated VIX Slope: {vix_slope}")
    audit_trace.append(f"Live Factor ETF Spreads Ingested ({len(live_factors)} pairs)")

    effective_key = get_gemini_api_key() if api_key is None else api_key.strip()
    is_degraded = False

    if effective_key:
        try:
            logger.info("Querying LLM Router for quantitative risk synthesis & stress testing...")
            prompt = SYNTHESIS_PROMPT_TEMPLATE.format(
                start_date=stage_2_input.coverage_start_date.isoformat(),
                end_date=stage_2_input.coverage_end_date.isoformat(),
                dominant_theme=stage_2_input.dominant_theme,
                as_of_time=stage_2_input.as_of_timestamp_et.isoformat(),
                mod_1=json.dumps([kv.model_dump() for kv in stage_2_input.raw_kv_store.module_1_plumbing]),
                mod_2=json.dumps([kv.model_dump() for kv in stage_2_input.raw_kv_store.module_2_macro_surprises]),
                mod_3=json.dumps([kv.model_dump() for kv in stage_2_input.raw_kv_store.module_3_earnings]),
                mod_4=json.dumps([kv.model_dump() for kv in stage_2_input.raw_kv_store.module_4_derivatives]),
                vix_slope=vix_slope,
                factor_regimes=json.dumps(factors_data),
            )
            parsed_json, model_used = execute_dynamic_json_query(
                prompt=prompt,
                api_key=effective_key,
                candidate_models=candidate_models,
                response_schema=Stage3QuantSynthesisOutput,
            )
            output = Stage3QuantSynthesisOutput.model_validate(parsed_json)
            output.factor_rotations = [FactorRotationRegime.model_validate(f) for f in factors_data]
            output.vix_curve_slope_pts = vix_slope
            audit_trace.append(f"Synthesized via LLM Router using model: {model_used}")
            output.audit_trace.extend(audit_trace)
        except Exception as exc:
            logger.error(f"Stage 3 Quant Synthesis failed: {exc}. Activating Degraded Mode.")
            write_error_log("stage_3_quant_llm", exc)
            output = fallback_baseline_synthesis(stage_2_input)
            is_degraded = True
    else:
        logger.warning("No API key provided. Running Stage 3 in Degraded Baseline Mode.")
        output = fallback_baseline_synthesis(stage_2_input)
        is_degraded = True

    if save_artifact:
        art_dir = get_storage_base_dir() / "artifacts"
        art_dir.mkdir(parents=True, exist_ok=True)
        out_file = art_dir / "stage_3_quant_output.json"
        with open(out_file, "w", encoding="utf-8") as out_f:
            out_f.write(output.model_dump_json(indent=2))
        logger.info(f"STAGE 3 artifact saved to: {out_file.resolve()}")

    logger.info(f"STAGE 3 complete. Ranked {len(output.top_left_tail_risks)} Left-Tail and {len(output.top_right_tail_risks)} Right-Tail risks.")
    return output
