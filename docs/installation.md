# Installation

## pip (recommended)

```bash
pip install ai-bom
```

## pipx (isolated install)

```bash
pipx install ai-bom
```

## From source

```bash
git clone https://github.com/trusera/ai-bom.git
cd ai-bom
pip install -e ".[dev]"
```

## Optional Dependencies

```bash
# All optional features
pip install ai-bom[all]

# Specific features
pip install ai-bom[dashboard]   # Web dashboard
pip install ai-bom[server]      # REST API server
pip install ai-bom[watch]       # File watch mode
pip install ai-bom[docs]        # Documentation building
pip install ai-bom[aws]         # AWS live scanning
pip install ai-bom[gcp]         # GCP live scanning
pip install ai-bom[azure]       # Azure live scanning
```

## Docker

```bash
docker pull ghcr.io/trusera/ai-bom:latest
docker run -v $(pwd):/scan ghcr.io/trusera/ai-bom scan /scan
```

## Verify Installation

```bash
ai-bom version
ai-bom list-scanners
```
