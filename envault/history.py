"""Vault operation history: track lock/unlock/rotate events per env file."""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Dict, Any, Optional

_HISTORY_FILENAME = ".envault_history.json"


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _history_path(vault_dir: str) -> Path:
    return Path(vault_dir) / _HISTORY_FILENAME


def record_operation(
    vault_dir: str,
    operation: str,
    env_file: str,
    profile: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Append an operation record to the history log and return the entry."""
    entry: Dict[str, Any] = {
        "timestamp": _now_iso(),
        "operation": operation,
        "env_file": env_file,
    }
    if profile is not None:
        entry["profile"] = profile
    if metadata:
        entry["metadata"] = metadata

    history = _load_history(vault_dir)
    history.append(entry)

    path = _history_path(vault_dir)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(history, fh, indent=2)

    return entry


def _load_history(vault_dir: str) -> List[Dict[str, Any]]:
    path = _history_path(vault_dir)
    if not path.exists():
        return []
    with open(path, "r", encoding="utf-8") as fh:
        return json.load(fh)


def get_history(
    vault_dir: str,
    operation: Optional[str] = None,
    env_file: Optional[str] = None,
    limit: Optional[int] = None,
) -> List[Dict[str, Any]]:
    """Return history entries, optionally filtered by operation or env_file."""
    entries = _load_history(vault_dir)

    if operation:
        entries = [e for e in entries if e.get("operation") == operation]
    if env_file:
        entries = [e for e in entries if e.get("env_file") == env_file]

    if limit is not None:
        entries = entries[-limit:]

    return entries


def clear_history(vault_dir: str) -> None:
    """Remove the history file entirely."""
    path = _history_path(vault_dir)
    if path.exists():
        os.remove(path)
