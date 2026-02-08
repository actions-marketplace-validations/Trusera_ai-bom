"""Base scanner class with auto-registration for AI-BOM scanner framework."""

from __future__ import annotations

import os
from abc import ABC, abstractmethod
from collections.abc import Iterator
from pathlib import Path

from ai_bom.config import EXCLUDED_DIRS
from ai_bom.models import AIComponent

# Global registry populated via __init_subclass__
_scanner_registry: list[type[BaseScanner]] = []


class BaseScanner(ABC):
    """Abstract base class for all scanners with automatic registration.

    Concrete scanners should:
    1. Set class attributes `name` and `description`
    2. Implement `supports()` to filter paths
    3. Implement `scan()` to detect AI components

    Auto-registration happens when the scanner class is defined (imported).
    """

    name: str = ""
    description: str = ""

    def __init_subclass__(cls, **kwargs: object) -> None:
        """Automatically register concrete scanner subclasses.

        Only registers classes that have a non-empty `name` attribute,
        ensuring abstract intermediate classes are not registered.

        Args:
            **kwargs: Forwarded to parent __init_subclass__
        """
        super().__init_subclass__(**kwargs)
        # Only register concrete classes with a name set
        if cls.name:
            _scanner_registry.append(cls)

    @abstractmethod
    def supports(self, path: Path) -> bool:
        """Check if this scanner should run on the given path.

        Args:
            path: Directory or file path to check

        Returns:
            True if this scanner can analyze the path, False otherwise
        """
        ...

    @abstractmethod
    def scan(self, path: Path) -> list[AIComponent]:
        """Scan the given path and return discovered AI components.

        Args:
            path: Directory or file path to scan

        Returns:
            List of detected AI components with metadata and risk assessments
        """
        ...

    def iter_files(
        self,
        root: Path,
        extensions: set[str] | None = None,
        filenames: set[str] | None = None,
        include_tests: bool = False,
    ) -> Iterator[Path]:
        """Walk directory tree yielding matching files with intelligent pruning.

        Automatically skips:
        - EXCLUDED_DIRS (node_modules, .git, __pycache__, etc.)
        - Test directories (test, tests, spec, specs) unless include_tests=True
        - Files larger than 1MB (binary or generated files)

        Args:
            root: Root directory to walk
            extensions: Set of file extensions to match (e.g., {".py", ".js"})
                       Extensions should include the dot prefix
            filenames: Set of exact filenames to match (e.g., {"Dockerfile", "requirements.txt"})
            include_tests: Whether to include test directories in the walk

        Yields:
            Path objects for files matching the criteria

        Examples:
            # Find all Python files
            for file in scanner.iter_files(root, extensions={".py"}):
                ...

            # Find Dockerfiles and docker-compose.yml files
            for file in scanner.iter_files(
                root,
                filenames={"Dockerfile", "docker-compose.yml"}
            ):
                ...
        """
        # Convert root to absolute path for consistency
        root = root.resolve()

        # Handle single file: yield it if it matches criteria, then return
        if root.is_file():
            # Skip files larger than 1MB to avoid binary/generated files
            try:
                if os.path.getsize(root) > 1_048_576:  # 1MB in bytes
                    return
            except OSError:
                return

            matches = False
            if extensions is not None and root.suffix.lower() in extensions:
                matches = True
            if filenames is not None and (root.name in filenames or root.name.lower() in filenames):
                matches = True
            if extensions is None and filenames is None:
                matches = True
            if matches:
                yield root
            return

        # Test directory names to exclude
        test_dirs = {"test", "tests", "spec", "specs"} if not include_tests else set()

        # Walk the directory tree
        for dirpath, dirnames, filenames_list in os.walk(root, topdown=True):
            # Prune excluded directories in-place (modifies dirnames)
            dirnames[:] = [
                d
                for d in dirnames
                if d not in EXCLUDED_DIRS and d not in test_dirs
            ]

            # Check each file in current directory
            for filename in filenames_list:
                file_path = Path(dirpath) / filename

                # Skip files larger than 1MB to avoid binary/generated files
                try:
                    if os.path.getsize(file_path) > 1_048_576:  # 1MB in bytes
                        continue
                except OSError:
                    # File might not exist or be inaccessible
                    continue

                # Match by extension or exact filename
                matches = False

                if extensions is not None:
                    file_ext = file_path.suffix.lower()
                    if file_ext in extensions:
                        matches = True

                if filenames is not None:
                    if filename in filenames or filename.lower() in filenames:
                        matches = True

                # If no filters specified, match all files
                if extensions is None and filenames is None:
                    matches = True

                if matches:
                    yield file_path


def get_all_scanners() -> list[BaseScanner]:
    """Instantiate and return all registered scanners.

    Returns:
        List of scanner instances ready to use for scanning

    Note:
        Scanner registration happens automatically when scanner
        modules are imported via __init_subclass__
    """
    return [scanner_cls() for scanner_cls in _scanner_registry]
