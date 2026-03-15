# Copyright 2024 Aerlix Consulting
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""cli — unified command-line interface for the drift detection pipeline.

Sub-commands
------------

``baseline capture``
    Create and store a baseline snapshot from a configuration file.

``drift compare``
    Compare a live system configuration against a stored baseline.

``compliance evaluate``
    Evaluate a drift report against a compliance profile.

``baseline list``
    List all baselines in the store.

Usage examples::

    drift-detect baseline capture \\
        --input examples/current_state.yaml \\
        --system-id webserver-prod-01 \\
        --profile cis-level2 \\
        --store baselines/

    drift-detect drift compare \\
        --baseline baselines/bl-20240301-webserver-prod-01.json \\
        --current examples/current_state.yaml \\
        --rules examples/compliance_profile.yaml \\
        --output reports/drift-report.json

    drift-detect compliance evaluate \\
        --drift-report reports/drift-report.json \\
        --rules examples/compliance_profile.yaml
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .baseline_store import Baseline, BaselineStore
from .compliance_rules import ComplianceEvaluator, ComplianceProfile
from .config_parser import load_config
from .drift_detector import DriftDetector


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="drift-detect",
        description="Secure Baseline Drift Detection — Aerlix Consulting",
    )
    sub = parser.add_subparsers(dest="command", metavar="COMMAND")
    sub.required = True

    # ------------------------------------------------------------------ #
    # baseline sub-command
    # ------------------------------------------------------------------ #
    baseline_cmd = sub.add_parser("baseline", help="Baseline management")
    baseline_sub = baseline_cmd.add_subparsers(dest="baseline_action", metavar="ACTION")
    baseline_sub.required = True

    # baseline capture
    cap = baseline_sub.add_parser("capture", help="Capture a new baseline snapshot")
    cap.add_argument("--input", required=True, metavar="PATH", help="Path to configuration file (YAML or JSON)")
    cap.add_argument("--system-id", required=True, metavar="ID", help="Logical system identifier")
    cap.add_argument("--profile", required=True, metavar="NAME", help="Compliance profile name (e.g. cis-level2)")
    cap.add_argument(
        "--store", default="baselines", metavar="DIR", help="Baseline store directory (default: baselines/)"
    )
    cap.add_argument("--description", default="", metavar="TEXT", help="Optional human-readable description")
    cap.add_argument(
        "--output", default=None, metavar="PATH", help="Write baseline JSON to this path instead of the store"
    )

    # baseline list
    lst = baseline_sub.add_parser("list", help="List stored baselines")
    lst.add_argument("--store", default="baselines", metavar="DIR", help="Baseline store directory")

    # ------------------------------------------------------------------ #
    # drift sub-command
    # ------------------------------------------------------------------ #
    drift_cmd = sub.add_parser("drift", help="Drift detection")
    drift_sub = drift_cmd.add_subparsers(dest="drift_action", metavar="ACTION")
    drift_sub.required = True

    cmp = drift_sub.add_parser("compare", help="Compare current state against a baseline")
    cmp.add_argument("--baseline", required=True, metavar="PATH", help="Path to baseline JSON file")
    cmp.add_argument("--current", required=True, metavar="PATH", help="Path to current state configuration file")
    cmp.add_argument("--rules", default=None, metavar="PATH", help="Optional path to compliance profile YAML")
    cmp.add_argument("--output", default=None, metavar="PATH", help="Write drift report JSON to this path")

    # ------------------------------------------------------------------ #
    # compliance sub-command
    # ------------------------------------------------------------------ #
    comp_cmd = sub.add_parser("compliance", help="Compliance evaluation")
    comp_sub = comp_cmd.add_subparsers(dest="compliance_action", metavar="ACTION")
    comp_sub.required = True

    evl = comp_sub.add_parser("evaluate", help="Evaluate a drift report against compliance rules")
    evl.add_argument("--drift-report", required=True, metavar="PATH", help="Path to drift report JSON")
    evl.add_argument("--rules", required=True, metavar="PATH", help="Path to compliance profile YAML")
    evl.add_argument("--output", default=None, metavar="PATH", help="Write compliance result JSON to this path")

    return parser


