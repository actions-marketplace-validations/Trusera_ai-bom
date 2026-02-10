"""Test suite for scan reliability hardening features."""

from __future__ import annotations

import os
import tempfile
from pathlib import Path

import pytest

from ai_bom.scanners.base import BaseScanner


class TestScanner(BaseScanner):
    """Concrete test scanner for testing base functionality."""

    name = "test_scanner"
    description = "Scanner for testing"

    def supports(self, path: Path) -> bool:
        """Test scanner supports all paths."""
        return True

    def scan(self, path: Path) -> list:
        """Test scanner returns empty list."""
        return []


@pytest.fixture
def scanner():
    """Create a test scanner instance."""
    return TestScanner()


@pytest.fixture
def temp_dir():
    """Create a temporary directory for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


class TestBinaryFileDetection:
    """Test that binary files with null bytes are skipped."""

    def test_binary_file_skipped(self, scanner, temp_dir):
        """Binary file with null bytes should be skipped."""
        binary_file = temp_dir / "binary.dat"
        binary_file.write_bytes(b"some text\x00\x00\x00more binary data")

        files = list(scanner.iter_files(temp_dir))
        assert binary_file not in files

    def test_text_file_included(self, scanner, temp_dir):
        """Text file without null bytes should be included."""
        text_file = temp_dir / "text.txt"
        text_file.write_text("This is plain text without null bytes")

        files = list(scanner.iter_files(temp_dir))
        assert text_file in files

    def test_binary_in_first_8kb(self, scanner, temp_dir):
        """File with null byte in first 8KB should be skipped."""
        binary_file = temp_dir / "binary.bin"
        # Create 4KB of text, then a null byte
        content = b"a" * 4096 + b"\x00" + b"b" * 4096
        binary_file.write_bytes(content)

        files = list(scanner.iter_files(temp_dir))
        assert binary_file not in files


class TestLargeFileGuard:
    """Test that files larger than 10MB are skipped with warning."""

    def test_small_file_included(self, scanner, temp_dir):
        """File under 10MB should be included."""
        small_file = temp_dir / "small.txt"
        small_file.write_text("Small file content")

        files = list(scanner.iter_files(temp_dir))
        assert small_file in files

    def test_large_file_skipped(self, scanner, temp_dir, caplog):
        """File over 10MB should be skipped with warning."""
        large_file = temp_dir / "large.txt"
        # Create a file slightly over 10MB
        with open(large_file, "wb") as f:
            f.write(b"x" * (10 * 1024 * 1024 + 1))

        files = list(scanner.iter_files(temp_dir))
        assert large_file not in files
        assert "Skipping large file (>10MB)" in caplog.text

    def test_exactly_10mb_included(self, scanner, temp_dir):
        """File exactly 10MB should be included."""
        file_10mb = temp_dir / "exact_10mb.txt"
        with open(file_10mb, "wb") as f:
            f.write(b"x" * (10 * 1024 * 1024))

        files = list(scanner.iter_files(temp_dir))
        assert file_10mb in files


class TestSymlinkSafety:
    """Test symlink cycle detection and boundary checking."""

    def test_symlink_cycle_detected(self, scanner, temp_dir, caplog):
        """Symlink creating a cycle should be detected and skipped."""
        subdir = temp_dir / "subdir"
        subdir.mkdir()

        # Create a symlink that points back to parent
        cycle_link = subdir / "cycle"
        cycle_link.symlink_to(temp_dir)

        # Create a file in subdir to ensure we try to walk it
        test_file = subdir / "test.txt"
        test_file.write_text("test")

        files = list(scanner.iter_files(temp_dir))

        # Should include the test file but detect the cycle
        assert test_file in files
        assert "symlink cycle" in caplog.text.lower() or len(files) == 1

    def test_symlink_outside_root_skipped(self, scanner, temp_dir, caplog):
        """Symlink pointing outside root directory should be skipped."""
        # Create a separate temp directory outside our root
        with tempfile.TemporaryDirectory() as outside_dir:
            outside_file = Path(outside_dir) / "outside.txt"
            outside_file.write_text("outside content")

            # Create symlink to outside directory
            link = temp_dir / "outside_link"
            link.symlink_to(outside_dir)

            files = list(scanner.iter_files(temp_dir))

            # Files from outside should not be included
            assert not any("outside.txt" in str(f) for f in files)
            assert "outside root" in caplog.text.lower()

    def test_valid_symlink_included(self, scanner, temp_dir):
        """Valid symlink within root should be followed."""
        # Create a file
        target_file = temp_dir / "target.txt"
        target_file.write_text("target content")

        # Create a subdirectory with a symlink to the file
        subdir = temp_dir / "subdir"
        subdir.mkdir()
        link = subdir / "link.txt"
        link.symlink_to(target_file)

        files = list(scanner.iter_files(temp_dir))

        # Should find the file (may be found twice if symlink is followed)
        assert target_file in files


class TestPermissionHandling:
    """Test handling of permission denied errors."""

    @pytest.mark.skipif(os.name == "nt", reason="Unix-specific permission test")
    def test_permission_denied_file(self, scanner, temp_dir, caplog):
        """File with no read permission should be skipped with warning."""
        no_perm_file = temp_dir / "no_permission.txt"
        no_perm_file.write_text("content")
        no_perm_file.chmod(0o000)

        try:
            files = list(scanner.iter_files(temp_dir))
            assert no_perm_file not in files
            assert "permission denied" in caplog.text.lower()
        finally:
            # Restore permissions for cleanup
            no_perm_file.chmod(0o644)

    @pytest.mark.skipif(os.name == "nt", reason="Unix-specific permission test")
    def test_permission_denied_directory(self, scanner, temp_dir, caplog):
        """Directory with no read permission should be skipped with warning."""
        no_perm_dir = temp_dir / "no_perm_dir"
        no_perm_dir.mkdir()

        # Add a file inside before removing permissions
        test_file = no_perm_dir / "test.txt"
        test_file.write_text("test")

        # Remove read permission
        no_perm_dir.chmod(0o000)

        try:
            files = list(scanner.iter_files(temp_dir))
            assert test_file not in files
        finally:
            # Restore permissions for cleanup
            no_perm_dir.chmod(0o755)


class TestEncodingFallback:
    """Test safe_read_text encoding fallback chain."""

    def test_utf8_success(self, scanner, temp_dir):
        """UTF-8 file should be read successfully."""
        utf8_file = temp_dir / "utf8.txt"
        utf8_file.write_text("Hello 世界 🌍", encoding="utf-8")

        content = scanner.safe_read_text(utf8_file)
        assert content is not None
        assert "Hello 世界 🌍" in content

    def test_latin1_fallback(self, scanner, temp_dir):
        """File with latin-1 encoding should fall back successfully."""
        latin1_file = temp_dir / "latin1.txt"
        # Write content that's valid latin-1 but not valid UTF-8
        latin1_file.write_bytes(b"Hello \xe9\xe8\xe0")  # Latin-1 accented chars

        content = scanner.safe_read_text(latin1_file)
        assert content is not None
        assert len(content) > 0

    def test_binary_file_returns_none(self, scanner, temp_dir):
        """Binary file with null bytes should return None."""
        binary_file = temp_dir / "binary.bin"
        binary_file.write_bytes(b"text\x00binary\x00data")

        content = scanner.safe_read_text(binary_file)
        assert content is None

    def test_unreadable_file_returns_none(self, scanner, temp_dir):
        """File that cannot be read should return None."""
        nonexistent = temp_dir / "does_not_exist.txt"

        content = scanner.safe_read_text(nonexistent)
        assert content is None


class TestPycFileExclusion:
    """Test that .pyc files are excluded."""

    def test_pyc_file_skipped(self, scanner, temp_dir):
        """Compiled Python .pyc files should be skipped."""
        pyc_file = temp_dir / "module.pyc"
        pyc_file.write_bytes(b"fake compiled python")

        files = list(scanner.iter_files(temp_dir))
        assert pyc_file not in files

    def test_py_file_included(self, scanner, temp_dir):
        """Regular .py files should be included."""
        py_file = temp_dir / "module.py"
        py_file.write_text("print('hello')")

        files = list(scanner.iter_files(temp_dir))
        assert py_file in files

    def test_pyc_in_pycache_skipped(self, scanner, temp_dir):
        """PyC files in __pycache__ should be skipped via directory exclusion."""
        pycache = temp_dir / "__pycache__"
        pycache.mkdir()
        pyc_file = pycache / "module.cpython-312.pyc"
        pyc_file.write_bytes(b"fake compiled")

        files = list(scanner.iter_files(temp_dir))
        # Should not find files in __pycache__ at all
        assert not any("__pycache__" in str(f) for f in files)


class TestSingleFileMode:
    """Test iter_files with single file path instead of directory."""

    def test_single_file_matched(self, scanner, temp_dir):
        """Single file path should be yielded if it matches criteria."""
        single_file = temp_dir / "single.txt"
        single_file.write_text("single file content")

        files = list(scanner.iter_files(single_file))
        assert single_file in files
        assert len(files) == 1

    def test_single_large_file_skipped(self, scanner, temp_dir, caplog):
        """Single large file should be skipped."""
        large_file = temp_dir / "large.txt"
        with open(large_file, "wb") as f:
            f.write(b"x" * (10 * 1024 * 1024 + 1))

        files = list(scanner.iter_files(large_file))
        assert len(files) == 0
        assert "Skipping large file" in caplog.text

    def test_single_binary_file_skipped(self, scanner, temp_dir):
        """Single binary file should be skipped."""
        binary_file = temp_dir / "binary.bin"
        binary_file.write_bytes(b"binary\x00data")

        files = list(scanner.iter_files(binary_file))
        assert len(files) == 0

    def test_single_pyc_file_skipped(self, scanner, temp_dir):
        """Single .pyc file should be skipped."""
        pyc_file = temp_dir / "module.pyc"
        pyc_file.write_bytes(b"fake compiled")

        files = list(scanner.iter_files(pyc_file))
        assert len(files) == 0


class TestExcludedDirectories:
    """Test that excluded directories are properly skipped."""

    def test_git_directory_excluded(self, scanner, temp_dir):
        """Files in .git directory should be excluded."""
        git_dir = temp_dir / ".git"
        git_dir.mkdir()
        git_file = git_dir / "config"
        git_file.write_text("git config")

        files = list(scanner.iter_files(temp_dir))
        assert git_file not in files

    def test_node_modules_excluded(self, scanner, temp_dir):
        """Files in node_modules should be excluded."""
        nm_dir = temp_dir / "node_modules"
        nm_dir.mkdir()
        package = nm_dir / "package.json"
        package.write_text("{}")

        files = list(scanner.iter_files(temp_dir))
        assert package not in files

    def test_venv_excluded(self, scanner, temp_dir):
        """Files in venv/.venv should be excluded."""
        venv_dir = temp_dir / ".venv"
        venv_dir.mkdir()
        lib_file = venv_dir / "lib.py"
        lib_file.write_text("import sys")

        files = list(scanner.iter_files(temp_dir))
        assert lib_file not in files
