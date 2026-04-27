"""Tests for envault.audit module."""

import json
import pytest
from pathlib import Path

from envault.audit import record_event, get_events, clear_events, AUDIT_FILENAME


@pytest.fixture()
def vault_dir(tmp_path):
    return tmp_path


class TestRecordEvent:
    def test_creates_audit_file(self, vault_dir):
        record_event(vault_dir, "lock", ".env")
        assert (vault_dir / AUDIT_FILENAME).exists()

    def test_entry_fields_present(self, vault_dir):
        entry = record_event(vault_dir, "lock", ".env", user="alice")
        assert entry["action"] == "lock"
        assert entry["env_file"] == ".env"
        assert entry["user"] == "alice"
        assert "timestamp" in entry

    def test_multiple_events_appended(self, vault_dir):
        record_event(vault_dir, "lock", ".env", user="alice")
        record_event(vault_dir, "unlock", ".env", user="bob")
        events = get_events(vault_dir)
        assert len(events) == 2
        assert events[0]["action"] == "lock"
        assert events[1]["action"] == "unlock"

    def test_extra_fields_stored(self, vault_dir):
        record_event(vault_dir, "sync", ".env", extra={"dest": "/tmp/other"})
        events = get_events(vault_dir)
        assert events[0]["dest"] == "/tmp/other"

    def test_audit_file_is_valid_json(self, vault_dir):
        record_event(vault_dir, "lock", ".env")
        raw = (vault_dir / AUDIT_FILENAME).read_text(encoding="utf-8")
        parsed = json.loads(raw)
        assert isinstance(parsed, list)


class TestGetEvents:
    def test_returns_empty_list_when_no_file(self, vault_dir):
        assert get_events(vault_dir) == []

    def test_returns_empty_list_on_corrupt_file(self, vault_dir):
        (vault_dir / AUDIT_FILENAME).write_text("not json", encoding="utf-8")
        assert get_events(vault_dir) == []


class TestClearEvents:
    def test_removes_audit_file(self, vault_dir):
        record_event(vault_dir, "lock", ".env")
        clear_events(vault_dir)
        assert not (vault_dir / AUDIT_FILENAME).exists()

    def test_clear_when_no_file_is_noop(self, vault_dir):
        clear_events(vault_dir)  # should not raise
