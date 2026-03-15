# Copyright 2024 Aerlix Consulting
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0

"""Tests for drift_detector module."""

from __future__ import annotations

import json
from pathlib import Path

from src.baseline_store import Baseline
from src.drift_detector import DriftDetector, DriftFinding, DriftReport, _values_differ

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

BASELINE_CONFIG = {
    "os.ssh.permit_root_login": "no",
    "os.ssh.password_authentication": "no",
    "os.firewall.enabled": True,
    "os.firewall.default_policy": "deny",
    "iam.mfa_required": True,
    "iam.password_min_length": 14,
    "network.tls_version_minimum": "1.2",
    "network.http_enabled": False,
}


def make_baseline(config: dict | None = None) -> Baseline:
    return Baseline(
        system_id="test-system-01",
        profile="cis-level2",
        config=config or BASELINE_CONFIG.copy(),
    )


# ---------------------------------------------------------------------------
# DriftFinding
# ---------------------------------------------------------------------------


class TestDriftFinding:
    def test_to_dict_has_required_keys(self):
        finding = DriftFinding(
            key="os.ssh.permit_root_login",
            drift_type="changed",
            baseline_value="no",
            current_value="yes",
        )
        d = finding.to_dict()
        assert d["key"] == "os.ssh.permit_root_login"
        assert d["drift_type"] == "changed"
        assert d["baseline_value"] == "no"
        assert d["current_value"] == "yes"
        assert "severity" in d
        assert "control_refs" in d
        assert "remediation" in d

    def test_repr_contains_key(self):
        f = DriftFinding("some.key", "added", None, "value")
        assert "some.key" in repr(f)


# ---------------------------------------------------------------------------
# DriftReport
# ---------------------------------------------------------------------------


class TestDriftReport:
    def test_empty_report_is_compliant(self):
        report = DriftReport(
            system_id="sys",
            baseline_id="bl-1",
            findings=[],
            total_baseline_keys=10,
            total_current_keys=10,
        )
        assert report.is_compliant
        assert report.drifted_count == 0

    def test_severity_counts(self):
        findings = [
            DriftFinding("a", "changed", "x", "y", severity="critical"),
            DriftFinding("b", "changed", "x", "z", severity="high"),
            DriftFinding("c", "added", None, "w", severity="high"),
        ]
        report = DriftReport("sys", "bl-1", findings)
        counts = report.severity_counts()
        assert counts["critical"] == 1
        assert counts["high"] == 2

    def test_to_dict_structure(self):
        findings = [
            DriftFinding("k", "removed", "v", None, severity="medium"),
        ]
        report = DriftReport("sys", "bl-1", findings, total_baseline_keys=5, total_current_keys=4)
        d = report.to_dict()
        assert d["system_id"] == "sys"
        assert d["baseline_id"] == "bl-1"
        assert "summary" in d
        assert d["summary"]["drifted"] == 1
        assert d["summary"]["medium"] == 1
        assert len(d["findings"]) == 1

    def test_checksum_is_stable(self):
        report = DriftReport("sys", "bl-1", [], total_baseline_keys=5, total_current_keys=5)
        assert report.checksum() == report.checksum()

    def test_save_writes_json(self, tmp_path):
        report = DriftReport("sys", "bl-1", [], total_baseline_keys=0, total_current_keys=0)
        out = str(tmp_path / "sub" / "report.json")
        report.save(out)
        loaded = json.loads(Path(out).read_text())
        assert loaded["system_id"] == "sys"


# ---------------------------------------------------------------------------
# DriftDetector
# ---------------------------------------------------------------------------


class TestDriftDetector:
    def test_no_drift_when_identical(self):
        baseline = make_baseline()
        current = BASELINE_CONFIG.copy()
        detector = DriftDetector(baseline)
        report = detector.compare(current)
        assert report.is_compliant
        assert report.drifted_count == 0

    def test_detects_changed_value(self):
        baseline = make_baseline()
        current = BASELINE_CONFIG.copy()
        current["os.ssh.permit_root_login"] = "yes"
        detector = DriftDetector(baseline)
        report = detector.compare(current)
        assert not report.is_compliant
        changed = [f for f in report.findings if f.drift_type == "changed"]
        assert any(f.key == "os.ssh.permit_root_login" for f in changed)

    def test_detects_removed_key(self):
        baseline = make_baseline()
        current = BASELINE_CONFIG.copy()
        del current["iam.mfa_required"]
        detector = DriftDetector(baseline)
        report = detector.compare(current)
        removed = [f for f in report.findings if f.drift_type == "removed"]
        assert any(f.key == "iam.mfa_required" for f in removed)

    def test_detects_added_key(self):
        baseline = make_baseline()
        current = BASELINE_CONFIG.copy()
        current["os.new_unexpected_setting"] = "enabled"
        detector = DriftDetector(baseline)
        report = detector.compare(current)
        added = [f for f in report.findings if f.drift_type == "added"]
        assert any(f.key == "os.new_unexpected_setting" for f in added)

    def test_multiple_drifts(self):
        baseline = make_baseline()
        current = BASELINE_CONFIG.copy()
        current["os.firewall.enabled"] = False
        current["iam.password_min_length"] = 8
        del current["network.tls_version_minimum"]
        detector = DriftDetector(baseline)
        report = detector.compare(current)
        assert report.drifted_count == 3

    def test_boolean_vs_string_no_false_positive(self):
        """True and 'true' should be treated as equal to avoid noise."""
        baseline = make_baseline({"flag": True})
        current = {"flag": "true"}
        detector = DriftDetector(baseline)
        report = detector.compare(current)
        assert report.is_compliant

    def test_report_has_correct_system_id(self):
        baseline = make_baseline()
        detector = DriftDetector(baseline)
        report = detector.compare(BASELINE_CONFIG.copy())
        assert report.system_id == "test-system-01"
        assert report.baseline_id == baseline.baseline_id

    def test_total_key_counts(self):
        baseline = make_baseline()
        current = BASELINE_CONFIG.copy()
        detector = DriftDetector(baseline)
        report = detector.compare(current)
        assert report.total_baseline_keys == len(BASELINE_CONFIG)
        assert report.total_current_keys == len(current)


# ---------------------------------------------------------------------------
# _values_differ helper
# ---------------------------------------------------------------------------


class TestValuesDiffer:
    def test_identical_values(self):
        assert not _values_differ("no", "no")
        assert not _values_differ(14, 14)
        assert not _values_differ(True, True)

    def test_case_insensitive(self):
        assert not _values_differ("NO", "no")
        assert not _values_differ("True", "true")

    def test_differs(self):
        assert _values_differ("yes", "no")
        assert _values_differ(8, 14)
        assert _values_differ(True, False)

    def test_int_string_no_false_positive(self):
        assert not _values_differ(0, "0")
        assert not _values_differ(1, "1")
