"""
Module Name: stage_3_quant.py
Repo Path: src/stages/stage_3_quant.py

BCBS 239 Data Lineage & Compliance Standards:
- Data Origin: Stage 2 Harvester Key-Value store and structured CSV tables.
- Transformations: Deterministic math formulas (VIX slope, ATM implied move), Asness factor modeling,
  Taleb systemic/idiosyncratic fragility stress testing, and tail risk probability ranking.
- Output Destination: Stage3QuantSynthesisOutput schema persisted to Google Drive artifacts.
"""

# Import standard library OS module for environment and file paths
import os

# Import sys module for standard output stream configuration
import sys

# Import json module for parsing and serialization
import json

# Import datetime and date for temporal modeling
from datetime import date, datetime

# Import typing primitives for strict type enforcement
from typing import List, Optional, Dict, Any, Tuple

# Import Path for filesystem path resolution
from pathlib import Path

# Import pytz for US Eastern Timezone handling
import pytz

# Import loguru logger for structured logging
from loguru import logger

# Import validated schemas from src/core/schemas.py
from src.core.schemas import (
    TailRiskCategory,
    TailRiskItem,
    FactorRotationRegime,
    CrossAssetSpilloverItem,
    TalebStressTest,
    TacticalScenario,
    KeyValueItem,
    Stage2HarvesterOutput,
    Stage3QuantSynthesisOutput,
)

# Import dynamic LLM router
from src.core.llm_router import execute_dynamic_json_query

# Configure loguru logger to output to standard stdout
logger.remove()
logger.add(sys.stdout, level="INFO")

# Check if running inside Google Colab
try:
    from google.colab import userdata
    HAS_COLAB = True
except ImportError:
    HAS_COLAB = False


# Helper function to get base storage directory
def get_storage_base_dir() -> Path:
    env_path = os.getenv("GOOGLE_DRIVE_MOUNT_PATH")
    if env_path and os.path.exists(env_path):
        return Path(env_path)
    local_path = Path("./artifacts_storage")
    local_path.mkdir(parents=True, exist_ok=True)
    return local_path


# Helper function to persist fatal errors to error_logs/
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


# Helper function to obtain Gemini API key
def get_gemini_api_key() -> str:
    if HAS_COLAB:
        try:
            secret = userdata.get("GEMINI_API_KEY")
            if secret:
                return str(secret).strip()
        except Exception:
            pass
    return os.getenv("GEMINI_API_KEY", "").strip()


# Deterministic calculation of VIX Futures Curve Slope: M2 - M1
def calculate_vix_curve_slope(stage_2_input: Stage2HarvesterOutput) -> str:
    # Check if vix_term_structure_table has data
    if stage_2_input.vix_term_structure_table:
        row = stage_2_input.vix_term_structure_table[0]
        try:
            m1_val = float(row.m1_future)
            m2_val = float(row.m2_future)
            slope = m2_val - m1_val
            regime = "Contango" if slope > 0 else ("Backwardation" if slope < 0 else "Flat")
            return f"{slope:+.2f} pts ({regime})"
        except (ValueError, TypeError):
            pass
    # Fallback to checking raw_kv_store
    for kv in stage_2_input.raw_kv_store.module_4_derivatives:
        if kv.key == "VIX_CURVE_SLOPE":
            return kv.value
    return "UNKNOWN"


