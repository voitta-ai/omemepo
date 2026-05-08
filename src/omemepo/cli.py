"""omemepo CLI entry point.

See docs/architecture.md for the design.
"""

import json
import shutil
from pathlib import Path

import typer

from omemepo import __version__
from omemepo.mcp import (
    PROFILE_DIR,
    backup_claude_json,
    extract_slice,
    list_servers,
    load_claude_json,
    merge_slice,
    write_claude_json,
)
from omemepo.pack import pack as pack_impl
from omemepo.publish import (
    ARTIFACT_TYPES,
    PublishError,
    detect_kind,
    publish_gh,
    publish_local,
)
from omemepo.redact import redact_json
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
    claude_json: str = typer.Option(
        None,
        "--claude-json",
        help="Override path to ~/.claude.json (used for tests).",
    ),
) -> None:
    """Pack your ~/.claude/ profile into a portable tarball."""
    home_path = Path(home) if home else None
    cj_path = Path(claude_json) if claude_json else None
    written = pack_impl(
        output=Path(output),
        home=home_path,
        redact_secrets=redact_secrets,
        include_plugin_contents=include_plugin_contents,
        claude_json=cj_path,
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
    claude_json: str = typer.Option(
        None,
        "--claude-json",
        help="Override path to ~/.claude.json (used for tests).",
    ),
    merge_mode: str = typer.Option(
        "merge",
        "--merge-mode",
        help="How to apply the carried claude.json slice: merge | replace.",
    ),
) -> None:
    """Unpack a profile tarball into ~/.claude/."""
    home_path = Path(home) if home else None
    cj_path = Path(claude_json) if claude_json else None
    try:
        restored, conflicts = unpack_impl(
            archive=Path(archive),
            home=home_path,
            force=force,
            claude_json=cj_path,
            merge_mode=merge_mode,
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
    if conflicts:
        typer.echo(
            "claude.json merge: kept existing values for conflicting servers: "
            + ", ".join(conflicts),
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


mcp_app = typer.Typer(
    help="Manage MCP servers and prompts (subsumes truffaldino for Claude Code).",
    no_args_is_help=True,
)
app.add_typer(mcp_app, name="mcp")


def _resolve_claude_json(claude_json):
    retval = Path(claude_json) if claude_json else (Path.home() / ".claude.json")
    return retval


def _scope_filter(slice_, scope):
    if scope == "all":
        retval = slice_
        return retval
    out = {}
    if scope == "user" and slice_.get("mcpServers"):
        out["mcpServers"] = slice_["mcpServers"]
    if scope == "project" and slice_.get("projects"):
        out["projects"] = slice_["projects"]
    retval = out
    return retval


@mcp_app.command(name="list")
def mcp_list(
    scope: str = typer.Option(
        "all",
        "--scope",
        help="Restrict to user | project | all.",
    ),
    show_secrets: bool = typer.Option(
        False,
        "--show-secrets",
        help="Print real secret values instead of <redacted>.",
    ),
    claude_json: str = typer.Option(
        None,
        "--claude-json",
        help="Override path to ~/.claude.json (used for tests).",
    ),
) -> None:
    """List configured MCP servers."""
    cj = _resolve_claude_json(claude_json)
    full = load_claude_json(cj)
    slice_ = _scope_filter(extract_slice(full), scope)
    if not show_secrets:
        slice_ = redact_json(slice_)
    rows = list_servers(slice_)
    if not rows:
        typer.echo("(no MCP servers)")
        return
    for s, name, cfg in rows:
        cmd = cfg.get("command") or cfg.get("type") or "?"
        typer.echo(f"{s:<40} {name:<30} {cmd}")


@mcp_app.command(name="export")
def mcp_export(
    output: str = typer.Argument(..., help="Output JSON path."),
    scope: str = typer.Option(
        "all",
        "--scope",
        help="Restrict to user | project | all.",
    ),
    redact_secrets: bool = typer.Option(
        True,
        "--redact-secrets/--no-redact-secrets",
        help="Redact secrets via key-name blacklist.",
    ),
    claude_json: str = typer.Option(
        None,
        "--claude-json",
        help="Override path to ~/.claude.json (used for tests).",
    ),
) -> None:
    """Export the MCP slice to a JSON file."""
    cj = _resolve_claude_json(claude_json)
    full = load_claude_json(cj)
    slice_ = _scope_filter(extract_slice(full), scope)
    if redact_secrets:
        slice_ = redact_json(slice_)
    out_path = Path(output).resolve()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(slice_, indent=2) + "\n", encoding="utf-8")
    typer.echo(str(out_path))


profile_app = typer.Typer(
    help="Named MCP profiles stored under ~/.claude/omemepo/profiles/.",
    no_args_is_help=True,
)
mcp_app.add_typer(profile_app, name="profile")


def _profile_path(name: str) -> Path:
    if not name or "/" in name or name.startswith("."):
        raise typer.BadParameter(f"invalid profile name: {name!r}")
    retval = PROFILE_DIR / f"{name}.json"
    return retval


@profile_app.command(name="create")
def profile_create(
    name: str = typer.Argument(..., help="Profile name."),
    scope: str = typer.Option(
        "all",
        "--scope",
        help="Restrict snapshot to user | project | all.",
    ),
    redact_secrets: bool = typer.Option(
        True,
        "--redact-secrets/--no-redact-secrets",
    ),
    overwrite: bool = typer.Option(
        False,
        "--overwrite",
        help="Replace an existing profile of the same name.",
    ),
    claude_json: str = typer.Option(None, "--claude-json"),
) -> None:
    """Snapshot the current MCP slice into a named profile."""
    cj = _resolve_claude_json(claude_json)
    dest = _profile_path(name)
    if dest.exists() and not overwrite:
        typer.echo(f"profile exists: {dest} (pass --overwrite)", err=True)
        raise typer.Exit(code=2)
    full = load_claude_json(cj)
    slice_ = _scope_filter(extract_slice(full), scope)
    if redact_secrets:
        slice_ = redact_json(slice_)
    PROFILE_DIR.mkdir(parents=True, exist_ok=True)
    dest.write_text(json.dumps(slice_, indent=2) + "\n", encoding="utf-8")
    typer.echo(str(dest))


@profile_app.command(name="list")
def profile_list() -> None:
    """List saved profiles."""
    if not PROFILE_DIR.is_dir():
        return
    profiles = sorted(PROFILE_DIR.glob("*.json"))
    for p in profiles:
        typer.echo(p.stem)


@profile_app.command(name="activate")
def profile_activate(
    name: str = typer.Argument(..., help="Profile name."),
    mode: str = typer.Option(
        "merge",
        "--mode",
        help="merge | replace.",
    ),
    claude_json: str = typer.Option(None, "--claude-json"),
) -> None:
    """Apply a named profile to ~/.claude.json."""
    cj = _resolve_claude_json(claude_json)
    src = _profile_path(name)
    if not src.is_file():
        typer.echo(f"no such profile: {src}", err=True)
        raise typer.Exit(code=2)
    slice_ = json.loads(src.read_text(encoding="utf-8"))
    existing = load_claude_json(cj)
    if cj.is_file():
        backup_claude_json(cj)
    merged, conflicts = merge_slice(existing, slice_, mode)
    write_claude_json(merged, cj)
    typer.echo(str(cj))
    if conflicts:
        typer.echo(
            "kept existing values for conflicting servers: "
            + ", ".join(conflicts),
            err=True,
        )


@profile_app.command(name="delete")
def profile_delete(
    name: str = typer.Argument(..., help="Profile name."),
) -> None:
    """Delete a named profile."""
    target = _profile_path(name)
    if not target.is_file():
        typer.echo(f"no such profile: {target}", err=True)
        raise typer.Exit(code=2)
    target.unlink()
    typer.echo(f"deleted {target}")


prompts_app = typer.Typer(
    help="Sync slash commands (~/.claude/commands/) between machines.",
    no_args_is_help=True,
)
mcp_app.add_typer(prompts_app, name="prompts")


def _user_commands_dir(home: Path = None) -> Path:
    base = home if home else (Path.home() / ".claude")
    retval = base / "commands"
    return retval


@prompts_app.command(name="list")
def prompts_list(
    home: str = typer.Option(None, "--home"),
) -> None:
    """List user-scope slash commands."""
    cmds = _user_commands_dir(Path(home) if home else None)
    if not cmds.is_dir():
        return
    for f in sorted(cmds.glob("*.md")):
        typer.echo(f.stem)


@prompts_app.command(name="export")
def prompts_export(
    output: str = typer.Argument(..., help="Output directory."),
    home: str = typer.Option(None, "--home"),
) -> None:
    """Copy user-scope slash commands into a directory."""
    src = _user_commands_dir(Path(home) if home else None)
    if not src.is_dir():
        typer.echo(f"no commands directory: {src}", err=True)
        raise typer.Exit(code=2)
    dest = Path(output).resolve()
    dest.mkdir(parents=True, exist_ok=True)
    for f in sorted(src.glob("*.md")):
        shutil.copy2(f, dest / f.name)
    typer.echo(str(dest))


@prompts_app.command(name="import")
def prompts_import(
    input_dir: str = typer.Argument(..., help="Input directory."),
    home: str = typer.Option(None, "--home"),
    overwrite: bool = typer.Option(
        False,
        "--overwrite",
        help="Overwrite existing commands of the same name.",
    ),
) -> None:
    """Copy slash commands from a directory into ~/.claude/commands/."""
    src = Path(input_dir).resolve()
    if not src.is_dir():
        typer.echo(f"input not found: {src}", err=True)
        raise typer.Exit(code=2)
    dest = _user_commands_dir(Path(home) if home else None)
    dest.mkdir(parents=True, exist_ok=True)
    skipped = []
    for f in sorted(src.glob("*.md")):
        target = dest / f.name
        if target.exists() and not overwrite:
            skipped.append(f.name)
            continue
        shutil.copy2(f, target)
    typer.echo(str(dest))
    if skipped:
        typer.echo(
            f"skipped {len(skipped)} existing (pass --overwrite): "
            + ", ".join(skipped),
            err=True,
        )


def _toggle_mcpjson_server(
    cj: Path,
    name: str,
    project: str,
    enable: bool,
) -> None:
    full = load_claude_json(cj)
    if cj.is_file():
        backup_claude_json(cj)
    projects = full.setdefault("projects", {})
    project_data = projects.setdefault(project, {})
    enabled = project_data.setdefault("enabledMcpjsonServers", [])
    disabled = project_data.setdefault("disabledMcpjsonServers", [])
    add_to = enabled if enable else disabled
    remove_from = disabled if enable else enabled
    if name not in add_to:
        add_to.append(name)
    if name in remove_from:
        remove_from.remove(name)
    write_claude_json(full, cj)


@mcp_app.command(name="enable")
def mcp_enable(
    name: str = typer.Argument(..., help="MCP server name."),
    project: str = typer.Option(
        ...,
        "--project",
        help="Absolute path of the project whose .mcp.json server to enable.",
    ),
    claude_json: str = typer.Option(None, "--claude-json"),
) -> None:
    """Enable a project-scope (.mcp.json) MCP server."""
    cj = _resolve_claude_json(claude_json)
    _toggle_mcpjson_server(cj, name, project, enable=True)
    typer.echo(f"enabled {name} in {project}")


@mcp_app.command(name="disable")
def mcp_disable(
    name: str = typer.Argument(..., help="MCP server name."),
    project: str = typer.Option(
        ...,
        "--project",
        help="Absolute path of the project whose .mcp.json server to disable.",
    ),
    claude_json: str = typer.Option(None, "--claude-json"),
) -> None:
    """Disable a project-scope (.mcp.json) MCP server."""
    cj = _resolve_claude_json(claude_json)
    _toggle_mcpjson_server(cj, name, project, enable=False)
    typer.echo(f"disabled {name} in {project}")


@mcp_app.command(name="diff")
def mcp_diff(
    a: str = typer.Argument(..., help="First source: 'live' or path to JSON."),
    b: str = typer.Argument(..., help="Second source: 'live' or path to JSON."),
    show_secrets: bool = typer.Option(False, "--show-secrets"),
    claude_json: str = typer.Option(
        None,
        "--claude-json",
        help="Path used when source is 'live' (default: ~/.claude.json).",
    ),
) -> None:
    """Show server-name differences between two MCP config sources."""
    cj = _resolve_claude_json(claude_json)

    def _load(source: str):
        if source == "live":
            data = load_claude_json(cj)
        else:
            p = Path(source).resolve()
            if not p.is_file():
                typer.echo(f"source not found: {p}", err=True)
                raise typer.Exit(code=2)
            data = load_claude_json(p)
        sl = extract_slice(data)
        if not show_secrets:
            sl = redact_json(sl)
        retval = sl
        return retval

    sa = _load(a)
    sb = _load(b)
    rows_a = {(scope, name): cfg for scope, name, cfg in list_servers(sa)}
    rows_b = {(scope, name): cfg for scope, name, cfg in list_servers(sb)}

    a_only = sorted(rows_a.keys() - rows_b.keys())
    b_only = sorted(rows_b.keys() - rows_a.keys())
    both = sorted(rows_a.keys() & rows_b.keys())
    differing = [k for k in both if rows_a[k] != rows_b[k]]

    typer.echo(f"=== only in {a} ({len(a_only)}) ===")
    for scope, name in a_only:
        typer.echo(f"{scope:<40} {name}")
    typer.echo(f"\n=== only in {b} ({len(b_only)}) ===")
    for scope, name in b_only:
        typer.echo(f"{scope:<40} {name}")
    typer.echo(f"\n=== differing ({len(differing)}) ===")
    for scope, name in differing:
        typer.echo(f"{scope:<40} {name}")
        typer.echo(f"  a: {json.dumps(rows_a[(scope, name)])}")
        typer.echo(f"  b: {json.dumps(rows_b[(scope, name)])}")

    if a_only or b_only or differing:
        raise typer.Exit(code=1)


@mcp_app.command(name="import")
def mcp_import(
    input_path: str = typer.Argument(
        ...,
        help="Input JSON path (slice shape).",
    ),
    mode: str = typer.Option(
        "merge",
        "--mode",
        help="merge (additive, conflict-safe) | replace (overwrite).",
    ),
    claude_json: str = typer.Option(
        None,
        "--claude-json",
        help="Override path to ~/.claude.json (used for tests).",
    ),
) -> None:
    """Merge a slice JSON file into ~/.claude.json."""
    cj = _resolve_claude_json(claude_json)
    src = Path(input_path).resolve()
    if not src.is_file():
        typer.echo(f"input not found: {src}", err=True)
        raise typer.Exit(code=2)
    slice_ = json.loads(src.read_text(encoding="utf-8"))
    existing = load_claude_json(cj)
    if cj.is_file():
        backup_claude_json(cj)
    merged, conflicts = merge_slice(existing, slice_, mode)
    write_claude_json(merged, cj)
    typer.echo(str(cj))
    if conflicts:
        typer.echo(
            "kept existing values for conflicting servers: "
            + ", ".join(conflicts),
            err=True,
        )


@app.command()
def version() -> None:
    """Print omemepo version."""
    typer.echo(__version__)
