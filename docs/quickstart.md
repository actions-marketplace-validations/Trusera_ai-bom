# Quick Start

## Basic Scan

```bash
# Scan current directory
ai-bom scan .

# Scan a specific path
ai-bom scan /path/to/project

# Scan a git repository
ai-bom scan https://github.com/user/repo.git
```

## Output Formats

```bash
# CycloneDX SBOM
ai-bom scan . --format cyclonedx -o ai-bom.cdx.json

# SARIF for GitHub Code Scanning
ai-bom scan . --format sarif -o results.sarif

# CSV for spreadsheet
ai-bom scan . --format csv -o components.csv

# HTML report
ai-bom scan . --format html -o report.html
```

## Filtering

```bash
# Only show high+ severity
ai-bom scan . --severity high

# Fail CI if critical findings
ai-bom scan . --fail-on critical --quiet
```

## Verbose Mode

```bash
# Show scanner details and timing
ai-bom scan . --verbose

# Full debug output
ai-bom scan . --debug
```

## CI/CD Integration

```yaml
# GitHub Actions
- uses: trusera/ai-bom@v2
  with:
    format: sarif
    fail-on: high
```

## Demo

```bash
ai-bom demo
```
