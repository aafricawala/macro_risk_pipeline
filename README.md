# MacroRisk Weekly Intelligence Pipeline (v8.6 Enterprise)

A deterministic, multi-stage micro-agent pipeline that produces an institution-grade Macro Risk Weekly Status Report and 7 BCBS 239-compliant structured CSV appendices for senior C-suite risk desks and multi-asset portfolio managers.

---

## 🏛️ Architecture Overview

The system operates as a 4-stage sequential DAG coordinated by `src/graph.py`:

```text
+-------------------------------------------------------------+
| STAGE 1: Temporal Anchoring & Regime Engine                 |
| (src/stages/stage_1_temporal.py)                            |
| - Determinstic US Eastern calendar math (28-day horizon)    |
| - Algorithmic Priority Matrix (Tier 1 > Tier 2 > Tier 3)    |
+------------------------------+------------------------------+
                               |
                               v
+-------------------------------------------------------------+
| STAGE 2: Market Plumbing & Catalyst Harvester               |
| (src/stages/stage_2_harvester.py)                           |
| - Harvests raw data across 7 Risk Modules (KV Store)        |
| - Enforces v14.6 UNKNOWN Rule & Two-Stage Epistemic Tagging |
| - Builds 7 Structured CSV tables & Audit Log                |
+------------------------------+------------------------------+
                               |
                               v
+-------------------------------------------------------------+
| STAGE 3: Quant Synthesis & Taleb Stress Tester              |
| (src/stages/stage_3_quant.py)                               |
| - Math Guardrails: VIX Slope (M2-M1) & ATM Implied Moves    |
| - Asness-Style Factor Regimes (MTUM/VLUE, QUAL/USMV)        |
| - Taleb Fragility: Systemic (10% Drawdown) & Liquidity Shock|
| - Top 3 Left-Tail & Top 3 Right-Tail Risk Ranking           |
+------------------------------+------------------------------+
                               |
                               v
+-------------------------------------------------------------+
| STAGE 4: Executive Formatter & Serialization                |
| (src/stages/stage_4_formatter.py)                           |
| - Token-budgeted C-suite Briefing (<= 150 words)            |
| - 4-Week Chronological Calendar with standard null-states   |
| - Serializes final report and 7 CSVs to Google Drive        |
+-------------------------------------------------------------+
```

---

## 🔒 Governance & BCBS 239 Data Lineage Standards

1. **Strict Data Contracts:** All inter-stage payloads are validated using immutable **Pydantic v2** models (`src/core/schemas.py`).
2. **Zero-Hallucination Epistemic Tagging:** Every ingested statement is tagged with certainty markers: `[VERIFIED_OFFICIAL]`, `[VERIFIED_SOCIAL_PRIMARY]`, or `[UNVERIFIED_RUMOR]`.
3. **The v14.6 Proprietary Data Rule:** Paywalled metrics (Zero-Gamma levels, dealer GEX) strictly log `UNKNOWN`.
4. **13F 45-Day Lag Epistemic Caveat:** Form 13F allocations are explicitly tagged `lagged snapshot (subject to 45-day reporting lag)`.
5. **Artifact Isolation:** The GitHub repository contains **strictly code**. All data artifacts (`.json`), error logs (`error_logs/`), and final production reports (`Production/`) persist to a mounted Google Drive folder.

---

## 🤖 Dynamic Zero-Hardcoding LLM Router

Inference is managed by `src/core/llm_router.py`. It queries Google AI Studio via `client.models.list()`, sorts models from newest to oldest (prioritizing `flash` tiers), and automatically cascades through available models if an endpoint is busy:
* `gemini-3.7-flash` -> `gemini-3.6-flash` -> `gemini-3.5-flash` -> `gemini-3.5-flash-lite`

---

## 📂 Repository Layout

```text
macro_risk_pipeline/
├── .gitignore
├── requirements.txt
├── README.md
├── src/
│   ├── core/
│   │   ├── schemas.py          # Canonical Pydantic v2 Schema Registry
│   │   └── llm_router.py       # Dynamic Model Discovery & Inference Router
│   ├── stages/
│   │   ├── stage_1_temporal.py   # Stage 1: Temporal Anchoring & Regime Engine
│   │   ├── stage_2_harvester.py  # Stage 2: Market Plumbing & Catalyst Harvester
│   │   ├── stage_3_quant.py      # Stage 3: Quant Synthesis & Taleb Stress Tester
│   │   └── stage_4_formatter.py  # Stage 4: Executive Formatter & Serialization
│   └── graph.py                # Master Pipeline DAG Coordinator
└── tests/                      # Automated Unit & Integration Tests (Mocked)
    ├── test_schemas.py
    ├── test_schemas_stage_2.py
    ├── test_schemas_stage_3.py
    ├── test_llm_router.py
    ├── test_stage_1_temporal.py
    ├── test_stage_2_harvester.py
    ├── test_stage_3_quant.py
    ├── test_stage_4_formatter.py
    └── test_graph.py
```

---

## 🚀 Execution Guide

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Run Full Automated Test Suite (Mocked)
```bash
pytest -v -s tests/
```

### 3. Run the End-to-End Pipeline in Python
```python
import os
from src.graph import run_pipeline

# Configure Google Drive mount path for data persistence
os.environ['GOOGLE_DRIVE_MOUNT_PATH'] = '/content/drive/MyDrive/Colab Notebooks/macro_risk_pipeline'

# Execute full pipeline DAG
final_report = run_pipeline()
print('Report generated at:', final_report.report_file_path)
```

---

## 📊 Production Outputs Generated

* **Production Markdown Report:** `Production/MacroRisk_Weekly_Intelligence_Report_{DATE}.md`
* **7 Standalone CSV Appendices (`Production/csv_appendices/`):**
  1. `treasury_auctions.csv`
  2. `central_bank_events.csv`
  3. `earnings_bellwethers.csv`
  4. `opex_and_gamma.csv`
  5. `cot_positioning.csv`
  6. `vix_term_structure.csv`
  7. `audit_log.csv` (Top 5 Load-Bearing Claims)
