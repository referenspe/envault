"""Tests for envault.profiles module."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from envault.profiles import ProfileManager, ProfileNotFoundError, PROFILES_FILENAME


@pytest.fixture()
def pm(tmp_path: Path) -> ProfileManager:
    return ProfileManager(tmp_path)


class TestProfileManager:
    def test_initial_list_is_empty(self, pm: ProfileManager) -> None:
        assert pm.list_profiles() == []

    def test_set_and_get_profile(self, pm: ProfileManager) -> None:
        pm.set_profile("dev", {"DEBUG": "true", "DB_URL": "sqlite://"})
        result = pm.get_profile("dev")
        assert result == {"DEBUG": "true", "DB_URL": "sqlite://"}

    def test_set_profile_persists_to_disk(self, pm: ProfileManager, tmp_path: Path) -> None:
        pm.set_profile("prod", {"APP_ENV": "production"})
        raw = json.loads((tmp_path / PROFILES_FILENAME).read_text())
        assert raw["prod"] == {"APP_ENV": "production"}

    def test_list_profiles_sorted(self, pm: ProfileManager) -> None:
        pm.set_profile("staging", {})
        pm.set_profile("dev", {})
        pm.set_profile("prod", {})
        assert pm.list_profiles() == ["dev", "prod", "staging"]

    def test_get_missing_profile_raises(self, pm: ProfileManager) -> None:
        with pytest.raises(ProfileNotFoundError):
            pm.get_profile("nonexistent")

    def test_delete_profile(self, pm: ProfileManager) -> None:
        pm.set_profile("dev", {"X": "1"})
        pm.delete_profile("dev")
        assert "dev" not in pm.list_profiles()

    def test_delete_missing_profile_raises(self, pm: ProfileManager) -> None:
        with pytest.raises(ProfileNotFoundError):
            pm.delete_profile("ghost")

    def test_profile_exists(self, pm: ProfileManager) -> None:
        pm.set_profile("dev", {})
        assert pm.profile_exists("dev") is True
        assert pm.profile_exists("prod") is False

    def test_overwrite_profile(self, pm: ProfileManager) -> None:
        pm.set_profile("dev", {"A": "1"})
        pm.set_profile("dev", {"B": "2"})
        assert pm.get_profile("dev") == {"B": "2"}

    def test_merge_into_profile_overwrite_true(self, pm: ProfileManager) -> None:
        pm.set_profile("dev", {"A": "old", "B": "keep"})
        result = pm.merge_into_profile("dev", {"A": "new", "C": "added"}, overwrite=True)
        assert result == {"A": "new", "B": "keep", "C": "added"}

    def test_merge_into_profile_overwrite_false(self, pm: ProfileManager) -> None:
        pm.set_profile("dev", {"A": "original"})
        result = pm.merge_into_profile("dev", {"A": "ignored", "B": "new"}, overwrite=False)
        assert result["A"] == "original"
        assert result["B"] == "new"

    def test_merge_creates_profile_if_missing(self, pm: ProfileManager) -> None:
        result = pm.merge_into_profile("fresh", {"KEY": "val"})
        assert result == {"KEY": "val"}
        assert pm.profile_exists("fresh")

    def test_profiles_reload_from_disk(self, tmp_path: Path) -> None:
        pm1 = ProfileManager(tmp_path)
        pm1.set_profile("dev", {"RELOAD": "yes"})
        pm2 = ProfileManager(tmp_path)
        assert pm2.get_profile("dev") == {"RELOAD": "yes"}
