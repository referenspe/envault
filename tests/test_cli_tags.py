"""Integration tests for the tags CLI sub-commands."""

import json
from pathlib import Path

import pytest
from click.testing import CliRunner

from envault.cli_tags import tags_cmd


@pytest.fixture
def runner() -> CliRunner:
    return CliRunner()


@pytest.fixture
def vault_dir(tmp_path: Path) -> str:
    return str(tmp_path)


class TestTagsCLI:
    def test_add_tag_success(self, runner: CliRunner, vault_dir: str) -> None:
        result = runner.invoke(tags_cmd, ["add", "DB_PASS", "secret", "--dir", vault_dir])
        assert result.exit_code == 0
        assert "Tagged" in result.output

    def test_add_tag_persists(self, runner: CliRunner, vault_dir: str) -> None:
        runner.invoke(tags_cmd, ["add", "API_KEY", "sensitive", "--dir", vault_dir])
        tags_file = Path(vault_dir) / ".envault_tags.json"
        data = json.loads(tags_file.read_text())
        assert "sensitive" in data["API_KEY"]

    def test_remove_tag(self, runner: CliRunner, vault_dir: str) -> None:
        runner.invoke(tags_cmd, ["add", "TOKEN", "temp", "--dir", vault_dir])
        result = runner.invoke(tags_cmd, ["remove", "TOKEN", "temp", "--dir", vault_dir])
        assert result.exit_code == 0
        assert "Removed" in result.output

    def test_list_all_tags(self, runner: CliRunner, vault_dir: str) -> None:
        runner.invoke(tags_cmd, ["add", "FOO", "alpha", "--dir", vault_dir])
        runner.invoke(tags_cmd, ["add", "BAR", "beta", "--dir", vault_dir])
        result = runner.invoke(tags_cmd, ["list", "--dir", vault_dir])
        assert result.exit_code == 0
        assert "FOO" in result.output
        assert "BAR" in result.output

    def test_list_by_key(self, runner: CliRunner, vault_dir: str) -> None:
        runner.invoke(tags_cmd, ["add", "MY_KEY", "important", "--dir", vault_dir])
        result = runner.invoke(tags_cmd, ["list", "--key", "MY_KEY", "--dir", vault_dir])
        assert result.exit_code == 0
        assert "important" in result.output

    def test_list_by_tag(self, runner: CliRunner, vault_dir: str) -> None:
        runner.invoke(tags_cmd, ["add", "K1", "shared", "--dir", vault_dir])
        runner.invoke(tags_cmd, ["add", "K2", "shared", "--dir", vault_dir])
        result = runner.invoke(tags_cmd, ["list", "--tag", "shared", "--dir", vault_dir])
        assert "K1" in result.output
        assert "K2" in result.output

    def test_list_empty(self, runner: CliRunner, vault_dir: str) -> None:
        result = runner.invoke(tags_cmd, ["list", "--dir", vault_dir])
        assert result.exit_code == 0
        assert "No tags" in result.output

    def test_list_key_no_tags(self, runner: CliRunner, vault_dir: str) -> None:
        result = runner.invoke(tags_cmd, ["list", "--key", "GHOST", "--dir", vault_dir])
        assert result.exit_code == 0
        assert "No tags" in result.output
