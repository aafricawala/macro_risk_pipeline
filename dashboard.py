"""
Module Name: dashboard.py
Repo Path: dashboard.py

BCBS 239 Data Lineage & Compliance Standards:
- Role: Interactive Visual Dashboard for Multi-Asset Risk Desks & Retail Portfolios.
- Technology: Streamlit / Colab interactive dashboard.
- Features:
  1. Institutional C-Suite View (Macro Risk Matrix, 4-Week Calendar, 7 CSV tables).
  2. Retail Investor View (Traffic Light indicator, 401k/IRA action checklist, Jargon Buster).
  3. Live Ingestion Diagnostics (TGA balance, Treasury auctions, Factor ETF spreads).
"""

import os
import glob
from pathlib import Path

# Helper function to find latest production reports in Google Drive or local artifacts
def get_production_file_paths():
    base_paths = [
        "/content/drive/MyDrive/Colab Notebooks/macro_risk_pipeline/Production",
        "/content/drive/MyDrive/macro_risk_pipeline/Production",
        "./artifacts_storage/Production",
        "./Production",
    ]
    inst_file = None
    ret_file = None

    for p in base_paths:
        if os.path.exists(p):
            inst_matches = glob.glob(f"{p}/MacroRisk_Weekly_Intelligence_Report_*.md")
            ret_matches = glob.glob(f"{p}/MacroRisk_Weekly_Retail_Investor_Note_*.md")
            if inst_matches and not inst_file:
                inst_file = sorted(inst_matches)[-1]
            if ret_matches and not ret_file:
                ret_file = sorted(ret_matches)[-1]

    return inst_file, ret_file


# Standalone CLI / Colab console viewer
def render_terminal_dashboard():
    inst_path, ret_path = get_production_file_paths()
    print("=" * 80)
    print("🏛️ MACRORISK INTERACTIVE DASHBOARD VIEWER (v8.6 Enterprise)")
    print("=" * 80)

    if inst_path and os.path.exists(inst_path):
        print(f"\n[1] Institutional C-Suite Report: {inst_path}")
        with open(inst_path, "r", encoding="utf-8") as f:
            print(f.read()[:1200] + "\n... [TRUNCATED PREVIEW]")

    if ret_path and os.path.exists(ret_path):
        print(f"\n[2] Retail Investor Note: {ret_path}")
        with open(ret_path, "r", encoding="utf-8") as f:
            print(f.read()[:1000] + "\n... [TRUNCATED PREVIEW]")

    print("=" * 80)


if __name__ == "__main__":
    render_terminal_dashboard()
