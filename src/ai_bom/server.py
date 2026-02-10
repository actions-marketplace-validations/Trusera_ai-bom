"""REST API server for AI-BOM scanning.

Provides HTTP endpoints for scanning directories and retrieving results.
Start with: ai-bom serve --port 8080
"""

from __future__ import annotations

import time
from pathlib import Path
from typing import Any

from ai_bom import __version__
from ai_bom.models import ScanResult
from ai_bom.scanners import get_all_scanners
from ai_bom.utils.risk_scorer import score_component


def create_server_app() -> Any:
    """Create and configure the FastAPI server application.

    Returns:
        FastAPI application instance.
    """
    try:
        from fastapi import FastAPI, HTTPException
        from fastapi.middleware.cors import CORSMiddleware
        from pydantic import BaseModel
    except ImportError as e:
        raise ImportError(
            "Server dependencies not installed. "
            "Install with: pip install ai-bom[server]"
        ) from e

    app = FastAPI(
        title="AI-BOM API",
        description="AI Bill of Materials — REST API for scanning AI/LLM components",
        version=__version__,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["GET", "POST"],
        allow_headers=["*"],
    )

    class ScanRequest(BaseModel):
        path: str = "."
        deep: bool = False
        severity: str | None = None

    class HealthResponse(BaseModel):
        status: str = "ok"
        version: str = __version__

    class VersionResponse(BaseModel):
        version: str = __version__
        name: str = "ai-bom"

    @app.get("/health", response_model=HealthResponse)
    async def health() -> HealthResponse:
        """Health check endpoint."""
        return HealthResponse()

    @app.get("/version", response_model=VersionResponse)
    async def version() -> VersionResponse:
        """Version info endpoint."""
        return VersionResponse()

    @app.post("/scan")
    async def scan_endpoint(request: ScanRequest) -> dict:
        """Scan a directory path for AI/LLM components.

        Args:
            request: Scan request with path and options.

        Returns:
            Scan result as JSON dict.
        """
        scan_path = Path(request.path).resolve()
        if not scan_path.exists():
            raise HTTPException(status_code=404, detail=f"Path not found: {request.path}")

        result = ScanResult(target_path=str(scan_path))
        start_time = time.time()

        scanners = get_all_scanners()
        if request.deep:
            from ai_bom.scanners.ast_scanner import ASTScanner
            for s in scanners:
                if isinstance(s, ASTScanner):
                    s.enabled = True

        for scanner in scanners:
            if not scanner.supports(scan_path):
                continue
            try:
                components = scanner.scan(scan_path)
                for comp in components:
                    comp.risk = score_component(comp)
                result.components.extend(components)
            except Exception:
                pass

        result.summary.scan_duration_seconds = time.time() - start_time
        result.build_summary()

        # Apply severity filter if specified
        if request.severity:
            severity_order = {"critical": 4, "high": 3, "medium": 2, "low": 1}
            min_level = severity_order.get(request.severity.lower(), 0)
            result.components = [
                c for c in result.components
                if severity_order.get(c.risk.severity.value, 0) >= min_level
            ]
            result.build_summary()

        return result.model_dump(mode="json")

    @app.get("/scanners")
    async def list_scanners() -> list[dict]:
        """List all available scanners."""
        scanners = get_all_scanners()
        return [
            {
                "name": s.name,
                "description": s.description,
                "enabled": getattr(s, "enabled", True),
            }
            for s in scanners
        ]

    return app
