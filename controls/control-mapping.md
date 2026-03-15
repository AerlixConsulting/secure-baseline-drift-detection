# Control Mapping

<!-- SPDX-License-Identifier: Apache-2.0 -->
<!-- Copyright 2024 Aerlix Consulting -->

This document maps the capabilities of the **Secure Baseline Drift Detection** system to NIST SP 800-53 Rev 5 controls, NIST Cybersecurity Framework (CSF) 1.1 subcategories, and the Risk Management Framework (RMF) lifecycle phases.

---

## Mapping Summary

| Capability | NIST 800-53 Controls | NIST CSF Subcategories | RMF Phase |
|---|---|---|---|
| Baseline configuration capture | CM-2, CM-8 | ID.AM-1, ID.AM-5 | Select / Implement |
| Baseline storage with metadata | CM-2(2), MP-6 | PR.DS-1 | Implement |
| Configuration change detection | CM-3, CM-6 | DE.CM-7 | Monitor |
| Compliance rule evaluation | CA-7, CA-2 | DE.CM-1, DE.AE-1 | Assess / Monitor |
| Severity-based findings | RA-3, RA-5 | ID.RA-3, ID.RA-6 | Assess |
| Drift report generation | AU-6, AU-12 | DE.AE-3, RS.AN-1 | Monitor |
| Remediation guidance | SI-2, CA-5 | RS.MI-3, RC.RP-1 | Monitor |
| Evidence for ATO packages | CA-2, SA-11 | ID.GV-4 | Assess |

---

## Detailed Control Mappings

### CM-2 — Baseline Configuration

> *Develop, document, and maintain under configuration control a current baseline configuration of the information system.*

**How this tool supports CM-2:**
- `baseline capture` creates a timestamped, machine-readable baseline configuration document
- Baselines include system ID, compliance profile, and schema version metadata
- Baselines can be stored in version-controlled repositories for audit trail

**Evidence artefacts:** `baselines/bl-{date}-{system-id}.json`

---

### CM-2(2) — Automation Support for Accuracy and Currency

> *Employ automated mechanisms to maintain an up-to-date, complete, accurate, and readily available baseline configuration.*

**How this tool supports CM-2(2):**
- Automated baseline capture integrates with configuration management tools (Ansible, CIS-CAT)
- CI/CD integration enables scheduled baseline refresh and drift detection

---

### CM-3 — Configuration Change Control

> *Determine the types of changes to the information system that are configuration-controlled.*

**How this tool supports CM-3:**
- Drift detection identifies all changes since the last baseline was captured
- `drift_type` classification (added / removed / changed) provides structured change evidence
- Non-zero exit code enables CI pipeline gates to block unauthorised changes

---

### CM-6 — Configuration Settings

> *Establish and document configuration settings for information technology products employed within the information system.*

**How this tool supports CM-6:**
- Compliance profiles encode the required configuration settings (expected values)
- Rule evaluation validates that current settings match required values
- Findings provide specific remediation guidance per setting

---

### CM-7 — Least Functionality

> *Configure the information system to provide only essential capabilities.*

**How this tool supports CM-7:**
- Rules can detect unauthorised or unnecessary services (e.g., `services.cups: active` when it should be `inactive`)
- Supports identification of added keys representing new, unplanned capabilities

---

### CM-8 — System Component Inventory

> *Develop and document an inventory of system components.*

**How this tool supports CM-8:**
- Baselines include comprehensive inventories of software packages, services, and configurations
- Changes to the inventory are surfaced as drift findings
- Supports asset tracking across managed system fleets

---

### CA-2 — Security Assessments

> *Develop a security assessment plan for the information system.*

**How this tool supports CA-2:**
- Drift reports and compliance results provide structured evidence for security assessments
- Output can be attached directly to assessment packages (eMASS, XACTA)

---

### CA-7 — Continuous Monitoring

> *Develop a continuous monitoring strategy and implement a continuous monitoring program.*

