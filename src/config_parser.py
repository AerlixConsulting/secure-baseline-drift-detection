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

"""config_parser — ingest and normalise system configuration from YAML or JSON.

Supports arbitrarily nested documents and flattens them into a canonical
``dict[str, str | int | float | bool | None]`` mapping that the rest of the
pipeline operates on.  Nested keys are joined with ``'.'`` separators:

    os:
      ssh:
        permit_root_login: "no"

becomes ``{"os.ssh.permit_root_login": "no"}``.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

try:
    import yaml
except ModuleNotFoundError as exc:  # pragma: no cover
    raise ImportError("PyYAML is required: pip install pyyaml") from exc


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

ConfigMap = dict[str, Any]


def load_config(path: str | Path) -> ConfigMap:
    """Load a YAML or JSON configuration file and return a flat key-value map.

    Args:
        path: Filesystem path to the configuration file.  The file extension
              determines the parser (``*.json`` → JSON; everything else → YAML).

    Returns:
        A flat dictionary with dotted-path keys and scalar values.

    Raises:
        FileNotFoundError: If *path* does not exist.
        ValueError: If the file cannot be parsed.
    """
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"Configuration file not found: {path}")

    raw = path.read_text(encoding="utf-8")
    try:
        data: Any = _parse(path, raw)
    except Exception as exc:
        raise ValueError(f"Failed to parse {path}: {exc}") from exc

    if not isinstance(data, dict):
        raise ValueError(f"Top-level structure in {path} must be a mapping (got {type(data).__name__})")

    return flatten(data)


def load_config_string(text: str, *, fmt: str = "yaml") -> ConfigMap:
    """Parse a configuration string directly (useful for testing).

    Args:
        text: Raw YAML or JSON text.
        fmt:  ``'yaml'`` (default) or ``'json'``.

    Returns:
        Flat key-value mapping.
    """
    if fmt == "json":
        data = json.loads(text)
    else:
        data = yaml.safe_load(text)

    if not isinstance(data, dict):
        raise ValueError(f"Top-level structure must be a mapping (got {type(data).__name__})")

    return flatten(data)


def flatten(data: dict[str, Any], *, prefix: str = "", sep: str = ".") -> ConfigMap:
    """Recursively flatten a nested dictionary into dotted-path keys.

    Args:
        data:   The dictionary to flatten.
        prefix: Key prefix accumulated during recursion (leave empty for top-level calls).
        sep:    Separator between key segments (default ``'.'``).

    Returns:
        Flat ``{key: value}`` dictionary.
    """
    result: ConfigMap = {}
    for key, value in data.items():
        full_key = f"{prefix}{sep}{key}" if prefix else str(key)
        if isinstance(value, dict):
            result.update(flatten(value, prefix=full_key, sep=sep))
        elif isinstance(value, list):
            # Represent lists as comma-separated sorted strings for diffing
            result[full_key] = _normalise_list(value)
        else:
            result[full_key] = value
    return result


def validate_schema(config: ConfigMap, required_keys: list[str]) -> list[str]:
    """Return a list of required keys that are absent from *config*.

    Args:
        config:        Flat configuration map.
        required_keys: Keys that must be present.

    Returns:
        Missing key names (empty list if all present).
    """
    return [k for k in required_keys if k not in config]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _parse(path: Path, raw: str) -> Any:
    if path.suffix.lower() == ".json":
        return json.loads(raw)
    return yaml.safe_load(raw)


def _normalise_list(items: list[Any]) -> str:
    """Convert a list to a stable comma-separated string for comparison."""
    normalised = []
    for item in items:
        if isinstance(item, dict):
            normalised.append(json.dumps(item, sort_keys=True))
        else:
            normalised.append(str(item))
    return ",".join(sorted(normalised))


def sanitise_key(key: str) -> str:
    """Return a sanitised dotted-path key (strips non-printable characters)."""
    return re.sub(r"[^\w.\-]", "_", key)
