"""Incremental scanning cache for AI-BOM.

Stores file hashes to enable incremental scanning - only re-scan
files that have changed since the last scan.
"""

from __future__ import annotations

import hashlib
import json
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

DEFAULT_CACHE_DIR = ".ai-bom-cache"


class ScanCache:
    """File-hash based cache for incremental scanning."""

    def __init__(self, cache_dir: str | Path = DEFAULT_CACHE_DIR) -> None:
        self.cache_dir = Path(cache_dir)
        self.cache_file = self.cache_dir / "file_hashes.json"
        self._hashes: dict[str, str] = {}
        self._load()

    def _load(self) -> None:
        """Load cached hashes from disk."""
        if self.cache_file.is_file():
            try:
                data = json.loads(self.cache_file.read_text(encoding="utf-8"))
                self._hashes = data.get("hashes", {})
                logger.debug("Loaded %d cached file hashes", len(self._hashes))
            except (json.JSONDecodeError, OSError) as e:
                logger.warning("Failed to load cache: %s", e)
                self._hashes = {}

    def save(self) -> None:
        """Save current hashes to disk."""
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        data = {"hashes": self._hashes}
        self.cache_file.write_text(json.dumps(data), encoding="utf-8")
        logger.debug("Saved %d file hashes to cache", len(self._hashes))

    def has_changed(self, file_path: Path) -> bool:
        """Check if a file has changed since last scan.

        Args:
            file_path: Path to check.

        Returns:
            True if the file is new or modified.
        """
        key = str(file_path.resolve())
        current_hash = self._hash_file(file_path)
        if current_hash is None:
            return True

        cached_hash = self._hashes.get(key)
        return cached_hash != current_hash

    def update(self, file_path: Path) -> None:
        """Update the cached hash for a file.

        Args:
            file_path: File to update hash for.
        """
        key = str(file_path.resolve())
        file_hash = self._hash_file(file_path)
        if file_hash is not None:
            self._hashes[key] = file_hash

    def clear(self) -> None:
        """Clear all cached hashes."""
        self._hashes = {}
        if self.cache_file.is_file():
            self.cache_file.unlink()

    @staticmethod
    def _hash_file(file_path: Path) -> str | None:
        """Compute SHA-256 hash of a file.

        Args:
            file_path: File to hash.

        Returns:
            Hex digest string or None if file can't be read.
        """
        try:
            h = hashlib.sha256()
            with open(file_path, "rb") as f:
                for chunk in iter(lambda: f.read(8192), b""):
                    h.update(chunk)
            return h.hexdigest()
        except OSError:
            return None
