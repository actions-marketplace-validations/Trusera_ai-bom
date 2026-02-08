# Security Policy

## Supported Versions

| Version | Supported          |
|---------|--------------------|
| 0.1.x   | :white_check_mark: |

## Reporting a Vulnerability

If you discover a security vulnerability in ai-bom, please report it responsibly.

**Do NOT open a public issue.**

Instead, please email **security@trusera.dev** with:

1. A description of the vulnerability
2. Steps to reproduce
3. Potential impact
4. Suggested fix (if any)

### Response Timeline

| Severity | Acknowledgement | Fix Target |
|----------|-----------------|------------|
| Critical | Within 24 hours | 3 days     |
| High     | Within 48 hours | 7 days     |
| Medium   | Within 72 hours | 14 days    |
| Low      | Within 1 week   | Next release |

If the primary contact is unavailable, please CC **info@trusera.dev** as a backup.

### Security Advisory Process

For confirmed vulnerabilities:
1. We will open a private GitHub Security Advisory
2. Coordinate a fix in a private fork
3. Publish the advisory alongside the patched release
4. Credit the reporter (unless anonymity is requested)

## Scope

ai-bom is a static analysis tool that reads files. It does not:
- Execute scanned code
- Send data to external services
- Require network access (except for git clone)

Security concerns most relevant to ai-bom include:
- Path traversal in file scanning
- Sensitive data exposure in scan output (API keys are masked)
- Dependency vulnerabilities
- Symlink following in file traversal
