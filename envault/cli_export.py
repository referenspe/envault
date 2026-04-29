"""CLI sub-command: envault export — dump decrypted secrets in various formats."""

from __future__ import annotations

import sys
from pathlib import Path

import click

from envault.cli import _get_vault
from envault.export import ExportFormat, export_env

_FORMATS = ["shell", "json", "docker"]


@click.command("export")
@click.argument("env_file", type=click.Path(exists=True, dir_okay=False))
@click.option(
    "--format",
    "fmt",
    type=click.Choice(_FORMATS),
    default="shell",
    show_default=True,
    help="Output format.",
)
@click.option(
    "--no-export",
    "no_export",
    is_flag=True,
    default=False,
    help="Omit 'export' keyword (shell format only).",
)
@click.option(
    "--output",
    "-o",
    type=click.Path(dir_okay=False, writable=True),
    default=None,
    help="Write output to FILE instead of stdout.",
)
@click.pass_context
def export_cmd(
    ctx: click.Context,
    env_file: str,
    fmt: ExportFormat,
    no_export: bool,
    output: str | None,
) -> None:
    """Decrypt ENV_FILE and print secrets in the chosen format."""
    vault = _get_vault(ctx, env_file)

    try:
        secrets = vault.unlock()
    except Exception as exc:  # noqa: BLE001
        raise click.ClickException(f"Failed to unlock vault: {exc}") from exc

    rendered = export_env(secrets, fmt, export_keyword=not no_export)  # type: ignore[arg-type]

    if output:
        Path(output).write_text(rendered + "\n", encoding="utf-8")
        click.echo(f"Exported {len(secrets)} secret(s) to {output} [{fmt}]")
    else:
        click.echo(rendered)
