"""Musicality critic — measurement infrastructure for M-task validation."""

from app.critic.fingerprint import Fingerprint, aggregate, compare, extract_fingerprint, load_reference
from app.critic.rules import Violation, check_hard_rules, format_violations
from app.critic.report import analyze_seed, analyze_seeds, format_report

__all__ = [
    "Fingerprint",
    "Violation",
    "aggregate",
    "analyze_seed",
    "analyze_seeds",
    "check_hard_rules",
    "compare",
    "extract_fingerprint",
    "format_report",
    "format_violations",
    "load_reference",
]
