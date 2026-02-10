# Architecture

## Overview

AI-BOM uses a plugin-based scanner architecture with automatic registration.

```
┌────────────┐     ┌──────────────┐     ┌────────────┐
│   CLI      │────▶│  Scanner     │────▶│  Reporter  │
│  (Typer)   │     │  Registry    │     │  Registry  │
└────────────┘     └──────────────┘     └────────────┘
                          │                    │
                   ┌──────┴──────┐      ┌──────┴──────┐
                   │  Scanners   │      │  Reporters  │
                   │  (13 total) │      │  (9 total)  │
                   └─────────────┘      └─────────────┘
```

## Scanner Registry

Scanners auto-register via Python's `__init_subclass__` mechanism:

```python
class BaseScanner(ABC):
    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        if cls.name:
            _scanner_registry.append(cls)
```

To add a new scanner:
1. Create a class extending `BaseScanner`
2. Set `name` and `description` class attributes
3. Implement `supports(path)` and `scan(path)` methods
4. Import the module in `scanners/__init__.py`

## Data Flow

1. **CLI** parses arguments and resolves target path
2. **Scanners** are instantiated from the registry
3. Each scanner runs `supports()` then `scan()` on the target
4. Results are `AIComponent` Pydantic models
5. **Risk Scorer** evaluates each component's flags
6. **Reporter** renders the final output

## Risk Scoring

Risk scoring is stateless — `score_component(component)` evaluates:
- Component flags (hardcoded_api_key, shadow_ai, etc.)
- Model deprecation status
- RISK_WEIGHTS mapping (0-100 scale)

Severity levels: critical (76-100), high (51-75), medium (26-50), low (0-25)

## File Structure

```
src/ai_bom/
├── cli.py              # Typer CLI application
├── models.py           # Pydantic v2 data models
├── config.py           # Detection patterns and config data
├── config_file.py      # .ai-bom.yml file loading
├── server.py           # FastAPI REST API
├── cache.py            # Incremental scanning cache
├── watcher.py          # File watch mode
├── policy.py           # Policy enforcement
├── scanners/
│   ├── base.py         # BaseScanner + auto-registration
│   ├── code_scanner.py
│   ├── docker_scanner.py
│   ├── network_scanner.py
│   ├── cloud_scanner.py
│   ├── n8n_scanner.py
│   ├── ast_scanner.py
│   ├── github_actions_scanner.py
│   ├── jupyter_scanner.py
│   ├── model_file_scanner.py
│   └── mcp_config_scanner.py
├── reporters/
│   ├── base.py         # BaseReporter
│   ├── cli_reporter.py
│   ├── cyclonedx.py
│   ├── sarif.py
│   ├── spdx3.py
│   ├── html_reporter.py
│   ├── markdown.py
│   ├── csv_reporter.py
│   ├── junit_reporter.py
│   └── diff_reporter.py
├── compliance/
│   ├── owasp_agentic.py
│   ├── eu_ai_act.py
│   └── licenses.py
├── detectors/
│   ├── llm_patterns.py
│   ├── endpoint_db.py
│   └── model_registry.py
└── utils/
    └── risk_scorer.py
```
