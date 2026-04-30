"""Top-level CLI entry point for envault."""

from __future__ import annotations

from pathlib import Path

import click

from envault.vault import Vault
from envault.keystore import KeyStore
from envault.cli_export import export_cmd
from envault.cli_tags import tags_cmd

_DEFAULT_ENV = ".env"
_DEFAULT_ENC = ".env.enc"
_DEFAULT_KS = "~/.envault/keystore.json"


def _get_vault(env_path: str, enc_path: str, ks_path: str) -> Vault:
    ks = KeyStore(Path(ks_path).expanduser())
    return Vault(env_file=Path(env_path), enc_file=Path(enc_path), keystore=ks)


@click.group()
def cli() -> None:
    """envault — encrypted .env manager."""


@cli.command()
@click.argument("password")
@click.option("--env", "env_path", default=_DEFAULT_ENV, show_default=True)
@click.option("--enc", "enc_path", default=_DEFAULT_ENC, show_default=True)
@click.option("--keystore", "ks_path", default=_DEFAULT_KS, show_default=True)
def lock(password: str, env_path: str, enc_path: str, ks_path: str) -> None:
    """Encrypt the .env file."""
    vault = _get_vault(env_path, enc_path, ks_path)
    vault.lock(password)
    click.echo(f"Locked: {enc_path}")


@cli.command()
@click.argument("password")
@click.option("--env", "env_path", default=_DEFAULT_ENV, show_default=True)
@click.option("--enc", "enc_path", default=_DEFAULT_ENC, show_default=True)
@click.option("--keystore", "ks_path", default=_DEFAULT_KS, show_default=True)
def unlock(password: str, env_path: str, enc_path: str, ks_path: str) -> None:
    """Decrypt the .env.enc file."""
    vault = _get_vault(env_path, enc_path, ks_path)
    vault.unlock(password)
    click.echo(f"Unlocked: {env_path}")


@cli.command()
@click.argument("password")
@click.option("--env", "env_path", default=_DEFAULT_ENV, show_default=True)
@click.option("--enc", "enc_path", default=_DEFAULT_ENC, show_default=True)
@click.option("--keystore", "ks_path", default=_DEFAULT_KS, show_default=True)
def sync(password: str, env_path: str, enc_path: str, ks_path: str) -> None:
    """Sync (merge) local .env with encrypted store."""
    vault = _get_vault(env_path, enc_path, ks_path)
    vault.sync(password)
    click.echo("Synced.")


cli.add_command(export_cmd, name="export")
cli.add_command(tags_cmd, name="tags")
