# StandaloneInterceptor - Local HTTP Monitoring

The `StandaloneInterceptor` provides HTTP request monitoring and policy enforcement **without requiring a Trusera API key or platform connection**. Perfect for local development, testing, air-gapped environments, and CI/CD pipelines.

## Features

- **No API Key Required**: Works completely offline
- **Cedar Policy Evaluation**: Enforce security policies on HTTP requests
- **Multiple Enforcement Modes**: `block`, `warn`, or `log`
- **Local JSONL Logging**: All events saved to a local file
- **Transparent Interception**: Automatically intercepts httpx requests
- **Context Manager Support**: Easy to use with `with` statements
- **Thread-Safe**: Safe for concurrent agents

## Quick Start

### Basic Usage (Logging Only)

```python
from trusera_sdk import StandaloneInterceptor
import httpx

# Create and install interceptor
with StandaloneInterceptor(
    enforcement="log",
    log_file="agent-events.jsonl"
) as interceptor:
    # All httpx requests are now intercepted and logged
    client = httpx.Client()
    response = client.get("https://api.example.com/data")

    # Check stats
    print(interceptor.get_stats())

# Events are logged to agent-events.jsonl
```

### With Cedar Policy (Block Mode)

```python
from trusera_sdk import StandaloneInterceptor, RequestBlockedError

# Create a policy file
policy = """
forbid (principal, action == Action::"http", resource)
when { request.hostname contains "deepseek.com" };

forbid (principal, action == Action::"http", resource)
when { request.method == "DELETE" };
"""

with open("policy.cedar", "w") as f:
    f.write(policy)

# Install interceptor with policy
with StandaloneInterceptor(
    policy_file="policy.cedar",
    enforcement="block",
    log_file="events.jsonl"
):
    client = httpx.Client()

    # This will raise RequestBlockedError
    try:
        client.get("https://api.deepseek.com/v1/chat")
    except RequestBlockedError as e:
        print(f"Blocked: {e}")
```

## API Reference

### StandaloneInterceptor

```python
StandaloneInterceptor(
    policy_file: str | None = None,
    enforcement: str = "log",
    log_file: str | None = None,
    exclude_patterns: list[str] | None = None,
    debug: bool = False
)
```

**Parameters:**

- `policy_file` (optional): Path to Cedar policy file. If not provided, all requests are allowed.
- `enforcement`: Enforcement mode - `"block"`, `"warn"`, or `"log"` (default: `"log"`)
  - `block`: Raises `RequestBlockedError` for policy violations
  - `warn`: Prints warnings to stderr but allows requests
  - `log`: Silently logs violations but allows requests
- `log_file` (optional): Path to JSONL log file for event recording
- `exclude_patterns` (optional): List of regex patterns for URLs to skip interception
- `debug`: Enable debug logging (default: False)

**Methods:**

- `install()`: Install the interceptor (monkey-patches httpx)
- `uninstall()`: Uninstall and restore original httpx methods
- `get_stats()`: Get statistics (events logged, configuration)

**Context Manager:**

```python
with StandaloneInterceptor(...) as interceptor:
    # Automatically installs on entry, uninstalls on exit
    pass
```

## Cedar Policy Syntax

The standalone interceptor uses a simplified Cedar-like policy syntax for defining HTTP request rules.

### Rule Structure

```cedar
forbid (principal, action == Action::"http", resource)
when {
    request.<field> <operator> "<value>"
};

permit (principal, action == Action::"http", resource)
when {
    request.<field> <operator> "<value>"
};
```

### Available Fields

- `url` - Full request URL
- `hostname` - Domain name (e.g., "api.openai.com")
- `path` - URL path (e.g., "/v1/chat")
- `method` - HTTP method (e.g., "GET", "POST", "DELETE")
- `scheme` - Protocol (e.g., "https")

### Operators

- `==` - Exact match (case-insensitive)
- `!=` - Not equal (case-insensitive)
- `contains` - Substring match
- `startswith` - Prefix match
- `endswith` - Suffix match

### Policy Evaluation

1. All `forbid` rules are evaluated first (highest priority)
2. If any `forbid` rule matches, the request is **denied**
3. All `permit` rules are evaluated second
4. If any `permit` rule matches, the request is **allowed**
5. If no rules match, the request is **allowed** (default allow)

