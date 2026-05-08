"""Pack ~/.claude/ profile into a portable tarball.

Default: identifiers-only for plugins, secrets redacted in JSON configs.
Toggle with include_plugin_contents / redact_secrets.
"""

import fnmatch
import io
import json
import tarfile
from pathlib import Path

from omemepo.mcp import extract_slice, load_claude_json
from omemepo.redact import redact_json, redact_text


INCLUDE_NAMES = (
    "CLAUDE.md",
    "agents",
    "commands",
    "hooks",
    "skills",
    "settings.json",
    "settings.local.json",
    "keybindings.json",
    "mcp-servers",
)

# JSON files whose values must be passed through redact_text before
# entering the tarball. Matched on the file's basename.
REDACT_NAMES = frozenset({
    "settings.json",
    "settings.local.json",
})

# Globs matched against each path's basename. Drops common ephemera.
EXCLUDE_GLOBS = (
    "*.bak",
    "*.bak-*",
    "*~",
    "#*#",
    ".DS_Store",
)

# Path-component names that exclude an entire subtree. Machine-specific
# virtualenv content; recreated on the destination if the user wants it.
EXCLUDE_PATH_COMPONENTS = frozenset({
    ".venv",
    "venv",
    "__pycache__",
    "node_modules",
})


def _excluded(name: str) -> bool:
    for pattern in EXCLUDE_GLOBS:
        if fnmatch.fnmatch(name, pattern):
            retval = True
            return retval
    retval = False
    return retval


def _excluded_path(p: Path, root: Path) -> bool:
    rel = p.relative_to(root)
    for part in rel.parts:
        if part in EXCLUDE_PATH_COMPONENTS:
            retval = True
            return retval
    retval = False
    return retval


def _add_file(
    tar: tarfile.TarFile,
    src: Path,
    arcname: str,
    redact_secrets: bool,
) -> None:
    if redact_secrets and src.name in REDACT_NAMES:
        text = src.read_text(encoding="utf-8")
        encoded = redact_text(text).encode("utf-8")
        info = tarfile.TarInfo(name=arcname)
        info.size = len(encoded)
        info.mode = 0o600
        tar.addfile(info, io.BytesIO(encoded))
    else:
        tar.add(src, arcname=arcname, recursive=False)


def _iter_files(root: Path):
    for p in sorted(root.rglob("*")):
        if not p.is_file():
            continue
        if _excluded(p.name):
            continue
        if _excluded_path(p, root):
            continue
        yield p


CLAUDE_JSON_SLICE_ARCNAME = "omemepo/claude-json-slice.json"


def _add_bytes(tar: tarfile.TarFile, arcname: str, payload: bytes) -> None:
    info = tarfile.TarInfo(name=arcname)
    info.size = len(payload)
    info.mode = 0o600
    tar.addfile(info, io.BytesIO(payload))


def pack(
    output: Path,
    home: Path = None,
    redact_secrets: bool = True,
    include_plugin_contents: bool = False,
    claude_json: Path = None,
) -> Path:
    """Pack ~/.claude/ profile into output tarball. Returns the output path."""
    if home is None:
        home = Path.home() / ".claude"
    home = home.resolve()
    output = output.resolve()
    output.parent.mkdir(parents=True, exist_ok=True)

    if claude_json is None:
        claude_json = Path.home() / ".claude.json"

    with tarfile.open(output, "w:gz") as tar:
        for name in INCLUDE_NAMES:
            src = home / name
            if not src.exists():
                continue
            if src.is_file():
                if _excluded(src.name):
                    continue
                _add_file(tar, src, f"omemepo/{name}", redact_secrets)
            else:
                for p in _iter_files(src):
                    rel = p.relative_to(home)
                    _add_file(tar, p, f"omemepo/{rel}", redact_secrets)

        plugins_dir = home / "plugins"
        if plugins_dir.is_dir():
            if include_plugin_contents:
                for p in _iter_files(plugins_dir):
                    rel = p.relative_to(home)
                    _add_file(tar, p, f"omemepo/{rel}", redact_secrets)
            else:
                manifest = plugins_dir / "installed_plugins.json"
                if manifest.is_file():
                    _add_file(
                        tar,
                        manifest,
                        "omemepo/plugins/installed_plugins.json",
                        False,
                    )

        if claude_json.is_file():
            full = load_claude_json(claude_json)
            slice_ = extract_slice(full)
            if slice_:
                if redact_secrets:
                    slice_ = redact_json(slice_)
                payload = (json.dumps(slice_, indent=2) + "\n").encode("utf-8")
                _add_bytes(tar, CLAUDE_JSON_SLICE_ARCNAME, payload)

    retval = output
    return retval