def cmd_baseline_capture(args: argparse.Namespace) -> int:
    config = load_config(args.input)
    baseline = Baseline(
        system_id=args.system_id,
        profile=args.profile,
        config=config,
        description=args.description,
    )

    if args.output:
        out_path = Path(args.output)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(json.dumps(baseline.to_dict(), indent=2) + "\n", encoding="utf-8")
        print(f"Baseline captured → {out_path}")
    else:
        store = BaselineStore(args.store)
        saved = store.save(baseline)
        print(f"Baseline captured → {saved}")

    print(f"  baseline_id : {baseline.baseline_id}")
    print(f"  system_id   : {baseline.system_id}")
    print(f"  profile     : {baseline.profile}")
    print(f"  captured_at : {baseline.captured_at}")
    print(f"  keys        : {len(config)}")
    return 0


def cmd_baseline_list(args: argparse.Namespace) -> int:
    store = BaselineStore(args.store)
    summaries = store.list_baselines()
    if not summaries:
        print(f"No baselines found in {args.store}")
        return 0
    print(f"{'BASELINE ID':<40}  {'SYSTEM ID':<25}  {'PROFILE':<15}  CAPTURED AT")
    print("-" * 110)
    for s in summaries:
        print(f"{s['baseline_id']:<40}  {s['system_id']:<25}  {s['profile']:<15}  {s['captured_at']}")
    return 0


def cmd_drift_compare(args: argparse.Namespace) -> int:
    from .baseline_store import BaselineStore  # noqa: F811

    store = BaselineStore()
    baseline = store.load_file(args.baseline)
    current = load_config(args.current)

    detector = DriftDetector(baseline)
    report = detector.compare(current)

    # Optionally annotate with compliance rules
    if args.rules:
        profile = ComplianceProfile.from_file(args.rules)
        evaluator = ComplianceEvaluator(profile)
        evaluator.annotate(report)

    report_dict = report.to_dict()

    if args.output:
        report.save(args.output)
        print(f"Drift report → {args.output}")
    else:
        print(json.dumps(report_dict, indent=2))

    summary = report_dict["summary"]
    print(
        f"\nSummary: {summary['drifted']} drifted / {summary['total_checks']} checks — "
        f"critical={summary['critical']} high={summary['high']} medium={summary['medium']} low={summary['low']}"
    )
    return 1 if report.drifted_count > 0 else 0


def cmd_compliance_evaluate(args: argparse.Namespace) -> int:
    from .drift_detector import DriftFinding, DriftReport  # noqa: F811

    # Re-hydrate the report from JSON
    data = json.loads(Path(args.drift_report).read_text(encoding="utf-8"))
    findings = [
        DriftFinding(
            key=f["key"],
            drift_type=f["drift_type"],
            baseline_value=f["baseline_value"],
            current_value=f["current_value"],
            severity=f.get("severity", "unknown"),
            control_refs=f.get("control_refs", []),
            remediation=f.get("remediation", ""),
        )
        for f in data.get("findings", [])
    ]
    report = DriftReport(
        system_id=data["system_id"],
        baseline_id=data["baseline_id"],
        findings=findings,
        report_id=data.get("report_id"),
        generated_at=data.get("generated_at"),
        total_baseline_keys=data.get("summary", {}).get("total_checks", 0),
        total_current_keys=data.get("summary", {}).get("total_checks", 0),
    )

    profile = ComplianceProfile.from_file(args.rules)
    evaluator = ComplianceEvaluator(profile)
    result = evaluator.evaluate(report)
    result_dict = result.to_dict()

    if args.output:
        out_path = Path(args.output)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(json.dumps(result_dict, indent=2) + "\n", encoding="utf-8")
        print(f"Compliance result → {args.output}")
    else:
        print(json.dumps(result_dict, indent=2))

    status = "PASS" if result.passed else "FAIL"
    print(
        f"\nCompliance status: {status} — {result.violation_count} violation(s), highest severity: {result.highest_severity}"
    )
    return 0 if result.passed else 1


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    handlers = {
        ("baseline", "capture"): cmd_baseline_capture,
        ("baseline", "list"): cmd_baseline_list,
        ("drift", "compare"): cmd_drift_compare,
        ("compliance", "evaluate"): cmd_compliance_evaluate,
    }

    action_key: tuple[str, str]
    if args.command == "baseline":
        action_key = ("baseline", args.baseline_action)
    elif args.command == "drift":
        action_key = ("drift", args.drift_action)
    elif args.command == "compliance":
        action_key = ("compliance", args.compliance_action)
    else:
        parser.print_help()
        sys.exit(1)

    handler = handlers.get(action_key)
    if handler is None:
        parser.print_help()
        sys.exit(1)

    sys.exit(handler(args))


if __name__ == "__main__":
    main()
