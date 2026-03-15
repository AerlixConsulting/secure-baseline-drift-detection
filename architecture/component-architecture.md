# Component Architecture Diagram

<!-- SPDX-License-Identifier: Apache-2.0 -->
<!-- Copyright 2024 Aerlix Consulting -->

This diagram shows the internal component structure of the Secure Baseline Drift Detection system and the relationships between modules.

```mermaid
classDiagram
    class CLI {
        +main()
        +cmd_baseline_capture(args)
        +cmd_baseline_list(args)
        +cmd_drift_compare(args)
        +cmd_compliance_evaluate(args)
        +build_parser() ArgumentParser
    }

    class ConfigParser {
        +load_config(path) ConfigMap
        +load_config_string(text, fmt) ConfigMap
        +flatten(data, prefix, sep) ConfigMap
        +validate_schema(config, required_keys) list
        -_parse(path, raw) Any
        -_normalise_list(items) str
    }

    class BaselineStore {
        +store_dir: Path
        +save(baseline) Path
        +load(baseline_id) Baseline
        +load_file(path) Baseline
        +list_baselines() list
        +latest_for_system(system_id) Baseline
    }

    class Baseline {
        +baseline_id: str
        +system_id: str
        +profile: str
        +config: ConfigMap
        +captured_at: str
        +schema_version: str
        +description: str
        +to_dict() dict
        +from_dict(data) Baseline
    }

    class DriftDetector {
        +baseline: Baseline
        +compare(current) DriftReport
    }

    class DriftReport {
        +report_id: str
        +system_id: str
        +baseline_id: str
        +generated_at: str
        +findings: list~DriftFinding~
        +drifted_count: int
        +is_compliant: bool
        +severity_counts() dict
        +to_dict() dict
        +to_json(indent) str
        +save(path)
        +checksum() str
    }

    class DriftFinding {
        +key: str
        +drift_type: DriftType
        +baseline_value: Any
        +current_value: Any
        +severity: str
        +control_refs: list~str~
        +remediation: str
        +to_dict() dict
    }

    class ComplianceProfile {
        +name: str
        +version: str
        +rules: list~ComplianceRule~
        +description: str
        +from_dict(data) ComplianceProfile
        +from_file(path) ComplianceProfile
        +rule_for_key(key) ComplianceRule
    }

    class ComplianceRule {
        +rule_id: str
        +key_pattern: str
        +expected: Any
        +severity: str
        +controls: list~str~
        +remediation: str
        +matches(key) bool
    }

    class ComplianceEvaluator {
        +profile: ComplianceProfile
        +annotate(report)
        +evaluate(report) ComplianceResult
    }

    class ComplianceResult {
        +report: DriftReport
        +profile: ComplianceProfile
        +violations: list~DriftFinding~
        +passed: bool
        +violation_count: int
        +highest_severity: str
        +severity_counts() dict
        +to_dict() dict
    }

    %% Relationships
    CLI --> ConfigParser : uses
    CLI --> BaselineStore : uses
    CLI --> DriftDetector : uses
    CLI --> ComplianceEvaluator : uses
    CLI --> ComplianceProfile : uses

    BaselineStore "1" --> "*" Baseline : persists
    Baseline --> ConfigParser : config from

    DriftDetector --> Baseline : references
    DriftDetector --> DriftReport : produces
    DriftReport "1" --> "*" DriftFinding : contains

    ComplianceProfile "1" --> "*" ComplianceRule : contains
    ComplianceEvaluator --> ComplianceProfile : uses
    ComplianceEvaluator --> DriftReport : annotates / evaluates
    ComplianceEvaluator --> ComplianceResult : produces
    ComplianceResult --> DriftReport : references
    ComplianceResult "1" --> "*" DriftFinding : violations
```

---

## Module Dependencies

```mermaid
graph LR
    cli["src/cli.py"] --> config_parser["src/config_parser.py"]
    cli --> baseline_store["src/baseline_store.py"]
    cli --> drift_detector["src/drift_detector.py"]
    cli --> compliance_rules["src/compliance_rules.py"]

    drift_detector --> baseline_store
    compliance_rules --> drift_detector

    baseline_store --> config_parser
```

---

## Component Descriptions

| Component | Module | Responsibility |
|---|---|---|
| CLI | `cli.py` | Entry point, argument parsing, orchestration |
| Config Parser | `config_parser.py` | File I/O, flattening, schema validation |
| Baseline Store | `baseline_store.py` | Baseline persistence and retrieval |
| Baseline | `baseline_store.Baseline` | Data model for a baseline snapshot |
| Drift Detector | `drift_detector.py` | Configuration comparison and finding generation |
| Drift Report | `drift_detector.DriftReport` | Aggregated comparison results |
| Drift Finding | `drift_detector.DriftFinding` | Single configuration difference record |
| Compliance Profile | `compliance_rules.ComplianceProfile` | Loaded rule set |
| Compliance Rule | `compliance_rules.ComplianceRule` | Single policy assertion with glob matching |
| Compliance Evaluator | `compliance_rules.ComplianceEvaluator` | Rule evaluation and severity annotation |
| Compliance Result | `compliance_rules.ComplianceResult` | Final compliance posture output |
