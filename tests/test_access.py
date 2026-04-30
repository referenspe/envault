"""Tests for envault.access and envault.cli_access."""
from __future__ import annotations

import pytest
from click.testing import CliRunner
from pathlib import Path

from envault.access import AccessManager, AccessError, READ, WRITE, DENY
from envault.cli_access import access_cmd


@pytest.fixture()
def vault_dir(tmp_path: Path) -> Path:
    return tmp_path


@pytest.fixture()
def am(vault_dir: Path) -> AccessManager:
    return AccessManager(vault_dir)


class TestAccessManager:
    def test_default_permission_is_write(self, am: AccessManager) -> None:
        assert am.get_permission("dev", "SECRET_KEY") == WRITE

    def test_set_and_get_permission(self, am: AccessManager) -> None:
        am.set_permission("dev", "DB_PASS", READ)
        assert am.get_permission("dev", "DB_PASS") == READ

    def test_set_deny(self, am: AccessManager) -> None:
        am.set_permission("ci", "ADMIN_TOKEN", DENY)
        assert am.get_permission("ci", "ADMIN_TOKEN") == DENY

    def test_invalid_permission_raises(self, am: AccessManager) -> None:
        with pytest.raises(ValueError, match="Invalid permission"):
            am.set_permission("dev", "KEY", "superuser")

    def test_persists_to_disk(self, vault_dir: Path) -> None:
        am1 = AccessManager(vault_dir)
        am1.set_permission("prod", "API_KEY", READ)
        am2 = AccessManager(vault_dir)
        assert am2.get_permission("prod", "API_KEY") == READ

    def test_remove_permission_reverts_to_default(self, am: AccessManager) -> None:
        am.set_permission("dev", "X", READ)
        am.remove_permission("dev", "X")
        assert am.get_permission("dev", "X") == WRITE

    def test_remove_nonexistent_is_safe(self, am: AccessManager) -> None:
        am.remove_permission("ghost", "MISSING")  # should not raise

    def test_check_passes_for_write_permission(self, am: AccessManager) -> None:
        am.set_permission("dev", "K", WRITE)
        am.check("dev", "K", WRITE)  # no exception

    def test_check_read_on_read_key_passes(self, am: AccessManager) -> None:
        am.set_permission("dev", "K", READ)
        am.check("dev", "K", READ)  # no exception

    def test_check_write_on_read_key_raises(self, am: AccessManager) -> None:
        am.set_permission("dev", "K", READ)
        with pytest.raises(AccessError, match="read-only"):
            am.check("dev", "K", WRITE)

    def test_check_deny_raises(self, am: AccessManager) -> None:
        am.set_permission("ci", "SECRET", DENY)
        with pytest.raises(AccessError, match="denied"):
            am.check("ci", "SECRET", READ)

    def test_list_rules(self, am: AccessManager) -> None:
        am.set_permission("dev", "A", READ)
        am.set_permission("dev", "B", DENY)
        rules = am.list_rules("dev")
        assert rules == {"A": READ, "B": DENY}

    def test_all_profiles(self, am: AccessManager) -> None:
        am.set_permission("dev", "X", READ)
        am.set_permission("prod", "Y", DENY)
        assert set(am.all_profiles()) == {"dev", "prod"}


class TestAccessCLI:
    @pytest.fixture()
    def runner(self) -> CliRunner:
        return CliRunner()

    def test_set_and_list(self, runner: CliRunner, vault_dir: Path) -> None:
        result = runner.invoke(access_cmd, ["set", "dev", "DB_PASS", "read", "--vault-dir", str(vault_dir)])
        assert result.exit_code == 0
        assert "read" in result.output

        result = runner.invoke(access_cmd, ["list", "dev", "--vault-dir", str(vault_dir)])
        assert result.exit_code == 0
        assert "DB_PASS" in result.output
        assert "read" in result.output

    def test_check_denied_exits_nonzero(self, runner: CliRunner, vault_dir: Path) -> None:
        runner.invoke(access_cmd, ["set", "ci", "TOKEN", "deny", "--vault-dir", str(vault_dir)])
        result = runner.invoke(access_cmd, ["check", "ci", "TOKEN", "read", "--vault-dir", str(vault_dir)])
        assert result.exit_code != 0

    def test_list_empty_profile(self, runner: CliRunner, vault_dir: Path) -> None:
        result = runner.invoke(access_cmd, ["list", "nobody", "--vault-dir", str(vault_dir)])
        assert result.exit_code == 0
        assert "default" in result.output
