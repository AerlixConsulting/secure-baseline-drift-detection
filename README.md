# Secure Baseline Drift Detection

[![CI](https://github.com/AerlixConsulting/secure-baseline-drift-detection/actions/workflows/ci.yml/badge.svg)](https://github.com/AerlixConsulting/secure-baseline-drift-detection/actions/workflows/ci.yml)
[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](LICENSE)

> **Aerlix Consulting** — Reference implementation for enterprise-grade configuration baseline management and drift detection, aligned to NIST 800-53, NIST CSF, and RMF.

---

## Overview

The **Secure Baseline Drift Detection** tool enables security and operations teams to:

1. **Capture** authoritative configuration baselines from OS hardening, IAM, and network configuration sources.
2. **Store** baselines with full metadata (timestamp, system ID, compliance profile, schema version).
3. **Detect drift** by comparing live system state against stored baselines and producing structured drift reports.
4. **Evaluate compliance** by scoring drift findings against rule-based compliance profiles (severity, must-have settings, criticality thresholds).

This tool is designed for use in regulated environments including FedRAMP, FISMA, CMMC, SOC 2, and enterprise security operations.

---

## Architecture

```
┌─────────────────────────────────────────────────────┐
│                   CLI Entrypoint                    │
│              src/cli.py  (drift-detect)             │
└──────────┬──────────────┬──────────────┬────────────┘
           │              │              │
    ┌──────▼──────┐ ┌─────▼──────┐ ┌────▼──────────┐
    │Config Parser│ │  Baseline  │ │ Drift Detector │
    │             │ │   Store    │ │                │
    └──────┬──────┘ └─────┬──────┘ └────┬──────────┘
           │              │              │
           └──────────────▼──────────────┘
                          │
                 ┌────────▼────────┐
                 │ Compliance Rules│
                 │    Engine       │
                 └─────────────────┘
```

Full Mermaid diagrams are in [`architecture/`](architecture/).

---

## Quick Start

### Prerequisites

- Python 3.11+
- pip

### Installation

```bash
git clone https://github.com/AerlixConsulting/secure-baseline-drift-detection.git
cd secure-baseline-drift-detection
pip install -e ".[dev]"
```

### Capture a Baseline

```bash
drift-detect baseline capture \
  --input examples/current_state.yaml \
  --system-id webserver-prod-01 \
  --profile cis-level2 \
  --output baselines/webserver-prod-01-baseline.json
```

### Detect Drift

```bash
drift-detect drift compare \
  --baseline baselines/webserver-prod-01-baseline.json \
  --current examples/current_state.yaml \
  --rules examples/compliance_profile.yaml \
  --output reports/drift-report.json
```

### Evaluate Compliance

```bash
drift-detect compliance evaluate \
  --drift-report reports/drift-report.json \
  --rules examples/compliance_profile.yaml
```

---

## Repository Structure

```
secure-baseline-drift-detection/
├── src/                        # Core Python modules
│   ├── __init__.py
│   ├── cli.py                  # CLI entrypoint
│   ├── config_parser.py        # YAML/JSON config ingestion
│   ├── baseline_store.py       # Baseline persistence + metadata
│   ├── drift_detector.py       # Diff engine and report builder
│   └── compliance_rules.py     # Rule evaluation and severity scoring
├── tests/                      # Pytest test suite
│   ├── test_drift_detector.py
│   └── test_compliance_rules.py
├── examples/
│   ├── baselines/              # Sample stored baselines
│   ├── current_state.yaml      # Sample current system state
│   ├── compliance_profile.yaml # Sample compliance rules
│   └── drift_report.json       # Sample output report
├── docs/
│   ├── architecture-overview.md
│   ├── use-cases.md
│   └── design-decisions.md
├── architecture/
│   ├── system-context.md
│   ├── component-architecture.md
│   ├── data-flow.md
│   └── trust-boundaries.md
├── controls/
│   └── control-mapping.md      # NIST CSF / 800-53 / RMF mapping
├── assets/                     # Diagrams and supporting images
├── tools/                      # Legacy helper scripts (retained)
├── .github/workflows/
│   ├── ci.yml                  # Lint + test
│   └── drift.yml               # Scheduled drift reporting
├── pyproject.toml
├── LICENSE
├── roadmap.md
└── CONTRIBUTING.md
```

---

## Modules

| Module | Description |
|---|---|
| `config_parser.py` | Loads and normalises YAML/JSON system configurations into a flat key→value map |
| `baseline_store.py` | Saves and loads baseline snapshots with metadata (system ID, profile, timestamp) |
| `drift_detector.py` | Diffs current state against baseline; produces structured drift findings |
| `compliance_rules.py` | Evaluates drift findings against rule-based compliance profiles with severity scoring |
| `cli.py` | Unified CLI with sub-commands: `baseline capture`, `drift compare`, `compliance evaluate` |

---

## Example Drift Report

```json
{
  "report_id": "dr-20240315-webserver-prod-01",
  "system_id": "webserver-prod-01",
  "baseline_id": "bl-20240301-webserver-prod-01",
  "generated_at": "2024-03-15T10:00:00Z",
  "summary": {
    "total_checks": 42,
    "drifted": 5,
    "compliant": 37,
    "critical": 1,
    "high": 2,
    "medium": 2,
    "low": 0
  },
  "findings": [
    {
      "key": "os.ssh.permit_root_login",
      "baseline_value": "no",
      "current_value": "yes",
      "severity": "critical",
      "control_refs": ["CM-6", "CM-2"],
      "remediation": "Set PermitRootLogin no in /etc/ssh/sshd_config and restart sshd"
    }
  ]
}
```

---

## Compliance Alignment

| Capability | NIST 800-53 | NIST CSF | RMF Phase |
|---|---|---|---|
| Baseline capture | CM-2, CM-8 | ID.AM-1 | Categorize / Select |
| Drift detection | CM-3, CM-6 | DE.CM-7 | Monitor |
| Compliance evaluation | CA-7, SI-2 | RS.AN-1 | Assess |
| Report generation | AU-6, IR-4 | RS.RP-1 | Monitor |

Full control mapping: [`controls/control-mapping.md`](controls/control-mapping.md)

---

## Development

```bash
# Install dev dependencies
pip install -e ".[dev]"

# Lint
ruff check src/ tests/

# Format
ruff format src/ tests/

# Test
pytest tests/ -v
```

---

## License

Copyright 2024 Aerlix Consulting. Licensed under the [Apache License, Version 2.0](LICENSE).
