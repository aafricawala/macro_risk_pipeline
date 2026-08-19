# MacroRisk Weekly Intelligence Pipeline (v8.6 Enterprise)

A deterministic, multi-stage micro-agent pipeline that produces an institution-grade Macro Risk Weekly Status Report, 7 BCBS 239-compliant structured CSV appendices, and an actionable Retail Investor Note for senior C-suite risk desks and multi-asset portfolio managers.

---

## 🏛️ Master Architecture (LangGraph Dual-Audited DAG)

The system operates as a 5-stage sequential and parallel-forked StateGraph coordinated by `src/graph.py`:

```text
+-------------------------------------------------------------+
| STAGE 1: Temporal Anchoring & Priority Matrix Engine        |
| (src/stages/stage_1_temporal.py)                            |
| - Determinstic US Eastern calendar math (28-day horizon)    |
| - Algorithmic Priority Matrix (Tier 1 > Tier 2 > Tier 3)    |
+------------------------------+------------------------------+
                               |
                               v
+-------------------------------------------------------------+
| STAGE 2: Market Plumbing & Multi-Source Harvester           |
| (src/stages/stage_2_harvester.py)                           |
| - Direct REST: US Fiscal Data API (TGA Cash & Auctions)     |
| - Clean Ingestion: Trafilatura HTML & Feedparser RSS        |
| - Enforces v14.6 UNKNOWN Rule & Two-Stage Epistemic Tagging |
| - Builds 7 Structured CSV tables & Audit Log                |
+------------------------------+------------------------------+
                               |
                               v
+-------------------------------------------------------------+
| STAGE 3: Quant Synthesis & Taleb Stress Tester              |
| (src/stages/stage_3_quant.py)                               |
| - Math Guardrails: VIX Slope (M2-M1) & ATM Implied Moves    |
| - Real-Time Asness Factor ETF Spreads via yfinance          |
| - Taleb Fragility: Systemic (10% Drawdown) & Liquidity Shock|
| - Top 3 Left-Tail & Top 3 Right-Tail Risk Ranking           |
+------------------------------+------------------------------+
                               |
        +----------------------+----------------------+
        | (Branch A: Institutional)                   | (Branch B: Retail)
        v                                             v
+-------------------------------+             +-------------------------------+
| STAGE 4: Executive Formatter  |             | STAGE 5: Retail Formatter     |
| (src/stages/stage_4_formatter) |             | (src/stages/stage_5_retail.py)|
| - C-Suite Briefing (<= 200 w) |             | - Traffic Light (GREEN/YEL/RED)|
| - 4-Week Risk Calendar        |             | - 401k/IRA Action Checklist   |
| - 7 BCBS 239 CSV Appendices   |             | - 30-Second Jargon Buster     |
+---------------+---------------+             +---------------+---------------+
                |                                             |
                +----------------------+----------------------+
                                       |
                                       v
+-------------------------------------------------------------+
| CONVERGENT GATEKEEPER: Fact-Auditor Critic Node             |
| (src/core/fact_auditor.py)                                  |
| - Cross-checks all numbers in BOTH reports against raw KV   |
| - Programmatically redacts ungrounded claims to UNKNOWN     |
+-------------------------------------------------------------+
```

---

## 🔒 Governance & BCBS 239 Zero-Hallucination Standards

1. **Strict Data Contracts:** All inter-stage payloads are validated using immutable **Pydantic v2** models (`src/core/schemas.py`).
2. **Zero-Math in Tokens:** All calculations (VIX curve slope, ATM straddles, factor ETF spreads, severity scores) execute in pure Python (`src/core/math_utils.py`, `src/data/factor_scraper.py`).
3. **Dual Fact-Auditor Gatekeeper:** `src/core/fact_auditor.py` cross-checks every numerical figure in both reports before publishing.
4. **The v14.6 Proprietary Data Rule:** Paywalled dealer metrics (Zero-Gamma, GEX) strictly log `UNKNOWN`.
5. **13F 45-Day Lag Caveat:** Form 13F allocations are explicitly tagged `lagged snapshot (subject to 45-day reporting lag)`.
6. **Tiered Cloud Storage:** Reports persist to Google Drive (`Production/`) with automated fallback to GitHub Actions artifacts [4] and local runner disk (`src/core/gdrive_sync.py`).

---

## 📂 Complete Repository Layout

```text
macro_risk_pipeline/
├── .github/workflows/
│   └── macro_risk_scheduled.yml # Automated Sunday Cron Workflow (22:00 UTC)
├── .gitignore                  # Enforces Zero Data Leaks to Git
├── requirements.txt            # Pinned Production Dependencies
├── README.md                   # System Architecture Documentation
├── dashboard.py                # Interactive Visual Dashboard Viewer
├── 00_github_sync.ipynb        # Dedicated Git Sync & Setup Utility
├── 01_pipeline_execution.ipynb  # Production Execution Workbench
├── docs/
│   ├── ADR_REGISTRY.md         # Architecture Decision Records (ADRs 001-006)
│   ├── GDRIVE_SETUP_GUIDE.md   # Step-by-Step Cloud Service Account Guide
│   └── CODEBASE_FOR_ADVERSARIAL_REVIEW.md # Multi-LLM Review Bundle
├── scripts/
│   └── export_for_ai_review.py # Automated Codebase Bundling Script
├── src/
│   ├── core/
│   │   ├── schemas.py          # Canonical Pydantic v2 Schema Registry
│   │   ├── llm_router.py       # Dynamic Model Discovery & Inference Router
│   │   ├── math_utils.py       # Deterministic ATM Straddle & VIX Math Engine
│   │   ├── fact_auditor.py     # Post-Generation Fact-Auditor Critic Node
│   │   ├── sanitizer.py        # Threat Modeling & Prompt Injection Defense
│   │   ├── gdrive_sync.py      # Headless Google Drive Cloud Sync Engine
│   │   └── vector_store.py     # Embedded ChromaDB Semantic Memory
│   ├── data/
│   │   ├── source_registry.py  # 47 Authorized Public Endpoint Registry
│   │   ├── public_macro_api.py # Direct U.S. Fiscal Data REST Ingestion
│   │   ├── factor_scraper.py   # Real-Time yfinance Factor ETF Spread Harvester
│   │   ├── web_ingester.py     # Trafilatura Clean HTML & Feedparser RSS Engine
│   │   └── shock_monitor.py    # Unscheduled Shock & Wire Break Detector
│   ├── stages/
│   │   ├── stage_1_temporal.py   # Stage 1: Temporal Anchoring & Regime Engine
│   │   ├── stage_2_harvester.py  # Stage 2: Market Plumbing & Multi-Source Harvester
│   │   ├── stage_3_quant.py      # Stage 3: Quant Synthesis & Taleb Stress Tester
│   │   ├── stage_4_formatter.py  # Stage 4: Institutional C-Suite Formatter
│   │   ├── stage_5_retail.py     # Stage 5: Retail Plain-English Formatter
│   │   └── pdf_exporter.py       # Institutional Presentation & HTML Exporter
│   └── graph.py                # Master LangGraph Dual-Audited StateGraph
└── tests/                      # Automated Pytest Suite (67 Tests Passing)
]

---

## 🚀 Quick Execution Guide

```python
from src.graph import run_pipeline

# Execute the full dual-audience LangGraph pipeline DAG
production_output = run_pipeline(save_artifacts=True)
print('Institutional Report:', production_output.report_file_path)
```
