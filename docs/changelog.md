# Changelog

## v3.0.0 (Unreleased)

### New Scanners
- GitHub Actions scanner — detect AI-powered actions and API key env vars
- Jupyter Notebook scanner — detect AI imports in .ipynb files
- Binary Model File scanner — detect .onnx, .pt, .safetensors, etc.
- MCP Config scanner — detect MCP server declarations

### New Output Formats
- CSV reporter for spreadsheet analysis
- JUnit XML reporter for CI/CD integration

### New Features
- `--verbose/-v` flag for scanner details and timing
- `--debug` flag for full stack traces
- `.ai-bomignore` file support (gitignore syntax)
- `.ai-bom.yml` configuration file support
- `ai-bom list-scanners` command
- `ai-bom diff` command to compare two scans
- `ai-bom serve` REST API server mode
- OWASP Agentic Top 10 compliance mapping
- EU AI Act compliance checker
- License compliance checking
- Incremental scanning with `--cache`
- Watch mode with `ai-bom watch`
- Multi-stage Docker image
- Expanded dependency parsing (Cargo.toml, go.mod, Gemfile, build.gradle, pom.xml, .csproj)
- Enhanced API key detection (Fireworks, Perplexity, DeepSeek, Together AI)

### Improvements
- Multi-stage Dockerfile for smaller images
- Parallel CI with separate lint, typecheck, test, security jobs
- mypy type checking in CI
- pip-audit security scanning in CI
- Coverage threshold enforcement (80%)
- Encoding fallback chain in file scanning
- Symlink cycle detection
- Binary file detection
- Large file guard (>10MB)
- PermissionError handling
- Pre-commit hooks configuration
- MkDocs documentation site

## v2.0.0

- 9 scanners, 7 reporters
- XSS fix in HTML reporter
- 313+ tests
- SPDX 3.0 support
- Policy enforcement
