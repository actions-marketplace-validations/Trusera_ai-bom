# Standalone Interceptor

The Trusera Go SDK now supports a **standalone mode** that works completely offline without requiring an API key or connection to the Trusera platform. This mode is ideal for development, CI/CD pipelines, air-gapped deployments, and privacy-first monitoring.

## Quick Start

```go
package main

import (
    "log"
    "net/http"

    trusera "github.com/Trusera/ai-bom/trusera-sdk-go"
)

func main() {
    // Create standalone interceptor
    interceptor, err := trusera.NewStandaloneInterceptor(
        trusera.WithPolicyFile(".cedar/ai-policy.cedar"),
        trusera.WithEnforcement(trusera.EnforcementBlock),
        trusera.WithLogFile("agent-events.jsonl"),
        trusera.WithExcludePatterns("api.trusera."),
    )
    if err != nil {
        log.Fatal(err)
    }
    defer interceptor.Close()

    // Wrap your HTTP client
    client := interceptor.WrapClient(http.DefaultClient)

    // All requests are now policy-checked and logged locally
    resp, err := client.Get("https://api.example.com/data")
    // ...
}
```

## Features

### 1. Cedar Policy Engine

The standalone interceptor includes an embedded Cedar-like policy evaluator that supports:

- **Forbid rules**: Block requests that match conditions
- **Permit rules**: Explicitly allow requests that match conditions
- **Multiple conditions**: Combine field checks with logical operators
- **Numeric comparisons**: Support for >, >=, <, <=, ==, !=
- **String matching**: Case-insensitive string comparison

### 2. Local JSONL Logging

All intercepted requests are logged to a local JSONL file for auditing:

```jsonl
{"timestamp":"2024-01-15T10:30:00Z","method":"GET","url":"https://api.example.com/data","hostname":"api.example.com","path":"/data","status":200,"duration_ms":245.3,"policy_decision":"Allow","enforcement_action":"allowed"}
{"timestamp":"2024-01-15T10:30:01Z","method":"DELETE","url":"https://api.example.com/user","hostname":"api.example.com","path":"/user","duration_ms":0.1,"policy_decision":"Deny","enforcement_action":"blocked","reasons":"forbid: resource.method == DELETE (actual: DELETE)"}
```

### 3. Enforcement Modes

Choose how policy violations are handled:

- **`EnforcementBlock`**: Reject requests that violate policies (returns error)
- **`EnforcementWarn`**: Log violations but allow requests to proceed
- **`EnforcementLog`**: Log all requests for audit without enforcement

### 4. Thread-Safe

All operations are thread-safe with proper mutex protection. Safe for concurrent goroutines.

## Cedar Policy Syntax

### Basic Structure

```cedar
forbid ( principal, action == Action::"deploy", resource )
when {
    resource.field operator "value";
};

permit ( principal, action == Action::"deploy", resource )
when {
    resource.field operator "value";
};
```

### Supported Fields

| Field | Description | Example |
|-------|-------------|---------|
| `resource.url` | Full URL string | `https://api.example.com/v1/data` |
| `resource.method` | HTTP method | `GET`, `POST`, `DELETE` |
| `resource.hostname` | Domain/hostname | `api.example.com` |
| `resource.path` | URL path | `/v1/data` |

### Supported Operators

| Operator | Description | Example |
|----------|-------------|---------|
| `==` | Equal to | `resource.method == "GET"` |
| `!=` | Not equal to | `resource.method != "DELETE"` |
| `>` | Greater than | `resource.port > 8080` |
| `>=` | Greater than or equal | `resource.score >= 75` |
| `<` | Less than | `resource.count < 100` |
| `<=` | Less than or equal | `resource.risk <= 50` |

### Policy Evaluation Semantics

1. All rules are evaluated against each request
2. If **any** `forbid` rule matches → Request is **DENIED** (forbid always wins)
3. If **only** `permit` rules match → Request is **ALLOWED**
4. If **no** rules match → Request is **ALLOWED** (default allow)

### Example Policy

