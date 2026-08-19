"""
Unit Tests for scripts/export_for_ai_review.py.
Verifies bundle generation and file inclusion.
"""
import os
from pathlib import Path
import pytest

from scripts.export_for_ai_review import generate_codebase_review_bundle


def test_generate_codebase_review_bundle():
    """Verify that review bundle is generated and includes core files."""
    test_output_file = "docs/test_bundle.md"
    bundle_path = generate_codebase_review_bundle(output_markdown_path=test_output_file)

    assert os.path.exists(bundle_path)
    with open(bundle_path, "r", encoding="utf-8") as f:
        content = f.read()

    assert "INSTITUTIONAL ADVERSARIAL CODE & RISK AUDIT PROMPT" in content
    assert "src/core/schemas.py" in content
    assert "src/graph.py" in content
    assert "src/core/fact_auditor.py" in content

    # Clean up test artifact
    if os.path.exists(test_output_file):
        os.remove(test_output_file)
