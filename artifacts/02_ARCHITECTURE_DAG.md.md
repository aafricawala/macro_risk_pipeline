# MACRORISK MICRO-AGENT DAG ARCHITECTURE (v1.0)
**Derived from:** `macrorisk-weekly-intelligence` (v8.6 Enterprise)
**Architecture Type:** 4-Stage Sequential StateGraph (LangGraph/Prefect)

---

## 🔹 STAGE 1: Temporal Anchoring & Regime Engine (`macrorisk-1-temporal-regime`)
**Architectural Goal:** Eliminate calendar hallucination and establish the baseline macro theme before any deep data harvesting begins.
*   **Inputs:** Current System Datetime (US Eastern).
*   **Processing Logic:** 
    *   Executes *Phase 1, Step 1 & 2* of the monolithic prompt.
    *   Calculates absolute YYYY-MM-DD bounds for `START_DATE`, `END_DATE`, and `WEEK_1` through `WEEK_4` windows.
    *   Runs a single Anchor Search for the 7-day economic calendar.
    *   Evaluates findings against the **Algorithmic Priority Matrix** (Tier 1, 2, and 3).
*   **Pydantic Output:** JSON containing exact date boundaries and the designated `Dominant Macro Theme`.

---

## 🔹 STAGE 2: Market Plumbing & Catalyst Harvester (`macrorisk-2-plumbing-harvester`)
**Architectural Goal:** Execute targeted, parallelized web searches across the 7 Risk Modules, enforcing free-tier constraints and epistemic tagging.
*   **Inputs:** Date Boundaries & Dominant Macro Theme (from Stage 1).
*   **Processing Logic:**
    *   Executes *Phase 1, Step 3, 4 & 5* of the monolithic prompt.
    *   Uses targeted operators (`site:fred.stlouisfed.org`, `site:sec.gov`, etc.) to gather raw data across the 7 Modules (Liquidity, Tech/Earnings, Derivatives, Geopolitics, etc.).
    *   Applies **Zero-Cost Social Ingestion** and cross-verifies public wires.
    *   Applies the **Proprietary Data Fallback (v14.6 Rule)**: Logs `UNKNOWN` if paywalled data (Zero-Gamma, GEX, dealer positioning) cannot be found in free public wires.
    *   Applies the **13F 45-Day Lag Epistemic Caveat**.
    *   Tags all text with `[VERIFIED_OFFICIAL]`, `[VERIFIED_SOCIAL_PRIMARY]`, or `[UNVERIFIED_RUMOR]`.
*   **Pydantic Output:** A massive, strict Key-Value JSON dictionary containing raw string metrics for all 7 Modules and 7 target CSV appendices. No narrative prose permitted.

---

## 🔹 STAGE 3: Quant Synthesis & Taleb Stress Tester (`macrorisk-3-quant-synthesis`)
**Architectural Goal:** Apply rigid mathematical formulas, factor rotations, and stress tests to the raw data without triggering web searches.
*   **Inputs:** Raw KV Data Dictionary (from Stage 2).
*   **Processing Logic:**
    *   Executes *Phase 2* of the monolithic prompt.
    *   **Math Guardrails:** Executes exact formulas for *ATM Straddle Implied Move* and *VIX Curve Slope (M1/M2)* using Stage 2 inputs. If inputs are missing, enforces `UNKNOWN`.
    *   **Asness-Style Mapping:** Evaluates factor rotations using ETF performance spreads (MTUM/VLUE, etc.).
    *   **Taleb Fragility Test:** Evaluates Systemic Shock (10% drawdown) and Idiosyncratic Shock (extreme margin debt velocity, CTA unwinds).
    *   Algorithmically ranks the Top 3 Left-Tail and Top 3 Right-Tail risks.
*   **Pydantic Output:** JSON containing structured Tail Risk Matrices, Cross-Asset Spillover Vectors, and the 3 Tactical Scenarios.

---

## 🔹 STAGE 4: Executive Formatter & Serialization (`macrorisk-4-executive-formatter`)
**Architectural Goal:** Render the final C-Suite Markdown report and BCBS 239 compliant CSV appendices matching the exact legacy formatting constraints.
*   **Inputs:** Time/Regime (Stage 1), Raw KV Data (Stage 2), Tail Risks & Scenarios (Stage 3).
*   **Processing Logic:**
    *   Executes *Phase 3* and *Section 1-6 Output Structures* of the monolithic prompt.
    *   Enforces Token Budgeting ($\le 150$ word exec briefing, Max 100 words per scenario).
    *   Applies Layer 1 (Structural) and Layer 2 (Derivatives) prose synthesis.
    *   Enforces standard null-states for Week 1-4 headings (e.g., `* No Tier-1/Tier-2 catalysts...`).
    *   Renders the 7 CSV files natively. Enforces double quotes for comma-strings, forbids markdown in CSVs, and uses the exact `N/A` single-row null state.
*   **Outputs:** The final Markdown text string and the 7 raw CSV files (persisted to Google Drive).

---
### 📋 VERSION REVISION LOG (DAG Architecture)
* **v1.0:** Initial conversion of the monolithic `macrorisk-weekly-intelligence` (v8.6) prompt into a 4-Stage DAG. Verified zero-drop conversion of all math formulas, fallback rules, null-states, and epistemic tagging protocols. Established strict boundaries between Data Harvesting (Stage 2) and Quantitative Synthesis (Stage 3) to prevent LLM hallucination of financial metrics.
