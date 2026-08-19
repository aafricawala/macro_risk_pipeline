"""
Module Name: pdf_exporter.py
Repo Path: src/stages/pdf_exporter.py

BCBS 239 Data Lineage & Compliance Standards:
- Role: Institutional Presentation Document & HTML/PDF Exporter.
- Styling: Goldman/Morgan Stanley institutional typography, monospace CSV tables, and dual-theme palettes.
- Output Destination: Persisted to Google Drive Production/MacroRisk_Weekly_Report_{DATE}.html.
"""

# Import standard library OS module for filesystem paths
import os

# Import sys module for standard output stream references
import sys

# Import json module for metadata parsing
import json

# Import datetime for timestamping
from datetime import datetime

# Import Path for filesystem path resolution
from pathlib import Path

# Import typing primitives for strict type safety
from typing import Optional, Dict, Any, Tuple

# Import loguru logger for structured logging
from loguru import logger

# Import markdown library to convert markdown to styled HTML
import markdown


# Institutional C-Suite CSS Styling Palette
INSTITUTIONAL_CSS = """
<style>
  body {
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
    line-height: 1.6;
    color: #1a1a1a;
    background-color: #fcfcfc;
    max-width: 1000px;
    margin: 0 auto;
    padding: 40px 20px;
  }
  h1, h2, h3, h4 {
    color: #0b1f3a;
    font-weight: 700;
    border-bottom: 1px solid #eaeaea;
    padding-bottom: 8px;
    margin-top: 30px;
  }
  h1 { font-size: 26px; border-bottom: 2px solid #0b1f3a; }
  h2 { font-size: 20px; }
  h3 { font-size: 16px; color: #1e3a8a; }
  table {
    width: 100%;
    border-collapse: collapse;
    margin: 20px 0;
    font-size: 14px;
    background: #ffffff;
    box-shadow: 0 1px 3px rgba(0,0,0,0.05);
  }
  th, td {
    padding: 10px 14px;
    border: 1px solid #e2e8f0;
    text-align: left;
  }
  th {
    background-color: #0b1f3a;
    color: #ffffff;
    font-weight: 600;
  }
  tr:nth-child(even) { background-color: #f8fafc; }
  code, pre {
    font-family: "SFMono-Regular", Consolas, "Liberation Mono", Menlo, monospace;
    background-color: #f1f5f9;
    padding: 2px 6px;
    border-radius: 4px;
    font-size: 13px;
  }
  pre {
    padding: 16px;
    overflow-x: auto;
    border-left: 4px solid #0b1f3a;
  }
  .tag-official { color: #059669; font-weight: bold; }
  .tag-social { color: #2563eb; font-weight: bold; }
  .tag-rumor { color: #dc2626; font-weight: bold; }
  .disclaimer { font-size: 12px; color: #64748b; margin-top: 40px; font-style: italic; border-top: 1px solid #e2e8f0; padding-top: 10px; }
</style>
"""


# Function to render styled HTML presentation report from Markdown
def export_markdown_to_styled_html(
    markdown_text: str,
    output_html_path: str,
    document_title: str = "MacroRisk Weekly Intelligence Report",
) -> str:
    """
    Converts raw Markdown report into an institutional HTML presentation document.
    """
    try:
        # Convert Markdown to HTML with table and code fence extensions
        html_body = markdown.markdown(
            markdown_text,
            extensions=["tables", "fenced_code", "nl2br"]
        )

        # Wrap in complete HTML5 presentation template
        full_html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>{document_title}</title>
  {INSTITUTIONAL_CSS}
</head>
<body>
  {html_body}
</body>
</html>
"""

        # Save HTML file to disk
        out_p = Path(output_html_path)
        out_p.parent.mkdir(parents=True, exist_ok=True)
        with open(out_p, "w", encoding="utf-8") as f:
            f.write(full_html)

        logger.info(f"Successfully generated styled presentation document: {out_p.resolve()}")
        return str(out_p.resolve())

    except Exception as exc:
        logger.error(f"HTML export failed: {exc}")
        return ""
