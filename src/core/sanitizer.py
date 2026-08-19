"""
Module Name: sanitizer.py
Repo Path: src/core/sanitizer.py

BCBS 239 Data Lineage & Compliance Standards:
- Role: Threat Modeling & Prompt Injection Sanitization Guardrail.
- Processing Logic:
  1. Strips HTML/XML script, style, and iframe tags from scraped web text.
  2. Removes zero-width spaces, directional control codes, and non-printable unicode artifacts.
  3. Neutralizes known prompt injection override patterns (e.g., 'ignore previous instructions').
  4. Truncates text length to enforce strict token budgeting.
"""

# Import regular expressions module for pattern matching and sanitization
import re

# Import unicodedata to normalize unicode representations
import unicodedata

# Import typing primitives for strict type safety
from typing import Optional, List, Set

# Import loguru logger for structured diagnostic logs
from loguru import logger


# Known prompt injection attack phrases and override triggers
INJECTION_OVERRIDE_PATTERNS: List[str] = [
    r"(?i)ignore\s+(all\s+)?(previous|prior|above)\s+instructions?",
    r"(?i)disregard\s+(all\s+)?(previous|prior|above)\s+instructions?",
    r"(?i)system\s+prompt\s+override",
    r"(?i)you\s+are\s+now\s+in\s+(dan|developer|jailbreak|unrestricted)\s+mode",
    r"(?i)new\s+instruction:\s*",
    r"(?i)<\|im_start\|>",
    r"(?i)<\|im_end\|>",
    r"(?i)\[INST\]",
    r"(?i)\[/INST\]",
]


# Function to sanitize third-party scraped web text before LLM prompt interpolation
def sanitize_scraped_text(
    raw_text: Optional[str],
    max_char_limit: int = 3500,
) -> str:
    """
    Sanitizes raw text extracted from third-party websites and RSS feeds.
    Strips prompt injection payloads, zero-width characters, and dangerous formatting tags.
    """
    # Check if input is None or empty
    if not raw_text or not isinstance(raw_text, str):
        # Return empty string for invalid inputs
        return ""

    # Normalize unicode characters to NFKC standard representation
    normalized = unicodedata.normalize("NFKC", raw_text)

    # Strip zero-width spaces, soft hyphens, and bidirectional control characters
    # \u200B=zero-width space, \u200C=ZWNJ, \u200D=ZWJ, \uFEFF=BOM, \u00AD=soft hyphen
    cleaned = re.sub(r"[\u200B-\u200D\uFEFF\u00AD\u202A-\u202E]", "", normalized)

    # Strip remaining HTML tags (e.g. <script>, <style>, <iframe>, <a>)
    cleaned = re.sub(r"<[^>]+>", " ", cleaned)

    # Neutralize known prompt injection override patterns with safety redactions
    for pattern in INJECTION_OVERRIDE_PATTERNS:
        # Substitute malicious pattern with sanitized marker
        cleaned = re.sub(pattern, "[UNAUTHORIZED_INSTRUCTION_REDACTED]", cleaned)

    # Replace multiple consecutive whitespace and newlines with clean double newlines
    cleaned = re.sub(r"[ \t]+", " ", cleaned)
    cleaned = re.sub(r"\n\s*\n\s*\n+", "\n\n", cleaned)

    # Strip leading and trailing whitespace
    cleaned = cleaned.strip()

    # Cap character length to enforce strict context budgeting
    return cleaned[:max_char_limit]