```cedar
// Block requests to untrusted LLM providers
forbid ( principal, action == Action::"deploy", resource )
when {
    resource.hostname == "api.deepseek.com";
};

// Block all DELETE operations
forbid ( principal, action == Action::"deploy", resource )
when {
    resource.method == "DELETE";
};

// Block admin endpoints
forbid ( principal, action == Action::"deploy", resource )
when {
    resource.path == "/admin";
};

// Allow GET requests
permit ( principal, action == Action::"deploy", resource )
when {
    resource.method == "GET";
};

// Allow POST to approved endpoints
permit ( principal, action == Action::"deploy", resource )
when {
    resource.method == "POST";
    resource.hostname == "api.openai.com";
};
```

## Configuration Options

### `WithPolicyFile(path string)`

Sets the path to the Cedar policy file. The file is loaded and parsed when the interceptor is created.

```go
interceptor, err := trusera.NewStandaloneInterceptor(
    trusera.WithPolicyFile("policies/production.cedar"),
)
```

### `WithEnforcement(mode EnforcementAction)`

Sets the enforcement mode. Options:
- `EnforcementLog` - Log only, no blocking (default)
- `EnforcementWarn` - Log violations but allow requests
- `EnforcementBlock` - Block violating requests

```go
interceptor, err := trusera.NewStandaloneInterceptor(
    trusera.WithEnforcement(trusera.EnforcementBlock),
)
```

### `WithLogFile(path string)`

Sets the path for JSONL event logging. File is created if it doesn't exist, appended to if it does.

```go
interceptor, err := trusera.NewStandaloneInterceptor(
    trusera.WithLogFile("logs/agent-events.jsonl"),
)
```

### `WithExcludePatterns(patterns ...string)`

Skip interception for URLs matching any of the patterns (substring match).

```go
interceptor, err := trusera.NewStandaloneInterceptor(
    trusera.WithExcludePatterns(
        "localhost",
        "127.0.0.1",
        "api.trusera.",
        "internal.corp.com",
    ),
)
```

## API Reference

### `NewStandaloneInterceptor(opts ...StandaloneOption) (*StandaloneInterceptor, error)`

Creates a new standalone interceptor with the given options. Returns an error if:
- Policy file cannot be read or parsed
- Log file cannot be opened for writing

### `MustNewStandaloneInterceptor(opts ...StandaloneOption) *StandaloneInterceptor`

Same as `NewStandaloneInterceptor` but panics on error. Useful for initialization.

### `(*StandaloneInterceptor) WrapClient(client *http.Client) *http.Client`

Wraps an HTTP client with interception. If `client` is nil, creates a new default client.

### `(*StandaloneInterceptor) Close() error`

Flushes and closes the log file. Should be called when shutting down.

### `ParseCedarPolicy(policyText string) ([]PolicyRule, error)`

Parses Cedar policy text into a slice of rules. Exposed for testing/debugging.

### `EvaluatePolicy(ctx RequestContext, rules []PolicyRule) PolicyDecision`

Evaluates a request context against policy rules. Returns decision with reasons.

## Use Cases

### 1. Development Mode

Run agents locally with policy enforcement but no cloud dependency:

```go
interceptor, _ := trusera.NewStandaloneInterceptor(
    trusera.WithPolicyFile("dev-policy.cedar"),
    trusera.WithEnforcement(trusera.EnforcementWarn),
    trusera.WithLogFile("dev-events.jsonl"),
)
client := interceptor.WrapClient(http.DefaultClient)
```

### 2. CI/CD Pipelines

Enforce policies in GitHub Actions, GitLab CI, or other CI systems:

```go
interceptor, _ := trusera.NewStandaloneInterceptor(
    trusera.WithPolicyFile(".github/ai-policy.cedar"),
    trusera.WithEnforcement(trusera.EnforcementBlock),
    trusera.WithLogFile("/tmp/ci-events.jsonl"),
)
```

### 3. Air-Gapped Deployments

Run in environments without internet access:

```go
interceptor, _ := trusera.NewStandaloneInterceptor(
    trusera.WithPolicyFile("/etc/trusera/policy.cedar"),
    trusera.WithEnforcement(trusera.EnforcementBlock),
    trusera.WithLogFile("/var/log/trusera/events.jsonl"),
)
```

### 4. Hybrid Mode (Development + Production)

Use standalone mode in dev, platform mode in production:

