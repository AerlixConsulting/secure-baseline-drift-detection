# System Context Diagram

<!-- SPDX-License-Identifier: Apache-2.0 -->
<!-- Copyright 2024 Aerlix Consulting -->

This diagram shows the Secure Baseline Drift Detection system in the context of the external actors and systems it interacts with.

```mermaid
flowchart TB
    subgraph External["External Actors"]
        Eng["Security Engineer\n(Baseline capture,\nRule authoring)"]
        SOC["SOC Analyst\n(Drift review,\nRemediation)"]
        AO["Authorising Official\n(Compliance reports)"]
        CI["CI/CD Pipeline\n(Automated checks)"]
    end

    subgraph System["Secure Baseline Drift Detection System"]
        CLI["CLI Entrypoint\ndrift-detect"]
        Engine["Detection Engine\n(Python modules)"]
        Store["Baseline Store\n(JSON on filesystem)"]
        Reports["Report Outputs\n(JSON)"]
    end

    subgraph Sources["Configuration Sources"]
        CfgMgmt["Configuration Management\n(Ansible, Chef, Puppet)"]
        CISCAT["CIS-CAT / SCAP\n(Automated benchmarking)"]
        Manual["Manual Configuration\n(YAML / JSON files)"]
    end

    subgraph Consumers["Downstream Consumers"]
        GRC["GRC Platform\n(ServiceNow, Archer)"]
        SIEM["SIEM\n(Splunk, Sentinel)"]
        Ticket["Ticketing System\n(Jira, ServiceNow)"]
        ATO_System["ATO Package\n(eMASS, XACTA)"]
    end

    Eng -->|"capture baseline\nevaluate rules"| CLI
    SOC -->|"review drift report\ntrack remediation"| Reports
    AO -->|"review compliance\nresult"| Reports
    CI -->|"automated drift gate\n(exit code check)"| CLI

    CfgMgmt -->|"current state YAML"| CLI
    CISCAT -->|"benchmark output JSON"| CLI
    Manual -->|"config file"| CLI

    CLI --> Engine
    Engine --> Store
    Engine --> Reports

    Reports -->|"compliance result"| GRC
    Reports -->|"drift events"| SIEM
    Reports -->|"violations"| Ticket
    Reports -->|"evidence artefacts"| ATO_System
```

---

## Actor Descriptions

| Actor | Role |
|---|---|
| Security Engineer | Authors compliance profiles, captures initial baselines post-hardening |
| SOC Analyst | Monitors drift reports, initiates remediation workflows |
| Authorising Official | Reviews compliance posture reports for ATO decisions |
| CI/CD Pipeline | Runs drift checks as quality gates in deployment pipelines |
| Configuration Management | Provides live system configuration as input |
| GRC Platform | Consumes compliance results for risk register and POA&M tracking |
| SIEM | Ingests drift events for alerting and correlation |
| ATO Package | Receives evidence artefacts (baseline JSON, drift reports) |
