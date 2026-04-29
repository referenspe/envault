"""Diff utilities for comparing .env files and vault snapshots."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple


@dataclass
class EnvDiff:
    """Represents the diff between two env variable sets."""

    added: Dict[str, str]
    removed: Dict[str, str]
    changed: Dict[str, Tuple[str, str]]  # key -> (old_value, new_value)
    unchanged: Dict[str, str]

    @property
    def has_changes(self) -> bool:
        return bool(self.added or self.removed or self.changed)

    def summary(self) -> str:
        lines: List[str] = []
        for key, value in sorted(self.added.items()):
            lines.append(f"+ {key}={value}")
        for key in sorted(self.removed.keys()):
            lines.append(f"- {key}")
        for key, (old, new) in sorted(self.changed.items()):
            lines.append(f"~ {key}: {old!r} -> {new!r}")
        return "\n".join(lines) if lines else "(no changes)"


def diff_envs(
    old: Dict[str, str],
    new: Dict[str, str],
    mask_values: bool = False,
) -> EnvDiff:
    """Compute the diff between two env dicts.

    Args:
        old: The previous set of env variables.
        new: The current set of env variables.
        mask_values: If True, replace values with '***' in the result.

    Returns:
        An EnvDiff describing additions, removals, and changes.
    """

    def _mask(v: str) -> str:
        return "***" if mask_values else v

    old_keys = set(old)
    new_keys = set(new)

    added = {k: _mask(new[k]) for k in new_keys - old_keys}
    removed = {k: _mask(old[k]) for k in old_keys - new_keys}
    changed = {
        k: (_mask(old[k]), _mask(new[k]))
        for k in old_keys & new_keys
        if old[k] != new[k]
    }
    unchanged = {k: _mask(new[k]) for k in old_keys & new_keys if old[k] == new[k]}

    return EnvDiff(
        added=added,
        removed=removed,
        changed=changed,
        unchanged=unchanged,
    )
