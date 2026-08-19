"""
Unit Tests for src/stages/pdf_exporter.py and dashboard.py.
"""
import os
from pathlib import Path
import pytest
from src.stages.pdf_exporter import export_markdown_to_styled_html
from dashboard import get_production_file_paths


def test_export_markdown_to_styled_html():
    """Verify Markdown is converted to valid HTML with CSS styling."""
    sample_md = "# MacroRisk Weekly\n\n### Section 1\n* Bullet point\n\n| Col A | Col B |\n|---|---|\n| 1 | 2 |"
    out_path = "artifacts_storage/test_report.html"

    res_path = export_markdown_to_styled_html(sample_md, out_path, "Test Report")

    assert os.path.exists(res_path)
    with open(res_path, "r", encoding="utf-8") as f:
        html_content = f.read()

    assert "<!DOCTYPE html>" in html_content
    assert "MacroRisk Weekly" in html_content
    assert "<table>" in html_content
    assert "INSTITUTIONAL_CSS" not in html_content  # CSS rendered properly

    # Cleanup
    if os.path.exists(out_path):
        os.remove(out_path)


def test_get_production_file_paths():
    """Verify dashboard path finder handles non-existent paths gracefully."""
    inst_path, ret_path = get_production_file_paths()
    # Should return strings or None without throwing exceptions
    assert inst_path is None or isinstance(inst_path, str)
    assert ret_path is None or isinstance(ret_path, str)
