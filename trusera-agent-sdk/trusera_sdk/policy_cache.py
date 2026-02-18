"""
Background-refreshing Cedar policy cache for the Trusera interceptor.

Fetches Cedar policy DSL from ``GET /api/v1/policies/cedar``, builds a
:class:`~trusera_sdk.cedar.CedarEvaluator` locally, and swaps it in
under a lock so that :meth:`evaluate_request` is always <1 ms.
"""

from __future__ import annotations

import hashlib
import logging
import threading
import time
from typing import Any

from .cedar import CedarEvaluator, EvaluationResult, PolicyDecision, parse_policy

logger = logging.getLogger(__name__)

_DEFAULT_TTL = 60  # seconds between refreshes
_DEFAULT_STALE_TTL = 300  # serve stale data for this long when API is unreachable


class PolicyCache:
    """Thread-safe policy cache with background refresh.

    The cache periodically fetches Cedar policies from the Trusera API
    and rebuilds a local :class:`CedarEvaluator`.  Between refreshes
    all evaluations are purely local (sub-millisecond).

    If the API becomes unreachable the cache continues to serve stale
    policies for *stale_ttl* seconds, then falls open (allow-all).
    """

    def __init__(
        self,
        client: Any | None = None,
        refresh_interval: float = _DEFAULT_TTL,
        stale_ttl: float = _DEFAULT_STALE_TTL,
    ) -> None:
        """
        Args:
            client: :class:`~trusera_sdk.client.TruseraClient` used to
                    fetch policies.  If ``None`` the cache stays empty
                    (allow-all).
            refresh_interval: Seconds between background refresh attempts.
            stale_ttl: How long to serve stale policies when the API is
                       unreachable.
        """
        self._client = client
        self._refresh_interval = refresh_interval
        self._stale_ttl = stale_ttl

        self._evaluator: CedarEvaluator | None = None
        self._policy_hash: str = ""
        self._last_success: float = 0.0
        self._lock = threading.Lock()
        self._shutdown = threading.Event()

        # Kick off a background refresh thread
        if client is not None:
            self._refresh_once()  # eager first load
            self._thread = threading.Thread(target=self._refresh_loop, daemon=True)
            self._thread.start()
        else:
            self._thread = None

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def evaluate_request(
        self,
        url: str,
        method: str = "GET",
        headers: dict[str, str] | None = None,
    ) -> EvaluationResult:
        """Evaluate an HTTP request against cached policies (<1 ms)."""
        with self._lock:
            evaluator = self._evaluator

        if evaluator is None:
            # No policies loaded -> fail open
            return EvaluationResult(
                decision=PolicyDecision.ALLOW,
                reason="No policies loaded (fail-open)",
            )

        # Check staleness
        if self._stale_ttl and self._last_success:
            age = time.time() - self._last_success
            if age > self._stale_ttl:
                logger.warning("Policy cache stale for %.0fs, failing open", age)
                return EvaluationResult(
                    decision=PolicyDecision.ALLOW,
                    reason=f"Policy cache stale ({age:.0f}s > {self._stale_ttl:.0f}s), fail-open",
                )

        return evaluator.evaluate(url, method, headers)

    def evaluate_action(
        self,
        action_type: str,
        target: str,
        context: dict[str, Any] | None = None,
    ) -> EvaluationResult:
        """Evaluate a non-HTTP action (tool call, LLM call, etc.).

        This wraps the action as a synthetic URL so it can be evaluated
        by the same Cedar rules that target ``request.*`` fields::

            action://tool_call/search_web

        The *context* dict is exposed as query parameters for
        ``request.url contains ...`` style rules.
        """
        synthetic_url = f"action://{action_type}/{target}"
        return self.evaluate_request(synthetic_url, method=action_type.upper())

    def invalidate(self) -> None:
        """Force an immediate refresh on the next check."""
        self._policy_hash = ""
        self._refresh_once()

    def stop(self) -> None:
        """Stop the background refresh thread."""
        self._shutdown.set()
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=self._refresh_interval + 1)

    # ------------------------------------------------------------------
    # Background refresh
    # ------------------------------------------------------------------

    def _refresh_loop(self) -> None:
        while not self._shutdown.is_set():
            self._shutdown.wait(self._refresh_interval)
            if not self._shutdown.is_set():
                self._refresh_once()

    def _refresh_once(self) -> None:
        if not self._client:
            return
        try:
            # Use the client's internal httpx client to fetch policies
            http = self._client._client  # httpx.Client instance
            url = f"{self._client.base_url}/api/v1/policies/cedar"
            resp = http.get(url)
            resp.raise_for_status()
            data = resp.json()

            policies = data.get("policies", [])
            # Concatenate all enabled policy DSL
            dsl_parts: list[str] = []
            for p in policies:
                if p.get("enabled", True):
                    dsl_parts.append(p.get("cedar_dsl", ""))
            combined_dsl = "\n".join(dsl_parts)

            # Hash-based change detection
            new_hash = hashlib.sha256(combined_dsl.encode()).hexdigest()
            if new_hash == self._policy_hash:
                self._last_success = time.time()
                return

            rules = parse_policy(combined_dsl)
            new_evaluator = CedarEvaluator(rules)

            with self._lock:
                self._evaluator = new_evaluator
                self._policy_hash = new_hash
                self._last_success = time.time()

            logger.info("Policy cache refreshed (%d rules)", len(rules))

        except Exception as e:
            logger.warning("Policy cache refresh failed: %s", e)
