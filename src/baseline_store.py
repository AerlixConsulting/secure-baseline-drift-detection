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

"""baseline_store — persist and retrieve configuration baseline snapshots.

A baseline is a point-in-time snapshot of a system's configuration,
annotated with:

* ``baseline_id``  — unique identifier (``bl-<date>-<system_id>``)
* ``system_id``    — logical identifier for the target system
* ``profile``      — compliance profile name (e.g. ``cis-level2``)
* ``captured_at``  — ISO-8601 UTC timestamp
* ``schema_version`` — document schema version for forward-compatibility
* ``config``       — flat configuration map (see :mod:`config_parser`)

Baselines are persisted as JSON files.  The store provides simple
``save`` / ``load`` / ``list_baselines`` operations.
"""

from __future__ import annotations

import json
import re
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

SCHEMA_VERSION = "1.0"
_BASELINE_ID_RE = re.compile(r"^bl-\d{8}-[\w\-]+$")


# ---------------------------------------------------------------------------
# Data model
# ---------------------------------------------------------------------------


class Baseline:
    """Represents a stored configuration baseline snapshot."""

    def __init__(
        self,
        system_id: str,
        profile: str,
        config: dict[str, Any],
        *,
        baseline_id: str | None = None,
        captured_at: str | None = None,
        schema_version: str = SCHEMA_VERSION,
        description: str = "",
    ) -> None:
        now = datetime.now(UTC)
        date_str = now.strftime("%Y%m%d")
        self.baseline_id: str = baseline_id or f"bl-{date_str}-{_slugify(system_id)}"
        self.system_id: str = system_id
        self.profile: str = profile
        self.config: dict[str, Any] = config
        self.captured_at: str = captured_at or now.isoformat()
        self.schema_version: str = schema_version
        self.description: str = description

    # ------------------------------------------------------------------
    # Serialisation
    # ------------------------------------------------------------------

    def to_dict(self) -> dict[str, Any]:
        """Serialise the baseline to a plain dictionary."""
        return {
            "schema_version": self.schema_version,
            "baseline_id": self.baseline_id,
            "system_id": self.system_id,
            "profile": self.profile,
            "captured_at": self.captured_at,
            "description": self.description,
            "config": self.config,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Baseline:
        """Deserialise a baseline from a plain dictionary."""
        _require_keys(data, ["baseline_id", "system_id", "profile", "config", "captured_at"])
        return cls(
            system_id=data["system_id"],
            profile=data["profile"],
            config=data["config"],
            baseline_id=data["baseline_id"],
            captured_at=data["captured_at"],
            schema_version=data.get("schema_version", SCHEMA_VERSION),
            description=data.get("description", ""),
        )

    def __repr__(self) -> str:
        return (
            f"Baseline(id={self.baseline_id!r}, system={self.system_id!r}, "
            f"profile={self.profile!r}, keys={len(self.config)})"
        )


# ---------------------------------------------------------------------------
# Store operations
# ---------------------------------------------------------------------------


class BaselineStore:
    """File-system-backed store for baseline snapshots.

    Args:
        store_dir: Directory where baseline JSON files are persisted.
                   Created automatically if it does not exist.
    """

    def __init__(self, store_dir: str | Path = "baselines") -> None:
        self.store_dir = Path(store_dir)
        self.store_dir.mkdir(parents=True, exist_ok=True)

    # ------------------------------------------------------------------
    # Write
    # ------------------------------------------------------------------

    def save(self, baseline: Baseline) -> Path:
        """Persist a :class:`Baseline` to disk.

        Args:
            baseline: The baseline snapshot to save.

        Returns:
            The path to the written JSON file.
        """
        out_path = self.store_dir / f"{baseline.baseline_id}.json"
        out_path.write_text(json.dumps(baseline.to_dict(), indent=2) + "\n", encoding="utf-8")
        return out_path

    # ------------------------------------------------------------------
    # Read
    # ------------------------------------------------------------------

    def load(self, baseline_id: str) -> Baseline:
        """Load a baseline by its ID.

        Args:
            baseline_id: The ``baseline_id`` string.

        Returns:
            A :class:`Baseline` instance.

        Raises:
            FileNotFoundError: If no matching baseline file exists.
        """
        path = self.store_dir / f"{baseline_id}.json"
        if not path.exists():
            raise FileNotFoundError(f"Baseline not found: {baseline_id} (looked in {self.store_dir})")
        return Baseline.from_dict(json.loads(path.read_text(encoding="utf-8")))

    def load_file(self, path: str | Path) -> Baseline:
        """Load a baseline directly from a file path.

        Args:
            path: Path to the baseline JSON file.

        Returns:
            A :class:`Baseline` instance.
        """
        path = Path(path)
        if not path.exists():
            raise FileNotFoundError(f"Baseline file not found: {path}")
        return Baseline.from_dict(json.loads(path.read_text(encoding="utf-8")))

    # ------------------------------------------------------------------
    # List / query
    # ------------------------------------------------------------------

    def list_baselines(self) -> list[dict[str, str]]:
        """Return summary metadata for all baselines in the store.

        Returns:
            List of ``{baseline_id, system_id, profile, captured_at}`` dicts,
            sorted by ``captured_at`` descending (most recent first).
        """
        summaries = []
        for json_file in sorted(self.store_dir.glob("*.json")):
            try:
                data = json.loads(json_file.read_text(encoding="utf-8"))
                summaries.append(
                    {
                        "baseline_id": data.get("baseline_id", json_file.stem),
                        "system_id": data.get("system_id", ""),
                        "profile": data.get("profile", ""),
                        "captured_at": data.get("captured_at", ""),
                    }
                )
            except (json.JSONDecodeError, KeyError):
                continue  # skip malformed files

        return sorted(summaries, key=lambda s: s["captured_at"], reverse=True)

    def latest_for_system(self, system_id: str) -> Baseline | None:
        """Return the most-recently-captured baseline for *system_id*, or None."""
        candidates = [s for s in self.list_baselines() if s["system_id"] == system_id]
        if not candidates:
            return None
        return self.load(candidates[0]["baseline_id"])


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _slugify(value: str) -> str:
    """Convert *value* to a filesystem-safe slug."""
    return re.sub(r"[^\w\-]", "-", value.lower()).strip("-")


def _require_keys(data: dict[str, Any], keys: list[str]) -> None:
    missing = [k for k in keys if k not in data]
    if missing:
        raise ValueError(f"Baseline document is missing required keys: {missing}")