# Prompt template for Stage 3 Quant Synthesis & Stress Testing (NO external web search permitted)
SYNTHESIS_PROMPT_TEMPLATE = """You are a Senior Institutional Quantitative Strategist and Chief Risk Officer at a multi-asset fund.
Coverage Window: {start_date} to {end_date}. Dominant Macro Theme: "{dominant_theme}".
Execution Time: {as_of_time} ET.

INPUT DATA FROM STAGE 2 HARVESTER (Zero new web searches permitted):
Module 1 Plumbing: {mod_1}
Module 2 Macro: {mod_2}
Module 3 Earnings: {mod_3}
Module 4 Derivatives: {mod_4}
Module 5 Regulatory: {mod_5}
Module 6 Geopolitics: {mod_6}
Module 7 Narratives: {mod_7}
Calculated VIX Slope: {vix_slope}

YOUR QUANTITATIVE SYNTHESIS MANDATE:
1. Asness-Style Factor Rotation Regimes: Analyze Momentum vs Value (MTUM/VLUE), Quality vs Low Vol (QUAL/USMV), Small vs Large (IWM/SPY).
2. Taleb Fragility & Convexity Stress Testing:
   - Systemic Shock: Impact of 10% equity drawdown on primary dealer balance sheets and corporate debt refinancing walls.
   - Idiosyncratic Shock: Feedback loops from liquidity drains, CTA momentum stop-loss unwinds, and margin debt velocity.
3. Tail Risk Ranking:
   - Rank exactly 3 Left-Tail risks (Downside/Vol Spikes) with estimated probability (%), direct impact asset, spillover vector, and asymmetric desk hedging stance.
   - Rank exactly 3 Right-Tail risks (Upside/Breakouts) with estimated probability (%), direct impact asset, spillover vector, and convexity capture stance.
4. Cross-Asset Spillover Matrix: Map macro catalysts to 10Y Yield (bps), DXY, Crude Oil, and Sector/Factor rotations.
5. Tactical Institutional Scenarios (MAX 100 words per scenario):
   - Base Case (Expected Path)
   - Hawkish / Liquidity Squeeze (Downside Fragility Case)
   - Goldilocks / Disinflationary Expansion (Upside Case)

Output must conform strictly to the Stage3QuantSynthesisOutput schema.
"""


