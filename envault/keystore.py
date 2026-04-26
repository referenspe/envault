"""Local key store for managing per-project vault passwords."""

import json
import os
from pathlib import Path

DEFAULT_KEYSTORE_PATH = Path.home() / ".envault" / "keystore.json"


class KeyStore:
    """Persists and retrieves vault passwords keyed by project name."""

    def __init__(self, path: Path = DEFAULT_KEYSTORE_PATH) -> None:
        self.path = path
        self._data: dict[str, str] = {}
        self._load()

    def _load(self) -> None:
        if self.path.exists():
            with self.path.open("r") as fh:
                self._data = json.load(fh)

    def _save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        # Restrict file permissions to owner only
        flags = os.O_WRONLY | os.O_CREAT | os.O_TRUNC
        fd = os.open(self.path, flags, 0o600)
        with os.fdopen(fd, "w") as fh:
            json.dump(self._data, fh, indent=2)

    def set(self, project: str, password: str) -> None:
        """Store a password for a project."""
        self._data[project] = password
        self._save()

    def get(self, project: str) -> str | None:
        """Retrieve the password for a project, or None if not found."""
        return self._data.get(project)

    def delete(self, project: str) -> bool:
        """Remove a project entry. Returns True if it existed."""
        if project in self._data:
            del self._data[project]
            self._save()
            return True
        return False

    def list_projects(self) -> list[str]:
        """Return all project names stored in the key store."""
        return list(self._data.keys())
