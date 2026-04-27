"""Parser and serializer for .env files."""

import re
from typing import Dict, Optional, Tuple


ENV_LINE_RE = re.compile(
    r'^\s*(?P<key>[A-Za-z_][A-Za-z0-9_]*)\s*=\s*(?P<value>.*)$'
)
COMMENT_RE = re.compile(r'^\s*#.*$')


def parse_env(content: str) -> Dict[str, str]:
    """Parse the text content of a .env file into a key-value dict.

    - Strips inline comments (values wrapped in quotes keep them).
    - Ignores blank lines and full-line comments.
    """
    result: Dict[str, str] = {}
    for line in content.splitlines():
        if not line.strip() or COMMENT_RE.match(line):
            continue
        m = ENV_LINE_RE.match(line)
        if m:
            key = m.group('key')
            value = _strip_value(m.group('value'))
            result[key] = value
    return result


def serialize_env(env: Dict[str, str]) -> str:
    """Serialize a key-value dict back to .env file text."""
    lines = []
    for key, value in env.items():
        if _needs_quoting(value):
            value = f'"{value}"'
        lines.append(f'{key}={value}')
    return '\n'.join(lines) + ('\n' if lines else '')


def merge_env(
    base: Dict[str, str], override: Dict[str, str]
) -> Tuple[Dict[str, str], Dict[str, str]]:
    """Merge *override* into *base*.

    Returns (merged, changed) where *changed* contains only the keys
    whose values differed from *base*.
    """
    merged = dict(base)
    changed: Dict[str, str] = {}
    for key, value in override.items():
        if merged.get(key) != value:
            changed[key] = value
        merged[key] = value
    return merged, changed


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _strip_value(raw: str) -> str:
    """Remove surrounding quotes and trailing inline comments."""
    raw = raw.strip()
    for quote in ('"', "'"):
        if raw.startswith(quote) and raw.endswith(quote) and len(raw) >= 2:
            return raw[1:-1]
    # Strip inline comment (space + #)
    raw = re.sub(r'\s+#.*$', '', raw)
    return raw


def _needs_quoting(value: str) -> bool:
    """Return True if *value* contains characters that require quoting."""
    return bool(re.search(r'[\s#"\']', value))