### Example Policies

#### Block Risky AI Providers

```cedar
// Block DeepSeek
forbid (principal, action == Action::"http", resource)
when { request.hostname contains "deepseek.com" };

// Block any URL containing blocked terms
forbid (principal, action == Action::"http", resource)
when { request.url contains "shadowapi.net" };
```

#### Block Destructive Operations

```cedar
// Block all DELETE requests
forbid (principal, action == Action::"http", resource)
when { request.method == "DELETE" };

// Block POST to admin endpoints
forbid (principal, action == Action::"http", resource)
when {
    request.method == "POST"
};

forbid (principal, action == Action::"http", resource)
when {
    request.path contains "/admin"
};
```

#### Whitelist Trusted APIs

```cedar
// Block everything external
forbid (principal, action == Action::"http", resource)
when { request.hostname contains "." };

// Explicitly allow trusted APIs
permit (principal, action == Action::"http", resource)
when { request.hostname == "api.openai.com" };

permit (principal, action == Action::"http", resource)
when { request.hostname == "api.anthropic.com" };
```

## Enforcement Modes

### 1. Log Mode (Default)

Logs all requests and policy violations but allows everything.

```python
interceptor = StandaloneInterceptor(
    policy_file="policy.cedar",
    enforcement="log",
    log_file="events.jsonl"
)
```

**Use case**: Monitoring and auditing without disrupting agent operations.

### 2. Warn Mode

Prints warnings to stderr for policy violations but allows requests.

```python
interceptor = StandaloneInterceptor(
    policy_file="policy.cedar",
    enforcement="warn"
)
```

Output:
```
⚠️  Policy violation (warn mode): POST https://blocked.com/api
   Reason: Forbidden by policy: request.hostname contains "blocked.com"
```

**Use case**: Development and testing - see violations in real-time.

### 3. Block Mode

Raises `RequestBlockedError` for policy violations.

```python
interceptor = StandaloneInterceptor(
    policy_file="policy.cedar",
    enforcement="block"
)

try:
    client.get("https://blocked.com/api")
except RequestBlockedError as e:
    print(f"Request blocked: {e}")
```

**Use case**: Production - strictly enforce security policies.

## JSONL Log Format

Events are logged as JSON objects, one per line:

```json
{"timestamp": "2026-02-13T10:30:45.123456+00:00", "method": "POST", "url": "https://api.example.com/v1/chat", "status_code": 200, "duration_ms": 245.67, "policy_decision": "allow", "enforcement_action": "allowed", "error": null}
{"timestamp": "2026-02-13T10:31:02.789012+00:00", "method": "DELETE", "url": "https://api.blocked.com/resource", "status_code": null, "duration_ms": 0.12, "policy_decision": "deny", "enforcement_action": "blocked", "error": "Forbidden by policy: request.method == \"DELETE\""}
```

**Fields:**

- `timestamp`: ISO 8601 timestamp
- `method`: HTTP method
- `url`: Request URL
- `status_code`: Response status (null if blocked before request)
- `duration_ms`: Request duration in milliseconds
- `policy_decision`: Cedar policy decision (`allow` or `deny`)
- `enforcement_action`: Action taken (`allowed`, `warned`, `blocked`, `error`)
- `error`: Error message (if any)

## Exclude Patterns

Use regex patterns to exclude certain URLs from interception:

```python
interceptor = StandaloneInterceptor(
    enforcement="log",
    exclude_patterns=[
        r"api\.trusera\.",      # Skip Trusera API calls
        r"localhost:\d+",        # Skip localhost
        r"127\.0\.0\.1",         # Skip loopback
        r"\.internal\.",         # Skip internal domains
    ]
)
```

**Use case**: Avoid logging internal/trusted APIs, reduce noise.

## Examples

See the [examples/standalone_usage.py](examples/standalone_usage.py) file for complete examples:

- Basic logging
- Policy enforcement
- Context manager usage
- Exclude patterns
- All enforcement modes

Run the examples:

```bash
cd examples
python standalone_usage.py
```

## Use Cases

### 1. Local Development

Monitor agent behavior during development without setting up the full Trusera platform:

```python
with StandaloneInterceptor(enforcement="log", log_file="dev.jsonl"):
    # Your agent code here
    agent.run()
```

### 2. CI/CD Pipeline Integration

