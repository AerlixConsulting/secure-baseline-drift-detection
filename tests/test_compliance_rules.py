# Copyright 2024 Aerlix Consulting
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0

"""Tests for compliance_rules module."""

from __future__ import annotations

import textwrap
from pathlib import Path

import pytest

from src.baseline_store import Baseline
from src.compliance_rules import (
    SEVERITY_ORDER,
    ComplianceEvaluator,
    ComplianceProfile,
    ComplianceResult,
    ComplianceRule,
)
from src.drift_detector import DriftDetector, DriftFinding, DriftReport

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

SAMPLE_PROFILE_YAML = textwrap.dedent("""\
    profile:
      name: test-cis-level2
      version: "1.0"
      description: Test compliance profile

    rules:
      - id: R-001
        key: os.ssh.permit_root_login
        expected: "no"
        severity: critical
        controls: [CM-6, CM-2]
        remediation: "Set PermitRootLogin no in sshd_config"

      - id: R-002
        key: os.firewall.enabled
        expected: true
        severity: high
        controls: [CM-7, SC-7]
        remediation: "Enable system firewall"

      - id: R-003
        key: iam.password_min_length
        expected: 14
        severity: medium
        controls: [IA-5]
        remediation: "Set minimum password length to 14"

      - id: R-004
        key: network.tls_version_minimum
        expected: "1.2"
        severity: high
        controls: [SC-8, SC-28]
        remediation: "Enforce TLS 1.2 or higher"

      - id: R-005
        key: os.audit.*
        expected: "enabled"
        severity: medium
        controls: [AU-2, AU-12]
        remediation: "Enable audit logging"
""")

BASELINE_CONFIG = {
    "os.ssh.permit_root_login": "no",
    "os.firewall.enabled": True,
    "iam.password_min_length": 14,
    "network.tls_version_minimum": "1.2",
    "os.audit.syscall": "enabled",
}


def make_profile(yaml_text: str = SAMPLE_PROFILE_YAML) -> ComplianceProfile:
    import yaml

    return ComplianceProfile.from_dict(yaml.safe_load(yaml_text))


def make_profile_file(tmp_path: Path, yaml_text: str = SAMPLE_PROFILE_YAML) -> Path:
    p = tmp_path / "profile.yaml"
    p.write_text(yaml_text, encoding="utf-8")
    return p


def make_baseline(config: dict | None = None) -> Baseline:
    return Baseline(
        system_id="test-system-01",
        profile="cis-level2",
        config=config or BASELINE_CONFIG.copy(),
    )


def run_detect(baseline_cfg: dict, current_cfg: dict) -> DriftReport:
    baseline = make_baseline(baseline_cfg)
    return DriftDetector(baseline).compare(current_cfg)


# ---------------------------------------------------------------------------
# ComplianceRule
# ---------------------------------------------------------------------------


class TestComplianceRule:
    def test_exact_key_match(self):
        rule = ComplianceRule("R-01", "os.ssh.permit_root_login", "no", "critical")
        assert rule.matches("os.ssh.permit_root_login")
        assert not rule.matches("os.ssh.permit_other")

    def test_glob_key_match(self):
        rule = ComplianceRule("R-02", "os.audit.*", "enabled", "medium")
        assert rule.matches("os.audit.syscall")
        assert rule.matches("os.audit.file_access")
        assert not rule.matches("os.ssh.something")

    def test_repr_contains_id(self):
        rule = ComplianceRule("R-99", "key.*", None, "low")
        assert "R-99" in repr(rule)


# ---------------------------------------------------------------------------
# ComplianceProfile
# ---------------------------------------------------------------------------


class TestComplianceProfile:
    def test_loads_from_yaml_dict(self):
        profile = make_profile()
        assert profile.name == "test-cis-level2"
        assert profile.version == "1.0"
        assert len(profile.rules) == 5

    def test_rule_for_key_exact(self):
        profile = make_profile()
        rule = profile.rule_for_key("os.ssh.permit_root_login")
        assert rule is not None
        assert rule.rule_id == "R-001"
        assert rule.severity == "critical"

    def test_rule_for_key_glob(self):
        profile = make_profile()
        rule = profile.rule_for_key("os.audit.syscall")
        assert rule is not None
        assert rule.rule_id == "R-005"

    def test_rule_for_key_no_match(self):
        profile = make_profile()
        rule = profile.rule_for_key("untracked.setting")
        assert rule is None

    def test_loads_from_file(self, tmp_path):
        profile_path = make_profile_file(tmp_path)
        profile = ComplianceProfile.from_file(profile_path)
        assert profile.name == "test-cis-level2"
        assert len(profile.rules) >= 5

    def test_missing_file_raises(self):
        with pytest.raises(FileNotFoundError):
            ComplianceProfile.from_file("/nonexistent/path/profile.yaml")

    def test_repr(self):
        profile = make_profile()
        assert "test-cis-level2" in repr(profile)


# ---------------------------------------------------------------------------
# ComplianceEvaluator — annotate
# ---------------------------------------------------------------------------


