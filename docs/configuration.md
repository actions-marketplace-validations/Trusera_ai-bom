# Configuration

## Config File

AI-BOM supports a `.ai-bom.yml` configuration file in your project root.

```yaml
# .ai-bom.yml
format: table
severity: medium
verbose: true
exclude:
  - tests/fixtures/
  - vendor/
```

Specify a custom config path:

```bash
ai-bom scan . --config path/to/.ai-bom.yml
```

## .ai-bomignore

Create a `.ai-bomignore` file (gitignore syntax) to exclude paths:

```
# Skip test fixtures
tests/fixtures/
tests/test_data/

# Skip vendored code
vendor/
third_party/
```

## Environment Variables

| Variable | Description |
|----------|-------------|
| `AI_BOM_CONFIG` | Path to config file |
| `N8N_API_KEY` | n8n API key for live scanning |
