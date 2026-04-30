"""Profile management for envault — allows named sets of env vars per environment."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List, Optional

PROFILES_FILENAME = ".envault_profiles.json"


class ProfileNotFoundError(KeyError):
    """Raised when a requested profile does not exist."""


class ProfileManager:
    """Manages named profiles (e.g. 'dev', 'staging', 'prod') for a vault directory."""

    def __init__(self, vault_dir: str | Path) -> None:
        self._path = Path(vault_dir) / PROFILES_FILENAME
        self._profiles: Dict[str, Dict[str, str]] = self._load()

    # ------------------------------------------------------------------
    # Persistence
    # ------------------------------------------------------------------

    def _load(self) -> Dict[str, Dict[str, str]]:
        if self._path.exists():
            with self._path.open("r", encoding="utf-8") as fh:
                return json.load(fh)
        return {}

    def _save(self) -> None:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        with self._path.open("w", encoding="utf-8") as fh:
            json.dump(self._profiles, fh, indent=2)
            fh.write("\n")

    # ------------------------------------------------------------------
    # CRUD
    # ------------------------------------------------------------------

    def list_profiles(self) -> List[str]:
        """Return sorted list of profile names."""
        return sorted(self._profiles.keys())

    def set_profile(self, name: str, env_vars: Dict[str, str]) -> None:
        """Create or overwrite a profile with the given env vars."""
        self._profiles[name] = dict(env_vars)
        self._save()

    def get_profile(self, name: str) -> Dict[str, str]:
        """Return env vars for *name*; raises ProfileNotFoundError if missing."""
        if name not in self._profiles:
            raise ProfileNotFoundError(f"Profile '{name}' not found.")
        return dict(self._profiles[name])

    def delete_profile(self, name: str) -> None:
        """Delete a profile; raises ProfileNotFoundError if missing."""
        if name not in self._profiles:
            raise ProfileNotFoundError(f"Profile '{name}' not found.")
        del self._profiles[name]
        self._save()

    def merge_into_profile(
        self, name: str, env_vars: Dict[str, str], overwrite: bool = True
    ) -> Dict[str, str]:
        """Merge *env_vars* into an existing (or new) profile.

        When *overwrite* is False, existing keys are preserved.
        Returns the resulting env vars.
        """
        existing = self._profiles.get(name, {})
        if overwrite:
            merged = {**existing, **env_vars}
        else:
            merged = {**env_vars, **existing}
        self._profiles[name] = merged
        self._save()
        return dict(merged)

    def profile_exists(self, name: str) -> bool:
        return name in self._profiles