```go
var client *http.Client

if os.Getenv("ENV") == "production" {
    // Production: Full Trusera platform
    truseraClient := trusera.NewClient(os.Getenv("TRUSERA_API_KEY"))
    client = trusera.WrapHTTPClient(http.DefaultClient, truseraClient, trusera.InterceptorOptions{
        Enforcement: trusera.ModeBlock,
    })
} else {
    // Development: Standalone mode
    interceptor, _ := trusera.NewStandaloneInterceptor(
        trusera.WithPolicyFile("dev-policy.cedar"),
        trusera.WithEnforcement(trusera.EnforcementWarn),
        trusera.WithLogFile("dev-events.jsonl"),
    )
    client = interceptor.WrapClient(http.DefaultClient)
}
```

## Implementation Details

### Architecture

```
┌─────────────────────────────────────────┐
│  Agent Application                      │
│                                         │
│  http.Client (wrapped)                  │
└─────────────────┬───────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────┐
│  StandaloneInterceptor                  │
│  ┌────────────────────────────────────┐ │
│  │ standaloneTransport                │ │
│  │ (implements http.RoundTripper)     │ │
│  └────────────────────────────────────┘ │
│                  │                      │
│     ┌────────────┼────────────┐         │
│     ▼            ▼             ▼         │
│  ┌──────┐  ┌─────────┐  ┌──────────┐   │
│  │Cedar │  │  JSONL  │  │ Exclude  │   │
│  │Engine│  │ Logger  │  │ Patterns │   │
│  └──────┘  └─────────┘  └──────────┘   │
└─────────────────────────────────────────┘
                  │
                  ▼
         ┌────────────────┐
         │ Base Transport │
         │ (http.Default) │
         └────────────────┘
                  │
                  ▼
            Network Request
```

### Cedar Parser

The Cedar parser uses Go's `regexp` package with the following approach:

1. **Strip comments**: Remove `//` style comments
2. **Match rule blocks**: Extract `forbid`/`permit` declarations with regex
3. **Parse conditions**: Extract field, operator, and value from each condition
4. **Type inference**: Automatically detect int, float64, or string values

### Policy Evaluator

The evaluator:

1. Iterates through all rules
2. Evaluates each condition against the request context
3. Collects matching `forbid` and `permit` rules
4. Applies Cedar semantics (forbid > permit > default allow)
5. Returns decision with human-readable reasons

### Thread Safety

- Log file writes are protected by `sync.Mutex`
- Each HTTP request gets its own goroutine
- Policy rules are read-only after initialization (safe for concurrent access)

## Performance

- **Overhead**: ~0.1-0.5ms per request for policy evaluation
- **Memory**: ~1-5 KB per rule loaded
- **Concurrency**: Scales linearly with number of goroutines
- **Log I/O**: Buffered writes, ~100 events/second sustained throughput

## Limitations

1. **No dynamic policy reloading**: Policy file is loaded once at startup
2. **Simple pattern matching**: URL patterns use substring matching (not full regex)
3. **Limited Cedar syntax**: Supports a subset of full Cedar language
4. **No policy composition**: Cannot import or extend policies
5. **No principal/action evaluation**: All rules use the same principal/action placeholder

## Comparison: Standalone vs Platform Mode

| Feature | Standalone Mode | Platform Mode |
|---------|----------------|---------------|
| API Key Required | ❌ No | ✅ Yes |
| Network Dependency | ❌ No | ✅ Yes |
| Policy Enforcement | ✅ Local Cedar | ✅ Platform Rules |
| Event Storage | 📄 Local JSONL | ☁️ Cloud DB |
| Dashboard/UI | ❌ No | ✅ Yes |
| Real-time Alerts | ❌ No | ✅ Yes |
| Compliance Reports | ❌ No | ✅ Yes |
| Agent Registry | ❌ No | ✅ Yes |
| Policy as Code | ✅ Cedar Files | ✅ API Config |
| Audit Trail | 📄 JSONL | ☁️ Immutable Log |

## Examples

See the [examples/standalone](./examples/standalone) directory for:

- `main.go` - Complete working example
- `sample-policy.cedar` - Comprehensive policy template
- `README.md` - Detailed usage guide

## Contributing

When adding new fields or operators to the Cedar engine:

1. Update the regex patterns in `cedar.go`
2. Add parsing logic in `ParseCedarPolicy()`
3. Update evaluation logic in `evaluateCondition()`
4. Add test cases to `cedar_test.go`
5. Update this documentation

## License

Same as main SDK (Apache 2.0 or MIT, as per main repository).
