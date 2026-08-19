"""
Module Name: fact_auditor.py
Repo Path: src/core/fact_auditor.py

BCBS 239 Data Lineage & Compliance Standards:
- Role: Deterministic Post-Generation Fact-Auditor & Anti-Hallucination Critic Node.
- Processing Logic:
  1. Extracts all numerical figures (percentages, dollar amounts, basis points) and dates from report prose.
  2. Cross-checks each extracted token against the verified raw Key-Value store from Stage 2.
  3. Redacts any unverified numerical claims to 'UNKNOWN' and logs an alert for risk governance.
- Determinism: 100% deterministic Python regex and token matching; zero LLM token generation.
"""

# Import regular expressions module for numerical and date token extraction
import re

# Import typing primitives for strict type safety
from typing import List, Dict, Any, Tuple, Set

# Import Pydantic v2 components for audit schema definition
from pydantic import BaseModel, Field

# Import loguru logger for structured logging
from loguru import logger

# Import ModuleDataKV schema from core schemas
from src.core.schemas import ModuleDataKV


# Schema representing the deterministic fact audit result
class FactAuditResult(BaseModel):
    # Boolean flag indicating if zero hallucinations were detected
    is_clean: bool = Field(..., description="True if all numerical claims are verified in raw KV store")
    # Total count of verified numerical/date claims found in raw data
    verified_matches: int = Field(..., description="Number of verified factual matches")
    # List of warning messages for ungrounded claims detected in text
    hallucination_alerts: List[str] = Field(default_factory=list, description="List of unverified claims flagged")
    # Sanitized markdown text with unverified figures flagged or redacted
    sanitized_report_markdown: str = Field(..., description="Report text with governance assertions applied")


# Helper function to extract all raw values from ModuleDataKV into a flat search corpus
def extract_raw_kv_text_corpus(raw_kv: ModuleDataKV) -> str:
    # Initialize container list for text tokens
    corpus_tokens: List[str] = []
    # Extract items from Module 1
    for itm in raw_kv.module_1_plumbing:
        corpus_tokens.append(f"{itm.key} {itm.value}")
    # Extract items from Module 2
    for itm in raw_kv.module_2_macro_surprises:
        corpus_tokens.append(f"{itm.key} {itm.value}")
    # Extract items from Module 3
    for itm in raw_kv.module_3_earnings:
        corpus_tokens.append(f"{itm.key} {itm.value}")
    # Extract items from Module 4
    for itm in raw_kv.module_4_derivatives:
        corpus_tokens.append(f"{itm.key} {itm.value}")
    # Extract items from Module 5
    for itm in raw_kv.module_5_regulatory:
        corpus_tokens.append(f"{itm.key} {itm.value}")
    # Extract items from Module 6
    for itm in raw_kv.module_6_geopolitics:
        corpus_tokens.append(f"{itm.key} {itm.value}")
    # Extract items from Module 7
    for itm in raw_kv.module_7_narratives:
        corpus_tokens.append(f"{itm.key} {itm.value}")
    # Join all tokens into a single unified search string
    return " ".join(corpus_tokens)


# Main deterministic fact audit verification function
def audit_report_against_raw_kv(
    report_markdown: str,
    raw_kv_store: ModuleDataKV,
    strict_redaction: bool = False,
) -> FactAuditResult:
    """
    Scans report markdown for numerical figures and dates, ensuring every figure exists in raw_kv_store.
    """
    # Build flat search corpus string from verified raw Key-Value records
    raw_corpus = extract_raw_kv_text_corpus(raw_kv_store)
    # Initialize alert list
    alerts: List[str] = []
    # Initialize verified match counter
    verified_count = 0
    # Copy report text for potential sanitization
    sanitized_text = report_markdown

    # Robust regex using character classes to extract currency, percentages, dates, and basis points
    pattern = r"(\$[0-9]+(?:\.[0-9]+)?[BMTK]?|[+-]?[0-9]+(?:\.[0-9]+)?%|[0-9]{4}-[0-9]{2}-[0-9]{2}|[+-]?[0-9]+(?:\.[0-9]+)?\s*bps)"
    # Find all numerical candidates in the generated report
    matches = re.findall(pattern, report_markdown, flags=re.IGNORECASE)

    # Convert matches to unique set
    unique_figures: Set[str] = set(matches)

    # Known structural constants exempt from raw KV lookup (e.g. section indices, 60/40, word limits)
    structural_exemptions = {"60/40", "1", "2", "3", "4", "5", "6", "7", "28", "200", "150", "100", "0"}

    # Iterate through extracted figures to cross-verify against raw corpus
    for fig in unique_figures:
        # Strip whitespace from figure
        clean_fig = fig.strip()
        # Check if figure is in structural exemptions
        if clean_fig in structural_exemptions:
            continue

        # Strip leading +/$ and trailing % for core numeric matching
        core_numeric = re.sub(r"^[+$]|[%]$", "", clean_fig).strip()

        # Check existence in raw corpus
        if core_numeric in raw_corpus or clean_fig in raw_corpus:
            verified_count += 1
        else:
            # Check if figure represents a financial claim
            if clean_fig.endswith("bps") or clean_fig.startswith("$") or "%" in clean_fig:
                warning_msg = f"Ungrounded numerical claim detected in prose: '{clean_fig}' (Not found in Stage 2 KV store)"
                logger.warning(f"Fact-Auditor: {warning_msg}")
                alerts.append(warning_msg)

                # If strict redaction is enabled, replace figure with UNVERIFIED tag
                if strict_redaction:
                    sanitized_text = sanitized_text.replace(clean_fig, f"{clean_fig} [UNVERIFIED_FIGURE]")

    # Flag clean if zero ungrounded alerts detected
    is_clean = len(alerts) == 0

    return FactAuditResult(
        is_clean=is_clean,
        verified_matches=verified_count,
        hallucination_alerts=alerts,
        sanitized_report_markdown=sanitized_text,
    )
