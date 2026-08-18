"""
Module Name: stage_1_temporal.py
Repo Path: src/stages/stage_1_temporal.py
Stage 1: Temporal Anchoring & Regime Engine with Dynamic Model Discovery.
"""

# Import standard library OS module for environment variables and filesystem operations
import os

# Import sys module for standard output stream reference
import sys

# Import JSON module for parsing structured output
import json

# Import date and datetime types for calendar math
from datetime import date, datetime, timedelta

# Import typing primitives for strict type safety
from typing import List, Optional, Dict, Any

# Import Path for filesystem path resolution
from pathlib import Path

# Import pytz for timezone conversion to US Eastern Time
import pytz

# Import loguru logger for structured logging
from loguru import logger

# Import validated data contracts from src/core/schemas.py
from src.core.schemas import (
    MacroTier,
    EpistemicTag,
    DateWindow,
    WeeklyCalendarWindows,
    AnchorEvent,
    DominantThemeClassification,
    Stage1TemporalOutput,
)

# Import dynamic query function from llm_router (no hardcoded model imports)
from src.core.llm_router import execute_dynamic_json_query

# Configure loguru to output to standard stdout
logger.remove()
logger.add(sys.stdout, level="INFO")

# Check if running inside Google Colab
try:
    # Import userdata from google.colab
    from google.colab import userdata
    # Set Colab flag to True
    HAS_COLAB = True
# Catch error if outside Colab
except ImportError:
    # Set Colab flag to False
    HAS_COLAB = False


# Helper function to get base storage directory
def get_storage_base_dir() -> Path:
    # Check custom mount path in environment
    env_path = os.getenv("GOOGLE_DRIVE_MOUNT_PATH")
    # Return custom path if valid
    if env_path and os.path.exists(env_path):
        # Return path object
        return Path(env_path)
    # Default to local artifacts_storage directory
    local_path = Path("./artifacts_storage")
    # Ensure local directory exists
    local_path.mkdir(parents=True, exist_ok=True)
    # Return local path object
    return local_path


# Helper function to write failure logs to error_logs/
def write_error_log(stage_name: str, exception_obj: Exception) -> Path:
    # Resolve base storage path
    base_dir = get_storage_base_dir()
    # Define error logs directory path
    error_dir = base_dir / "error_logs"
    # Create error logs directory
    error_dir.mkdir(parents=True, exist_ok=True)
    # Generate timestamp string
    ts_str = datetime.now(pytz.utc).strftime("%Y%m%d_%H%M%S")
    # Formulate error log file path
    error_file = error_dir / f"{stage_name}_error_{ts_str}.log"
    # Open error log file in write mode
    with open(error_file, "w", encoding="utf-8") as ef:
        # Write stage title
        ef.write(f"PIPELINE FAILURE IN: {stage_name}\n")
        # Write failure timestamp
        ef.write(f"TIMESTAMP: {datetime.now(pytz.utc).isoformat()} UTC\n")
        # Write exception representation
        ef.write(f"EXCEPTION: {type(exception_obj).__name__}: {str(exception_obj)}\n")
        # Import traceback
        import traceback
        # Write formatted stack trace
        ef.write(traceback.format_exc())
    # Log structured error message
    logger.error(f"Fatal error logged to: {error_file.resolve()}")
    # Return path to written error log
    return error_file


# Helper function to get Gemini API key
def get_gemini_api_key() -> str:
    # Check if running in Google Colab
    if HAS_COLAB:
        # Attempt to read from Colab userdata secret vault
        try:
            # Fetch secret
            secret = userdata.get("GEMINI_API_KEY")
            # If valid, return stripped secret
            if secret:
                return str(secret).strip()
        # Catch secret retrieval exceptions
        except Exception:
            pass
    # Return key from environment variable
    return os.getenv("GEMINI_API_KEY", "").strip()


# Compute 4-week calendar windows in US Eastern Time
def compute_calendar_windows(anchor_dt: Optional[datetime] = None) -> WeeklyCalendarWindows:
    # Set US Eastern timezone
    tz_et = pytz.timezone("America/New_York")
    # Default to current time in US Eastern if not supplied
    if anchor_dt is None:
        anchor_dt = datetime.now(pytz.utc).astimezone(tz_et)
    # Extract start date
    start_d = anchor_dt.date()
    # Calculate rolling 7-day bounds
    w1_start, w1_end = start_d, start_d + timedelta(days=6)
    w2_start, w2_end = start_d + timedelta(days=7), start_d + timedelta(days=13)
    w3_start, w3_end = start_d + timedelta(days=14), start_d + timedelta(days=20)
    w4_start, w4_end = start_d + timedelta(days=21), start_d + timedelta(days=27)
    # Return structured WeeklyCalendarWindows object
    return WeeklyCalendarWindows(
        week_1=DateWindow(week_number=1, start_date=w1_start, end_date=w1_end, label=f"WEEK 1: {w1_start} to {w1_end}"),
        week_2=DateWindow(week_number=2, start_date=w2_start, end_date=w2_end, label=f"WEEK 2: {w2_start} to {w2_end}"),
        week_3=DateWindow(week_number=3, start_date=w3_start, end_date=w3_end, label=f"WEEK 3: {w3_start} to {w3_end}"),
        week_4=DateWindow(week_number=4, start_date=w4_start, end_date=w4_end, label=f"WEEK 4: {w4_start} to {w4_end}")
    )


