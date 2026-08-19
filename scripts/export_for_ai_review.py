"""
Module Name: export_for_ai_review.py
Repo Path: scripts/export_for_ai_review.py

BCBS 239 Data Lineage & Compliance Standards:
- Role: Automated Codebase Bundler for Multi-LLM Adversarial Code Review.
- Supported Review Models: Claude 3.5 Sonnet, OpenAI o3/GPT-4o, DeepSeek R1/V3, Kimi K3.
- Output Destination: docs/CODEBASE_FOR_ADVERSARIAL_REVIEW.md.
"""

# Import standard library OS module for directory traversal
import os

# Import datetime for timestamping
from datetime import datetime

# Import Path for filesystem operations
from pathlib import Path

# Import typing primitives for strict type safety
from typing import List, Dict, Optional


# Pre-configured institutional adversarial review prompt
ADVERSARIAL_PROMPT_HEADER = """# INSTITUTIONAL ADVERSARIAL CODE & RISK AUDIT PROMPT
**Target Reviewers:** Claude 3.5 Sonnet | OpenAI o3 / GPT-4o | DeepSeek R1 | Kimi K3
**Role:** Senior AI/ML Architect & Tier-1 Quantitative Risk Auditor

You are tasked with conducting an uncompromising, adversarial code review of the **MacroRisk Weekly Intelligence Pipeline (v8.6 Enterprise)**.
The codebase implements an autonomous multi-stage micro-agent pipeline in Python using Pydantic v2, LangGraph StateGraph, and Google Gemini 3.x Flash.

### YOUR AUDIT MANDATE:
Critique the bundled codebase across these 5 strict institutional dimensions:
1. **Mathematical Rigor & Guardrails:** Are the deterministic formulas for ATM Straddle Implied Moves, VIX Curve Slope (M2-M1), and Asness Factor Spreads mathematically sound?
2. **BCBS 239 Governance & Data Isolation:** Are data artifacts strictly isolated from Git, and are all inter-stage contracts immutable?
3. **Zero-Hallucination Guardrails:** Is the v14.6 UNKNOWN rule properly enforced for paywalled metrics? Does the Fact-Auditor (fact_auditor.py) successfully catch hallucinated figures?
4. **LangGraph Concurrency & State Machine:** Are state updates atomic, and are list reducers (operator.add) properly configured for parallel branching?
5. **Prompt Injection & Feed Sanitization:** Are there security vulnerabilities in how raw scraped text from Trafilatura/Feedparser is fed into LLM prompts?

Provide a structured scorecard:
- **Verdict:** [APPROVED / APPROVED WITH MINOR REVISIONS / REJECTED]
- **Critical Vulnerabilities (Severity 5/5):** (if any)
- **High-Risk Observations (Severity 3-4/5):** (if any)
- **Actionable Surgical Patches:** (exact code diffs)

---
# COMPLETE CODEBASE BUNDLE:
"""


# Function to collect and bundle all repository code files
def generate_codebase_review_bundle(
    output_markdown_path: str = "docs/CODEBASE_FOR_ADVERSARIAL_REVIEW.md",
) -> str:
    """
    Scans repository for all active Python source files, tests, configurations, and workflows,
    and bundles them into a single Markdown file with the adversarial review prompt.
    """
    bundle_lines = [ADVERSARIAL_PROMPT_HEADER]
    bundle_lines.append(f"**Bundle Generated At:** {datetime.utcnow().isoformat()} UTC\n")

    # Files and directories to include
    target_paths = [
        "requirements.txt",
        ".gitignore",
        "README.md",
        ".github/workflows/macro_risk_scheduled.yml",
        "src/core/schemas.py",
        "src/core/llm_router.py",
        "src/core/math_utils.py",
        "src/core/fact_auditor.py",
        "src/core/gdrive_sync.py",
        "src/core/vector_store.py",
        "src/data/source_registry.py",
        "src/data/public_macro_api.py",
        "src/data/factor_scraper.py",
        "src/data/web_ingester.py",
        "src/data/shock_monitor.py",
        "src/stages/stage_1_temporal.py",
        "src/stages/stage_2_harvester.py",
        "src/stages/stage_3_quant.py",
        "src/stages/stage_4_formatter.py",
        "src/stages/stage_5_retail.py",
        "src/graph.py",
    ]

    # Add each target file to the bundle
    for rel_path in target_paths:
        p = Path(rel_path)
        if p.exists():
            bundle_lines.append(f"\n{'=' * 80}")
            bundle_lines.append(f"### FILE: `{rel_path}`")
            bundle_lines.append(f"{'=' * 80}")
            
            # Determine code block language
            ext = p.suffix.replace(".", "") or "txt"
            if ext == "yml":
                ext = "yaml"
            
            bundle_lines.append(f"```{ext}")
            with open(p, "r", encoding="utf-8") as f:
                bundle_lines.append(f.read().strip())
            bundle_lines.append("```\n")

    # Write final bundle to disk
    out_p = Path(output_markdown_path)
    out_p.parent.mkdir(parents=True, exist_ok=True)
    with open(out_p, "w", encoding="utf-8") as f:
        f.write("\n".join(bundle_lines))

    return str(out_p.resolve())


if __name__ == "__main__":
    generated_file = generate_codebase_review_bundle()
    print(f"Codebase bundle generated at: {generated_file}")
