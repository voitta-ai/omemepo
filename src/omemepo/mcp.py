"""MCP config slice management for omemepo.

Claude Code persists MCP configuration in ~/.claude.json. omemepo cares
about a small subset of that file:

- top-level ``mcpServers`` (user-scope MCP servers)
- ``projects[<path>].mcpServers`` (per-project user-scope additions)
- ``projects[<path>].enabledMcpjsonServers``
- ``projects[<path>].disabledMcpjsonServers``

This module extracts that slice for inclusion in pack tarballs and
merges it back on unpack. Backups of the live ~/.claude.json are
written before any mutation.
"""

import json
import shutil
from datetime import datetime, timezone
from pathlib import Path


CLAUDE_JSON = Path.home() / ".claude.json"

USER_SCOPE_KEY = "mcpServers"

PROJECT_KEYS = (
    "mcpServers",
    "enabledMcpjsonServers",
    "disabledMcpjsonServers",
)

BACKUP_DIR = Path.home() / ".claude" / "omemepo" / "backups"
PROFILE_DIR = Path.home() / ".claude" / "omemepo" / "profiles"
MAX_BACKUPS = 10


class McpError(RuntimeError):
    pass


def load_claude_json(path: Path = None) -> dict:
    target = path if path else CLAUDE_JSON
    if not target.is_file():
        retval = {}
        return retval
    with target.open(encoding="utf-8") as f:
        retval = json.load(f)
    return retval


def extract_slice(claude_json: dict) -> dict:
    """Pull mcp-relevant keys out of a parsed ~/.claude.json."""
    slice_ = {}
    user_servers = claude_json.get(USER_SCOPE_KEY)
    if user_servers:
        slice_[USER_SCOPE_KEY] = user_servers

    projects_in = claude_json.get("projects") or {}
    projects_out = {}
    for path, project in projects_in.items():
        project_slice = {}
        for key in PROJECT_KEYS:
            value = project.get(key)
            if value:
                project_slice[key] = value
        if project_slice:
            projects_out[path] = project_slice
    if projects_out:
        slice_["projects"] = projects_out

    retval = slice_
    return retval


def _merge_servers(base: dict, incoming: dict, mode: str) -> tuple:
    """Return (merged, conflicts) where conflicts is a list of names."""
    if mode == "replace":
        retval = (dict(incoming), [])
        return retval
    merged = dict(base)
    conflicts = []
    for name, cfg in incoming.items():
        if name in merged and merged[name] != cfg:
            conflicts.append(name)
        else:
            merged[name] = cfg
    retval = (merged, conflicts)
    return retval


def merge_slice(claude_json: dict, slice_: dict, mode: str = "merge") -> tuple:
    """Apply slice to claude_json. Returns (new_claude_json, conflicts).

    mode='merge' adds missing entries and skips conflicting ones (reported
    in conflicts). mode='replace' overwrites incoming server names. The
    parent claude_json dict is not mutated.
    """
    if mode not in ("merge", "replace"):
        raise McpError(f"unknown merge mode: {mode}")

    new = dict(claude_json)
    conflicts = []

    incoming_user = slice_.get(USER_SCOPE_KEY) or {}
    base_user = new.get(USER_SCOPE_KEY) or {}
    merged_user, user_conflicts = _merge_servers(base_user, incoming_user, mode)
    if merged_user:
        new[USER_SCOPE_KEY] = merged_user
    conflicts.extend(f"user:{n}" for n in user_conflicts)

    incoming_projects = slice_.get("projects") or {}
    base_projects = dict(new.get("projects") or {})
    for path, project_slice in incoming_projects.items():
        existing = dict(base_projects.get(path) or {})
        for key in PROJECT_KEYS:
            incoming_value = project_slice.get(key)
            if incoming_value is None:
                continue
            if key == USER_SCOPE_KEY:
                base = existing.get(key) or {}
                merged, project_conflicts = _merge_servers(
                    base, incoming_value, mode
                )
                existing[key] = merged
                conflicts.extend(
                    f"project:{path}:{n}" for n in project_conflicts
                )
            else:
                if mode == "replace":
                    existing[key] = list(incoming_value)
                else:
                    base_list = existing.get(key) or []
                    seen = set(base_list)
                    for item in incoming_value:
                        if item not in seen:
                            base_list.append(item)
                            seen.add(item)
                    existing[key] = base_list
        base_projects[path] = existing
    if base_projects:
        new["projects"] = base_projects

    retval = (new, conflicts)
    return retval


def backup_claude_json(path: Path = None) -> Path:
    """Copy live ~/.claude.json into the omemepo backups dir. Returns dest."""
    target = path if path else CLAUDE_JSON
    if not target.is_file():
        raise McpError(f"no such file: {target}")
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    dest = BACKUP_DIR / f"claude-json-{timestamp}.json"
    shutil.copy2(target, dest)
    _prune_backups()
    retval = dest
    return retval


def _prune_backups() -> None:
    if not BACKUP_DIR.is_dir():
        return
    backups = sorted(
        BACKUP_DIR.glob("claude-json-*.json"),
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )
    for stale in backups[MAX_BACKUPS:]:
        stale.unlink()


def write_claude_json(new_data: dict, path: Path = None) -> Path:
    target = path if path else CLAUDE_JSON
    target.parent.mkdir(parents=True, exist_ok=True)
    text = json.dumps(new_data, indent=2) + "\n"
    target.write_text(text, encoding="utf-8")
    retval = target
    return retval


def list_servers(slice_: dict) -> list:
    """Flatten a slice into [(scope, name, config_dict), ...]."""
    rows = []
    user_servers = slice_.get(USER_SCOPE_KEY) or {}
    for name in sorted(user_servers):
        rows.append(("user", name, user_servers[name]))
    projects = slice_.get("projects") or {}
    for path in sorted(projects):
        project_servers = projects[path].get(USER_SCOPE_KEY) or {}
        for name in sorted(project_servers):
            rows.append(
                (f"project:{path}", name, project_servers[name])
            )
    retval = rows
    return retval