**How this tool supports CA-7:**
- Scheduled drift detection (CI cron jobs, weekly workflows) implements continuous monitoring
- Compliance results provide quantified posture metrics over time
- Integration with SIEM enables real-time alerting on critical drift events

---

### AU-2 — Event Logging

> *Identify the types of events that the system is capable of logging.*

**How this tool supports AU-2:**
- Audit subsystem configuration rules (e.g., `os.audit.*`) verify that required logging is enabled
- Findings flag disabled audit capabilities as compliance violations

---

### AU-6 — Audit Record Review, Analysis, and Reporting

> *Review and analyze information system audit records for indications of inappropriate or unusual activity.*

**How this tool supports AU-6:**
- Drift reports provide structured, machine-readable output for consumption by SIEM and analytics platforms
- Report generation timestamps support trending and historical analysis

---

### RA-3 — Risk Assessment

> *Conduct a risk assessment of the information system.*

**How this tool supports RA-3:**
- Severity scoring (critical / high / medium / low) supports risk prioritisation
- Control references link findings to specific risk areas

---

### RA-5 — Vulnerability Scanning

> *Scan for vulnerabilities in the information system.*

**How this tool supports RA-5 (partial):**
- Configuration-based vulnerability indicators (e.g., weak SSH settings, disabled firewalls) are surfaced as findings
- Note: This tool is not a substitute for network/host vulnerability scanners

---

### SI-2 — Flaw Remediation

> *Identify, report, and correct information system flaws.*

**How this tool supports SI-2:**
- Remediation guidance is embedded in each rule definition
- Compliance results include actionable remediation instructions per violation
- Integration with ticketing systems enables tracked remediation workflows

---

### SI-7 — Software, Firmware, and Information Integrity

> *Employ integrity verification tools to detect unauthorized changes to software, firmware, and information.*

**How this tool supports SI-7:**
- Baseline configurations include package installation state (aide, rkhunter)
- Drift detection identifies removed integrity checking tools

---

### IA-5 — Authenticator Management

> *Manage information system authenticators.*

**How this tool supports IA-5:**
- IAM rules check password policy settings (minimum length, complexity, max age)
- MFA configuration is validated as a compliance requirement
- SSH key-only authentication is enforced through rules

---

## NIST CSF Mapping

| CSF Category | CSF Subcategory | Capability |
|---|---|---|
| **IDENTIFY** | ID.AM-1: Physical devices and systems inventoried | Baseline captures system configuration inventory |
| **IDENTIFY** | ID.AM-5: Resources prioritised based on classification | Severity scoring prioritises remediation effort |
| **IDENTIFY** | ID.RA-3: Threats identified and documented | Drift findings represent threat indicators |
| **PROTECT** | PR.DS-1: Data-at-rest is protected | Baseline files stored with ACL protection |
| **PROTECT** | PR.IP-1: Baseline configuration established | Automated baseline capture |
| **DETECT** | DE.CM-1: Network monitored for anomalies | Network configuration drift detection |
| **DETECT** | DE.CM-7: Monitoring for unauthorized personnel, connections, devices, and software | Drift detection against authorised baseline |
| **DETECT** | DE.AE-3: Event data aggregated and correlated | Drift reports aggregated by system and time |
| **RESPOND** | RS.AN-1: Notifications from detection systems investigated | Drift reports provide investigation starting point |
| **RESPOND** | RS.MI-3: Newly identified vulnerabilities mitigated | Remediation guidance per finding |
| **RECOVER** | RC.RP-1: Recovery plan executed | Remediation instructions support recovery |

---

## RMF Lifecycle Alignment

| RMF Phase | Activity | Tool Capability |
|---|---|---|
| **Categorise** | Identify information types and impact levels | System ID and profile metadata in baselines |
| **Select** | Select security controls | Compliance profiles encode control-derived rules |
| **Implement** | Implement security controls | Baseline capture validates post-implementation state |
| **Assess** | Assess control effectiveness | Compliance evaluation scores against rules |
| **Authorise** | Review risk posture | Drift reports and compliance results as ATO evidence |
| **Monitor** | Continuously monitor controls | Scheduled drift detection and report generation |
