"""Tests for envault.tags.TagManager."""

import pytest
from pathlib import Path

from envault.tags import TagManager


@pytest.fixture
def tm(tmp_path: Path) -> TagManager:
    return TagManager(tmp_path)


class TestTagManager:
    def test_initial_state_is_empty(self, tm: TagManager) -> None:
        assert tm.snapshot() == {}

    def test_add_tag_to_key(self, tm: TagManager) -> None:
        tm.add_tag("DB_PASSWORD", "secret")
        assert "secret" in tm.get_tags("DB_PASSWORD")

    def test_add_duplicate_tag_is_idempotent(self, tm: TagManager) -> None:
        tm.add_tag("API_KEY", "sensitive")
        tm.add_tag("API_KEY", "sensitive")
        assert tm.get_tags("API_KEY").count("sensitive") == 1

    def test_remove_tag(self, tm: TagManager) -> None:
        tm.add_tag("TOKEN", "sensitive")
        tm.remove_tag("TOKEN", "sensitive")
        assert tm.get_tags("TOKEN") == []

    def test_remove_nonexistent_tag_is_silent(self, tm: TagManager) -> None:
        tm.remove_tag("MISSING_KEY", "ghost")  # should not raise

    def test_keys_with_tag(self, tm: TagManager) -> None:
        tm.add_tag("DB_PASS", "secret")
        tm.add_tag("API_KEY", "secret")
        tm.add_tag("DEBUG", "config")
        result = tm.keys_with_tag("secret")
        assert set(result) == {"DB_PASS", "API_KEY"}

    def test_keys_with_unknown_tag_is_empty(self, tm: TagManager) -> None:
        assert tm.keys_with_tag("nonexistent") == []

    def test_all_tags_sorted_deduped(self, tm: TagManager) -> None:
        tm.add_tag("A", "z-tag")
        tm.add_tag("B", "a-tag")
        tm.add_tag("C", "a-tag")
        assert tm.all_tags() == ["a-tag", "z-tag"]

    def test_clear_key(self, tm: TagManager) -> None:
        tm.add_tag("SECRET", "sensitive")
        tm.clear_key("SECRET")
        assert tm.get_tags("SECRET") == []

    def test_persistence_across_instances(self, tmp_path: Path) -> None:
        tm1 = TagManager(tmp_path)
        tm1.add_tag("FOO", "bar")
        tm2 = TagManager(tmp_path)
        assert "bar" in tm2.get_tags("FOO")

    def test_snapshot_is_copy(self, tm: TagManager) -> None:
        tm.add_tag("X", "y")
        snap = tm.snapshot()
        snap["X"].append("mutated")
        assert "mutated" not in tm.get_tags("X")

    def test_remove_last_tag_removes_key_entry(self, tm: TagManager) -> None:
        tm.add_tag("ONLY", "lone")
        tm.remove_tag("ONLY", "lone")
        assert "ONLY" not in tm.snapshot()
