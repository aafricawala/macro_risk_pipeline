"""
Module Name: stage_5_retail.py
Repo Path: src/stages/stage_5_retail.py

BCBS 239 Data Lineage & Compliance Standards:
- Role: Stage 5 Retail Investor Formatter (Parallel Forked DAG Branch).
- Plain-English Translation Layer: Translates VIX slope, factor rotations, and Taleb stress tests
  into intuitive portfolio action items for educated retail investors (401k/IRA, Bonds, Cash).
- Output Destination: Persisted to Google Drive Production/MacroRisk_Weekly_Retail_Investor_Note_{DATE}.md.
"""

# Import standard library OS module for directory and filesystem operations
import os

# Import sys module for standard output stream references
import sys

# Import json module for metadata parsing
import json

# Import datetime and date types for timestamps
from datetime import date, datetime

# Import typing primitives for strict type safety
from typing import List, Optional, Dict, Any, Tuple

# Import Path for filesystem path resolution
from pathlib import Path

# Import pytz for timezone management
import pytz

# Import loguru logger for structured logging
from loguru import logger

# Import validated schemas from src/core/schemas.py
from src.core.schemas import (
    Stage1TemporalOutput,
    Stage3QuantSynthesisOutput,
    Stage5RetailFormatterOutput,
    TrafficLightStatus,
    RetailActionItem,
)

# Import dynamic LLM router
from src.core.llm_router import execute_dynamic_json_query

# Configure loguru logger to output to standard stdout
logger.remove()
logger.add(sys.stdout, level="INFO")

# Check if running in Google Colab
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


# Deterministic calculation of Retail Traffic Light Status based on VIX slope and tail risk
def determine_traffic_light_status(s3: Stage3QuantSynthesisOutput) -> Tuple[TrafficLightStatus, str]:
    """
    Evaluates quantitative state to determine plain-English market traffic light:
    - GREEN: VIX in Contango, low left-tail probabilities (< 30%).
    - YELLOW: VIX flat/moderate Contango, elevated macro catalyst events (30-40%).
    - RED: VIX in Backwardation (inversion) or high left-tail probability (> 40%).
    """
    vix_str = s3.vix_curve_slope_pts.lower()
    
    # Check for VIX backwardation inversion (Red Alert)
    if "backwardation" in vix_str or "-" in vix_str:
        return TrafficLightStatus.RED, "RED (High Caution): Market volatility term structure is inverted, indicating elevated near-term market turbulence."

    # Check top left-tail risk estimated probability
    if s3.top_left_tail_risks:
        top_prob_str = s3.top_left_tail_risks[0].est_prob_pct.replace("%", "").strip()
        try:
            top_prob = float(top_prob_str)
            if top_prob >= 35.0:
                return TrafficLightStatus.YELLOW, "YELLOW (Moderate Caution): Approaching major central bank policy and earnings catalysts; rangebound market conditions expected."
        except ValueError:
            pass

    # Default to Green if Contango calm persists
    return TrafficLightStatus.GREEN, "GREEN (Favorable / Calm): Market fear indicators are subdued with volatility in standard contango; maintain long-term core allocations."


# Prompt template for Stage 5 Plain-English Retail Translation
RETAIL_PROMPT_TEMPLATE = """You are a Senior Wealth Advisor and Personal Finance Strategist translating complex institutional macro intelligence for everyday educated retail investors.
Coverage Window: {start_date} to {end_date}. Dominant Macro Theme: "{dominant_theme}".
Traffic Light: {traffic_light_status} - {traffic_light_summary}
VIX Term Structure Slope: {vix_slope}
Top Left-Tail Risk: {left_tail_1}
Top Right-Tail Catalyst: {right_tail_1}
Key Tactical Scenario: {base_scenario}

Write a high-signal, engaging, plain-English retail newsletter markdown report following this exact structure:
# 🚦 MACRORISK WEEKLY RETAIL NOTE: {dominant_theme}
**Coverage Window:** {start_date} to {end_date} | **Traffic Light Status:** {traffic_light_status}

### 1. 💡 The 3 Big Things You Need to Know This Week
(3 bullet points explaining the macro environment in simple, relatable terms without financial jargon).

### 2. 📊 What This Means for Your Money (Action Checklist)
* **Stocks & Retirement (401k / IRA):** (Practical advice on broad market index funds vs dividend/growth tilt).
* **Bonds & Fixed Income (CDs & Treasuries):** (Guidance on locking in cash/bond yields).
* **Cash & Savings (Emergency Fund):** (Where to hold short-term reserves).

### 3. ⚠️ Top 2 Pitfalls to Avoid This Week
(2 common behavioral mistakes retail investors make in this specific market regime).

### 4. 📅 Plain-English Events Watchlist
(Top 2 upcoming events explained in 1 simple sentence each).

### 5. 📖 30-Second Jargon Buster
(Pick one term: VIX Contango, Real Yields, or Treasury Supply, and explain it using a simple everyday analogy).

Output ONLY the complete retail markdown text.
"""


