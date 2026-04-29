"""CLI entry point for envault."""

from __future__ import annotations

import os
from pathlib import Path

import click

from envault.audit import record_event
from envault.diff import diff_envs
from envault.env_parser import parse_env
from envault.keystore import KeyStore
from envault.vault import Vault


def _get_vault(env_file: str, keystore_path: str, password: str) -> Vault:
    ks = KeyStore(path=keystore_path, password=password)
    return Vault(env_file=env_file, keystore=ks)


@click.group()
def cli() -> None:
    """envault — encrypt and sync .env files."""


@cli.command()
@click.argument("env_file")
@click.option("--keystore", default=".envault_keys", show_default=True)
@click.password_option(prompt="Master password")
def lock(env_file: str, keystore: str, password: str) -> None:
    """Encrypt ENV_FILE and store it as <ENV_FILE>.enc."""
    vault = _get_vault(env_file, keystore, password)
    vault.lock()
    record_event("lock", env_file, Path(env_file).parent)
    click.echo(f"Locked: {env_file} -> {env_file}.enc")


@cli.command()
@click.argument("enc_file")
@click.option("--keystore", default=".envault_keys", show_default=True)
@click.password_option(prompt="Master password")
def unlock(enc_file: str, keystore: str, password: str) -> None:
    """Decrypt ENC_FILE and restore the original .env file."""
    env_file = enc_file.removesuffix(".enc")
    vault = _get_vault(env_file, keystore, password)
    vault.unlock()
    record_event("unlock", enc_file, Path(enc_file).parent)
    click.echo(f"Unlocked: {enc_file} -> {env_file}")


@cli.command()
@click.argument("env_file")
@click.option("--keystore", default=".envault_keys", show_default=True)
@click.option("--mask", is_flag=True, default=False, help="Mask secret values in diff output.")
@click.password_option(prompt="Master password")
def sync(env_file: str, keystore: str, mask: bool, password: str) -> None:
    """Sync ENV_FILE with its encrypted counterpart, showing a diff."""
    enc_file = env_file + ".enc"

    old_vars: dict = {}
    if Path(enc_file).exists():
        vault_old = _get_vault(env_file, keystore, password)
        try:
            old_content = vault_old.unlock(return_content=True)
            old_vars = parse_env(old_content) if old_content else {}
        except Exception:
            old_vars = {}

    new_vars: dict = {}
    if Path(env_file).exists():
        new_vars = parse_env(Path(env_file).read_text())

    result = diff_envs(old_vars, new_vars, mask_values=mask)
    if result.has_changes:
        click.echo("Changes detected:")
        click.echo(result.summary())
    else:
        click.echo("No changes detected.")

    vault = _get_vault(env_file, keystore, password)
    vault.sync()
    record_event("sync", env_file, Path(env_file).parent)
    click.echo(f"Synced: {env_file}")
