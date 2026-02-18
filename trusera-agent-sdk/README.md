# Trusera Python SDK

[![PyPI version](https://badge.fury.io/py/trusera-sdk.svg)](https://badge.fury.io/py/trusera-sdk)
[![Python versions](https://img.shields.io/pypi/pyversions/trusera-sdk.svg)](https://pypi.org/project/trusera-sdk/)
[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)

Python SDK for monitoring **and intercepting** AI agent actions with [Trusera](https://trusera.dev). Track LLM invocations, tool calls, data access, and enforce Cedar security policies before actions execute.

## Installation

```bash
pip install trusera-sdk
```

### Optional Dependencies

```bash
# Framework integrations
pip install trusera-sdk[langchain]
pip install trusera-sdk[crewai]
pip install trusera-sdk[autogen]

# LLM client wrappers
pip install trusera-sdk[openai]
pip install trusera-sdk[anthropic]

# Everything
pip install trusera-sdk[all]

# Development tools
pip install trusera-sdk[dev]
```

## Quick Start: Passive Monitoring

```python
from trusera_sdk import TruseraClient, Event, EventType

client = TruseraClient(api_key="tsk_your_api_key")
agent_id = client.register_agent(name="my-agent", framework="custom")

client.track(Event(
    type=EventType.TOOL_CALL,
    name="web_search",
    payload={"query": "latest AI news"},
))

client.close()
```

## Active Interception (v0.3.0+)

The SDK now supports **active interception** - evaluating agent actions against Cedar policies *before* they execute. Use `intercept()` for a one-liner setup, or `TruseraInterceptor` for full control.

### `intercept()` - One-Liner Setup

```python
import trusera_sdk

client = trusera_sdk.TruseraClient(api_key="tsk_...")
client.register_agent("my-agent", "custom")

# Intercept all HTTP calls (requests, httpx, urllib3)
interceptor = trusera_sdk.intercept(client, enforcement="block")

# Your agent code runs normally - policy violations raise PolicyViolationError
import requests
requests.get("https://allowed-api.com/data")  # OK
requests.get("https://blocked-api.com/data")  # Raises PolicyViolationError

interceptor.uninstall()
```

### `TruseraInterceptor` - Full Control

```python
from trusera_sdk import TruseraClient, TruseraInterceptor
from trusera_sdk.policy_cache import PolicyCache

client = TruseraClient(api_key="tsk_...")
cache = PolicyCache(client=client, refresh_interval=30)

with TruseraInterceptor(client=client, policy_cache=cache, enforcement="warn") as i:
    # All outbound HTTP is evaluated against Cedar policies
    # Warn mode logs violations but allows requests to proceed
    pass
```

### Enforcement Modes

| Mode | Behavior |
|------|----------|
| `block` | Raise `PolicyViolationError` and prevent the action |
| `warn` | Log a warning to stderr, allow the action |
| `log` | Silently record the violation, allow the action |

## Using the Decorator

```python
from trusera_sdk import TruseraClient, monitor, set_default_client, EventType

client = TruseraClient(api_key="tsk_your_api_key")
client.register_agent("my-agent", "custom")
set_default_client(client)

@monitor(event_type=EventType.TOOL_CALL)
def search_database(query: str) -> list[dict]:
    return [{"id": 1, "title": "Result"}]

@monitor(event_type=EventType.LLM_INVOKE, name="gpt4_call")
async def call_llm(prompt: str) -> str:
    return "AI response"
```

## Framework Integrations

### LangChain (Active Interception)

```python
from trusera_sdk import TruseraClient
from trusera_sdk.policy_cache import PolicyCache
from trusera_sdk.integrations.langchain_interceptor import TruseraLangChainInterceptor

client = TruseraClient(api_key="tsk_...")
cache = PolicyCache(client=client)

with TruseraLangChainInterceptor(client=client, policy_cache=cache, enforcement="block"):
    # BaseTool._run and BaseLLM._generate are now policy-checked
    agent.run("Your query here")
```

### LangChain (Passive Monitoring)

```python
from trusera_sdk.integrations.langchain import TruseraCallbackHandler

handler = TruseraCallbackHandler(client)
llm = OpenAI(callbacks=[handler])
```

### CrewAI (Active Interception)

```python
from trusera_sdk.integrations.crewai_interceptor import TruseraCrewAIInterceptor

with TruseraCrewAIInterceptor(client=client, policy_cache=cache, enforcement="warn"):
    crew.kickoff()
```

### AutoGen (Active Interception)

```python
from trusera_sdk.integrations.autogen_interceptor import TruseraAutoGenInterceptor

interceptor = TruseraAutoGenInterceptor(client=client, policy_cache=cache, enforcement="block")
interceptor.install()

# Optionally wrap individual agent functions
interceptor.intercept_agent(my_agent)
```

### OpenAI / Anthropic (LLM Interceptor)

```python
from openai import OpenAI
from trusera_sdk.integrations.llm_interceptor import TruseraLLMInterceptor

llm_interceptor = TruseraLLMInterceptor(
    client=trusera_client,
    policy_cache=cache,
    enforcement="warn",
    redact_pii=True,  # Redact emails, phones, SSNs from logged prompts
)

openai_client = OpenAI()
llm_interceptor.wrap_openai(openai_client)

# Tool-use calls in responses are now policy-checked
# PII is redacted from logged prompts (never from actual API calls)
```

## Policy Cache

The `PolicyCache` fetches Cedar policies from the Trusera API and evaluates them locally (<1ms). It runs a background thread to keep policies fresh.

```python
from trusera_sdk.policy_cache import PolicyCache

cache = PolicyCache(
    client=trusera_client,
    refresh_interval=60,   # Seconds between refreshes (default: 60)
    stale_ttl=300,         # Serve stale policies for this long when API is down (default: 300)
)

# Manual cache invalidation (e.g. on webhook)
cache.invalidate()

# Clean shutdown
cache.stop()
```

## PII Redaction

```python
from trusera_sdk import PIIRedactor

redactor = PIIRedactor()
redactor.redact_text("Email: john@example.com")
# => "Email: [REDACTED_EMAIL]"

redactor.redact({"user": "john@example.com", "age": 30})
# => {"user": "[REDACTED_EMAIL]", "age": 30}
```

## Event Types

- `EventType.TOOL_CALL` - Tool or function invocations
- `EventType.LLM_INVOKE` - LLM API calls
- `EventType.DATA_ACCESS` - Database queries, file reads
- `EventType.API_CALL` - External API requests
- `EventType.FILE_WRITE` - File system modifications
- `EventType.DECISION` - Agent decision points
- `EventType.POLICY_VIOLATION` - Cedar policy violations (new in 0.3.0)
- `EventType.INTERCEPTION` - Intercepted HTTP requests (new in 0.3.0)

## Migration from v0.2 to v0.3

v0.3.0 is fully backward compatible. All existing `monitor()`, `TruseraClient`, and `StandaloneInterceptor` APIs work unchanged.

**New in v0.3.0:**
- `TruseraInterceptor` - Multi-library HTTP interceptor (requests + httpx + urllib3)
- `intercept()` - One-liner convenience function
- `PolicyCache` - Background-refreshing policy cache
- `PolicyViolationError` - Typed exception for blocked actions
- `EnforcementMode` - Enum for block/warn/log
- `PIIRedactor` - PII detection and redaction
- Framework interceptors: LangChain, CrewAI, AutoGen, OpenAI/Anthropic
- New event types: `POLICY_VIOLATION`, `INTERCEPTION`

## Configuration

```python
client = TruseraClient(
    api_key="tsk_your_api_key",
    base_url="https://api.trusera.dev",
    flush_interval=5.0,
    batch_size=100,
    timeout=10.0,
)
```

## Development

```bash
git clone https://github.com/Trusera/ai-bom.git
cd ai-bom/trusera-agent-sdk
pip install -e ".[dev]"
pytest
ruff check .
```

## Documentation

Full documentation at [docs.trusera.dev/sdk/python](https://docs.trusera.dev/sdk/python)

## Support

- Website: [trusera.dev](https://trusera.dev)
- Documentation: [docs.trusera.dev](https://docs.trusera.dev)
- Issues: [GitHub Issues](https://github.com/Trusera/ai-bom/issues)
- Email: dev@trusera.dev

## License

Apache License 2.0 - see [LICENSE](LICENSE) file for details.
