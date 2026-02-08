# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.1.0] - 2026-02-08

### Added
- 5 scanners: code, docker, network, cloud (Terraform/CloudFormation), n8n workflows
- AI SDK detection for OpenAI, Anthropic, Google, Mistral, Cohere, HuggingFace, and more
- Model version pinning and deprecation checks
- Shadow AI detection (undeclared AI dependencies)
- Hardcoded API key detection
- n8n workflow agent chain analysis with MCP risk assessment
- 5 output formats: table, JSON/CycloneDX, HTML, Markdown, SARIF
- SARIF 2.1.0 output for GitHub Code Scanning integration
- Single-file and directory scanning
- Git repository URL scanning (auto-clone)
- Severity filtering (critical, high, medium, low)
- Risk scoring engine with multi-factor assessment
- GitHub Action for CI/CD integration (`trusera/ai-bom@v1`)
- Docker container distribution
- 124 tests with full coverage of scanners and reporters

[Unreleased]: https://github.com/trusera/ai-bom/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/trusera/ai-bom/releases/tag/v0.1.0
