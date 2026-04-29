"""Export decrypted secrets to various formats (shell, JSON, Docker)."""

from __future__ import annotations

import json
import shlex
from typing import Dict, Literal

ExportFormat = Literal["shell", "json", "docker"]


def export_env(
    secrets: Dict[str, str],
    fmt: ExportFormat = "shell",
    *,
    export_keyword: bool = True,
) -> str:
    """Render *secrets* as a string in the requested format.

    Parameters
    ----------
    secrets:
        Mapping of key -> value pairs.
    fmt:
        One of ``"shell"``, ``"json"``, or ``"docker"``.
    export_keyword:
        When *fmt* is ``"shell"``, prefix each line with ``export ``.
    """
    if fmt == "json":
        return _to_json(secrets)
    if fmt == "docker":
        return _to_docker(secrets)
    return _to_shell(secrets, export_keyword=export_keyword)


def _to_shell(secrets: Dict[str, str], *, export_keyword: bool) -> str:
    """KEY=value pairs suitable for sourcing in bash/zsh."""
    lines: list[str] = []
    prefix = "export " if export_keyword else ""
    for key, value in secrets.items():
        quoted = shlex.quote(value)
        lines.append(f"{prefix}{key}={quoted}")
    return "\n".join(lines)


def _to_json(secrets: Dict[str, str]) -> str:
    """Pretty-printed JSON object."""
    return json.dumps(secrets, indent=2)


def _to_docker(secrets: Dict[str, str]) -> str:
    """``--env KEY=value`` flags for use with ``docker run``."""
    parts: list[str] = []
    for key, value in secrets.items():
        escaped = value.replace("\\", "\\\\").replace('"', '\\"')
        parts.append(f'--env {key}="{escaped}"')
    return " ".join(parts)
