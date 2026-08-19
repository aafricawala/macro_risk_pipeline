"""
Module Name: shock_monitor.py
Repo Path: src/data/shock_monitor.py
Role: Unscheduled Shock & Wire Break Detection Engine with Dependency Injection.
"""
import os
import sys
import re
from datetime import datetime, date
from typing import List, Dict, Optional, Any, Tuple
from loguru import logger
from src.core.schemas import (
    ShockType,
    UnscheduledShockItem,
    ShockMonitorResult,
    EpistemicTag,
)
from src.data.web_ingester import fetch_and_extract_rss

logger.remove()
logger.add(sys.stdout, level="INFO")

SHOCK_PATTERNS = {
    ShockType.BANK_FAILURE_FDIC: [
        r"(failed|closed|closure|receivership|assumes all deposits|purchase and assumption|seized)",
        r"(bridge bank|systemic risk exception|emergency lending facility)"
    ],
    ShockType.SOVEREIGN_RATING_ACTION: [
        r"(downgrades|downgraded|credit watch negative|negative outlook|sovereign rating lowered)",
        r"(default rating|debt ceiling risk|treasury credit watch)"
    ],
    ShockType.GEOPOLITICAL_KINETIC: [
        r"(missile strike|strait of hormuz closed|blockade|kinetic action|naval confrontation)",
        r"(emergency sanctions|export embargo|maritime chokepoint)"
    ],
    ShockType.PBOC_STEALTH_LIQUIDITY: [
        r"(medium-term lending facility|mlf injection|reserve requirement ratio|rrr cut)",
        r"(yuan fix deviation|counter-cyclical factor|liquidity injection)"
    ],
}

def scan_fdic_bank_failures(items_feed: Optional[List[Dict[str, str]]] = None) -> List[UnscheduledShockItem]:
    logger.info("Shock Monitor: Scanning FDIC press release feed for bank closures...")
    items = items_feed if items_feed is not None else fetch_and_extract_rss("https://www.fdic.gov/news/press-releases", max_entries=5)
    detected: List[UnscheduledShockItem] = []
    ts_now = datetime.now().strftime("%Y-%m-%d %H:%M:%S ET")

    for entry in items:
        text_to_scan = f"{entry.get('title', '')} {entry.get('summary', '')}".lower()
        for pat in SHOCK_PATTERNS[ShockType.BANK_FAILURE_FDIC]:
            if re.search(pat, text_to_scan, re.IGNORECASE):
                shock = UnscheduledShockItem(
                    shock_type=ShockType.BANK_FAILURE_FDIC,
                    title=entry.get("title", "FDIC Regulatory Action"),
                    summary=entry.get("summary", "FDIC emergency receivership action."),
                    source_url=entry.get("link", "https://fdic.gov"),
                    epistemic_tag=EpistemicTag.VERIFIED_OFFICIAL,
                    timestamp_et=ts_now,
                    severity_score=5,
                )
                detected.append(shock)
                logger.warning(f"EMERGENCY SHOCK DETECTED: {shock.title}")
                break
    return detected

def scan_newswire_breaking_shocks(items_feed: Optional[List[Dict[str, str]]] = None) -> List[UnscheduledShockItem]:
    logger.info("Shock Monitor: Scanning breaking newswires for sovereign downgrades and kinetic events...")
    items = items_feed if items_feed is not None else fetch_and_extract_rss("https://www.reutersagency.com/feed/?best-topics=business-finance&post_type=best", max_entries=5)
    detected: List[UnscheduledShockItem] = []
    ts_now = datetime.now().strftime("%Y-%m-%d %H:%M:%S ET")

    for entry in items:
        text_to_scan = f"{entry.get('title', '')} {entry.get('summary', '')}".lower()
        for pat in SHOCK_PATTERNS[ShockType.SOVEREIGN_RATING_ACTION]:
            if re.search(pat, text_to_scan, re.IGNORECASE):
                shock = UnscheduledShockItem(
                    shock_type=ShockType.SOVEREIGN_RATING_ACTION,
                    title=entry.get("title", "Sovereign Rating Action"),
                    summary=entry.get("summary", "Credit rating agency action detected."),
                    source_url=entry.get("link", "https://reuters.com"),
                    epistemic_tag=EpistemicTag.VERIFIED_OFFICIAL,
                    timestamp_et=ts_now,
                    severity_score=5,
                )
                detected.append(shock)
                logger.warning(f"SOVEREIGN RATING SHOCK DETECTED: {shock.title}")
                break

        for pat in SHOCK_PATTERNS[ShockType.GEOPOLITICAL_KINETIC]:
            if re.search(pat, text_to_scan, re.IGNORECASE):
                shock = UnscheduledShockItem(
                    shock_type=ShockType.GEOPOLITICAL_KINETIC,
                    title=entry.get("title", "Geopolitical Escalation"),
                    summary=entry.get("summary", "Kinetic conflict or chokepoint disruption detected."),
                    source_url=entry.get("link", "https://reuters.com"),
                    epistemic_tag=EpistemicTag.VERIFIED_OFFICIAL,
                    timestamp_et=ts_now,
                    severity_score=4,
                )
                detected.append(shock)
                logger.warning(f"GEOPOLITICAL SHOCK DETECTED: {shock.title}")
                break
    return detected

def scan_for_unscheduled_shocks() -> ShockMonitorResult:
    all_shocks: List[UnscheduledShockItem] = []
    try:
        all_shocks.extend(scan_fdic_bank_failures())
    except Exception as e:
        logger.warning(f"FDIC shock scan skipped: {e}")

    try:
        all_shocks.extend(scan_newswire_breaking_shocks())
    except Exception as e:
        logger.warning(f"Newswire shock scan skipped: {e}")

    shocks_detected = len(all_shocks) > 0
    is_emergency = any(s.severity_score >= 5 for s in all_shocks)
    return ShockMonitorResult(
        shocks_detected=shocks_detected,
        active_shock_alerts=all_shocks,
        is_emergency_regime=is_emergency,
    )
