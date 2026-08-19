#!/usr/bin/env python3
"""CLI musicality report — hard rules + fingerprint KL vs golden_age."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

from app.critic.report import analyze_seeds, format_report  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="Musicality critic report")
    parser.add_argument("--dance", choices=["tango", "vals", "milonga"], default="tango")
    parser.add_argument("--seeds", type=int, default=100, help="Number of seeds (1..N)")
    parser.add_argument("--json", action="store_true", help="Emit JSON instead of text")
    parser.add_argument(
        "--baseline",
        type=Path,
        default=None,
        help="Optional prior baseline JSON for delta comparison",
    )
    args = parser.parse_args()

    report = analyze_seeds(dance_type=args.dance, seeds=range(1, args.seeds + 1))

    if args.baseline and args.baseline.exists():
        prior = json.loads(args.baseline.read_text(encoding="utf-8"))
        report["prior_baseline"] = prior
        kl_now = report["kl_vs_golden_age"]
        kl_prior = prior.get("kl_vs_golden_age", {})
        report["kl_delta_from_prior"] = {
            k: kl_now.get(k, 0) - kl_prior.get(k, 0) for k in kl_now if "delta" not in k
        }

    if args.json:
        # Fingerprint dataclass not JSON-serializable in report — strip heavy fields
        out = {k: v for k, v in report.items() if k != "aggregated_fingerprint"}
        print(json.dumps(out, indent=2))
    else:
        print(format_report(report))
        if report.get("kl_delta_from_prior"):
            print("\n## KL delta vs prior baseline")
            for k, v in report["kl_delta_from_prior"].items():
                sign = "+" if v >= 0 else ""
                print(f"- {k}: {sign}{v:.4f}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
