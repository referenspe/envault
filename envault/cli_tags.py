"""CLI sub-commands for managing key tags (add-tag, remove-tag, list-tags)."""

from __future__ import annotations

import click

from envault.tags import TagManager


@click.group("tags")
def tags_cmd() -> None:
    """Manage tags attached to secret keys."""


@tags_cmd.command("add")
@click.argument("key")
@click.argument("tag")
@click.option("--dir", "vault_dir", default=".", show_default=True,
              help="Vault directory containing the .env file.")
def add_tag(key: str, tag: str, vault_dir: str) -> None:
    """Attach TAG to KEY."""
    tm = TagManager(vault_dir)
    tm.add_tag(key, tag)
    click.echo(f"Tagged '{key}' with '{tag}'.")


@tags_cmd.command("remove")
@click.argument("key")
@click.argument("tag")
@click.option("--dir", "vault_dir", default=".", show_default=True,
              help="Vault directory containing the .env file.")
def remove_tag(key: str, tag: str, vault_dir: str) -> None:
    """Remove TAG from KEY."""
    tm = TagManager(vault_dir)
    tm.remove_tag(key, tag)
    click.echo(f"Removed tag '{tag}' from '{key}'.")


@tags_cmd.command("list")
@click.option("--key", default=None, help="Filter by a specific key.")
@click.option("--tag", default=None, help="List all keys carrying this tag.")
@click.option("--dir", "vault_dir", default=".", show_default=True,
              help="Vault directory containing the .env file.")
def list_tags(key: str | None, tag: str | None, vault_dir: str) -> None:
    """List tags.  Use --key or --tag to filter."""
    tm = TagManager(vault_dir)

    if key:
        tags = tm.get_tags(key)
        if tags:
            click.echo("  ".join(tags))
        else:
            click.echo(f"No tags for '{key}'.")
    elif tag:
        keys = tm.keys_with_tag(tag)
        if keys:
            click.echo("\n".join(sorted(keys)))
        else:
            click.echo(f"No keys with tag '{tag}'.")
    else:
        snap = tm.snapshot()
        if not snap:
            click.echo("No tags defined.")
        else:
            for k in sorted(snap):
                click.echo(f"{k}: {', '.join(snap[k])}")
