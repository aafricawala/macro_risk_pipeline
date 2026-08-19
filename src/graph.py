"""
Module Name: graph.py
Repo Path: src/graph.py

BCBS 239 Data Lineage & Compliance Standards:
- Role: Master Pipeline LangGraph StateGraph Coordinator with Parallel Dual-Auditing.
- Architecture: Typed StateGraph with atomic delta state returns and Annotated operator.add reducers.
- Flow: START -> S1 -> S2 -> S3 -> [S4 (Institutional) | S5 (Retail)] -> Fact-Auditor Gatekeeper -> END.
"""

# Import standard library OS module for environment configuration
import os

# Import sys module for standard output stream references
import sys

# Import json module for state serializations
import json

# Import operator for LangGraph list reducer concatenation
import operator

# Import datetime and date for temporal modeling
from datetime import datetime, date

# Import typing primitives, Annotated, and TypedDict for LangGraph state typing
from typing import Optional, List, Dict, Any, TypedDict, Tuple, Annotated

# Import Path for filesystem path resolution
from pathlib import Path

# Import pytz for timezone management
import pytz

# Import loguru logger for structured diagnostic logs
from loguru import logger

# Import LangGraph state machine components
from langgraph.graph import StateGraph, START, END

# Import core schemas and models
from src.core.schemas import (
    Stage1TemporalOutput,
    Stage2HarvesterOutput,
    Stage3QuantSynthesisOutput,
    Stage4FormatterOutput,
    Stage5RetailFormatterOutput,
)

# Import fact auditor model and verification function
from src.core.fact_auditor import FactAuditResult, audit_report_against_raw_kv

# Import stage runners
from src.stages.stage_1_temporal import run_stage_1
from src.stages.stage_2_harvester import run_stage_2
from src.stages.stage_3_quant import run_stage_3
from src.stages.stage_4_formatter import run_stage_4
from src.stages.stage_5_retail import run_stage_5

# Reconfigure logger output stream to stdout
logger.remove()
logger.add(sys.stdout, level="INFO")


# Define typed state schema for the LangGraph StateGraph with list reducers
class MacroRiskGraphState(TypedDict, total=False):
    # Execution timestamp in US Eastern Time
    anchor_dt: Optional[datetime]
    # Gemini API key
    api_key: Optional[str]
    # Optional candidate models list for dynamic router
    candidate_models: Optional[List[str]]
    # Flag to persist outputs to Google Drive
    save_artifacts: bool
    # Stage 1 Temporal output
    stage_1_output: Optional[Stage1TemporalOutput]
    # Stage 2 Harvester output
    stage_2_output: Optional[Stage2HarvesterOutput]
    # Stage 3 Quant output
    stage_3_output: Optional[Stage3QuantSynthesisOutput]
    # Stage 4 Institutional Formatter output
    stage_4_output: Optional[Stage4FormatterOutput]
    # Stage 5 Retail Formatter output
    stage_5_output: Optional[Stage5RetailFormatterOutput]
    # Post-generation fact-auditor verification for Institutional report
    institutional_fact_audit: Optional[FactAuditResult]
    # Post-generation fact-auditor verification for Retail note
    retail_fact_audit: Optional[FactAuditResult]
    # Cumulative data lineage audit trace using operator.add reducer for parallel branch merging
    audit_trace: Annotated[List[str], operator.add]
    # Error message if any stage encounters fatal failure
    error: Optional[str]


# Node 1: Temporal Anchoring & Priority Matrix Engine
def node_temporal_regime(state: MacroRiskGraphState) -> Dict[str, Any]:
    logger.info(">>> [LangGraph Node 1] Executing Temporal Anchoring & Regime Engine...")
    s1_out = run_stage_1(
        anchor_dt=state.get("anchor_dt"),
        api_key=state.get("api_key"),
        candidate_models=state.get("candidate_models"),
        save_artifact=state.get("save_artifacts", True),
    )
    return {
        "stage_1_output": s1_out,
        "audit_trace": [f"LangGraph Node 1 Completed: Theme='{s1_out.regime.dominant_theme}' [{s1_out.regime.tier.value}]"]
    }


