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

"""drift_detector — compare a current system configuration against a stored baseline.

The detector produces a structured :class:`DriftReport` that lists every
configuration key where the current value differs from the baseline value,
as well as keys that have been added or removed since the baseline was captured.

Drift findings are categorised as:

* ``added``    — key present in current state but absent from baseline
* ``removed``  — key present in baseline but absent from current state
* ``changed``  — key present in both but value differs
"""

from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime
from typing import Any, Literal

from .baseline_store import Baseline

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

DriftType = Literal["added", "removed", "changed"]


# ---------------------------------------------------------------------------
# Data models
# ---------------------------------------------------------------------------


class DriftFinding:
    """A single configuration drift finding."""

    def __init__(
        self,
        key: str,
        drift_type: DriftType,
        baseline_value: Any,
        current_value: Any,
        *,
        severity: str = "unknown",
        control_refs: list[str] | None = None,
        remediation: str = "",
    ) -> None:
        self.key = key
        self.drift_type: DriftType = drift_type
        self.baseline_value = baseline_value
        self.current_value = current_value
        self.severity = severity
        self.control_refs: list[str] = control_refs or []
        self.remediation = remediation

    def to_dict(self) -> dict[str, Any]:
        return {
            "key": self.key,
            "drift_type": self.drift_type,
            "baseline_value": self.baseline_value,
            "current_value": self.current_value,
            "severity": self.severity,
            "control_refs": self.control_refs,
            "remediation": self.remediation,
        }

    def __repr__(self) -> str:
        return f"DriftFinding(key={self.key!r}, type={self.drift_type!r}, severity={self.severity!r})"


class DriftReport:
    """Aggregated result of a drift comparison run."""

    def __init__(
        self,
        system_id: str,
        baseline_id: str,
        findings: list[DriftFinding],
        *,
        report_id: str | None = None,
        generated_at: str | None = None,
        total_baseline_keys: int = 0,
        total_current_keys: int = 0,
    ) -> None:
        now = datetime.now(UTC)
        date_str = now.strftime("%Y%m%d")
        self.report_id: str = report_id or f"dr-{date_str}-{system_id}"
        self.system_id = system_id
        self.baseline_id = baseline_id
        self.generated_at: str = generated_at or now.isoformat()
        self.findings: list[DriftFinding] = findings
        self.total_baseline_keys = total_baseline_keys
        self.total_current_keys = total_current_keys

    # ------------------------------------------------------------------
    # Summary helpers
    # ------------------------------------------------------------------

    @property
    def drifted_count(self) -> int:
        return len(self.findings)

    @property
    def is_compliant(self) -> bool:
        return self.drifted_count == 0

    def severity_counts(self) -> dict[str, int]:
        counts: dict[str, int] = {}
        for f in self.findings:
            counts[f.severity] = counts.get(f.severity, 0) + 1
        return counts

    # ------------------------------------------------------------------
    # Serialisation
    # ------------------------------------------------------------------

    def to_dict(self) -> dict[str, Any]:
        sev = self.severity_counts()
        total_checks = max(self.total_baseline_keys, self.total_current_keys)
        return {
            "report_id": self.report_id,
            "system_id": self.system_id,
            "baseline_id": self.baseline_id,
            "generated_at": self.generated_at,
            "summary": {
                "total_checks": total_checks,
                "drifted": self.drifted_count,
                "compliant": total_checks - self.drifted_count,
                "critical": sev.get("critical", 0),
                "high": sev.get("high", 0),
                "medium": sev.get("medium", 0),
                "low": sev.get("low", 0),
                "unknown": sev.get("unknown", 0),
            },
            "findings": [f.to_dict() for f in self.findings],
        }

    def to_json(self, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), indent=indent)

    def save(self, path: str) -> None:
        """Write the report to *path* as JSON."""
        import os

        os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(self.to_json() + "\n")

    # ------------------------------------------------------------------
    # Integrity
    # ------------------------------------------------------------------

    def checksum(self) -> str:
        """Return a SHA-256 hex digest of the serialised report."""
        return hashlib.sha256(self.to_json().encode()).hexdigest()


# ---------------------------------------------------------------------------
# Detector
# ---------------------------------------------------------------------------


class DriftDetector:
    """Compare a current configuration map against a stored baseline.

    Args:
        baseline: The authoritative :class:`~baseline_store.Baseline` snapshot.
    """

    def __init__(self, baseline: Baseline) -> None:
        self.baseline = baseline

    def compare(self, current: dict[str, Any]) -> DriftReport:
        """Perform the drift comparison.

        Args:
            current: Flat configuration map representing the live system state.

        Returns:
            A :class:`DriftReport` with all findings populated (severity set to
            ``'unknown'`` at this stage — call
            :meth:`~compliance_rules.ComplianceEvaluator.annotate` to enrich
            findings with rule-based severity).
        """
        baseline_cfg = self.baseline.config
        findings: list[DriftFinding] = []

        all_keys = set(baseline_cfg.keys()) | set(current.keys())

        for key in sorted(all_keys):
            in_baseline = key in baseline_cfg
            in_current = key in current

            if in_baseline and not in_current:
                findings.append(
                    DriftFinding(
                        key=key,
                        drift_type="removed",
                        baseline_value=baseline_cfg[key],
                        current_value=None,
                    )
                )
            elif in_current and not in_baseline:
                findings.append(
                    DriftFinding(
                        key=key,
                        drift_type="added",
                        baseline_value=None,
                        current_value=current[key],
                    )
                )
            elif _values_differ(baseline_cfg[key], current[key]):
                findings.append(
                    DriftFinding(
                        key=key,
                        drift_type="changed",
                        baseline_value=baseline_cfg[key],
                        current_value=current[key],
                    )
                )

        return DriftReport(
            system_id=self.baseline.system_id,
            baseline_id=self.baseline.baseline_id,
            findings=findings,
            total_baseline_keys=len(baseline_cfg),
            total_current_keys=len(current),
        )


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _values_differ(a: Any, b: Any) -> bool:
    """Return True if *a* and *b* are semantically different.

    Compares string representations to handle minor type mismatches (e.g. the
    integer ``0`` vs the string ``"0"`` are treated as equal).
    """
    if a == b:
        return False
    # Normalise to string for comparison (handles bool/int/str edge cases)
    return str(a).strip().lower() != str(b).strip().lower()