# Fallback deterministic retail note generator
def fallback_baseline_retail_note(s1: Stage1TemporalOutput, s3: Stage3QuantSynthesisOutput) -> Stage5RetailFormatterOutput:
    logger.warning("Degraded Mode: Generating Baseline Retail Formatter Payload.")
    status, summary = determine_traffic_light_status(s3)
    start_str = s1.coverage_start_date.isoformat()
    end_str = s1.coverage_end_date.isoformat()

    retail_md = (
        f"# 🚦 MACRORISK WEEKLY RETAIL NOTE: {s1.regime.dominant_theme}\n"
        f"**Coverage Window:** {start_str} to {end_str} | **Traffic Light Status:** {status.value}\n\n"
        f"**Weekly Market Vibe:** {summary}\n\n"
        "### 1. 💡 The 3 Big Things You Need to Know This Week\n"
        "* **The Fed is Watching Inflation Data Closely:** Central bankers are preparing their next interest rate policy decisions; markets expect interest rates to remain steady for now.\n"
        f"* **Market Calm Meter (VIX):** Fear gauges are in normal calm mode ({s3.vix_curve_slope_pts}), meaning options traders do not see an immediate market panic.\n"
        "* **Big Tech & Earnings Season:** Major corporate announcements will drive day-to-day stock swings, making steady diversification important.\n\n"
        "### 2. 📊 What This Means for Your Money (Action Checklist)\n"
        "* **Stocks & Retirement (401k / IRA):** Stay diversified in low-cost S&P 500 or total stock market index funds. Avoid making emotional trades around single-day headlines.\n"
        "* **Bonds & Fixed Income:** Yields on high-quality short-term Treasuries and CDs remain attractive. It is a good time to keep fixed income balanced.\n"
        "* **Cash & Emergency Savings:** Keep emergency savings parked in high-yield savings accounts (HYSA) or Treasury money market funds yielding competitive safe cash returns.\n\n"
        "### 3. ⚠️ Top 2 Pitfalls to Avoid This Week\n"
        "1. **Don't Panic-Sell on Headlines:** Day-to-day news around speech transcripts often causes temporary noise that smooths out over multi-month horizons.\n"
        "2. **Avoid Chasing Overheated Stocks:** Stick to scheduled dollar-cost averaging into broad indexes rather than jumping into parabolic momentum movers.\n\n"
        "### 4. 📅 Plain-English Events Watchlist\n"
        "* **Federal Reserve Meeting Minutes:** An official recap showing how central bankers view current economic health.\n"
        "* **Flash Economic Growth Prints (PMI):** A survey showing whether businesses are expanding or slowing down.\n\n"
        "### 5. 📖 30-Second Jargon Buster: 'VIX Contango'\n"
        "* **What it means:** Think of the VIX like hurricane insurance. 'Contango' simply means market insurance for next month costs slightly more than today because the immediate skies look clear!\n\n"
        "---\n"
        "*Disclaimer: Prepared for educational and personal financial research purposes.*"
    )

    checklist = [
        RetailActionItem(asset_bucket="Stocks (401k / IRA)", action_guidance="Maintain steady dollar-cost averaging into broad low-cost index funds; resist chasing hype."),
        RetailActionItem(asset_bucket="Bonds / CDs", action_guidance="Lock in competitive safe yields on short-to-intermediate government bonds."),
        RetailActionItem(asset_bucket="Cash Reserves", action_guidance="Keep 3-6 months emergency savings in High-Yield Savings Accounts (HYSA)."),
    ]

    return Stage5RetailFormatterOutput(
        as_of_timestamp_et=s1.as_of_timestamp_et,
        coverage_start_date=s1.coverage_start_date,
        coverage_end_date=s1.coverage_end_date,
        traffic_light_status=status,
        traffic_light_summary=summary,
        retail_report_markdown=retail_md,
        retail_file_path="./Production/MacroRisk_Weekly_Retail_Investor_Note.md",
        action_checklist=checklist,
        audit_trace=["Stage 5 Baseline Retail Formatter Utilized."],
    )


# Helper function to load upstream artifacts
def load_upstream_s1_and_s3() -> Tuple[Stage1TemporalOutput, Stage3QuantSynthesisOutput]:
    base_dir = get_storage_base_dir() / "artifacts"
    p1 = base_dir / "stage_1_temporal_output.json"
    p3 = base_dir / "stage_3_quant_output.json"

    if not p1.exists() or not p3.exists():
        raise FileNotFoundError(f"Missing artifacts in {base_dir.resolve()}. Run Stages 1 and 3 first.")

    with open(p1, "r", encoding="utf-8") as f:
        s1 = Stage1TemporalOutput.model_validate(json.load(f))
    with open(p3, "r", encoding="utf-8") as f:
        s3 = Stage3QuantSynthesisOutput.model_validate(json.load(f))

    return s1, s3


