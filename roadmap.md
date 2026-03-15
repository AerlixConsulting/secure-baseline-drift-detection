# Roadmap

<!-- SPDX-License-Identifier: Apache-2.0 -->
<!-- Copyright 2024 Aerlix Consulting -->

This document describes the planned development roadmap for the **Secure Baseline Drift Detection** tool.  Items are organised by phase and priority.

---

## v1.0 — Foundation (Current Release)

- [x] Core Python modules: `config_parser`, `baseline_store`, `drift_detector`, `compliance_rules`
- [x] CLI entrypoint with `baseline capture`, `drift compare`, `compliance evaluate` sub-commands
- [x] YAML/JSON configuration ingestion with recursive flattening
- [x] Baseline persistence as versioned JSON files
- [x] Glob-pattern compliance rule matching
- [x] Severity scoring: critical / high / medium / low
- [x] NIST 800-53, NIST CSF, and RMF control mapping
- [x] Sample compliance profile (CIS Ubuntu 22.04 Level 2)
- [x] Example baselines, current state, and drift reports
- [x] CI workflow with ruff + pytest

---

## v1.1 — Compliance Profile Expansion

**Target:** Q3 2024

- [ ] Additional compliance profiles:
  - [ ] CIS Red Hat Enterprise Linux 9 Level 2
  - [ ] CIS Amazon Linux 2023 Level 1
  - [ ] DISA STIG Ubuntu 22.04
  - [ ] FedRAMP Moderate baseline
  - [ ] CMMC Level 2 configuration controls
- [ ] Profile inheritance (extend a base profile with organisation-specific overrides)
- [ ] Profile validation CLI command: `drift-detect profile validate --rules profile.yaml`
- [ ] Profile version compatibility checking between stored baselines and current profiles

---

## v1.2 — Automation and Integration

**Target:** Q4 2024

- [ ] Ansible integration module — gather system facts and pipe directly to baseline capture
- [ ] Terraform provider stub for infrastructure configuration baselines
- [ ] Jira/ServiceNow webhook output for automatic ticket creation on high/critical findings
- [ ] Structured log output (JSON lines) for SIEM ingestion (Splunk, Microsoft Sentinel)
- [ ] GitHub Actions reusable workflow for drift gate integration
- [ ] Docker image for containerised execution in CI pipelines

---

## v1.3 — Multi-System Fleet Support

**Target:** Q1 2025

- [ ] Fleet-level comparison: compare all systems against a golden baseline
- [ ] Aggregated fleet compliance report with heat-map output
- [ ] System group / tagging support (e.g., group systems by environment: prod / staging / dev)
- [ ] Baseline lineage tracking: visualise drift evolution across multiple captures
- [ ] Delta baseline: create a new baseline that updates only the changed keys

---

## v2.0 — Pluggable Storage Backends

**Target:** Q2 2025

- [ ] Abstract `BaselineBackend` interface for pluggable storage
- [ ] Amazon S3 backend for cloud-native deployments
- [ ] PostgreSQL backend for enterprise fleet management
- [ ] Read-only S3 mode for security-hardened deployments
- [ ] Encryption at rest for baseline files (AES-256)
- [ ] Signed baselines using SHA-256 HMAC or GPG for tamper detection

---

## v2.1 — Web API and Dashboard

**Target:** Q3 2025

- [ ] FastAPI REST service exposing baseline capture, drift detection, and compliance evaluation
- [ ] OpenAPI schema for API documentation and client generation
- [ ] Web dashboard (React or Streamlit) for visual drift review
- [ ] Time-series compliance posture trending
- [ ] Role-based access control (RBAC) for multi-tenant deployments

---

## v3.0 — AI-Assisted Analysis

**Target:** 2026

- [ ] LLM-assisted remediation guidance generation
- [ ] Anomaly detection: identify statistically unusual drift patterns
- [ ] Natural language compliance profile authoring assistant
- [ ] Automated baseline refresh recommendations based on patch events

---

## Contributing to the Roadmap

If you have feature requests or would like to contribute to a roadmap item, please open an issue with the label `enhancement` and reference the roadmap item.

See [CONTRIBUTING.md](CONTRIBUTING.md) for contribution guidelines.
