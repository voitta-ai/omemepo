"""omemepo CLI entry point.

Commands are stubs at this stage. See docs/architecture.md for the design.
"""

import typer

from omemepo import __version__


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
        help="Redact MCP tokens and similar secrets from settings.",
    ),
) -> None:
    """Pack your ~/.claude/ profile into a portable tarball."""
    typer.echo(
        f"pack: not implemented yet (would write {output}, redact={redact_secrets})"
    )
    raise typer.Exit(code=1)


@app.command()
def unpack(
    archive: str = typer.Argument(..., help="Path to profile tarball."),
) -> None:
    """Unpack a profile tarball into ~/.claude/."""
    typer.echo(f"unpack: not implemented yet (would read {archive})")
    raise typer.Exit(code=1)


@app.command()
def publish(
    path: str = typer.Argument(
        ..., help="Path to a local skill/agent/command to promote."
    ),
    marketplace: str = typer.Option(
        "voitta-ai/voitta-omemepo",
        "--marketplace",
        "-m",
        help="Target marketplace repo (owner/name).",
    ),
) -> None:
    """Open a PR promoting a local artifact to a marketplace."""
    typer.echo(
        f"publish: not implemented yet (would PR {path} to {marketplace})"
    )
    raise typer.Exit(code=1)


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
