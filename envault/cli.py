"""Command-line interface for envault."""

import sys
from pathlib import Path

import click

from envault.keystore import KeyStore
from envault.vault import Vault

DEFAULT_ENV_FILE = ".env"
DEFAULT_KEYSTORE = "~/.envault/keystore.json"


def _get_vault(env_file: str, keystore_path: str) -> Vault:
    ks = KeyStore(Path(keystore_path).expanduser())
    return Vault(env_file=Path(env_file), keystore=ks)


@click.group()
@click.version_option(prog_name="envault")
def cli():
    """envault — encrypt and sync .env files across dev environments."""


@cli.command()
@click.argument("env_file", default=DEFAULT_ENV_FILE)
@click.option("--keystore", default=DEFAULT_KEYSTORE, show_default=True, help="Path to key store file.")
@click.password_option("--password", prompt="Master password", help="Master password for encryption.")
def lock(env_file: str, keystore: str, password: str):
    """Encrypt ENV_FILE and store the key."""
    try:
        vault = _get_vault(env_file, keystore)
        enc_path = vault.lock(password)
        click.echo(f"Locked: {enc_path}")
    except FileNotFoundError as exc:
        click.echo(f"Error: {exc}", err=True)
        sys.exit(1)


@cli.command()
@click.argument("enc_file", default=DEFAULT_ENV_FILE + ".enc")
@click.option("--keystore", default=DEFAULT_KEYSTORE, show_default=True, help="Path to key store file.")
@click.option("--out", default=DEFAULT_ENV_FILE, show_default=True, help="Output .env file path.")
@click.option("--password", prompt="Master password", hide_input=True, help="Master password for decryption.")
def unlock(enc_file: str, keystore: str, out: str, password: str):
    """Decrypt ENC_FILE and restore the .env file."""
    try:
        vault = _get_vault(out, keystore)
        env_path = vault.unlock(password, enc_path=Path(enc_file))
        click.echo(f"Unlocked: {env_path}")
    except (FileNotFoundError, ValueError) as exc:
        click.echo(f"Error: {exc}", err=True)
        sys.exit(1)


@cli.command()
@click.argument("source_enc", default=DEFAULT_ENV_FILE + ".enc")
@click.option("--keystore", default=DEFAULT_KEYSTORE, show_default=True, help="Path to key store file.")
@click.option("--env-file", default=DEFAULT_ENV_FILE, show_default=True, help="Local .env file to merge into.")
@click.option("--password", prompt="Master password", hide_input=True, help="Master password.")
def sync(source_enc: str, keystore: str, env_file: str, password: str):
    """Sync secrets from SOURCE_ENC into the local .env file."""
    try:
        vault = _get_vault(env_file, keystore)
        result_path = vault.sync(password, enc_path=Path(source_enc))
        click.echo(f"Synced: {result_path}")
    except (FileNotFoundError, ValueError) as exc:
        click.echo(f"Error: {exc}", err=True)
        sys.exit(1)


if __name__ == "__main__":
    cli()
