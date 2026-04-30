"""CLI commands for managing key-level access permissions."""
from __future__ import annotations

import click

from envault.access import AccessManager, VALID_PERMISSIONS, AccessError


@click.group("access")
def access_cmd() -> None:
    """Manage read/write/deny permissions for keys per profile."""


@access_cmd.command("set")
@click.argument("profile")
@click.argument("key")
@click.argument("permission", type=click.Choice(list(VALID_PERMISSIONS)))
@click.option("--vault-dir", default=".", show_default=True, help="Vault directory.")
def set_permission(profile: str, key: str, permission: str, vault_dir: str) -> None:
    """Set PERMISSION for KEY under PROFILE."""
    am = AccessManager(vault_dir)
    am.set_permission(profile, key, permission)
    click.echo(f"Set '{permission}' on '{key}' for profile '{profile}'.")


@access_cmd.command("remove")
@click.argument("profile")
@click.argument("key")
@click.option("--vault-dir", default=".", show_default=True, help="Vault directory.")
def remove_permission(profile: str, key: str, vault_dir: str) -> None:
    """Remove an explicit permission rule for KEY under PROFILE."""
    am = AccessManager(vault_dir)
    am.remove_permission(profile, key)
    click.echo(f"Removed explicit rule for '{key}' under profile '{profile}'.")


@access_cmd.command("list")
@click.argument("profile")
@click.option("--vault-dir", default=".", show_default=True, help="Vault directory.")
def list_permissions(profile: str, vault_dir: str) -> None:
    """List all explicit permission rules for PROFILE."""
    am = AccessManager(vault_dir)
    rules = am.list_rules(profile)
    if not rules:
        click.echo(f"No explicit rules for profile '{profile}' (all keys default to 'write').")
        return
    click.echo(f"Permissions for profile '{profile}':")
    for key, perm in sorted(rules.items()):
        click.echo(f"  {key}: {perm}")


@access_cmd.command("check")
@click.argument("profile")
@click.argument("key")
@click.argument("required", type=click.Choice(["read", "write"]))
@click.option("--vault-dir", default=".", show_default=True, help="Vault directory.")
def check_permission(profile: str, key: str, required: str, vault_dir: str) -> None:
    """Check whether PROFILE has REQUIRED permission for KEY."""
    am = AccessManager(vault_dir)
    try:
        am.check(profile, key, required)
        click.echo(f"Access granted: '{profile}' has '{required}' permission on '{key}'.")
    except AccessError as exc:
        click.echo(f"Access denied: {exc}", err=True)
        raise SystemExit(1)
