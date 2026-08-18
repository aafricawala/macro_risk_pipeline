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
| - Direct REST Ingestion: US Fiscal Data API (TGA & Auctions)|
| - Enforces v14.6 UNKNOWN Rule & Two-Stage Epistemic Tagging |
| - Builds 7 Structured CSV tables & Audit Log                |
+------------------------------+------------------------------+
                               |
                               v
+-------------------------------------------------------------+
| STAGE 3: Quant Synthesis & Taleb Stress Tester              |
| (src/stages/stage_3_quant.py)                               |
| - Math Guardrails: VIX Slope (M2-M1) & ATM Implied Moves    |
| - Real-Time Asness Factor Regimes via yfinance              |
| - Taleb Fragility: Systemic (10% Drawdown) & Liquidity Shock|
| - Top 3 Left-Tail & Top 3 Right-Tail Risk Ranking           |
+------------------------------+------------------------------+
                               |
                               v
+-------------------------------------------------------------+
| STAGE 4: Executive Formatter & Serialization                |
| (src/stages/stage_4_formatter.py)                           |
| - Token-budgeted C-suite Briefing (<= 150 words)            |
| - Algorithmic 1-5 Event Severity Scoring                    |
| - 4-Week Chronological Calendar with standard null-states   |
| - Serializes final report and 7 CSVs to Google Drive        |
+-------------------------------------------------------------+
```

---

## ⏰ Automated Production Scheduling

The pipeline is scheduled via **GitHub Actions** (`.github/workflows/macro_risk_scheduled.yml`) to execute every **Sunday at 6:00 PM US Eastern Time (22:00 UTC)**, running all 33 test suites and publishing the production report artifacts.

---

## 📂 Complete Repository Layout

```text
macro_risk_pipeline/
├── .github/workflows/
│   └── macro_risk_scheduled.yml # Automated Sunday Cron & Dispatch Workflow
├── .gitignore                  # Enforces Zero Data Leaks to Git
├── requirements.txt            # Pinned Dependencies
├── README.md                   # System Architecture Documentation
├── src/
│   ├── core/
│   │   ├── schemas.py          # Canonical Pydantic v2 Schema Registry
│   │   ├── llm_router.py       # Dynamic Model Discovery & Inference Router
│   │   └── math_utils.py       # Deterministic ATM Straddle & VIX Math
│   ├── data/
│   │   ├── factor_scraper.py   # Live yfinance Factor ETF Spreads
│   │   └── public_macro_api.py # Direct U.S. Fiscal Data REST Ingestion
│   ├── stages/
│   │   ├── stage_1_temporal.py   # Stage 1: Temporal Anchoring & Regime Engine
│   │   ├── stage_2_harvester.py  # Stage 2: Market Plumbing & Catalyst Harvester
│   │   ├── stage_3_quant.py      # Stage 3: Quant Synthesis & Taleb Stress Tester
│   │   └── stage_4_formatter.py  # Stage 4: Executive Formatter & Serialization
│   └── graph.py                # Master Pipeline DAG Coordinator
└── tests/                      # Automated Unit & Integration Tests (33 Passed)
```

---

## 🚀 Quick Execution Guide

```python
from src.graph import run_pipeline

# Execute the full 4-stage pipeline DAG
production_output = run_pipeline()
print('Report generated at:', production_output.report_file_path)
```
