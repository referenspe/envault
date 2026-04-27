"""Tests for the envault CLI commands."""

from pathlib import Path

import pytest
from click.testing import CliRunner

from envault.cli import cli
from envault.keystore import KeyStore


PASSWORD = "test-secret-pass"


@pytest.fixture()
def runner():
    return CliRunner()


@pytest.fixture()
def env_dir(tmp_path):
    env_file = tmp_path / ".env"
    env_file.write_text("API_KEY=abc123\nDEBUG=true\n")
    return tmp_path


def _keystore_path(tmp_path: Path) -> str:
    return str(tmp_path / "keystore.json")


class TestLockCommand:
    def test_lock_creates_enc_file(self, runner, env_dir):
        ks_path = _keystore_path(env_dir)
        result = runner.invoke(
            cli,
            ["lock", str(env_dir / ".env"), "--keystore", ks_path, "--password", PASSWORD],
        )
        assert result.exit_code == 0, result.output
        assert "Locked:" in result.output
        assert (env_dir / ".env.enc").exists()

    def test_lock_missing_env_file_exits_nonzero(self, runner, env_dir):
        ks_path = _keystore_path(env_dir)
        result = runner.invoke(
            cli,
            ["lock", str(env_dir / "missing.env"), "--keystore", ks_path, "--password", PASSWORD],
        )
        assert result.exit_code != 0
        assert "Error" in result.output


class TestUnlockCommand:
    def test_unlock_restores_env_file(self, runner, env_dir):
        ks_path = _keystore_path(env_dir)
        env_path = str(env_dir / ".env")
        enc_path = str(env_dir / ".env.enc")

        runner.invoke(
            cli,
            ["lock", env_path, "--keystore", ks_path, "--password", PASSWORD],
        )

        restored = env_dir / ".env.restored"
        result = runner.invoke(
            cli,
            ["unlock", enc_path, "--keystore", ks_path, "--out", str(restored), "--password", PASSWORD],
        )
        assert result.exit_code == 0, result.output
        assert restored.exists()
        content = restored.read_text()
        assert "API_KEY" in content

    def test_unlock_wrong_password_exits_nonzero(self, runner, env_dir):
        ks_path = _keystore_path(env_dir)
        env_path = str(env_dir / ".env")
        enc_path = str(env_dir / ".env.enc")

        runner.invoke(
            cli,
            ["lock", env_path, "--keystore", ks_path, "--password", PASSWORD],
        )

        result = runner.invoke(
            cli,
            ["unlock", enc_path, "--keystore", ks_path, "--out", str(env_dir / ".env.out"), "--password", "wrong"],
        )
        assert result.exit_code != 0


class TestSyncCommand:
    def test_sync_merges_remote_secrets(self, runner, env_dir):
        ks_path = _keystore_path(env_dir)
        env_path = str(env_dir / ".env")
        enc_path = str(env_dir / ".env.enc")

        runner.invoke(
            cli,
            ["lock", env_path, "--keystore", ks_path, "--password", PASSWORD],
        )

        # Create a local .env with a different key
        local_env = env_dir / ".env.local"
        local_env.write_text("LOCAL_ONLY=yes\n")

        result = runner.invoke(
            cli,
            ["sync", enc_path, "--keystore", ks_path, "--env-file", str(local_env), "--password", PASSWORD],
        )
        assert result.exit_code == 0, result.output
        merged = local_env.read_text()
        assert "API_KEY" in merged
        assert "LOCAL_ONLY" in merged
