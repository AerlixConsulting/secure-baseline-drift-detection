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

"""compliance_rules — rule-based evaluation and severity scoring of drift findings.

A **compliance profile** is a YAML document that defines a set of rules.
Each rule specifies:

* ``key``       — the configuration key it applies to (supports glob patterns)
* ``expected``  — the expected (compliant) value
* ``severity``  — ``critical | high | medium | low``
* ``controls``  — list of NIST 800-53 / CSF control identifiers
* ``remediation`` — human-readable remediation guidance

The :class:`ComplianceEvaluator` loads a profile and annotates
:class:`~drift_detector.DriftFinding` objects with severity and control
references, then produces a :class:`ComplianceResult` summarising the
overall compliance posture.
"""

from __future__ import annotations

import fnmatch
from pathlib import Path
from typing import Any

try:
    import yaml
except ModuleNotFoundError as exc:  # pragma: no cover
    raise ImportError("PyYAML is required: pip install pyyaml") from exc

from .drift_detector import DriftFinding, DriftReport

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

SEVERITY_ORDER = ["critical", "high", "medium", "low", "unknown"]
SEVERITY_SCORE = {"critical": 4, "high": 3, "medium": 2, "low": 1, "unknown": 0}


# ---------------------------------------------------------------------------
# Data models
# ---------------------------------------------------------------------------


class ComplianceRule:
    """A single rule from a compliance profile."""

    def __init__(
        self,
        rule_id: str,
        key_pattern: str,
        expected: Any,
        severity: str,
        *,
        controls: list[str] | None = None,
        remediation: str = "",
        description: str = "",
    ) -> None:
        self.rule_id = rule_id
        self.key_pattern = key_pattern
        self.expected = expected
        self.severity = severity.lower()
        self.controls: list[str] = controls or []
        self.remediation = remediation
        self.description = description

    def matches(self, key: str) -> bool:
        """Return True if *key* matches this rule's key pattern (glob-style)."""
        return fnmatch.fnmatch(key, self.key_pattern)

    def __repr__(self) -> str:
        return f"ComplianceRule(id={self.rule_id!r}, pattern={self.key_pattern!r}, severity={self.severity!r})"


class ComplianceProfile:
    """Loaded set of compliance rules.

    Args:
        name:        Profile name (e.g. ``'cis-level2'``).
        version:     Profile version string.
        rules:       Ordered list of :class:`ComplianceRule` objects.
        description: Optional human-readable description.
    """

    def __init__(
        self,
        name: str,
        version: str,
        rules: list[ComplianceRule],
        description: str = "",
    ) -> None:
        self.name = name
        self.version = version
        self.rules = rules
        self.description = description

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ComplianceProfile:
        """Parse a compliance profile from a plain dictionary."""
        rules_data = data.get("rules", [])
        rules = []
        for i, r in enumerate(rules_data):
            rule_id = r.get("id", f"rule-{i + 1:04d}")
            rules.append(
                ComplianceRule(
                    rule_id=rule_id,
                    key_pattern=r["key"],
                    expected=r.get("expected"),
                    severity=r.get("severity", "medium"),
                    controls=r.get("controls", []),
                    remediation=r.get("remediation", ""),
                    description=r.get("description", ""),
                )
            )
        return cls(
            name=data.get("profile", {}).get("name", "unknown"),
            version=data.get("profile", {}).get("version", "0.0"),
            rules=rules,
            description=data.get("profile", {}).get("description", ""),
        )

    @classmethod
    def from_file(cls, path: str | Path) -> ComplianceProfile:
        """Load a compliance profile from a YAML file.

        Args:
            path: Path to the YAML compliance profile.

        Returns:
            A :class:`ComplianceProfile` instance.

        Raises:
            FileNotFoundError: If *path* does not exist.
        """
        path = Path(path)
        if not path.exists():
            raise FileNotFoundError(f"Compliance profile not found: {path}")
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
        return cls.from_dict(data)

    def rule_for_key(self, key: str) -> ComplianceRule | None:
        """Return the first rule whose pattern matches *key*, or ``None``."""
        for rule in self.rules:
            if rule.matches(key):
                return rule
        return None

    def __repr__(self) -> str:
        return f"ComplianceProfile(name={self.name!r}, rules={len(self.rules)})"


