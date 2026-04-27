"""Audit log for envault vault operations."""

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional

AUDIT_FILENAME = ".envault_audit.json"


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _audit_path(vault_dir: Path) -> Path:
    return vault_dir / AUDIT_FILENAME


def record_event(
    vault_dir: Path,
    action: str,
    env_file: str,
    user: Optional[str] = None,
    extra: Optional[dict] = None,
) -> dict:
    """Append an audit event to the log for *vault_dir* and return the entry."""
    entry = {
        "timestamp": _now_iso(),
        "action": action,
        "env_file": env_file,
        "user": user or os.environ.get("USER", "unknown"),
    }
    if extra:
        entry.update(extra)

    path = _audit_path(vault_dir)
    events = _load_events(path)
    events.append(entry)
    path.write_text(json.dumps(events, indent=2), encoding="utf-8")
    return entry


def _load_events(path: Path) -> List[dict]:
    if path.exists():
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return []
    return []


def get_events(vault_dir: Path) -> List[dict]:
    """Return all audit events recorded for *vault_dir*."""
    return _load_events(_audit_path(vault_dir))


def clear_events(vault_dir: Path) -> None:
    """Remove the audit log for *vault_dir* (used in tests / admin tasks)."""
    path = _audit_path(vault_dir)
    if path.exists():
        path.unlink()
