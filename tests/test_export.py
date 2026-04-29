"""Tests for envault.export."""

import json

import pytest

from envault.export import export_env

SECRETS = {
    "DATABASE_URL": "postgres://user:pass@localhost/db",
    "SECRET_KEY": "s3cr3t!",
    "PORT": "8080",
}


class TestShellExport:
    def test_default_format_is_shell(self):
        out = export_env(SECRETS)
        assert "export DATABASE_URL=" in out

    def test_export_keyword_present_by_default(self):
        out = export_env(SECRETS, "shell")
        for line in out.splitlines():
            assert line.startswith("export ")

    def test_export_keyword_omitted(self):
        out = export_env(SECRETS, "shell", export_keyword=False)
        for line in out.splitlines():
            assert not line.startswith("export ")

    def test_values_are_shell_quoted(self):
        secrets = {"MSG": "hello world"}
        out = export_env(secrets, "shell")
        # shlex.quote wraps in single quotes when spaces present
        assert "MSG='hello world'" in out

    def test_each_key_on_own_line(self):
        out = export_env(SECRETS, "shell")
        assert len(out.splitlines()) == len(SECRETS)

    def test_empty_secrets(self):
        assert export_env({}, "shell") == ""


class TestJsonExport:
    def test_valid_json(self):
        out = export_env(SECRETS, "json")
        parsed = json.loads(out)
        assert parsed == SECRETS

    def test_pretty_printed(self):
        out = export_env(SECRETS, "json")
        # pretty-printed JSON contains newlines
        assert "\n" in out

    def test_empty_secrets(self):
        out = export_env({}, "json")
        assert json.loads(out) == {}


class TestDockerExport:
    def test_contains_env_flags(self):
        out = export_env(SECRETS, "docker")
        assert "--env DATABASE_URL=" in out
        assert "--env SECRET_KEY=" in out

    def test_values_double_quoted(self):
        secrets = {"FOO": "bar"}
        out = export_env(secrets, "docker")
        assert '--env FOO="bar"' == out

    def test_double_quotes_in_value_escaped(self):
        secrets = {"GREETING": 'say "hi"'}
        out = export_env(secrets, "docker")
        assert '\\"' in out

    def test_multiple_keys_space_separated(self):
        out = export_env(SECRETS, "docker")
        assert out.count("--env") == len(SECRETS)

    def test_empty_secrets(self):
        assert export_env({}, "docker") == ""
