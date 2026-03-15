# Contributing to Secure Baseline Drift Detection

<!-- SPDX-License-Identifier: Apache-2.0 -->
<!-- Copyright 2024 Aerlix Consulting -->

Thank you for your interest in contributing to the **Secure Baseline Drift Detection** project.  This document describes the contribution process, coding standards, and community expectations.

---

## Code of Conduct

All contributors are expected to engage respectfully and professionally.  Harassment, discrimination, or abusive behaviour will not be tolerated.

---

## Getting Started

### Prerequisites

- Python 3.11+
- Git

### Set Up Your Development Environment

```bash
# Fork the repository on GitHub, then clone your fork
git clone https://github.com/<your-org>/secure-baseline-drift-detection.git
cd secure-baseline-drift-detection

# Install the package in editable mode with dev dependencies
pip install -e ".[dev]"

# Verify your environment
ruff check src/ tests/
pytest tests/ -v
```

---

## Branching Model

We use a simple trunk-based branching model:

| Branch | Purpose |
|---|---|
| `main` | Stable, releasable code |
| `copilot/*` | Agent-generated contributions |
| `feature/<name>` | New features |
| `fix/<name>` | Bug fixes |
| `docs/<name>` | Documentation-only changes |

**Branch naming convention:**

```
feature/multi-system-fleet-support
fix/boolean-normalisation-edge-case
docs/update-control-mapping-cmmc
```

---

## Commit Standards

We follow the [Conventional Commits](https://www.conventionalcommits.org/) specification:

```
<type>(<scope>): <description>

[optional body]

[optional footer(s)]
```

**Types:**

| Type | When to use |
|---|---|
| `feat` | New feature |
| `fix` | Bug fix |
| `docs` | Documentation only |
| `test` | Test additions or changes |
| `refactor` | Code restructuring without behaviour change |
| `chore` | Build, tooling, or dependency updates |
| `ci` | CI/CD workflow changes |

**Examples:**

```
feat(compliance): add CIS RHEL 9 Level 2 profile
fix(drift_detector): handle None values in current state correctly
docs(architecture): add trust boundary diagram
test(compliance_rules): add glob pattern edge case coverage
```

---

## Pull Request Process

1. Open a pull request against `main`
2. Fill in the PR template with:
   - Description of the change
   - Link to the related issue (if applicable)
   - Checklist: tests added, lint passes, docs updated
3. All CI checks must pass (ruff + pytest)
4. At least one review is required before merge

---

## Code Quality Standards

### Linting

We use [ruff](https://docs.astral.sh/ruff/) for linting and formatting.

```bash
# Check
ruff check src/ tests/

# Format
ruff format src/ tests/

# Auto-fix
ruff check src/ tests/ --fix
```

### Testing

- All new modules must have corresponding tests in `tests/`
- Test files are named `test_<module>.py`
- Test classes are named `Test<ClassName>`
- Test functions are named `test_<behaviour>`
- Use `pytest` fixtures and `tmp_path` for file-based tests
- Aim for ≥ 80% branch coverage on new code

```bash
# Run tests with coverage
pytest tests/ --cov=src --cov-report=term-missing
```

### Type Hints

- All public functions must have complete type annotations
- Use `from __future__ import annotations` in all modules
- Prefer `X | Y` union syntax over `Optional[X]`

---

## Documentation Standards

### File Headers

All Python source files must include the Apache-2.0 licence header:

```python
# Copyright 2024 Aerlix Consulting
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
```

### Docstrings

Use Google-style docstrings:

```python
def compare(self, current: dict[str, Any]) -> DriftReport:
    """Compare current configuration against the stored baseline.

    Args:
        current: Flat configuration map representing the live system state.

    Returns:
        A DriftReport with all findings populated.

    Raises:
        ValueError: If the current map is empty.
    """
```

### Markdown Documentation

- Use sentence case for headings
- Include a table of contents for documents longer than 3 sections
- Include code examples in fenced code blocks with language hints
- Architecture diagrams must use Mermaid syntax

---

## Adding a Compliance Profile

Compliance profiles live in `examples/` for reference profiles. To add a new profile:

1. Create a YAML file following the schema in `examples/compliance_profile.yaml`
2. Ensure every rule includes `id`, `key`, `expected`, `severity`, `controls`, and `remediation`
3. Test the profile with the example data:

```bash
drift-detect drift compare \
  --baseline examples/baselines/bl-20240301-webserver-prod-01.json \
  --current examples/current_state.yaml \
  --rules examples/your-new-profile.yaml \
  --output /tmp/test-drift.json
```

4. Add the profile to `controls/control-mapping.md` if it maps to new controls

---

## Reporting Security Issues

**Do not open public GitHub issues for security vulnerabilities.**

Please report security issues to: **security@aerlixconsulting.com**

Include:
- Description of the vulnerability
- Steps to reproduce
- Potential impact assessment
- Suggested remediation (if known)

We target a 48-hour acknowledgement and 14-day remediation timeline for verified vulnerabilities.

---

## Licence

By contributing to this project, you agree that your contributions will be licensed under the [Apache License, Version 2.0](LICENSE).