# ---------------------------------------------------------------------------
# Evaluator
# ---------------------------------------------------------------------------


class ComplianceResult:
    """Output of a compliance evaluation pass."""

    def __init__(
        self,
        report: DriftReport,
        profile: ComplianceProfile,
        violations: list[DriftFinding],
    ) -> None:
        self.report = report
        self.profile = profile
        self.violations = violations

    @property
    def passed(self) -> bool:
        """Return True if there are zero violations."""
        return len(self.violations) == 0

    @property
    def violation_count(self) -> int:
        """Return the number of compliance violations."""
        return len(self.violations)

    @property
    def highest_severity(self) -> str:
        """Return the highest severity level found among violations."""
        if not self.violations:
            return "none"
        scores = [SEVERITY_SCORE.get(v.severity, 0) for v in self.violations]
        best = max(scores)
        return next(s for s, v in SEVERITY_SCORE.items() if v == best)

    def severity_counts(self) -> dict[str, int]:
        counts: dict[str, int] = {}
        for v in self.violations:
            counts[v.severity] = counts.get(v.severity, 0) + 1
        return counts

    def to_dict(self) -> dict[str, Any]:
        sev = self.severity_counts()
        return {
            "profile": self.profile.name,
            "profile_version": self.profile.version,
            "passed": self.passed,
            "highest_severity": self.highest_severity,
            "violation_count": len(self.violations),
            "severity_breakdown": {s: sev.get(s, 0) for s in SEVERITY_ORDER},
            "violations": [v.to_dict() for v in self.violations],
        }


class ComplianceEvaluator:
    """Evaluate a :class:`~drift_detector.DriftReport` against a :class:`ComplianceProfile`.

    Args:
        profile: The compliance profile to evaluate against.
    """

    def __init__(self, profile: ComplianceProfile) -> None:
        self.profile = profile

    def annotate(self, report: DriftReport) -> None:
        """Enrich each :class:`~drift_detector.DriftFinding` in *report* with
        severity and control references drawn from the compliance profile.

        This mutates the findings in-place.

        Args:
            report: The drift report to annotate.
        """
        for finding in report.findings:
            rule = self.profile.rule_for_key(finding.key)
            if rule:
                finding.severity = rule.severity
                finding.control_refs = rule.controls
                finding.remediation = rule.remediation

    def evaluate(self, report: DriftReport) -> ComplianceResult:
        """Annotate findings and return a :class:`ComplianceResult`.

        A finding is treated as a **violation** when:

        * it matches a rule in the profile *and*
        * the current value does not equal the expected value (or the key
          is missing from the current state for ``must-have`` settings).

        Args:
            report: The drift report to evaluate.

        Returns:
            A :class:`ComplianceResult` with violations and summary.
        """
        self.annotate(report)
        violations = []

        for finding in report.findings:
            rule = self.profile.rule_for_key(finding.key)
            if rule is None:
                # No rule for this key — finding is informational only
                continue

            # A violation occurs when the value is not what the rule expects
            if finding.drift_type in ("removed", "changed"):
                if rule.expected is not None:
                    # Only flag as violation if current value differs from expected
                    if not _values_equal(finding.current_value, rule.expected):
                        violations.append(finding)
                else:
                    # Rule has no expected value — any drift is a violation
                    violations.append(finding)
            elif finding.drift_type == "added":
                # Additions are violations only if the rule explicitly forbids them
                # (indicated by expected == None and severity != 'low')
                if rule.expected is None and rule.severity in ("critical", "high"):
                    violations.append(finding)

        return ComplianceResult(report=report, profile=self.profile, violations=violations)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _values_equal(a: Any, b: Any) -> bool:
    """Flexible equality check that normalises types."""
    if a == b:
        return True
    return str(a).strip().lower() == str(b).strip().lower()
