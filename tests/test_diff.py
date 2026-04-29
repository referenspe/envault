"""Tests for envault.diff module."""

import pytest

from envault.diff import EnvDiff, diff_envs


OLD = {"DB_HOST": "localhost", "DB_PORT": "5432", "SECRET": "old_secret"}
NEW = {
    "DB_HOST": "prod.db.example.com",
    "DB_PORT": "5432",
    "API_KEY": "abc123",
}


class TestDiffEnvs:
    def test_detects_added_keys(self):
        result = diff_envs(OLD, NEW)
        assert "API_KEY" in result.added
        assert result.added["API_KEY"] == "abc123"

    def test_detects_removed_keys(self):
        result = diff_envs(OLD, NEW)
        assert "SECRET" in result.removed

    def test_detects_changed_keys(self):
        result = diff_envs(OLD, NEW)
        assert "DB_HOST" in result.changed
        old_val, new_val = result.changed["DB_HOST"]
        assert old_val == "localhost"
        assert new_val == "prod.db.example.com"

    def test_detects_unchanged_keys(self):
        result = diff_envs(OLD, NEW)
        assert "DB_PORT" in result.unchanged

    def test_has_changes_true(self):
        result = diff_envs(OLD, NEW)
        assert result.has_changes is True

    def test_has_changes_false_when_identical(self):
        result = diff_envs(OLD, OLD)
        assert result.has_changes is False

    def test_empty_dicts(self):
        result = diff_envs({}, {})
        assert not result.has_changes

    def test_mask_values_hides_added(self):
        result = diff_envs(OLD, NEW, mask_values=True)
        assert result.added["API_KEY"] == "***"

    def test_mask_values_hides_changed(self):
        result = diff_envs(OLD, NEW, mask_values=True)
        old_val, new_val = result.changed["DB_HOST"]
        assert old_val == "***"
        assert new_val == "***"

    def test_mask_values_hides_removed(self):
        result = diff_envs(OLD, NEW, mask_values=True)
        assert result.removed["SECRET"] == "***"


class TestEnvDiffSummary:
    def test_summary_no_changes(self):
        result = diff_envs({"A": "1"}, {"A": "1"})
        assert result.summary() == "(no changes)"

    def test_summary_contains_added_prefix(self):
        result = diff_envs({}, {"NEW_KEY": "val"})
        assert result.summary().startswith("+")

    def test_summary_contains_removed_prefix(self):
        result = diff_envs({"OLD_KEY": "val"}, {})
        assert result.summary().startswith("-")

    def test_summary_contains_changed_prefix(self):
        result = diff_envs({"K": "old"}, {"K": "new"})
        assert result.summary().startswith("~")

    def test_summary_all_change_types(self):
        result = diff_envs(
            {"A": "1", "B": "old"},
            {"B": "new", "C": "3"},
        )
        summary = result.summary()
        assert "- A" in summary
        assert "~ B" in summary
        assert "+ C" in summary
