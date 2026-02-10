# AI-BOM: AI Bill of Materials

**Discover and inventory all AI/LLM agents, models, and API integrations across your infrastructure.**

AI-BOM is a security scanner that creates a comprehensive inventory of AI components in your codebase, similar to how an SBOM (Software Bill of Materials) inventories software dependencies.

## What It Detects

- **AI SDK imports** — OpenAI, Anthropic, LangChain, HuggingFace, and 50+ more
- **Model references** — GPT-4, Claude, Gemini, Llama, and version pinning issues
- **API keys** — Hardcoded credentials for AI services
- **Docker/K8s AI services** — Ollama, vLLM, vector databases
- **Cloud AI services** — AWS Bedrock, GCP Vertex AI, Azure OpenAI (via Terraform/CloudFormation)
- **n8n AI workflows** — LangChain agents, LLM nodes, MCP tools
- **Jupyter notebooks** — AI imports and model loading in notebooks
- **GitHub Actions** — AI-powered actions and API key env vars
- **MCP servers** — Model Context Protocol server configurations
- **Binary model files** — .onnx, .pt, .safetensors, .gguf, and more

## Quick Start

```bash
pip install ai-bom
ai-bom scan .
```

## Output Formats

AI-BOM supports 9 output formats:

| Format | Flag | Use Case |
|--------|------|----------|
| Table | `--format table` | Terminal display (default) |
| CycloneDX | `--format cyclonedx` | SBOM standard |
| SARIF | `--format sarif` | GitHub Code Scanning |
| SPDX 3.0 | `--format spdx3` | SBOM standard |
| HTML | `--format html` | Shareable reports |
| CSV | `--format csv` | Spreadsheet import |
| JUnit | `--format junit` | CI/CD integration |
| Markdown | `--format markdown` | Documentation |
| JSON | `--format json` | API integration |
