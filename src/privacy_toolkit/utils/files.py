"""File system helpers."""

from __future__ import annotations

import hashlib
import shutil
from pathlib import Path


def sha256_file(path: Path) -> str:
    """Return hex SHA-256 of a file's contents."""
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def safe_write(path: Path, content: str, encoding: str = "utf-8") -> None:
    """Write *content* to *path*, creating parent dirs as needed."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding=encoding)


def safe_copy(src: Path, dst: Path) -> None:
    """Copy *src* to *dst*, creating parent dirs."""
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)


def ensure_dir(path: Path) -> Path:
    """Create *path* as a directory if it doesn't exist, return it."""
    path.mkdir(parents=True, exist_ok=True)
    return path


def file_size_label(path: Path) -> str:
    """Return a human-readable file size string."""
    if not path.exists():
        return "—"
    size = path.stat().st_size
    for unit in ("B", "KB", "MB", "GB"):
        if size < 1024:
            return f"{size:.1f} {unit}"
        size //= 1024
    return f"{size:.1f} TB"
