"""omemepo CLI entry point.

See docs/architecture.md for the design.
"""

from pathlib import Path

import typer

from omemepo import __version__
from omemepo.pack import pack as pack_impl
from omemepo.publish import (
    ARTIFACT_TYPES,
    PublishError,
    detect_kind,
    publish_gh,
    publish_local,
)
from omemepo.unpack import unpack as unpack_impl, UnpackError


app = typer.Typer(
    name="omemepo",
    help="Portable Claude Code profiles and Voitta marketplace.",
    no_args_is_help=True,
)


@app.command()
def pack(
    output: str = typer.Option(
        "omemepo-profile.tar.gz",
        "--output",
        "-o",
        help="Output archive path.",
    ),
    redact_secrets: bool = typer.Option(
        True,
        "--redact-secrets/--no-redact-secrets",
        help="Redact secrets from settings.json by key-name blacklist.",
    ),
    include_plugin_contents: bool = typer.Option(
        False,
        "--include-plugin-contents/--no-include-plugin-contents",
        help=(
            "Include the full ~/.claude/plugins/ tree. Default carries only "
            "installed_plugins.json so unpack can re-install via /plugin."
        ),
    ),
    home: str = typer.Option(
        None,
        "--home",
        help="Override Claude home (default: ~/.claude).",
    ),
) -> None:
    """Pack your ~/.claude/ profile into a portable tarball."""
    home_path = Path(home) if home else None
    written = pack_impl(
        output=Path(output),
        home=home_path,
        redact_secrets=redact_secrets,
        include_plugin_contents=include_plugin_contents,
    )
    typer.echo(str(written))


@app.command()
def unpack(
    archive: str = typer.Argument(..., help="Path to profile tarball."),
    home: str = typer.Option(
        None,
        "--home",
        help="Override Claude home (default: ~/.claude).",
    ),
    force: bool = typer.Option(
        False,
        "--force",
        help="Allow extracting into a non-empty target home.",
    ),
) -> None:
    """Unpack a profile tarball into ~/.claude/."""
    home_path = Path(home) if home else None
    try:
        restored = unpack_impl(
            archive=Path(archive),
            home=home_path,
            force=force,
        )
    except UnpackError as exc:
        typer.echo(str(exc), err=True)
        raise typer.Exit(code=2)
    typer.echo(str(restored))
    plugins_manifest = restored / "plugins" / "installed_plugins.json"
    full_plugins_tree = (restored / "plugins" / "marketplaces").is_dir()
    if plugins_manifest.is_file() and not full_plugins_tree:
        typer.echo(
            "note: plugins/installed_plugins.json restored (identifiers only). "
            "Run /plugin marketplace add and /plugin install in Claude Code to "
            "complete plugin restoration.",
            err=True,
        )


@app.command()
def publish(
    path: str = typer.Argument(
        ..., help="Path to a local skill/agent/command to promote."
    ),
    marketplace: str = typer.Option(
        "voitta-ai/omemepo",
        "--marketplace",
        "-m",
        help="Target marketplace repo (owner/name). Used in gh mode.",
    ),
    plugin: str = typer.Option(
        "voitta-misc",
        "--plugin",
        help="Target plugin directory under plugins/.",
    ),
    kind: str = typer.Option(
        None,
        "--type",
        help=f"Artifact type ({', '.join(ARTIFACT_TYPES)}); auto-detected if omitted.",
    ),
    checkout: str = typer.Option(
        None,
        "--checkout",
        help=(
            "Local marketplace checkout path. If set, only copies the artifact "
            "into the checkout tree; user commits/pushes/PRs by hand. If "
            "omitted, uses gh CLI for the full flow."
        ),
    ),
    title: str = typer.Option(None, "--title", help="PR title (gh mode)."),
    body: str = typer.Option(None, "--body", help="PR body (gh mode)."),
    dry_run: bool = typer.Option(
        False,
        "--dry-run",
        help="In gh mode, print the planned commands and exit.",
    ),
) -> None:
    """Promote a local artifact to a marketplace plugin."""
    src = Path(path).resolve()
    if not src.exists():
        typer.echo(f"path not found: {src}", err=True)
        raise typer.Exit(code=2)
    try:
        resolved_kind = kind or detect_kind(src)
        if resolved_kind not in ARTIFACT_TYPES:
            typer.echo(
                f"--type must be one of {', '.join(ARTIFACT_TYPES)}",
                err=True,
            )
            raise typer.Exit(code=2)
        if checkout:
            dest = publish_local(
                src=src,
                checkout=Path(checkout).resolve(),
                plugin=plugin,
                kind=resolved_kind,
            )
            typer.echo(str(dest))
            typer.echo(
                f"copied. Next: cd {checkout} && git checkout -b <branch> && "
                f"git add plugins/{plugin} && git commit && git push && "
                f"gh pr create",
                err=True,
            )
        else:
            result = publish_gh(
                src=src,
                marketplace=marketplace,
                plugin=plugin,
                kind=resolved_kind,
                title=title,
                body=body,
                dry_run=dry_run,
            )
            typer.echo(result)
    except PublishError as exc:
        typer.echo(str(exc), err=True)
        raise typer.Exit(code=2)


@app.command()
def diff() -> None:
    """Show local ~/.claude/ vs configured marketplace delta."""
    typer.echo("diff: not implemented yet")
    raise typer.Exit(code=1)


@app.command()
def mcp() -> None:
    """Sync MCP servers and prompts (subsumes truffaldino for Claude Code)."""
    typer.echo("mcp: not implemented yet")
    raise typer.Exit(code=1)


@app.command()
def version() -> None:
    """Print omemepo version."""
    typer.echo(__version__)
