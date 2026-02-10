# Stage 1: Build
FROM python:3.12-slim AS builder

WORKDIR /build
COPY pyproject.toml README.md ./
COPY src/ src/

RUN pip install --no-cache-dir build && \
    python -m build --wheel

# Stage 2: Runtime
FROM python:3.12-slim

LABEL org.opencontainers.image.source="https://github.com/trusera/ai-bom"
LABEL org.opencontainers.image.description="AI Bill of Materials — discover AI/LLM components"
LABEL org.opencontainers.image.licenses="Apache-2.0"

RUN groupadd -r aibom && useradd -r -g aibom -m aibom

WORKDIR /app

COPY --from=builder /build/dist/*.whl /tmp/
RUN pip install --no-cache-dir /tmp/*.whl && rm -rf /tmp/*.whl

USER aibom

ENTRYPOINT ["ai-bom"]
CMD ["scan", "--help"]
