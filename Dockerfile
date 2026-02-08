FROM python:3.12-slim

LABEL org.opencontainers.image.source="https://github.com/trusera/ai-bom"
LABEL org.opencontainers.image.description="AI Bill of Materials — discover AI/LLM components"
LABEL org.opencontainers.image.licenses="Apache-2.0"

WORKDIR /app

COPY . .
RUN pip install --no-cache-dir .

ENTRYPOINT ["ai-bom"]
CMD ["scan", "/scan"]
