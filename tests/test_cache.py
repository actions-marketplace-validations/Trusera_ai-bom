"""Tests for incremental scanning cache (ScanCache)."""
from __future__ import annotations

from pathlib import Path

from ai_bom.cache import ScanCache


def test_cache_save_and_load(tmp_path: Path) -> None:
    """Cache should persist hashes to disk and reload them."""
    cache_dir = tmp_path / ".ai-bom-cache"

    # Create a test file and update the cache
    test_file = tmp_path / "hello.py"
    test_file.write_text("print('hello')")

    cache = ScanCache(cache_dir=cache_dir)
    cache.update(test_file)
    cache.save()

    # Reload from disk
    cache2 = ScanCache(cache_dir=cache_dir)
    assert not cache2.has_changed(test_file), "File should be unchanged after reload"


def test_has_changed_new_file(tmp_path: Path) -> None:
    """A file never seen before should be reported as changed."""
    cache_dir = tmp_path / ".ai-bom-cache"
    cache = ScanCache(cache_dir=cache_dir)

    new_file = tmp_path / "new.py"
    new_file.write_text("x = 1")

    assert cache.has_changed(new_file), "New (unknown) file should be reported as changed"


def test_has_changed_modified_file(tmp_path: Path) -> None:
    """Modifying a file after caching should flag it as changed."""
    cache_dir = tmp_path / ".ai-bom-cache"
    test_file = tmp_path / "mod.py"
    test_file.write_text("v1")

    cache = ScanCache(cache_dir=cache_dir)
    cache.update(test_file)
    cache.save()

    # Modify the file
    test_file.write_text("v2")

    cache2 = ScanCache(cache_dir=cache_dir)
    assert cache2.has_changed(test_file), "Modified file should be reported as changed"


def test_has_changed_unmodified_file(tmp_path: Path) -> None:
    """An unmodified file should NOT be reported as changed."""
    cache_dir = tmp_path / ".ai-bom-cache"
    test_file = tmp_path / "same.py"
    test_file.write_text("unchanged")

    cache = ScanCache(cache_dir=cache_dir)
    cache.update(test_file)
    cache.save()

    # Reload — same file, same content
    cache2 = ScanCache(cache_dir=cache_dir)
    assert not cache2.has_changed(test_file), "Unmodified file should not be changed"


def test_cache_clear(tmp_path: Path) -> None:
    """Clearing the cache should remove all stored hashes."""
    cache_dir = tmp_path / ".ai-bom-cache"
    test_file = tmp_path / "clear.py"
    test_file.write_text("data")

    cache = ScanCache(cache_dir=cache_dir)
    cache.update(test_file)
    cache.save()

    # Ensure the cache file exists
    assert (cache_dir / "file_hashes.json").is_file()

    cache.clear()

    # After clear, the file should be reported as changed (no cached hash)
    assert cache.has_changed(test_file), "After clear, file should be reported as changed"
    # Cache file should be removed
    assert not (cache_dir / "file_hashes.json").is_file()


def test_cache_nonexistent_file(tmp_path: Path) -> None:
    """Hashing a non-existent file should report it as changed."""
    cache_dir = tmp_path / ".ai-bom-cache"
    cache = ScanCache(cache_dir=cache_dir)
    ghost = tmp_path / "ghost.py"

    assert cache.has_changed(ghost), "Non-existent file should be reported as changed"