# Fallback baseline synthesis model used when offline or degraded mode is triggered
def fallback_baseline_synthesis(stage_2_input: Stage2HarvesterOutput) -> Stage3QuantSynthesisOutput:
    logger.warning("Degraded Mode: Generating Baseline Quant Synthesis & Stress Test Payload.")
    vix_slope = calculate_vix_curve_slope(stage_2_input)

    return Stage3QuantSynthesisOutput(
        as_of_timestamp_et=stage_2_input.as_of_timestamp_et,
        coverage_start_date=stage_2_input.coverage_start_date,
        coverage_end_date=stage_2_input.coverage_end_date,
        dominant_theme=stage_2_input.dominant_theme,
        vix_curve_slope_pts=vix_slope if vix_slope != "UNKNOWN" else "+0.75 pts (Contango baseline)",
        atm_straddle_implied_moves=[
            KeyValueItem(key="SPX_1W_IMPLIED_MOVE", value="1.15% (Baseline ATM proxy)"),
            KeyValueItem(key="NVDA_EARNINGS_IMPLIED_MOVE", value="UNKNOWN (v14.6 Rule)"),
        ],
        factor_rotations=[
            FactorRotationRegime(
                factor_pair="Momentum vs Value (MTUM/VLUE)",
                regime_state="Momentum Extension / Crowding Risk",
                spread_observation="Spread in upper quartile vs 1-year historical range",
                transmission_mechanics="Duration repricing sensitivity elevates multiple contraction risk.",
            ),
            FactorRotationRegime(
                factor_pair="Quality vs Low Vol (QUAL/USMV)",
                regime_state="Quality Leadership",
                spread_observation="Balance sheet strength outperforming defensive yield proxies",
                transmission_mechanics="Refinancing spread stability drives institutional allocation to high-ROIC cash flows.",
            ),
            FactorRotationRegime(
                factor_pair="Small vs Large (IWM/SPY)",
                regime_state="Large-Cap Dominance",
                spread_observation="Small-cap discount persists near cycle lows",
                transmission_mechanics="High floating-rate debt exposure suppresses small-cap interest coverage ratios.",
            ),
        ],
        top_left_tail_risks=[
            TailRiskItem(
                category=TailRiskCategory.LEFT_TAIL,
                rank=1,
                catalyst_event="Hawkish Central Bank Policy Pivot / Persistent Core Inflation",
                date_horizon="Rolling 4 Weeks",
                est_prob_pct="35%",
                direct_impact_asset="US 10-Year Real Yield (TIPS)",
                spillover_vector="Real rates push > 2.25% -> Compression of mega-cap valuation multiples -> CTA momentum flip.",
                desk_hedging_stance="Long SPX 1-Month 25-delta Put Spreads funded by selling out-of-the-money upside call skew.",
            ),
            TailRiskItem(
                category=TailRiskCategory.LEFT_TAIL,
                rank=2,
                catalyst_event="Treasury Supply Indigestion & Primary Dealer Balance Sheet Constriction",
                date_horizon="Mid-Horizon Coupon Settlement",
                est_prob_pct="25%",
                direct_impact_asset="SOFR / Treasury Repo Spreads",
                spillover_vector="Primary dealers hit balance sheet capacity -> Yield curve steepens aggressively -> Cross-asset liquidity premium widens.",
                desk_hedging_stance="Payer swaptions on 5Y/30Y curve steepeners; reduce risk-parity gross leverage.",
            ),
            TailRiskItem(
                category=TailRiskCategory.LEFT_TAIL,
                rank=3,
                catalyst_event="Geopolitical Escalation at Strategic Energy Chokepoints",
                date_horizon="Continuous Rolling Window",
                est_prob_pct="20%",
                direct_impact_asset="Brent / WTI Crude Oil",
                spillover_vector="Crude oil spikes > $90/bbl -> Inflation expectations un-anchor -> Consumer discretionary margin compression.",
                desk_hedging_stance="Long 2-Month OTM WTI Call Options as asymmetric commodity spike hedge.",
            ),
        ],
        top_right_tail_risks=[
            TailRiskItem(
                category=TailRiskCategory.RIGHT_TAIL,
                rank=1,
                catalyst_event="Synchronized Disinflationary Soft Landing & Central Bank Easing Cycle",
                date_horizon="Rolling 4 Weeks",
                est_prob_pct="40%",
                direct_impact_asset="Broad Equity Indices (SPX/NDX)",
                spillover_vector="Lower discount rates + stable earnings -> Multiple expansion broadens beyond Mag-7 into cyclicals.",
                desk_hedging_stance="Overweight Quality Cyclicals; utilize call ladders on equal-weight S&P 500 (RSP).",
            ),
            TailRiskItem(
                category=TailRiskCategory.RIGHT_TAIL,
                rank=2,
                catalyst_event="Mega-Cap AI Productivity Realization & Semiconductor Capex Acceleration",
                date_horizon="Tech Earnings Window",
                est_prob_pct="30%",
                direct_impact_asset="Semiconductors (SOX Index)",
                spillover_vector="Hyperscaler capex guidance beats consensus -> Semiconductor equipment billings re-accelerate -> Tech EPS upgrades.",
                desk_hedging_stance="Bull call spreads on SOXX/SMH; long Momentum factor overlay.",
            ),
            TailRiskItem(
                category=TailRiskCategory.RIGHT_TAIL,
                rank=3,
                catalyst_event="Corporate Buyback Window Reopening Post-Earnings Blackout",
                date_horizon="Late Coverage Horizon",
                est_prob_pct="25%",
                direct_impact_asset="S&P 500 Large-Cap Equity",
                spillover_vector="Corporate repurchase desks execute > $5B/day daily passive flow -> Downside volatility suppressed.",
                desk_hedging_stance="Monetize downside put options; implement systematic delta-neutral volatility harvesting.",
            ),
        ],
        cross_asset_spillovers=[
            CrossAssetSpilloverItem(
                forward_macro_event="Jackson Hole Policy Guidance / FOMC Path",
                us_10y_yield_impact="▲ +10 bps (Hawkish) / ▼ -12 bps (Dovish)",
                dxy_impact="▲ Stronger on higher terminal rate pricing",
                crude_oil_impact="Neutral to modest softening on USD strength",
                equity_sector_factor_tilts="Outperform: Energy, Financials, Cash-flow Quality <br> Underperform: Real Estate, High-Multiple Growth",
            ),
            CrossAssetSpilloverItem(
                forward_macro_event="Mega-Cap AI Infrastructure Earnings Prints",
                us_10y_yield_impact="Neutral (Driven by micro fundamentals)",
                dxy_impact="Neutral",
                crude_oil_impact="Neutral",
                equity_sector_factor_tilts="Outperform: Semiconductor Equipment, Hyperscale Cloud <br> Underperform: Software-as-a-Service, Legacy Hardware",
            ),
        ],
        taleb_stress_test=TalebStressTest(
            systemic_shock_10pct_drawdown="A rapid 10% equity drawdown widens high-yield credit spreads by +65 bps. Primary dealer absorption capacity remains constrained by Tier-1 leverage ratios, forcing corporate borrowers with sub-BBB refinancing walls into expensive private credit channels.",
            idiosyncratic_liquidity_shock="Simultaneous TGA liquidity rebuild and ON RRP floor stagnation reduces bank reserves below comfortable thresholds. CTA momentum stop-losses trigger at index 50-DMA, accelerating systematic selling into illiquid dealer bid-ask spreads.",
        ),
        tactical_scenarios=[
            TacticalScenario(
                scenario_name="Base Case: Orderly Disinflation & Rangebound Valuation Consolidation",
                probability_pct="55%",
                core_thesis="Central banks maintain flexible data-dependency. Economic growth decelerates modestly toward trend without entering contraction. Corporate earnings meet consensus expectations, keeping equity multiples rangebound while real yields anchor around 2.00%.",
                multi_asset_positioning="Neutral benchmark duration; overweight Quality and Large-Cap Cash Cows; underweight floating-rate debt.",
            ),
            TacticalScenario(
                scenario_name="Hawkish / Liquidity Squeeze (Downside Fragility Stress Test)",
                probability_pct="25%",
                core_thesis="Core inflation components stall above 3.0%, forcing central banks to maintain restrictive terminal rates. Treasury auction concessions push 10Y yields higher, compressing equity risk premium and triggering systematic CTA de-leveraging.",
                multi_asset_positioning="Underweight duration and high-multiple growth; long volatility skew via SPX put spreads; overweight cash and energy.",
            ),
            TacticalScenario(
                scenario_name="Goldilocks / Disinflationary Expansion (Upside Case)",
                probability_pct="20%",
                core_thesis="Cooling labor costs drive core inflation back to target while productivity gains sustain profit margins. Central banks initiate gradual easing, lowering discount rates and sparking broad market participation beyond mega-caps.",
                multi_asset_positioning="Overweight Equity Beta and Small-Cap Cyclicals (IWM); extend duration in intermediate Treasuries.",
            ),
        ],
        degraded_mode=True,
        audit_trace=["Stage 3 Degraded Baseline Synthesis Utilized."],
    )


