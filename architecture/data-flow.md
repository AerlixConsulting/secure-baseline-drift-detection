# Data Flow Diagram

<!-- SPDX-License-Identifier: Apache-2.0 -->
<!-- Copyright 2024 Aerlix Consulting -->

This diagram traces the flow of data through the Secure Baseline Drift Detection pipeline from raw configuration input to compliance-evaluated output.

## End-to-End Pipeline

```mermaid
flowchart LR
    subgraph Input["Input Layer"]
        raw_yaml["System Config\nYAML / JSON"]
        profile_yaml["Compliance Profile\nYAML"]
        baseline_file["Stored Baseline\nJSON"]
    end

    subgraph Parse["Parse & Normalise"]
        load_config["config_parser\n.load_config()"]
        flat_map["Flat ConfigMap\n{key: value}"]
    end

    subgraph Store["Baseline Store"]
        capture["BaselineStore\n.save()"]
        baseline_json["Baseline JSON\nbl-YYYYMMDD-{id}.json"]
        load_baseline["BaselineStore\n.load_file()"]
    end

    subgraph Detect["Drift Detection"]
        detector["DriftDetector\n.compare()"]
        findings["DriftFindings\n[added|removed|changed]"]
        report["DriftReport\n{summary, findings}"]
    end

    subgraph Evaluate["Compliance Evaluation"]
        load_profile["ComplianceProfile\n.from_file()"]
        evaluator["ComplianceEvaluator\n.annotate() + .evaluate()"]
        result["ComplianceResult\n{violations, severity}"]
    end

    subgraph Output["Output Layer"]
        drift_json["drift-report.json"]
        compliance_json["compliance-result.json"]
        exit_code["Exit Code\n0=clean / 1=drift"]
        stdout["Console Summary"]
    end

    raw_yaml --> load_config
    load_config --> flat_map
    flat_map --> capture
    capture --> baseline_json

    baseline_file --> load_baseline
    load_baseline --> detector
    raw_yaml --> load_config
    flat_map --> detector

    detector --> findings
    findings --> report

    profile_yaml --> load_profile
    load_profile --> evaluator
    report --> evaluator
    evaluator --> result

    report --> drift_json
    result --> compliance_json
    report --> exit_code
    result --> stdout
```

---

## Baseline Capture Data Flow

```mermaid
sequenceDiagram
    actor Eng as Security Engineer
    participant CLI as drift-detect CLI
    participant Parser as config_parser
    participant Store as BaselineStore

    Eng->>CLI: drift-detect baseline capture --input config.yaml --system-id srv-01 --profile cis
    CLI->>Parser: load_config("config.yaml")
    Parser->>Parser: parse YAML
    Parser->>Parser: flatten(nested_dict)
    Parser-->>CLI: ConfigMap {key: value}
    CLI->>Store: Baseline(system_id, profile, config)
    Store->>Store: assign baseline_id + timestamp
    Store->>Store: write JSON to filesystem
    Store-->>CLI: saved path
    CLI-->>Eng: "Baseline captured → baselines/bl-20240301-srv-01.json"
```

---

## Drift Detection Data Flow

```mermaid
sequenceDiagram
    actor SOC as SOC Analyst / CI Pipeline
    participant CLI as drift-detect CLI
    participant Store as BaselineStore
    participant Parser as config_parser
    participant Detector as DriftDetector
    participant Evaluator as ComplianceEvaluator

    SOC->>CLI: drift-detect drift compare --baseline bl.json --current state.yaml --rules profile.yaml
    CLI->>Store: load_file("bl.json")
    Store-->>CLI: Baseline object
    CLI->>Parser: load_config("state.yaml")
    Parser-->>CLI: current ConfigMap
    CLI->>Detector: DriftDetector(baseline).compare(current)
    Detector->>Detector: set diff (added/removed/changed)
    Detector-->>CLI: DriftReport{findings}
    CLI->>Evaluator: ComplianceEvaluator(profile).annotate(report)
    Evaluator->>Evaluator: match each finding to rule
    Evaluator->>Evaluator: set severity + control_refs
    Evaluator-->>CLI: annotated DriftReport
    CLI->>CLI: report.save("drift-report.json")
    CLI-->>SOC: Summary + exit code 1 (drift detected)
```

---

## Data Schema

### Baseline JSON Schema

```
{
  schema_version: "1.0",
  baseline_id: "bl-{YYYYMMDD}-{system-id}",
  system_id: string,
  profile: string,
  captured_at: ISO-8601 timestamp,
  description: string,
  config: {
    "{dotted.path.key}": scalar_value,
    ...
  }
}
```

### Drift Report JSON Schema

```
{
  report_id: "dr-{YYYYMMDD}-{system-id}",
  system_id: string,
  baseline_id: string,
  generated_at: ISO-8601 timestamp,
  summary: {
    total_checks: int,
    drifted: int,
    compliant: int,
    critical: int,
    high: int,
    medium: int,
    low: int,
    unknown: int
  },
  findings: [
    {
      key: string,
      drift_type: "added" | "removed" | "changed",
      baseline_value: any,
      current_value: any,
      severity: "critical" | "high" | "medium" | "low" | "unknown",
      control_refs: [string, ...],
      remediation: string
    }
  ]
}
```
