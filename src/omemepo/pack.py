"""Pack ~/.claude/ profile into a portable tarball.

Default: identifiers-only for plugins, secrets redacted in JSON configs.
Toggle with include_plugin_contents / redact_secrets.
"""

import fnmatch
import io
import tarfile
from pathlib import Path

from omemepo.redact import redact_text


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


def _excluded(name: str) -> bool:
    for pattern in EXCLUDE_GLOBS:
        if fnmatch.fnmatch(name, pattern):
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
        if p.is_file() and not _excluded(p.name):
            yield p


def pack(
    output: Path,
    home: Path = None,
    redact_secrets: bool = True,
    include_plugin_contents: bool = False,
) -> Path:
    """Pack ~/.claude/ profile into output tarball. Returns the output path."""
    if home is None:
        home = Path.home() / ".claude"
    home = home.resolve()
    output = output.resolve()
    output.parent.mkdir(parents=True, exist_ok=True)

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

    retval = output
    return retval
