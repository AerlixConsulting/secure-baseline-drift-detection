# Architecture Overview

<!-- SPDX-License-Identifier: Apache-2.0 -->
<!-- Copyright 2024 Aerlix Consulting -->

## Purpose

The **Secure Baseline Drift Detection** system provides a structured capability for detecting and evaluating configuration drift in managed systems.  It closes the gap between point-in-time hardening activities and the continuous monitoring required by NIST 800-53, FedRAMP Continuous Monitoring, and CMMC practices.

---

## Core Concepts

| Concept | Description |
|---|---|
| **Baseline** | An authoritative snapshot of a system's configuration at a known-good point in time, annotated with compliance profile, system ID, and timestamp |
| **Current State** | A live (or recently-collected) representation of a system's configuration |
| **Drift** | Any difference between the current state and the stored baseline (added keys, removed keys, or changed values) |
| **Compliance Rule** | A policy assertion that maps a configuration key to an expected value, severity level, and NIST control reference |
| **Drift Report** | A structured JSON document enumerating all drift findings for a specific system and baseline pair |
| **Compliance Result** | An evaluated view of the drift report scored against a compliance profile, identifying violations and overall posture |

---

## System Architecture

The tool is composed of four Python modules and a CLI layer:

```
┌──────────────────────────────────────────────────────────────────┐
│                       External Inputs                           │
│   YAML/JSON config files  │  Compliance profiles  │  Baselines  │
└──────────┬────────────────┴───────────────────────┴─────────────┘
           │
    ┌──────▼──────────────────────────────────────────────────────┐
    │                     CLI Layer  (src/cli.py)                 │
    │  drift-detect baseline capture | drift compare | evaluate   │
    └──────┬────────────────┬────────────────────┬───────────────┘
           │                │                    │
    ┌──────▼──────┐  ┌──────▼──────┐  ┌─────────▼──────────────┐
    │  Config     │  │  Baseline   │  │   Drift Detector        │
    │  Parser     │  │  Store      │  │                         │
    │             │  │             │  │  DriftDetector.compare()│
    │  load_config│  │  save/load  │  │  → DriftReport          │
    │  flatten()  │  │  list/query │  │                         │
    └──────┬──────┘  └──────┬──────┘  └─────────┬──────────────┘
           │                │                    │
           └────────────────┴────────────────────┘
                                  │
                     ┌────────────▼───────────────┐
                     │   Compliance Rules Engine   │
                     │                             │
                     │  ComplianceProfile.load()   │
                     │  ComplianceEvaluator        │
                     │   .annotate(report)         │
                     │   .evaluate(report)         │
                     │  → ComplianceResult         │
                     └─────────────────────────────┘
```

---

## Module Responsibilities

### `config_parser.py`

- Loads YAML or JSON configuration files
- Recursively flattens nested structures into dotted-path key maps: `os.ssh.permit_root_login`
- Normalises list values into sorted, stable strings for deterministic diffing
- Validates required key presence

### `baseline_store.py`

- Defines the `Baseline` data model (schema version, system ID, profile, config, metadata)
- Provides `BaselineStore` for file-system-backed persistence (one JSON file per baseline)
- Supports `save`, `load`, `load_file`, `list_baselines`, and `latest_for_system` operations

### `drift_detector.py`

- Implements `DriftDetector.compare(current)` which diffs current state against a stored baseline
- Produces `DriftFinding` objects typed as `added`, `removed`, or `changed`
- Produces a `DriftReport` with summary counts and finding list
- Normalises type differences (bool vs. string "true") to avoid false positives

### `compliance_rules.py`

- Loads compliance profiles from YAML (supports multiple profiles: CIS, STIG, custom)
- `ComplianceRule` supports glob-pattern key matching for families of settings
- `ComplianceEvaluator.annotate(report)` enriches findings with severity and control references
- `ComplianceEvaluator.evaluate(report)` returns a `ComplianceResult` with violations and posture summary
- Severity ordering: `critical > high > medium > low > unknown`

### `cli.py`

- Provides `drift-detect` CLI entry point with sub-commands
- `baseline capture` — ingest config file and store baseline
- `baseline list` — enumerate stored baselines
- `drift compare` — compare current state against stored baseline
- `compliance evaluate` — score a drift report against rules

---

## Data Flow

```
Configuration File (YAML/JSON)
    │
    ▼ config_parser.load_config()
Flat ConfigMap {key: value}
    │
    ▼ baseline_store.BaselineStore.save()
Baseline JSON File  ◄────── metadata (id, timestamp, profile)
    │
    │   (later)
    │
    ▼ drift_detector.DriftDetector.compare(current_state)
DriftReport {findings: [...]}
    │
    ▼ compliance_rules.ComplianceEvaluator.evaluate(report)
ComplianceResult {violations: [...], severity: "critical"}
    │
    ▼ cli.py / output
drift-report.json + compliance-result.json
```

---

## Key Design Decisions

See [`docs/design-decisions.md`](design-decisions.md) for rationale.

| Decision | Choice |
|---|---|
| Configuration representation | Flat dotted-path key map |
| Baseline storage format | JSON files on filesystem |
| Comparison strategy | Set-based key diff with value normalisation |
| Rule matching | Glob patterns (supports families of keys) |
| Severity model | 4-tier: critical / high / medium / low |
| Control framework | NIST 800-53 Rev 5 with CSF cross-references |

---

## Compliance Alignment

| Capability | NIST 800-53 | NIST CSF | RMF Phase |
|---|---|---|---|
| Baseline capture | CM-2, CM-8 | ID.AM-1 | Categorize / Select |
| Baseline storage | CM-2(2), MP-6 | PR.DS-1 | Implement |
| Drift detection | CM-3, CM-6 | DE.CM-7 | Monitor |
| Compliance evaluation | CA-7, SI-2 | RS.AN-1 | Assess |
| Report generation | AU-6, IR-4 | RS.RP-1 | Monitor |

Full mapping: [`controls/control-mapping.md`](../controls/control-mapping.md)
