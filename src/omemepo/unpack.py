"""Restore an omemepo profile tarball into ~/.claude/.

Refuses non-empty targets unless force=True. Strips the omemepo/ prefix
and rejects entries that would write outside the target home.
"""

import json
import tarfile
from pathlib import Path

from omemepo.mcp import (
    backup_claude_json,
    load_claude_json,
    merge_slice,
    write_claude_json,
)


ARCHIVE_PREFIX = "omemepo/"

CLAUDE_JSON_SLICE_ARCNAME = "omemepo/claude-json-slice.json"


class UnpackError(RuntimeError):
    pass


def _safe_relpath(arcname: str) -> str:
    if not arcname.startswith(ARCHIVE_PREFIX):
        raise UnpackError(f"unexpected entry outside omemepo/: {arcname}")
    rel = arcname[len(ARCHIVE_PREFIX):]
    if rel.startswith("/"):
        raise UnpackError(f"absolute path in archive: {arcname}")
    if ".." in Path(rel).parts:
        raise UnpackError(f"path traversal in archive: {arcname}")
    retval = rel
    return retval


def _has_only_identifiers(home: Path) -> bool:
    plugins = home / "plugins"
    if not plugins.is_dir():
        retval = False
        return retval
    entries = list(plugins.iterdir())
    only = (
        len(entries) == 1
        and entries[0].name == "installed_plugins.json"
    )
    retval = only
    return retval


def unpack(
    archive: Path,
    home: Path = None,
    force: bool = False,
    claude_json: Path = None,
    merge_mode: str = "merge",
):
    """Extract archive into home (default ~/.claude/).

    Returns (home_path, conflicts_list). conflicts_list is non-empty when
    a claude.json merge skipped overlapping entries (merge mode only).
    """
    if home is None:
        home = Path.home() / ".claude"
    home = home.resolve()
    archive = Path(archive).resolve()

    if home.exists() and any(home.iterdir()) and not force:
        raise UnpackError(
            f"refusing to unpack into non-empty {home}; pass --force to override"
        )
    home.mkdir(parents=True, exist_ok=True)

    if claude_json is None:
        claude_json = Path.home() / ".claude.json"

    pending_slice = None

    with tarfile.open(archive, "r:gz") as tar:
        for member in tar.getmembers():
            if member.name == CLAUDE_JSON_SLICE_ARCNAME:
                stream = tar.extractfile(member)
                if stream is not None:
                    pending_slice = json.loads(
                        stream.read().decode("utf-8")
                    )
                continue
            rel = _safe_relpath(member.name)
            if not rel:
                continue
            target = home / rel
            if member.isdir():
                target.mkdir(parents=True, exist_ok=True)
                continue
            if not member.isfile():
                continue
            target.parent.mkdir(parents=True, exist_ok=True)
            stream = tar.extractfile(member)
            if stream is None:
                continue
            with target.open("wb") as out:
                while True:
                    chunk = stream.read(65536)
                    if not chunk:
                        break
                    out.write(chunk)
            mode = member.mode if member.mode else 0o644
            target.chmod(mode)

    conflicts = []
    if pending_slice is not None:
        if claude_json.is_file():
            backup_claude_json(claude_json)
        existing = load_claude_json(claude_json)
        merged, conflicts = merge_slice(existing, pending_slice, merge_mode)
        write_claude_json(merged, claude_json)

    retval = (home, conflicts)
    return retval
