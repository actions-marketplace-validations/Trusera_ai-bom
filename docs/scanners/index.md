# Scanners

AI-BOM includes 13 scanners that detect AI components across different technologies.

| Scanner | Description | File Types |
|---------|-------------|------------|
| `code` | AI SDK imports and usage | .py, .js, .ts, .java, .go, .rs |
| `docker` | AI containers and services | Dockerfile, docker-compose.yml |
| `network` | AI endpoints and credentials | .env, .yaml, .json, .toml |
| `cloud` | Cloud AI services (IaC) | .tf, .json, .yaml |
| `n8n` | n8n workflow AI nodes | .json (n8n exports) |
| `jupyter` | Jupyter notebook AI usage | .ipynb |
| `github-actions` | AI-powered GitHub Actions | .github/workflows/*.yml |
| `model-files` | Binary model files | .onnx, .pt, .safetensors, etc. |
| `mcp-config` | MCP server configs | mcp.json, claude_desktop_config.json |
| `ast` | Deep Python AST analysis | .py (requires --deep) |
| `aws-live` | Live AWS account scan | (API calls) |
| `gcp-live` | Live GCP project scan | (API calls) |
| `azure-live` | Live Azure subscription scan | (API calls) |

## List Available Scanners

```bash
ai-bom list-scanners
```
