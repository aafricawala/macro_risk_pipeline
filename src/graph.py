"""
Module Name: graph.py
Repo Path: src/graph.py

BCBS 239 Data Lineage & Compliance Standards:
- Role: Master Pipeline DAG Orchestrator & State Coordinator.
- Execution Flow: Stage 1 (Temporal) -> Stage 2 (Harvester) -> Stage 3 (Quant) -> Stage 4 (Formatter).
- Idempotency: Safe to re-run; writes structured audit trails and isolates data to Google Drive.
"""

# Import standard library OS module for environment configuration
import os

# Import sys module for standard output stream references
import sys

# Import datetime and typing primitives for strict type safety
from datetime import datetime
from typing import Optional, List, Dict, Any
from pathlib import Path

# Import pytz for timezone management
import pytz

# Import loguru logger for structured logging
from loguru import logger

# Import schemas from src/core/schemas.py
from src.core.schemas import (
    Stage1TemporalOutput,
    Stage2HarvesterOutput,
    Stage3QuantSynthesisOutput,
    Stage4FormatterOutput,
)

# Import stage runners
from src.stages.stage_1_temporal import run_stage_1
from src.stages.stage_2_harvester import run_stage_2
from src.stages.stage_3_quant import run_stage_3
from src.stages.stage_4_formatter import run_stage_4

# Re-configure logger output
logger.remove()
logger.add(sys.stdout, level="INFO")


# Master execution function running the complete 4-stage pipeline DAG
def run_pipeline(
    anchor_dt: Optional[datetime] = None,
    api_key: Optional[str] = None,
    candidate_models: Optional[List[str]] = None,
    save_artifacts: bool = True,
) -> Stage4FormatterOutput:
    """
    Executes the complete MacroRisk Weekly Intelligence DAG:
    Stage 1: Temporal Anchoring & Regime Engine
    Stage 2: Market Plumbing & Catalyst Harvester
    Stage 3: Quant Synthesis & Taleb Stress Tester
    Stage 4: Executive Formatter & Serialization
    """
    # Start timer and log DAG initialization
    start_time = datetime.now(pytz.utc)
    logger.info("=" * 80)
    logger.info("STARTING MACRORISK PRODUCTION PIPELINE DAG (v8.6 Enterprise)")
    logger.info(f"Execution Start: {start_time.isoformat()} UTC")
    logger.info("=" * 80)

    # -------------------------------------------------------------
    # STAGE 1: TEMPORAL ANCHORING & REGIME ENGINE
    # -------------------------------------------------------------
    logger.info(">>> [STAGE 1/4] Executing Temporal Anchoring & Regime Engine...")
    s1_output = run_stage_1(
        anchor_dt=anchor_dt,
        api_key=api_key,
        candidate_models=candidate_models,
        save_artifact=save_artifacts,
    )
    logger.info(f"[STAGE 1 DONE] Theme: [{s1_output.regime.tier.value}] {s1_output.regime.dominant_theme}")

    # -------------------------------------------------------------
    # STAGE 2: MARKET PLUMBING & CATALYST HARVESTER
    # -------------------------------------------------------------
    logger.info(">>> [STAGE 2/4] Executing Market Plumbing & Catalyst Harvester...")
    s2_output = run_stage_2(
        stage_1_input=s1_output,
        api_key=api_key,
        candidate_models=candidate_models,
        save_artifact=save_artifacts,
    )
    logger.info(f"[STAGE 2 DONE] Harvested {len(s2_output.raw_kv_store.module_1_plumbing)} plumbing metrics, {len(s2_output.audit_log_table)} audit claims.")

    # -------------------------------------------------------------
    # STAGE 3: QUANT SYNTHESIS & TALEB STRESS TESTER
    # -------------------------------------------------------------
    logger.info(">>> [STAGE 3/4] Executing Quant Synthesis & Taleb Stress Tester...")
    s3_output = run_stage_3(
        stage_2_input=s2_output,
        api_key=api_key,
        candidate_models=candidate_models,
        save_artifact=save_artifacts,
    )
    logger.info(f"[STAGE 3 DONE] Ranked {len(s3_output.top_left_tail_risks)} Left-Tail & {len(s3_output.top_right_tail_risks)} Right-Tail risks.")

    # -------------------------------------------------------------
    # STAGE 4: EXECUTIVE FORMATTER & SERIALIZATION
    # -------------------------------------------------------------
    logger.info(">>> [STAGE 4/4] Executing Executive Formatter & Serialization...")
    s4_output = run_stage_4(
        stage_1_input=s1_output,
        stage_2_input=s2_output,
        stage_3_input=s3_output,
        api_key=api_key,
        save_production=save_artifacts,
    )
    logger.info(f"[STAGE 4 DONE] Production Report generated ({s4_output.word_count_briefing} briefing words).")

    # Log completion metrics
    elapsed_seconds = (datetime.now(pytz.utc) - start_time).total_seconds()
    logger.info("=" * 80)
    logger.info(f"MACRORISK PIPELINE DAG COMPLETED IN {elapsed_seconds:.2f}s")
    logger.info(f"Report Location: {s4_output.report_file_path}")
    logger.info(f"CSV Appendices:  {len(s4_output.csv_file_paths)} files persisted to Production/csv_appendices/")
    logger.info("=" * 80)

    return s4_output


if __name__ == "__main__":
    run_pipeline()
