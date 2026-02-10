"""Tests for parallel scanner execution."""
from __future__ import annotations

from pathlib import Path

from ai_bom.models import AIComponent, ComponentType, SourceLocation, UsageType
from ai_bom.scanners import run_scanners_parallel
from ai_bom.scanners.base import BaseScanner

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_component(name: str = "test-comp") -> AIComponent:
    return AIComponent(
        name=name,
        type=ComponentType.llm_provider,
        provider="TestProvider",
        location=SourceLocation(file_path="test.py", line_number=1),
        usage_type=UsageType.completion,
        source="test",
    )


class _StubScanner(BaseScanner):
    """Non-registering stub scanner for tests."""

    # Empty name so __init_subclass__ does NOT add it to the global registry.
    name = ""
    description = "stub"

    def __init__(
        self,
        *,
        supported: bool = True,
        components: list | None = None,
        error: Exception | None = None,
    ):
        self.supported = supported
        self._components = components or []
        self._error = error

    def supports(self, path: Path) -> bool:
        return self.supported

    def scan(self, path: Path) -> list[AIComponent]:
        if self._error:
            raise self._error
        return self._components


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

def test_run_scanners_parallel_returns_list(tmp_path: Path) -> None:
    """Parallel scanning should return a flat list of AIComponent."""
    comp = _make_component("a")
    scanner = _StubScanner(components=[comp])
    result = run_scanners_parallel([scanner], tmp_path, workers=2)

    assert isinstance(result, list)
    assert len(result) == 1
    assert result[0].name == "a"


def test_parallel_handles_scanner_error(tmp_path: Path) -> None:
    """A scanner that raises should not crash others; results should still come back."""
    good_comp = _make_component("good")
    good_scanner = _StubScanner(components=[good_comp])
    bad_scanner = _StubScanner(error=RuntimeError("boom"))

    result = run_scanners_parallel([bad_scanner, good_scanner], tmp_path, workers=2)

    # The good scanner's component should still be present
    assert len(result) == 1
    assert result[0].name == "good"


def test_parallel_skips_unsupported(tmp_path: Path) -> None:
    """Scanners that don't support the path should be silently skipped."""
    unsupported = _StubScanner(supported=False, components=[_make_component("skip")])
    supported = _StubScanner(supported=True, components=[_make_component("keep")])

    result = run_scanners_parallel([unsupported, supported], tmp_path, workers=2)

    names = [c.name for c in result]
    assert "keep" in names
    assert "skip" not in names


def test_parallel_workers_count(tmp_path: Path) -> None:
    """Workers param should be forwarded (smoke test: runs without error)."""
    scanner = _StubScanner(components=[_make_component()])
    # 1 worker — effectively sequential but via the thread pool
    result = run_scanners_parallel([scanner], tmp_path, workers=1)
    assert len(result) == 1


def test_sequential_vs_parallel_same_results(tmp_path: Path) -> None:
    """Parallel and sequential runs should return the same components."""
    comps_a = [_make_component("a1"), _make_component("a2")]
    comps_b = [_make_component("b1")]
    scanner_a = _StubScanner(components=comps_a)
    scanner_b = _StubScanner(components=comps_b)

    # Sequential
    seq_results: list[AIComponent] = []
    for s in [scanner_a, scanner_b]:
        if s.supports(tmp_path):
            seq_results.extend(s.scan(tmp_path))

    # Parallel
    par_results = run_scanners_parallel([scanner_a, scanner_b], tmp_path, workers=2)

    seq_names = sorted(c.name for c in seq_results)
    par_names = sorted(c.name for c in par_results)
    assert seq_names == par_names


def test_parallel_empty_scanner_list(tmp_path: Path) -> None:
    """Empty scanner list should return empty results."""
    result = run_scanners_parallel([], tmp_path, workers=2)
    assert result == []