# Helper function to load Stage 2 artifact
def load_stage_2_artifact() -> Stage2HarvesterOutput:
    art_path = get_storage_base_dir() / "artifacts" / "stage_2_harvester_output.json"
    if not art_path.exists():
        raise FileNotFoundError(f"Stage 2 artifact not found at {art_path.resolve()}. Run Stage 2 first.")
    with open(art_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return Stage2HarvesterOutput.model_validate(data)


# Main callable entry point for Stage 3
def run_stage_3(
    stage_2_input: Optional[Stage2HarvesterOutput] = None,
    api_key: Optional[str] = None,
    candidate_models: Optional[List[str]] = None,
    save_artifact: bool = True,
) -> Stage3QuantSynthesisOutput:
    """
    Executes Stage 3: Quant Synthesis & Taleb Stress Tester.
    """
    logger.info("Initializing STAGE 3: Quant Synthesis & Taleb Stress Tester...")
    audit_trace: List[str] = [f"Initialized at {datetime.now(pytz.utc).isoformat()} UTC"]
    if stage_2_input is None:
        stage_2_input = load_stage_2_artifact()
    audit_trace.append(f"Synthesizing data for theme: {stage_2_input.dominant_theme}")

    # Calculate deterministic VIX slope
    vix_slope = calculate_vix_curve_slope(stage_2_input)
    audit_trace.append(f"Calculated VIX Slope: {vix_slope}")

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
                mod_5=json.dumps([kv.model_dump() for kv in stage_2_input.raw_kv_store.module_5_regulatory]),
                mod_6=json.dumps([kv.model_dump() for kv in stage_2_input.raw_kv_store.module_6_geopolitics]),
                mod_7=json.dumps([kv.model_dump() for kv in stage_2_input.raw_kv_store.module_7_narratives]),
                vix_slope=vix_slope,
            )
            parsed_json, model_used = execute_dynamic_json_query(
                prompt=prompt,
                api_key=effective_key,
                candidate_models=candidate_models,
                response_schema=Stage3QuantSynthesisOutput,
            )
            output = Stage3QuantSynthesisOutput.model_validate(parsed_json)
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
