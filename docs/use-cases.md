# Use Cases

<!-- SPDX-License-Identifier: Apache-2.0 -->
<!-- Copyright 2024 Aerlix Consulting -->

## Overview

This document describes the primary use cases for the **Secure Baseline Drift Detection** tool, along with the personas, triggers, inputs, and expected outputs for each scenario.

---

## UC-01: Initial Hardening Baseline Capture

**Persona:** Security Engineer / System Administrator  
**Trigger:** Post-hardening of a new or rebuilt system  
**Context:** After applying a CIS or STIG hardening script, capture the known-good configuration state.

### Inputs
- System configuration file (gathered by Ansible, CIS-CAT, or custom script)
- Compliance profile name (e.g., `cis-ubuntu-22-04-level2`)
- System identifier (e.g., `webserver-prod-01`)

### Steps
```bash
drift-detect baseline capture \
  --input /tmp/webserver-prod-01-config.yaml \
  --system-id webserver-prod-01 \
  --profile cis-ubuntu-22-04-level2 \
  --store /data/baselines/
```

### Outputs
- `baselines/bl-20240301-webserver-prod-01.json` with full config and metadata
- Terminal confirmation with baseline ID, key count, and timestamp

### Value
Establishes a cryptographically-referenced starting point for continuous compliance monitoring.  Satisfies CM-2 (Baseline Configuration) and CM-8 (System Component Inventory) under NIST 800-53.

---

## UC-02: Scheduled Drift Detection

**Persona:** Security Operations Center (SOC) Analyst  
**Trigger:** Scheduled CI/CD pipeline run or cron job (e.g., weekly)  
**Context:** Detect unauthorised or unplanned configuration changes since the last baseline capture.

### Inputs
- Current system state (gathered by configuration management tooling)
- Stored baseline JSON from the baseline store
- Optional: compliance profile for severity annotation

### Steps
```bash
# Gather current state (example: via Ansible)
ansible -m setup webserver-prod-01 > /tmp/current-state.yaml

# Run drift detection
drift-detect drift compare \
  --baseline /data/baselines/bl-20240301-webserver-prod-01.json \
  --current /tmp/current-state.yaml \
  --rules /config/profiles/cis-ubuntu-22-04-level2.yaml \
  --output /reports/drift-$(date +%Y%m%d).json
```

### Outputs
- `drift-20240315.json` with all findings, severities, and control references
- Non-zero exit code if drift is detected (suitable for CI gate)

### Value
Enables continuous monitoring as required by FedRAMP CM-3 and NIST CSF DE.CM-7.  Provides evidence for Plan of Action and Milestones (POA&M) if violations are found.

---

## UC-03: Pre-Change Validation (Change Management Gate)

**Persona:** Change Advisory Board (CAB) / DevOps Engineer  
**Trigger:** Before applying a configuration change in a change management workflow  
**Context:** Validate that planned changes are the only differences from baseline, not unintended drift.

### Steps
1. Capture pre-change baseline
2. Apply change
3. Capture post-change state
4. Run drift compare to verify only planned changes occurred

```bash
# Pre-change
drift-detect baseline capture --input pre-change.yaml --system-id prod-01 --profile cis --store /baselines/

# Post-change  
drift-detect drift compare --baseline /baselines/bl-...-prod-01.json --current post-change.yaml --output diff.json
```

### Value
Provides change traceability and audit evidence.  Satisfies CM-3 (Configuration Change Control) and supports RMF continuous monitoring.

---

## UC-04: Compliance Posture Assessment

**Persona:** Compliance Analyst / Authorising Official (AO)  
**Trigger:** Before a security assessment, ATO renewal, or internal audit  
**Context:** Evaluate overall compliance posture of managed systems against a specific regulatory profile.

### Steps
```bash
# Run full drift + compliance evaluation pipeline
for system in webserver-01 database-01 jumphost-01; do
  drift-detect drift compare \
    --baseline baselines/bl-latest-${system}.json \
    --current current-states/${system}.yaml \
    --rules profiles/fedramp-moderate.yaml \
    --output reports/${system}-drift.json

  drift-detect compliance evaluate \
    --drift-report reports/${system}-drift.json \
    --rules profiles/fedramp-moderate.yaml \
    --output reports/${system}-compliance.json
done
```

### Outputs
- Per-system compliance result JSON with violation counts and highest severity
- Input to dashboard or GRC platform

### Value
Provides objective, repeatable compliance evidence.  Supports CA-7 (Continuous Monitoring) and SA-11 (Developer Security Testing and Evaluation).

---

## UC-05: Incident Response Investigation

**Persona:** Incident Responder / Digital Forensics Analyst  
**Trigger:** After a security incident or anomalous behaviour detection  
**Context:** Determine if system compromise involved configuration manipulation.

### Steps
```bash
# Compare incident-time snapshot against known-good baseline
drift-detect drift compare \
  --baseline baselines/bl-20240301-compromised-host.json \
  --current incident/compromised-host-snapshot.yaml \
  --rules profiles/incident-response.yaml \
  --output reports/incident-drift-report.json
```

### Value
Provides structured evidence of configuration manipulation.  Supports IR-4 (Incident Handling) and SI-2 (Flaw Remediation).  Output can be attached directly to the incident record.

---

## UC-06: Multi-System Fleet Comparison

**Persona:** Platform Engineer / Cloud Security Architect  
**Trigger:** After fleet-wide update deployment or periodic audit  
**Context:** Identify configuration inconsistencies across a fleet of like systems.

### Concept
Compare each system in a fleet against the authoritative golden baseline.  Systems that have diverged are flagged for remediation or baseline refresh.

### Value
Enables CM-8 (System Component Inventory) enforcement and supports identification of lateral movement or policy exceptions.

---

## Anti-Patterns (What This Tool Does Not Do)

| Anti-Pattern | Explanation |
|---|---|
| Automated remediation | This tool reports drift; remediation is orchestrated by Ansible, Terraform, or a human process |
| Real-time monitoring | Drift is detected at comparison time, not continuously via agent |
| Vulnerability scanning | Use dedicated scanners (Tenable, Qualys) for CVE detection; this tool focuses on configuration policy |
| Identity management | IAM posture checks are limited to configuration settings; use identity providers for authoritative IAM governance |
