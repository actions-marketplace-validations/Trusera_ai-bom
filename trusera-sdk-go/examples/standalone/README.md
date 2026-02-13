# Standalone Interceptor Example

This example demonstrates the Trusera Standalone Interceptor - a lightweight, API-key-free mode that works entirely offline with Cedar-like policy evaluation.

## Features

- **No API Key Required**: Works completely standalone without connecting to Trusera platform
- **Cedar Policy Engine**: Embedded policy evaluator supporting forbid/permit rules
- **Local JSONL Logging**: All events logged to a local file for audit
- **Three Enforcement Modes**:
  - `block` - Reject requests that violate policies
  - `warn` - Log violations but allow requests
  - `log` - Log all requests for audit

## Running the Example

```bash
go run main.go
```

## Policy Format

The standalone interceptor uses a simplified Cedar-like policy syntax:

```cedar
// Block requests to untrusted domains
forbid ( principal, action == Action::"deploy", resource )
when {
    resource.hostname == "untrusted-api.example.com";
};

// Block DELETE requests
forbid ( principal, action == Action::"deploy", resource )
when {
    resource.method == "DELETE";
};

// Allow GET requests
permit ( principal, action == Action::"deploy", resource )
when {
    resource.method == "GET";
};
```

### Supported Fields

- `resource.url` - Full URL string
- `resource.method` - HTTP method (GET, POST, DELETE, etc.)
- `resource.hostname` - Domain/hostname from URL
- `resource.path` - URL path

### Supported Operators

- `==` - Equal to
- `!=` - Not equal to
- `>` - Greater than
- `>=` - Greater than or equal
- `<` - Less than
- `<=` - Less than or equal

### Policy Semantics

- Any `forbid` rule match results in denial (even if `permit` rules also match)
- If only `permit` rules match, request is allowed
- If no rules match, request is allowed by default

## JSONL Event Format

Each line in the log file is a JSON object:

```json
{
  "timestamp": "2024-01-15T10:30:00Z",
  "method": "GET",
  "url": "https://api.example.com/data",
  "hostname": "api.example.com",
  "path": "/data",
  "status": 200,
  "duration_ms": 245.3,
  "policy_decision": "Allow",
  "enforcement_action": "allowed",
  "reasons": "permit: resource.method == GET (actual: GET)"
}
```

## Use Cases

1. **Offline Development**: Test agent behavior without network access
2. **CI/CD Pipelines**: Enforce policies in automated environments
3. **Air-Gapped Deployments**: Security monitoring without external dependencies
4. **Privacy-First Monitoring**: All data stays local
5. **Prototyping**: Test policies before deploying to production

## Integration with Trusera Platform

The standalone interceptor can be used alongside the full Trusera SDK:

```go
// Development: Use standalone mode
if os.Getenv("ENV") == "development" {
    interceptor, _ := trusera.NewStandaloneInterceptor(
        trusera.WithPolicyFile(".cedar/policy.cedar"),
        trusera.WithEnforcement(trusera.EnforcementWarn),
    )
    client = interceptor.WrapClient(client)
}

// Production: Use full Trusera platform
if os.Getenv("ENV") == "production" {
    truseraClient := trusera.NewClient(os.Getenv("TRUSERA_API_KEY"))
    client = trusera.WrapHTTPClient(client, truseraClient, trusera.InterceptorOptions{
        Enforcement: trusera.ModeBlock,
    })
}
```
