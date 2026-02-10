# CI/CD Integration

## GitHub Actions

```yaml
name: AI-BOM Scan
on: [push, pull_request]

permissions:
  security-events: write
  contents: read

jobs:
  ai-bom:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: trusera/ai-bom@v2
        with:
          format: sarif
          fail-on: high
```

## GitLab CI

```yaml
ai-bom-scan:
  image: ghcr.io/trusera/ai-bom:latest
  script:
    - ai-bom scan . --format sarif -o ai-bom.sarif --quiet
  artifacts:
    reports:
      sast: ai-bom.sarif
```

## Policy Enforcement

```bash
# Fail if any critical findings
ai-bom scan . --fail-on critical --quiet

# Use a policy file
ai-bom scan . --policy policy.yml --quiet
```
