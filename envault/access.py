"""Access control: manage read/write permissions per key per profile."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List, Set

ACCESS_FILENAME = ".envault_access.json"

# Permission levels
READ = "read"
WRITE = "write"
DENY = "deny"

VALID_PERMISSIONS = {READ, WRITE, DENY}


class AccessError(Exception):
    """Raised when an access control violation occurs."""


class AccessManager:
    """Manages per-key, per-profile access permissions.

    Storage format::

        {
          "<profile>": {
            "<key>": "read" | "write" | "deny"
          }
        }
    """

    def __init__(self, vault_dir: str | Path) -> None:
        self._path = Path(vault_dir) / ACCESS_FILENAME
        self._rules: Dict[str, Dict[str, str]] = self._load()

    def _load(self) -> Dict[str, Dict[str, str]]:
        if self._path.exists():
            return json.loads(self._path.read_text())
        return {}

    def _save(self) -> None:
        self._path.write_text(json.dumps(self._rules, indent=2))

    def set_permission(self, profile: str, key: str, permission: str) -> None:
        """Set a permission for *key* under *profile*."""
        if permission not in VALID_PERMISSIONS:
            raise ValueError(f"Invalid permission '{permission}'. Choose from {VALID_PERMISSIONS}.")
        self._rules.setdefault(profile, {})[key] = permission
        self._save()

    def get_permission(self, profile: str, key: str) -> str:
        """Return the permission for *key* under *profile* (defaults to 'write')."""
        return self._rules.get(profile, {}).get(key, WRITE)

    def remove_permission(self, profile: str, key: str) -> None:
        """Remove an explicit permission rule (falls back to default 'write')."""
        if profile in self._rules and key in self._rules[profile]:
            del self._rules[profile][key]
            if not self._rules[profile]:
                del self._rules[profile]
            self._save()

    def check(self, profile: str, key: str, required: str) -> None:
        """Raise *AccessError* if *profile* does not have *required* permission for *key*."""
        perm = self.get_permission(profile, key)
        if perm == DENY:
            raise AccessError(f"Profile '{profile}' is denied access to key '{key}'.")
        if required == WRITE and perm == READ:
            raise AccessError(f"Profile '{profile}' has read-only access to key '{key}'.")

    def list_rules(self, profile: str) -> Dict[str, str]:
        """Return all explicit rules for *profile*."""
        return dict(self._rules.get(profile, {}))

    def all_profiles(self) -> List[str]:
        """Return every profile that has at least one explicit rule."""
        return list(self._rules.keys())
