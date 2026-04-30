"""Tests for envault.history module."""

from __future__ import annotations

import json
import pytest
from pathlib import Path

from envault.history import (
    record_operation,
    get_history,
    clear_history,
    _history_path,
)


@pytest.fixture
def vault_dir(tmp_path: Path) -> str:
    return str(tmp_path)


class TestRecordOperation:
    def test_creates_history_file(self, vault_dir: str) -> None:
        record_operation(vault_dir, "lock", ".env")
        assert _history_path(vault_dir).exists()

    def test_entry_has_required_fields(self, vault_dir: str) -> None:
        entry = record_operation(vault_dir, "lock", ".env")
        assert entry["operation"] == "lock"
        assert entry["env_file"] == ".env"
        assert "timestamp" in entry

    def test_entry_includes_profile_when_given(self, vault_dir: str) -> None:
        entry = record_operation(vault_dir, "unlock", ".env", profile="staging")
        assert entry["profile"] == "staging"

    def test_entry_includes_metadata_when_given(self, vault_dir: str) -> None:
        meta = {"keys_rotated": 3}
        entry = record_operation(vault_dir, "rotate", ".env", metadata=meta)
        assert entry["metadata"] == meta

    def test_multiple_entries_appended(self, vault_dir: str) -> None:
        record_operation(vault_dir, "lock", ".env")
        record_operation(vault_dir, "unlock", ".env")
        history = get_history(vault_dir)
        assert len(history) == 2

    def test_history_file_is_valid_json(self, vault_dir: str) -> None:
        record_operation(vault_dir, "lock", ".env")
        raw = _history_path(vault_dir).read_text(encoding="utf-8")
        parsed = json.loads(raw)
        assert isinstance(parsed, list)


class TestGetHistory:
    def test_returns_empty_list_when_no_history(self, vault_dir: str) -> None:
        assert get_history(vault_dir) == []

    def test_filter_by_operation(self, vault_dir: str) -> None:
        record_operation(vault_dir, "lock", ".env")
        record_operation(vault_dir, "unlock", ".env")
        results = get_history(vault_dir, operation="lock")
        assert all(e["operation"] == "lock" for e in results)
        assert len(results) == 1

    def test_filter_by_env_file(self, vault_dir: str) -> None:
        record_operation(vault_dir, "lock", ".env")
        record_operation(vault_dir, "lock", ".env.staging")
        results = get_history(vault_dir, env_file=".env")
        assert len(results) == 1
        assert results[0]["env_file"] == ".env"

    def test_limit_returns_last_n_entries(self, vault_dir: str) -> None:
        for i in range(5):
            record_operation(vault_dir, "lock", f"file{i}.env")
        results = get_history(vault_dir, limit=2)
        assert len(results) == 2
        assert results[-1]["env_file"] == "file4.env"


class TestClearHistory:
    def test_removes_history_file(self, vault_dir: str) -> None:
        record_operation(vault_dir, "lock", ".env")
        clear_history(vault_dir)
        assert not _history_path(vault_dir).exists()

    def test_clear_on_empty_vault_does_not_raise(self, vault_dir: str) -> None:
        clear_history(vault_dir)  # should not raise
