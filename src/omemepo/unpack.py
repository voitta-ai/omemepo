"""Restore an omemepo profile tarball into ~/.claude/.

Refuses non-empty targets unless force=True. Strips the omemepo/ prefix
and rejects entries that would write outside the target home.
"""

import tarfile
from pathlib import Path


ARCHIVE_PREFIX = "omemepo/"


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
) -> Path:
    """Extract archive into home (default ~/.claude/). Returns home path."""
    if home is None:
        home = Path.home() / ".claude"
    home = home.resolve()
    archive = Path(archive).resolve()

    if home.exists() and any(home.iterdir()) and not force:
        raise UnpackError(
            f"refusing to unpack into non-empty {home}; pass --force to override"
        )
    home.mkdir(parents=True, exist_ok=True)

    with tarfile.open(archive, "r:gz") as tar:
        for member in tar.getmembers():
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

    retval = home
    return retval