# Route classification prompt through dynamic LLM router
def classify_macro_regime_routed(
    start_date: date,
    end_date: date,
    as_of_time: datetime,
    api_key: str,
    candidate_models: Optional[List[str]] = None
) -> tuple[DominantThemeClassification, str]:
    # Construct prompt
    prompt = (
        f"You are a Senior Institutional Risk Manager evaluating the macro calendar for rolling 7 days: {start_date} to {end_date}. "
        f"Execution Timestamp: {as_of_time} ET. Classify the week against the Algorithmic Priority Matrix:\n"
        f"- TIER_1 (Highest Priority): FOMC Rate Decision / Press Conference, Headline CPI / Core PCE, NFP, Advance GDP, Mag-7 Tech Earnings, Sovereign Credit Actions.\n"
        f"- TIER_2 (Secondary Priority): PPI, Retail Sales Control Group, ISM PMIs, Global Central Banks (ECB, BOJ, BOE, PBoC), OpEx, OPEC+ JMMC.\n"
        f"- TIER_3 (Baseline Plumbing): Regional Fed surveys, Claims, Treasury Auctions, Fed H.4.1 (TGA/ON RRP), TIPS yields.\n"
        f"Output must conform strictly to the DominantThemeClassification schema."
    )
    # Execute query through dynamic router with strict response_schema
    parsed_json, selected_model = execute_dynamic_json_query(
        prompt=prompt,
        api_key=api_key,
        candidate_models=candidate_models,
        response_schema=DominantThemeClassification,
    )
    # Return validated Pydantic model and selected model name
    return DominantThemeClassification.model_validate(parsed_json), selected_model


# Fallback baseline regime classifier
def fallback_baseline_regime(start_date: date, end_date: date) -> DominantThemeClassification:
    # Log warning notifying degraded mode
    logger.warning("Degraded Mode: Falling back to Structural Liquidity Baseline.")
    # Return deterministic Tier-3 plumbing regime
    return DominantThemeClassification(
        tier=MacroTier.TIER_3,
        dominant_theme="Structural Liquidity & Historical Baseline Plumbing",
        rationale="Fallback baseline mode triggered. Monitoring Fed H.4.1 and Treasury supply.",
        anchor_events=[AnchorEvent(event_name="Federal Reserve H.4.1 Release", event_date=start_date, tier=MacroTier.TIER_3, source_citation="federalreserve.gov", is_verified=True)]
    )


# Main callable entrypoint for Stage 1
def run_stage_1(
    anchor_dt: Optional[datetime] = None,
    api_key: Optional[str] = None,
    candidate_models: Optional[List[str]] = None,
    save_artifact: bool = True
) -> Stage1TemporalOutput:
    # Log initialization
    logger.info("Initializing STAGE 1: Temporal Anchoring & Regime Engine...")
    # Initialize audit trail list
    audit_trace: List[str] = [f"Initialized at {datetime.now(pytz.utc).isoformat()} UTC"]
    # Resolve US Eastern timezone
    tz_et = pytz.timezone("America/New_York")
    # Resolve anchor timestamp
    if anchor_dt is None:
        anchor_dt = datetime.now(pytz.utc).astimezone(tz_et)
    # Record anchor timestamp
    audit_trace.append(f"Anchored ET timestamp: {anchor_dt.isoformat()}")
    # Calculate 4-week date windows
    windows = compute_calendar_windows(anchor_dt=anchor_dt)
    # Resolve effective API key
    effective_key = get_gemini_api_key() if api_key is None else api_key.strip()
    # Initialize degraded flag
    is_degraded = False

    # Check if API key is present
    if effective_key:
        try:
            # Log commencement of dynamic router query
            logger.info("Querying LLM Router for macro regime classification...")
            # Execute routed query
            regime, model_used = classify_macro_regime_routed(
                start_date=windows.week_1.start_date,
                end_date=windows.week_1.end_date,
                as_of_time=anchor_dt,
                api_key=effective_key,
                candidate_models=candidate_models
            )
            # Record success in audit trail
            audit_trace.append(f"Classified via LLM Router using model: {model_used} (Tier={regime.tier.value})")
        except Exception as exc:
            # Log failure
            logger.error(f"All models in LLM Router failed: {exc}. Activating Degraded Mode.")
            # Persist error log to disk
            write_error_log("stage_1_temporal_llm", exc)
            # Use fallback baseline regime
            regime = fallback_baseline_regime(windows.week_1.start_date, windows.week_1.end_date)
            # Set degraded flag to True
            is_degraded = True
            # Record fallback in audit trail
            audit_trace.append("Degraded fallback mode activated due to model failure.")
    else:
        # Log missing key warning
        logger.warning("No API key provided. Activating Degraded Mode.")
        # Trigger fallback regime
        regime = fallback_baseline_regime(windows.week_1.start_date, windows.week_1.end_date)
        # Set degraded flag to True
        is_degraded = True
        # Record missing key in audit trail
        audit_trace.append("No API key provided: Degraded baseline enforced.")

    # Assemble output contract
    output = Stage1TemporalOutput(
        as_of_timestamp_et=anchor_dt,
        coverage_start_date=windows.week_1.start_date,
        coverage_end_date=windows.week_4.end_date,
        windows=windows,
        regime=regime,
        degraded_mode=is_degraded,
        audit_trace=audit_trace
    )

    # Save artifact if requested
    if save_artifact:
        # Resolve artifacts path
        art_dir = get_storage_base_dir() / "artifacts"
        art_dir.mkdir(parents=True, exist_ok=True)
        out_file = art_dir / "stage_1_temporal_output.json"
        # Write JSON to file
        with open(out_file, "w", encoding="utf-8") as out_f:
            out_f.write(output.model_dump_json(indent=2))
        logger.info(f"Artifact saved to: {out_file.resolve()}")

    # Log completion
    logger.info(f"STAGE 1 complete. [{output.regime.tier.value}] {output.regime.dominant_theme}")
    # Return output
    return output
