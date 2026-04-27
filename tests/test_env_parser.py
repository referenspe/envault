"""Tests for envault.env_parser."""

import pytest
from envault.env_parser import parse_env, serialize_env, merge_env


class TestParseEnv:
    def test_simple_key_value(self):
        result = parse_env('FOO=bar\nBAZ=qux\n')
        assert result == {'FOO': 'bar', 'BAZ': 'qux'}

    def test_ignores_blank_lines(self):
        result = parse_env('\nFOO=bar\n\n')
        assert result == {'FOO': 'bar'}

    def test_ignores_comments(self):
        result = parse_env('# comment\nFOO=bar\n')
        assert result == {'FOO': 'bar'}

    def test_double_quoted_value(self):
        result = parse_env('FOO="hello world"')
        assert result == {'FOO': 'hello world'}

    def test_single_quoted_value(self):
        result = parse_env("FOO='hello world'")
        assert result == {'FOO': 'hello world'}

    def test_inline_comment_stripped(self):
        result = parse_env('FOO=bar # inline comment')
        assert result == {'FOO': 'bar'}

    def test_value_with_equals(self):
        result = parse_env('DB_URL=postgres://user:pass@host/db')
        assert result == {'DB_URL': 'postgres://user:pass@host/db'}

    def test_empty_value(self):
        result = parse_env('EMPTY=')
        assert result == {'EMPTY': ''}

    def test_spaces_around_equals(self):
        result = parse_env('FOO = bar')
        assert result == {'FOO': 'bar'}


class TestSerializeEnv:
    def test_basic_round_trip(self):
        env = {'FOO': 'bar', 'BAZ': 'qux'}
        text = serialize_env(env)
        assert parse_env(text) == env

    def test_value_with_space_is_quoted(self):
        text = serialize_env({'MSG': 'hello world'})
        assert '"hello world"' in text

    def test_empty_dict_produces_empty_string(self):
        assert serialize_env({}) == ''

    def test_ends_with_newline(self):
        text = serialize_env({'A': '1'})
        assert text.endswith('\n')


class TestMergeEnv:
    def test_new_keys_added(self):
        merged, changed = merge_env({'A': '1'}, {'B': '2'})
        assert merged == {'A': '1', 'B': '2'}
        assert changed == {'B': '2'}

    def test_changed_keys_reported(self):
        merged, changed = merge_env({'A': '1'}, {'A': '99'})
        assert merged == {'A': '99'}
        assert changed == {'A': '99'}

    def test_unchanged_keys_not_in_changed(self):
        _, changed = merge_env({'A': '1', 'B': '2'}, {'A': '1'})
        assert changed == {}

    def test_base_keys_not_in_override_preserved(self):
        merged, _ = merge_env({'A': '1', 'B': '2'}, {'A': '99'})
        assert merged['B'] == '2'
