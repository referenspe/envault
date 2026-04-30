"""Tag management for .env secrets — attach labels to keys for grouping/filtering."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List, Optional

_TAGS_FILENAME = ".envault_tags.json"


class TagManager:
    """Persist and query per-key tags within a vault directory."""

    def __init__(self, vault_dir: str | Path) -> None:
        self._path = Path(vault_dir) / _TAGS_FILENAME
        self._data: Dict[str, List[str]] = self._load()

    # ------------------------------------------------------------------
    # Persistence
    # ------------------------------------------------------------------

    def _load(self) -> Dict[str, List[str]]:
        if self._path.exists():
            with self._path.open() as fh:
                return json.load(fh)
        return {}

    def _save(self) -> None:
        with self._path.open("w") as fh:
            json.dump(self._data, fh, indent=2)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def add_tag(self, key: str, tag: str) -> None:
        """Add *tag* to *key*, ignoring duplicates."""
        tags = self._data.setdefault(key, [])
        if tag not in tags:
            tags.append(tag)
        self._save()

    def remove_tag(self, key: str, tag: str) -> None:
        """Remove *tag* from *key*.  Silently ignores missing tag/key."""
        if key in self._data and tag in self._data[key]:
            self._data[key].remove(tag)
            if not self._data[key]:
                del self._data[key]
            self._save()

    def get_tags(self, key: str) -> List[str]:
        """Return list of tags for *key* (empty list if none)."""
        return list(self._data.get(key, []))

    def keys_with_tag(self, tag: str) -> List[str]:
        """Return all keys that carry *tag*."""
        return [k for k, tags in self._data.items() if tag in tags]

    def all_tags(self) -> List[str]:
        """Return sorted deduplicated list of every tag in use."""
        seen: set[str] = set()
        for tags in self._data.values():
            seen.update(tags)
        return sorted(seen)

    def clear_key(self, key: str) -> None:
        """Remove all tags for *key*."""
        if key in self._data:
            del self._data[key]
            self._save()

    def snapshot(self) -> Dict[str, List[str]]:
        """Return a copy of the full tag mapping."""
        return {k: list(v) for k, v in self._data.items()}
