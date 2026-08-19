"""Human-readable musicality reports."""

from __future__ import annotations

from collections import Counter
from dataclasses import asdict
from typing import Any

from app.critic.fingerprint import Fingerprint, aggregate, compare, extract_fingerprint, load_reference
from app.critic.rules import Violation, check_hard_rules, format_violations
from app.engine import SIMPLE_PROFILE, render_skeleton
from app.engine.skeleton import build_skeleton


def _render_for_critic(skeleton: dict[str, Any]) -> dict[str, Any]:
    return render_skeleton(
        skeleton,
        SIMPLE_PROFILE,
        seed=int(skeleton["seed"]),
        include_midi=False,
        include_musicxml=False,
    )


def analyze_seed(
    *,
    dance_type: str,
    seed: int,
    include_render: bool = True,
) -> dict[str, Any]:
    skeleton = build_skeleton(dance_type=dance_type, seed=seed)
    rendered = _render_for_critic(skeleton) if include_render else None
    violations = check_hard_rules(skeleton, rendered)
    fp = extract_fingerprint(skeleton)
    ref = load_reference(dance_type)
    kl = compare(fp, ref)
    return {
        "seed": seed,
        "dance_type": dance_type,
        "violations": violations,
        "fingerprint": fp,
        "kl": kl,
    }


def analyze_seeds(
    *,
    dance_type: str,
    seeds: range | list[int],
    include_render: bool = True,
) -> dict[str, Any]:
    seed_list = list(seeds)
    per_seed: list[dict[str, Any]] = []
    fps: list[Fingerprint] = []
    rule_counts: Counter[str] = Counter()
    error_counts: Counter[str] = Counter()
    warning_counts: Counter[str] = Counter()

    for seed in seed_list:
        skeleton = build_skeleton(dance_type=dance_type, seed=seed)
        rendered = _render_for_critic(skeleton) if include_render else None
        violations = check_hard_rules(skeleton, rendered)
        fp = extract_fingerprint(skeleton)
        fps.append(fp)
        per_seed.append({"seed": seed, "violation_count": len(violations)})
        for v in violations:
            rule_counts[v.rule_id] += 1
            if v.severity == "error":
                error_counts[v.rule_id] += 1
            else:
                warning_counts[v.rule_id] += 1

    agg = aggregate(fps)
    ref = load_reference(dance_type)
    kl = compare(agg, ref)

    return {
        "dance_type": dance_type,
        "seeds": seed_list,
        "seed_count": len(seed_list),
        "aggregated_fingerprint": agg,
        "kl_vs_golden_age": kl,
        "rule_violation_counts": dict(rule_counts),
        "error_violation_counts": dict(error_counts),
        "warning_violation_counts": dict(warning_counts),
        "scalar_means": {
            "notes_per_bar": agg.notes_per_bar,
            "rest_ratio": agg.rest_ratio,
            "repeated_note_ratio": agg.repeated_note_ratio,
            "leap_ratio": agg.leap_ratio,
        },
        "per_seed_summary": per_seed,
    }


def format_report(report: dict[str, Any]) -> str:
    lines = [
        f"# Musicality report — {report['dance_type']} ({report['seed_count']} seeds)",
        "",
        "## KL divergence vs golden_age (expert prior)",
    ]
    kl = report["kl_vs_golden_age"]
    for key in ("interval_hist", "onset_hist", "duration_hist"):
        lines.append(f"- {key}: {kl[key]:.4f}")
    lines.extend(
        [
            "",
            "## Scalar means (aggregated)",
            f"- notes_per_bar: {report['scalar_means']['notes_per_bar']:.3f}",
            f"- rest_ratio: {report['scalar_means']['rest_ratio']:.3f}",
            f"- repeated_note_ratio: {report['scalar_means']['repeated_note_ratio']:.3f}",
            f"- leap_ratio: {report['scalar_means']['leap_ratio']:.3f}",
            "",
            "## Rule violations (total counts)",
        ]
    )
    counts = report.get("rule_violation_counts") or {}
    if not counts:
        lines.append("- (none)")
    else:
        for rule_id in sorted(counts):
            err = report.get("error_violation_counts", {}).get(rule_id, 0)
            warn = report.get("warning_violation_counts", {}).get(rule_id, 0)
            lines.append(f"- {rule_id}: {counts[rule_id]} (errors={err}, warnings={warn})")
    return "\n".join(lines)


def violation_summary(report: dict[str, Any]) -> str:
    """Sample violations from first failing seed for debugging."""
    dance = report["dance_type"]
    for seed in report["seeds"][:5]:
        skeleton = build_skeleton(dance_type=dance, seed=seed)
        rendered = _render_for_critic(skeleton)
        violations = check_hard_rules(skeleton, rendered)
        if violations:
            return format_violations(violations[:10])
    return "(no violations in first 5 seeds)"


def fingerprint_to_dict(fp: Fingerprint) -> dict[str, Any]:
    return asdict(fp)