Block risky requests in CI/CD:

```python
with StandaloneInterceptor(
    policy_file=".github/policies/ai-security.cedar",
    enforcement="block"
):
    # Run tests - blocks violations
    pytest.main()
```

### 3. Air-Gapped Environments

Use in restricted networks without internet access:

```python
# No API key needed, works completely offline
with StandaloneInterceptor(
    policy_file="/etc/security/ai-policy.cedar",
    enforcement="block",
    log_file="/var/log/ai-agent.jsonl"
):
    agent.run()
```

### 4. Proof of Concept

Try Trusera's policy engine without signing up:

```python
with StandaloneInterceptor(policy_file="demo-policy.cedar", enforcement="warn"):
    # Test agent with policy warnings
    demo_agent.run()
```

## Comparison: Standalone vs TruseraClient

| Feature | StandaloneInterceptor | TruseraClient |
|---------|----------------------|---------------|
| API Key Required | ❌ No | ✅ Yes |
| Works Offline | ✅ Yes | ❌ No |
| Cedar Policies | ✅ Local file | ✅ Cloud-managed |
| Event Logging | ✅ Local JSONL | ✅ Cloud dashboard |
| Real-time Alerts | ❌ No | ✅ Yes |
| Compliance Reports | ❌ No | ✅ Yes |
| Multi-agent Dashboard | ❌ No | ✅ Yes |
| Policy Enforcement | ✅ Yes | ✅ Yes |

**When to use StandaloneInterceptor:**
- Local development and testing
- CI/CD pipelines
- Air-gapped environments
- Proof of concept
- Cost-sensitive deployments

**When to use TruseraClient:**
- Production monitoring
- Compliance reporting
- Multi-agent deployments
- Real-time alerting
- Centralized policy management

## Migration Path

Start with `StandaloneInterceptor` for development, migrate to `TruseraClient` for production:

```python
import os
from trusera_sdk import StandaloneInterceptor, TruseraClient

# Use standalone in dev, cloud in production
if os.getenv("APP_ENV") == "production":
    client = TruseraClient(api_key=os.getenv("TRUSERA_API_KEY"))
    client.register_agent("my-agent", "custom")
else:
    # Development mode - no API key needed
    with StandaloneInterceptor(
        policy_file="dev-policy.cedar",
        enforcement="warn",
        log_file="dev-events.jsonl"
    ):
        # Your agent code
        pass
```

## Troubleshooting

### Interceptor not working?

Make sure you're using `httpx` (not `requests`):

```python
import httpx  # ✅ Supported
# import requests  # ❌ Not supported
```

### Policy not blocking?

1. Check policy syntax (see examples above)
2. Enable debug mode: `StandaloneInterceptor(debug=True)`
3. Verify enforcement mode is `"block"`

### Tests failing after installing interceptor?

Always uninstall after use:

```python
interceptor = StandaloneInterceptor(...)
try:
    interceptor.install()
    # Your code
finally:
    interceptor.uninstall()  # Always uninstall
```

Or use context manager (automatic cleanup):

```python
with StandaloneInterceptor(...):
    # Your code
```

## Advanced Usage

### Thread-Safe Logging

The interceptor is thread-safe for concurrent agents:

```python
import threading

with StandaloneInterceptor(enforcement="log", log_file="multi-agent.jsonl"):
    threads = [
        threading.Thread(target=agent1.run),
        threading.Thread(target=agent2.run),
        threading.Thread(target=agent3.run),
    ]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
```

### Custom Policy Evaluation

Access the Cedar evaluator directly:

```python
from trusera_sdk import CedarEvaluator

evaluator = CedarEvaluator.from_file("policy.cedar")
result = evaluator.evaluate("https://api.example.com", "POST")

if result.decision == PolicyDecision.DENY:
    print(f"Would be blocked: {result.reason}")
```

### Programmatic Policy Creation

Create policies dynamically:

```python
from trusera_sdk import CedarEvaluator

policy_text = f"""
forbid (principal, action == Action::"http", resource)
when {{ request.hostname == "{blocked_domain}" }};
"""

evaluator = CedarEvaluator.from_text(policy_text)
```

## Contributing

See the main [README.md](README.md) for contributing guidelines.

## License

Apache-2.0 License - see [LICENSE](LICENSE) for details.
