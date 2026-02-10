# CLI Reference

## Commands

### `ai-bom scan`

Scan a directory or repository for AI/LLM components.

```
ai-bom scan [TARGET] [OPTIONS]
```

| Option | Description |
|--------|-------------|
| `TARGET` | Path, directory, or git URL (default: `.`) |
| `--format, -f` | Output format (default: `table`) |
| `--output, -o` | Output file path |
| `--deep` | Enable AST-based Python analysis |
| `--severity, -s` | Minimum severity filter |
| `--verbose, -v` | Show scanner details and timing |
| `--debug` | Enable debug logging |
| `--config` | Path to .ai-bom.yml config file |
| `--quiet, -q` | Suppress banner and progress |
| `--no-color` | Disable colored output |
| `--fail-on` | Exit code 1 if severity threshold met |
| `--policy` | Path to YAML policy file |
| `--save-dashboard` | Save results to dashboard DB |
| `--n8n-url` | n8n instance URL for live scanning |
| `--n8n-api-key` | n8n API key |
| `--n8n-local` | Scan local ~/.n8n/ directory |

### `ai-bom scan-cloud`

Scan a cloud provider for managed AI/ML services.

```
ai-bom scan-cloud <PROVIDER> [OPTIONS]
```

### `ai-bom diff`

Compare two scan results.

```
ai-bom diff <SCAN1> <SCAN2> [--format table|json|markdown]
```

### `ai-bom list-scanners`

List all registered scanners and their status.

### `ai-bom serve`

Start the REST API server.

```
ai-bom serve [--host 0.0.0.0] [--port 8080]
```

### `ai-bom dashboard`

Launch the web dashboard.

### `ai-bom demo`

Run a demo scan on the bundled example project.

### `ai-bom version`

Show AI-BOM version.