class TestComplianceEvaluatorAnnotate:
    def test_annotates_severity_on_findings(self):
        profile = make_profile()
        evaluator = ComplianceEvaluator(profile)

        current = BASELINE_CONFIG.copy()
        current["os.ssh.permit_root_login"] = "yes"  # drift
        report = run_detect(BASELINE_CONFIG, current)

        evaluator.annotate(report)
        finding = next(f for f in report.findings if f.key == "os.ssh.permit_root_login")
        assert finding.severity == "critical"
        assert "CM-6" in finding.control_refs

    def test_unannotated_finding_stays_unknown(self):
        profile = make_profile()
        evaluator = ComplianceEvaluator(profile)

        current = BASELINE_CONFIG.copy()
        current["untracked.key"] = "something"
        report = run_detect(BASELINE_CONFIG, current)

        evaluator.annotate(report)
        finding = next(f for f in report.findings if f.key == "untracked.key")
        assert finding.severity == "unknown"


# ---------------------------------------------------------------------------
# ComplianceEvaluator — evaluate
# ---------------------------------------------------------------------------


class TestComplianceEvaluatorEvaluate:
    def test_pass_when_no_drift(self):
        profile = make_profile()
        evaluator = ComplianceEvaluator(profile)
        report = run_detect(BASELINE_CONFIG, BASELINE_CONFIG.copy())
        result = evaluator.evaluate(report)
        assert result.passed
        assert result.violation_count == 0

    def test_violation_for_changed_critical_key(self):
        profile = make_profile()
        evaluator = ComplianceEvaluator(profile)

        current = BASELINE_CONFIG.copy()
        current["os.ssh.permit_root_login"] = "yes"
        report = run_detect(BASELINE_CONFIG, current)
        result = evaluator.evaluate(report)

        assert not result.passed
        assert result.violation_count >= 1
        assert any(v.key == "os.ssh.permit_root_login" for v in result.violations)

    def test_violation_for_removed_required_key(self):
        profile = make_profile()
        evaluator = ComplianceEvaluator(profile)

        current = BASELINE_CONFIG.copy()
        del current["os.firewall.enabled"]
        report = run_detect(BASELINE_CONFIG, current)
        result = evaluator.evaluate(report)

        assert not result.passed
        assert any(v.key == "os.firewall.enabled" for v in result.violations)

    def test_highest_severity_critical_trumps_high(self):
        profile = make_profile()
        evaluator = ComplianceEvaluator(profile)

        current = BASELINE_CONFIG.copy()
        current["os.ssh.permit_root_login"] = "yes"  # critical
        current["os.firewall.enabled"] = False  # high
        report = run_detect(BASELINE_CONFIG, current)
        result = evaluator.evaluate(report)

        assert result.highest_severity == "critical"

    def test_highest_severity_none_when_passing(self):
        profile = make_profile()
        evaluator = ComplianceEvaluator(profile)
        report = run_detect(BASELINE_CONFIG, BASELINE_CONFIG.copy())
        result = evaluator.evaluate(report)
        assert result.highest_severity == "none"

    def test_severity_counts(self):
        profile = make_profile()
        evaluator = ComplianceEvaluator(profile)

        current = BASELINE_CONFIG.copy()
        current["os.ssh.permit_root_login"] = "yes"  # critical
        current["iam.password_min_length"] = 8  # medium
        report = run_detect(BASELINE_CONFIG, current)
        result = evaluator.evaluate(report)

        counts = result.severity_counts()
        assert counts.get("critical", 0) >= 1
        assert counts.get("medium", 0) >= 1

    def test_to_dict_structure(self):
        profile = make_profile()
        evaluator = ComplianceEvaluator(profile)
        report = run_detect(BASELINE_CONFIG, BASELINE_CONFIG.copy())
        result = evaluator.evaluate(report)
        d = result.to_dict()
        assert "profile" in d
        assert "passed" in d
        assert "violations" in d
        assert "severity_breakdown" in d
        assert all(s in d["severity_breakdown"] for s in SEVERITY_ORDER)

    def test_glob_rule_fires_on_changed_audit_key(self):
        """Rule R-005 uses 'os.audit.*' glob — verify it triggers."""
        profile = make_profile()
        evaluator = ComplianceEvaluator(profile)

        current = BASELINE_CONFIG.copy()
        current["os.audit.syscall"] = "disabled"
        report = run_detect(BASELINE_CONFIG, current)
        result = evaluator.evaluate(report)

        assert any(v.key == "os.audit.syscall" for v in result.violations)


# ---------------------------------------------------------------------------
# ComplianceResult
# ---------------------------------------------------------------------------


class TestComplianceResult:
    def _make_result(self, violations: list[DriftFinding]) -> ComplianceResult:
        profile = make_profile()
        report = DriftReport("sys", "bl-1", violations)
        return ComplianceResult(report=report, profile=profile, violations=violations)

    def test_passed_property(self):
        result = self._make_result([])
        assert result.passed

    def test_failed_property(self):
        finding = DriftFinding("k", "changed", "a", "b", severity="high")
        result = self._make_result([finding])
        assert not result.passed