# Main callable entry point for Stage 5 Retail Formatter
def run_stage_5(
    stage_1_input: Optional[Stage1TemporalOutput] = None,
    stage_3_input: Optional[Stage3QuantSynthesisOutput] = None,
    api_key: Optional[str] = None,
    candidate_models: Optional[List[str]] = None,
    save_production: bool = True,
) -> Stage5RetailFormatterOutput:
    """
    Executes Stage 5: Retail Investor Plain-English Formatter.
    """
    logger.info("Initializing STAGE 5: Retail Investor Formatter...")
    audit_trace: List[str] = [f"Initialized at {datetime.now(pytz.utc).isoformat()} UTC"]

    if stage_1_input is None or stage_3_input is None:
        s1, s3 = load_upstream_s1_and_s3()
    else:
        s1, s3 = stage_1_input, stage_3_input

    # Determine deterministic Traffic Light status
    status, summary = determine_traffic_light_status(s3)
    audit_trace.append(f"Determined Traffic Light Status: {status.value}")

    effective_key = get_gemini_api_key() if api_key is None else api_key.strip()
    generated_md = ""

    lt1_event = s3.top_left_tail_risks[0].catalyst_event if s3.top_left_tail_risks else "Policy Rate Repricing"
    rt1_event = s3.top_right_tail_risks[0].catalyst_event if s3.top_right_tail_risks else "Soft Landing Growth"
    base_sc = s3.tactical_scenarios[0].core_thesis if s3.tactical_scenarios else "Orderly Disinflation"

    if effective_key:
        try:
            logger.info("Querying LLM Router for plain-English retail newsletter synthesis...")
            prompt = RETAIL_PROMPT_TEMPLATE.format(
                start_date=s1.coverage_start_date.isoformat(),
                end_date=s1.coverage_end_date.isoformat(),
                dominant_theme=s1.regime.dominant_theme,
                traffic_light_status=status.value,
                traffic_light_summary=summary,
                vix_slope=s3.vix_curve_slope_pts,
                left_tail_1=lt1_event,
                right_tail_1=rt1_event,
                base_scenario=base_sc,
            )
            from google import genai
            from google.genai import types
            client = genai.Client(api_key=effective_key)
            resp = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=prompt,
                config=types.GenerateContentConfig(temperature=0.3)
            )
            if resp.text:
                generated_md = resp.text.strip()
                audit_trace.append("Synthesized retail note via Gemini 2.5 Flash.")
        except Exception as exc:
            logger.warning(f"LLM retail note synthesis failed: {exc}. Utilizing baseline retail note.")
            write_error_log("stage_5_retail_llm", exc)

    if not generated_md:
        fallback_res = fallback_baseline_retail_note(s1, s3)
        generated_md = fallback_res.retail_report_markdown

    # Action checklist items
    action_items = [
        RetailActionItem(asset_bucket="Stocks (401k / IRA)", action_guidance="Maintain steady dollar-cost averaging into broad low-cost index funds; resist chasing hype."),
        RetailActionItem(asset_bucket="Bonds / CDs", action_guidance="Lock in competitive safe yields on short-to-intermediate government bonds."),
        RetailActionItem(asset_bucket="Cash Reserves", action_guidance="Keep 3-6 months emergency savings in High-Yield Savings Accounts (HYSA)."),
    ]

    report_file_path = ""
    if save_production:
        base_dir = get_storage_base_dir()
        prod_dir = base_dir / "Production"
        prod_dir.mkdir(parents=True, exist_ok=True)
        rep_date = s1.coverage_start_date.isoformat()
        report_file = prod_dir / f"MacroRisk_Weekly_Retail_Investor_Note_{rep_date}.md"
        with open(report_file, "w", encoding="utf-8") as f:
            f.write(generated_md)
        report_file_path = str(report_file.resolve())
        logger.info(f"Retail Investor Note written to Google Drive: {report_file_path}")

    output = Stage5RetailFormatterOutput(
        as_of_timestamp_et=s1.as_of_timestamp_et,
        coverage_start_date=s1.coverage_start_date,
        coverage_end_date=s1.coverage_end_date,
        traffic_light_status=status,
        traffic_light_summary=summary,
        retail_report_markdown=generated_md,
        retail_file_path=report_file_path or "./Retail_Note.md",
        action_checklist=action_items,
        audit_trace=audit_trace,
    )

    logger.info(f"STAGE 5 complete. Retail report generated with Traffic Light [{status.value}].")
    return output
