# Design Decisions

<!-- SPDX-License-Identifier: Apache-2.0 -->
<!-- Copyright 2024 Aerlix Consulting -->

This document captures the key architectural and engineering decisions made in the design of the Secure Baseline Drift Detection tool, along with the rationale and trade-offs considered.

---

## DD-01: Flat Dotted-Path Key Representation

**Decision:** All configuration data is flattened into a single-level `dict[str, Any]` with dotted-path keys.

**Rationale:**
- Simplifies diffing logic — comparing two flat dicts is trivially O(n) and produces precise per-key findings
- Enables glob-pattern rule matching on key families (e.g., `os.audit.*`)
- Avoids recursive diff algorithms which produce ambiguous results on nested structures
- YAML and JSON are naturally hierarchical but drift detection is most useful at the leaf level

**Trade-offs:**
- Information about structural changes (moved keys) is lost
- Very long flat key paths can be hard to read in reports

**Alternative Considered:** Deep recursive diff (e.g., `deepdiff` library). Rejected because it produces verbose output that is difficult to map to individual compliance rules.

---

## DD-02: File-System JSON Baseline Storage

**Decision:** Baselines are stored as individual JSON files on the filesystem, one file per baseline.

**Rationale:**
- No external database dependency — the tool works in air-gapped and offline environments
- Baselines are human-readable and can be version-controlled in Git
- Simple `glob("*.json")` enumeration is sufficient for list/query operations at typical scale
- JSON files are easy to transfer, archive, and attach as evidence artefacts

**Trade-offs:**
- Not suitable for very large fleets (thousands of systems) without a backing database
- No atomic update semantics — concurrent writes could corrupt a file

**Planned Extension:** Pluggable storage backends (S3, PostgreSQL) via a `BaselineBackend` interface in a future release.

---

## DD-03: Value Normalisation for Boolean/String Equivalence

**Decision:** Comparison of values normalises both sides to lowercase strings before checking equality.

**Rationale:**
- Configuration files sourced from different tools use inconsistent types:
  - Ansible facts: `True` (Python bool)
  - CIS-CAT output: `"true"` (string)
  - Chef/Puppet: `1` (integer)
- Without normalisation, these generate spurious drift findings that are false positives
- Reduces alert fatigue and improves signal-to-noise ratio

**Trade-offs:**
- The integer `0` and the string `"0"` are treated as equivalent, which may mask intentional type changes

**Caveat:** Explicit type-aware comparison is available by overriding the `_values_differ` helper if strict mode is needed.

---

## DD-04: Glob-Pattern Rule Matching

**Decision:** Compliance rules use `fnmatch` glob patterns to match configuration keys.

**Rationale:**
- Real compliance profiles have families of related settings (e.g., all audit subsystems)
- Specifying each key individually would produce brittle, verbose profiles
- `fnmatch` is a stdlib module with no additional dependencies
- Patterns like `os.audit.*` match all audit keys regardless of the number of subsystems

**Trade-offs:**
- First-match wins; rule ordering matters
- Glob patterns do not support negation or complex expressions

**Alternative Considered:** Regular expressions. Rejected in favour of fnmatch for readability by non-developers who maintain compliance profiles.

---

## DD-05: Severity Four-Tier Model

**Decision:** Findings are classified as `critical`, `high`, `medium`, or `low`.

**Rationale:**
- Aligns with CVSS-style severity models familiar to security practitioners
- Enables priority-based remediation workflows
- Maps cleanly to POA&M priority levels in RMF and FedRAMP

**Trade-offs:**
- Subjective assignment of severity to individual rules requires expert judgement and periodic review
- Does not capture contextual risk (a critical finding on an internet-facing system is more severe than on an isolated dev workstation)

---

## DD-06: Non-Zero Exit Codes for CI Integration

**Decision:** The `drift compare` command returns exit code `1` if any drift is detected, `0` if clean.

**Rationale:**
- Enables drift detection to act as a quality gate in CI/CD pipelines
- Consistent with UNIX convention (zero = success, non-zero = error)
- Allows pipeline authors to decide whether to fail-fast or capture and report

---

## DD-07: Separation of Drift Detection from Compliance Evaluation

**Decision:** Drift detection and compliance rule evaluation are separate stages.

**Rationale:**
- Drift (factual observation) is distinct from compliance (policy assertion)
- A configuration change may be intentional and approved without being a compliance violation
- Separating the stages allows drift reports to be used without a compliance profile (e.g., for change tracking)
- Compliance profiles can be updated independently of the detection logic

**Trade-offs:**
- Two-stage pipeline adds slightly more complexity to the CLI workflow

---

## DD-08: Apache-2.0 License

**Decision:** The project is licensed under Apache License, Version 2.0.

**Rationale:**
- Permissive licence suitable for enterprise adoption and commercial embedding
- Includes an explicit patent grant, important for security tooling in regulated industries
- Compatible with most enterprise open-source policies
- Required by Aerlix Consulting portfolio alignment