# Node 2: Market Plumbing & Catalyst Harvester
def node_market_plumbing_harvester(state: MacroRiskGraphState) -> Dict[str, Any]:
    logger.info(">>> [LangGraph Node 2] Executing Market Plumbing & Catalyst Harvester...")
    s1_out = state.get("stage_1_output")
    s2_out = run_stage_2(
        stage_1_input=s1_out,
        api_key=state.get("api_key"),
        candidate_models=state.get("candidate_models"),
        save_artifact=state.get("save_artifacts", True),
    )
    return {
        "stage_2_output": s2_out,
        "audit_trace": [f"LangGraph Node 2 Completed: {len(s2_out.raw_kv_store.module_1_plumbing)} plumbing metrics, {len(s2_out.treasury_auctions_table)} auctions"]
    }


# Node 3: Quant Synthesis & Taleb Stress Tester
def node_quant_synthesis(state: MacroRiskGraphState) -> Dict[str, Any]:
    logger.info(">>> [LangGraph Node 3] Executing Quant Synthesis & Taleb Stress Tester...")
    s2_out = state.get("stage_2_output")
    s3_out = run_stage_3(
        stage_2_input=s2_out,
        api_key=state.get("api_key"),
        candidate_models=state.get("candidate_models"),
        save_artifact=state.get("save_artifacts", True),
    )
    return {
        "stage_3_output": s3_out,
        "audit_trace": [f"LangGraph Node 3 Completed: Ranked {len(s3_out.top_left_tail_risks)} Left-Tail & {len(s3_out.top_right_tail_risks)} Right-Tail risks"]
    }


# Node 4: Executive Formatter (Branch A - Institutional)
def node_executive_formatter(state: MacroRiskGraphState) -> Dict[str, Any]:
    logger.info(">>> [LangGraph Branch A] Executing Institutional C-Suite Formatter...")
    s1_out = state.get("stage_1_output")
    s2_out = state.get("stage_2_output")
    s3_out = state.get("stage_3_output")
    s4_out = run_stage_4(
        stage_1_input=s1_out,
        stage_2_input=s2_out,
        stage_3_input=s3_out,
        api_key=state.get("api_key"),
        save_production=state.get("save_artifacts", True),
    )
    return {
        "stage_4_output": s4_out,
        "audit_trace": [f"LangGraph Branch A Completed: Institutional report rendered ({s4_out.word_count_briefing} words)"]
    }


# Node 5: Retail Investor Formatter (Branch B - Plain English)
def node_retail_formatter(state: MacroRiskGraphState) -> Dict[str, Any]:
    logger.info(">>> [LangGraph Branch B] Executing Retail Investor Plain-English Formatter...")
    s1_out = state.get("stage_1_output")
    s3_out = state.get("stage_3_output")
    s5_out = run_stage_5(
        stage_1_input=s1_out,
        stage_3_input=s3_out,
        api_key=state.get("api_key"),
        candidate_models=state.get("candidate_models"),
        save_production=state.get("save_artifacts", True),
    )
    return {
        "stage_5_output": s5_out,
        "audit_trace": [f"LangGraph Branch B Completed: Retail report rendered with Traffic Light [{s5_out.traffic_light_status.value}]"]
    }


# Node 6: Fact-Auditor Critic & Anti-Hallucination Gatekeeper (Dual Convergent Audit)
def node_fact_auditor_critic(state: MacroRiskGraphState) -> Dict[str, Any]:
    logger.info(">>> [LangGraph Convergent Node 6] Executing Dual Fact-Auditor Verification (Institutional & Retail)...")
    s2_out = state.get("stage_2_output")
    s4_out = state.get("stage_4_output")
    s5_out = state.get("stage_5_output")

    inst_audit = None
    ret_audit = None
    audit_logs: List[str] = []

    if s2_out:
        # 1. Audit Institutional C-Suite Report
        if s4_out:
            inst_audit = audit_report_against_raw_kv(
                report_markdown=s4_out.report_markdown,
                raw_kv_store=s2_out.raw_kv_store,
                strict_redaction=False,
            )
            logger.info(f"Institutional Audit: Clean={inst_audit.is_clean} ({inst_audit.verified_matches} claims grounded, {len(inst_audit.hallucination_alerts)} alerts)")
            audit_logs.append(f"Institutional Audit: Clean={inst_audit.is_clean} ({inst_audit.verified_matches} grounded)")

        # 2. Audit Retail Investor Note
        if s5_out:
            ret_audit = audit_report_against_raw_kv(
                report_markdown=s5_out.retail_report_markdown,
                raw_kv_store=s2_out.raw_kv_store,
                strict_redaction=False,
            )
            logger.info(f"Retail Note Audit: Clean={ret_audit.is_clean} ({ret_audit.verified_matches} claims grounded, {len(ret_audit.hallucination_alerts)} alerts)")
            audit_logs.append(f"Retail Note Audit: Clean={ret_audit.is_clean} ({ret_audit.verified_matches} grounded)")

    return {
        "institutional_fact_audit": inst_audit,
        "retail_fact_audit": ret_audit,
        "audit_trace": audit_logs,
    }


