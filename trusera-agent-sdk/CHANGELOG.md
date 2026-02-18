# Changelog

All notable changes to the Trusera Python SDK will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.3.0] - 2026-02-18

### Added
- **Active Interception**: `TruseraInterceptor` evaluates Cedar policies before HTTP requests execute
- **Multi-library support**: Patches `requests`, `httpx`, and `urllib3` transparently
- **`intercept()` convenience function**: One-liner to create and install an interceptor
- **`PolicyCache`**: Background-refreshing policy cache with stale fallback and hash-based change detection
- **`PolicyViolationError`**: Typed exception with `action`, `target`, `reason`, `policy_id` attributes
- **`EnforcementMode`**: Enum for `block`, `warn`, `log` enforcement modes
- **`PIIRedactor`**: Regex-based PII detection and redaction (email, phone, SSN, credit card, IPv4)
- **LangChain interceptor**: Patches `BaseTool._run/_arun` and `BaseLLM._generate` for policy enforcement
- **CrewAI interceptor**: Patches `crewai.tools.BaseTool._run` for policy enforcement
- **AutoGen interceptor**: Patches `ConversableAgent._execute_function` with AG2 compatibility
- **LLM interceptor**: Wraps OpenAI/Anthropic clients for policy enforcement and PII redaction on logged prompts
- New event types: `POLICY_VIOLATION`, `INTERCEPTION`
- Optional dependencies: `openai`, `anthropic`, `all` extras in pyproject.toml

### Changed
- Version bump to 0.3.0 (minor version for new interception capabilities)
- `client.py` User-Agent updated from `0.1.0` to `0.3.0`
- SDK description updated to include "intercepting"

### Fixed
- User-Agent version in `client.py` was hardcoded as `0.1.0`

## [0.2.2] - 2026-02-18

### Added
- **Cedar Policy Gate**: Client-side policy evaluation with `CedarEvaluator`
- **Standalone Interceptor**: `StandaloneInterceptor` works without API key for local-only monitoring

### Changed
- Version bump to 0.2.2 (aligns with PyPI release track)
- Repository URLs point to ai-bom monorepo

## [0.1.0] - 2026-02-13

### Added
- Initial release of the Trusera Python SDK
- Core `TruseraClient` for event tracking and API communication
- Event types: `TOOL_CALL`, `LLM_INVOKE`, `DATA_ACCESS`, `API_CALL`, `FILE_WRITE`, `DECISION`
- `@monitor` decorator for automatic function tracking
- Support for both sync and async functions
- Automatic batching and background flushing
- Context manager support for clean resource management
- LangChain integration with `TruseraCallbackHandler`
- CrewAI integration with `TruseraCrewCallback`
- AutoGen integration with `TruseraAutoGenHook`
- Comprehensive test suite with >90% coverage
- Type hints throughout the codebase
- Apache 2.0 license

### Framework Support
- LangChain Core >=0.1.0
- CrewAI >=0.1.0
- AutoGen >=0.2.0

### Development Tools
- pytest for testing
- pytest-asyncio for async test support
- ruff for linting
- mypy for type checking
- GitHub Actions for CI/CD

[0.3.0]: https://github.com/Trusera/ai-bom/compare/sdk-v0.2.2...sdk-v0.3.0
[0.2.2]: https://github.com/Trusera/ai-bom/compare/sdk-v0.1.0...sdk-v0.2.2
[0.1.0]: https://github.com/Trusera/ai-bom/releases/tag/v0.1.0