# Build and compile the master dual-audited LangGraph StateGraph
def build_macrorisk_graph():
    builder = StateGraph(MacroRiskGraphState)

    # Register all 6 nodes
    builder.add_node("temporal_regime", node_temporal_regime)
    builder.add_node("market_plumbing_harvester", node_market_plumbing_harvester)
    builder.add_node("quant_synthesis", node_quant_synthesis)
    builder.add_node("executive_formatter", node_executive_formatter)
    builder.add_node("retail_formatter", node_retail_formatter)
    builder.add_node("fact_auditor_critic", node_fact_auditor_critic)

    # Sequential upstream flow
    builder.add_edge(START, "temporal_regime")
    builder.add_edge("temporal_regime", "market_plumbing_harvester")
    builder.add_edge("market_plumbing_harvester", "quant_synthesis")

    # PARALLEL FORKING FROM STAGE 3
    builder.add_edge("quant_synthesis", "executive_formatter")
    builder.add_edge("quant_synthesis", "retail_formatter")

    # CONVERGENT MERGE INTO DUAL FACT-AUDITOR GATEKEEPER
    builder.add_edge("executive_formatter", "fact_auditor_critic")
    builder.add_edge("retail_formatter", "fact_auditor_critic")
    builder.add_edge("fact_auditor_critic", END)

    # Compile executable graph
    return builder.compile()


# Master callable entrypoint executing the compiled LangGraph StateGraph
def run_pipeline(
    anchor_dt: Optional[datetime] = None,
    api_key: Optional[str] = None,
    candidate_models: Optional[List[str]] = None,
    save_artifacts: bool = True,
) -> Stage4FormatterOutput:
    """
    Executes the complete Dual-Audited MacroRisk Weekly Intelligence pipeline via LangGraph StateGraph.
    """
    start_time = datetime.now(pytz.utc)
    logger.info("=" * 80)
    logger.info("STARTING MACRORISK DUAL-AUDITED LANGGRAPH STATEGRAPH PIPELINE")
    logger.info(f"Execution Start: {start_time.isoformat()} UTC")
    logger.info("=" * 80)

    # Compile the LangGraph state machine
    graph = build_macrorisk_graph()

    # Define initial input state
    initial_state: MacroRiskGraphState = {
        "anchor_dt": anchor_dt,
        "api_key": api_key,
        "candidate_models": candidate_models,
        "save_artifacts": save_artifacts,
        "audit_trace": [f"Pipeline initialized at {start_time.isoformat()} UTC"],
    }

    # Execute graph invocation (executes both branches and converges at Fact-Auditor)
    final_state = graph.invoke(initial_state)

    # Extract Stage 4 (Institutional) and Stage 5 (Retail) outputs
    s4_output = final_state.get("stage_4_output")
    s5_output = final_state.get("stage_5_output")

    if s4_output is None:
        raise RuntimeError("LangGraph execution completed but stage_4_output was not generated.")

    # Attach audit trace to final output
    s4_output.audit_trace.extend(final_state.get("audit_trace", []))

    elapsed = (datetime.now(pytz.utc) - start_time).total_seconds()
    logger.info("=" * 80)
    logger.info(f"MACRORISK DUAL-AUDITED PIPELINE COMPLETED IN {elapsed:.2f}s")
    logger.info(f"Institutional Report: {s4_output.report_file_path}")
    if s5_output:
        logger.info(f"Retail Investor Note: {s5_output.retail_file_path} (Traffic Light: {s5_output.traffic_light_status.value})")
    logger.info("=" * 80)

    return s4_output


if __name__ == "__main__":
    run_pipeline()
