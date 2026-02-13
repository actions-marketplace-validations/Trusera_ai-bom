# StandaloneInterceptor - Zero-Platform Mode

The `StandaloneInterceptor` provides a **platform-independent** mode for the Trusera SDK that works WITHOUT any API key or connection to the Trusera platform.

## Use Cases

- **Local development**: Test policy enforcement without platform access
- **Air-gapped environments**: Deploy agents in isolated networks
- **Offline mode**: Continue monitoring even when platform is unavailable
- **CI/CD pipelines**: Policy checks in GitHub Actions, GitLab CI, etc.
- **Testing**: Unit test your agents with policy enforcement

## Quick Start

```typescript
import { StandaloneInterceptor } from "trusera-sdk";

const interceptor = new StandaloneInterceptor({
  policyFile: ".cedar/ai-policy.cedar",
  enforcement: "block",
  logFile: "agent-events.jsonl",
  excludePatterns: ["api\\.trusera\\."],
  debug: false
});

interceptor.install();

// All fetch calls are now monitored
await fetch("https://api.github.com/repos/test");

interceptor.uninstall();
```

## Configuration Options

### `policyFile` (optional)
Path to Cedar policy file. If not provided, all requests are allowed.

```typescript
policyFile: ".cedar/ai-policy.cedar"
```

### `enforcement` (optional, default: "log")
How to handle policy violations:
- `"block"`: Throw error and block the request
- `"warn"`: Log warning to console but allow request
- `"log"`: Silent logging only

```typescript
enforcement: "block"
```

### `logFile` (optional)
Path to JSONL log file. Events are appended to this file.

```typescript
logFile: "agent-events.jsonl"
```

**Log format:**
```jsonl
{"timestamp":"2026-02-13T02:00:00.000Z","method":"GET","url":"https://api.github.com/repos/test","status":200,"duration_ms":145,"policy_decision":"Allow","enforcement_action":"allowed"}
{"timestamp":"2026-02-13T02:01:00.000Z","method":"POST","url":"https://blocked.com/api","policy_decision":"Deny","policy_reasons":["Policy violation: hostname == blocked.com"],"enforcement_action":"blocked"}
```

### `excludePatterns` (optional)
Array of regex patterns to exclude from interception.

```typescript
excludePatterns: [
  "^https://api\\.trusera\\.",  // Exclude Trusera API calls
  "^https://internal\\.example\\.com"
]
```

### `debug` (optional, default: false)
Enable debug logging to console.

```typescript
debug: true
```

## Cedar Policy Language

The StandaloneInterceptor uses a simplified Cedar-like policy language.

### Policy Syntax

```cedar
forbid (principal, action == Action::"http.get", resource)
when { resource.hostname == "malicious.com" };

forbid (principal, action == Action::"*", resource)
when { resource.url contains "blocked-domain" };
```

### Supported Actions

- `http.get`, `http.post`, `http.put`, `http.delete`, etc.
- `*` - Matches all HTTP methods

### Supported Conditions

- `resource.hostname` - Hostname from URL
- `resource.url` - Full URL
- `resource.path` - URL path
- `resource.method` - HTTP method

### Supported Operators

- `==` - Equals (case-insensitive)
- `!=` - Not equals (case-insensitive)
- `contains` - String contains (case-insensitive)
- `startsWith` - String starts with (case-insensitive)
- `endsWith` - String ends with (case-insensitive)

### Example Policies

**Block untrusted domains:**
```cedar
forbid (principal, action == Action::"*", resource)
when { resource.hostname == "malicious.com" };
```

**Block sensitive paths:**
```cedar
forbid (principal, action == Action::"http.post", resource)
when { resource.path startsWith "/admin" };
```

**Block file downloads:**
```cedar
forbid (principal, action == Action::"*", resource)
when { resource.url endsWith ".exe" };
```

**Block all except trusted domain:**
```cedar
forbid (principal, action == Action::"*", resource)
when { resource.hostname != "trusted.com" };
```

## Complete Example

```typescript
import { StandaloneInterceptor } from "trusera-sdk";
import * as fs from "node:fs";

// Define security policy
const policy = `
// Block requests to untrusted AI providers
forbid (principal, action == Action::"*", resource)
when { resource.hostname contains "deepseek" };

forbid (principal, action == Action::"*", resource)
when { resource.hostname contains "anthropic" };

// Block data exfiltration attempts
forbid (principal, action == Action::"http.post", resource)
when { resource.path contains "upload" };

// Block admin actions
forbid (principal, action == Action::"http.delete", resource)
when { resource.path startsWith "/api" };
`;

fs.writeFileSync(".cedar/ai-policy.cedar", policy);

// Install interceptor
const interceptor = new StandaloneInterceptor({
  policyFile: ".cedar/ai-policy.cedar",
  enforcement: "block",
  logFile: "agent-events.jsonl",
  excludePatterns: ["^https://api\\.trusera\\.io"],
  debug: true
});

interceptor.install();

// Your agent code here
async function runAgent() {
  // This will be blocked
  try {
    await fetch("https://api.deepseek.com/chat");
  } catch (error) {
    console.error("Blocked:", error.message);
  }

  // This will succeed
  const response = await fetch("https://api.github.com/repos/test");
  console.log("Status:", response.status);
}

await runAgent();

// Cleanup
interceptor.uninstall();
```

## Comparison with TruseraClient

| Feature | TruseraClient | StandaloneInterceptor |
|---------|---------------|----------------------|
| Requires API key | ✅ Yes | ❌ No |
| Platform connection | ✅ Yes | ❌ No |
| Cloud policy sync | ✅ Yes | ❌ No |
| Local policy files | ❌ No | ✅ Yes |
| Local event logging | ❌ No | ✅ Yes |
| Event batching | ✅ Yes | ❌ No |
| Dashboard visibility | ✅ Yes | ❌ No |
| Air-gapped support | ❌ No | ✅ Yes |

## Integration Examples

### GitHub Actions

```yaml
name: AI Agent Tests

on: [push]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Create policy
        run: |
          mkdir -p .cedar
          cat > .cedar/ci-policy.cedar << EOF
          forbid (principal, action == Action::"*", resource)
          when { resource.hostname contains "malicious" };
          EOF

      - name: Run tests with policy enforcement
        run: |
          npm test
        env:
          TRUSERA_POLICY_FILE: .cedar/ci-policy.cedar
          TRUSERA_ENFORCEMENT: block

      - name: Upload event logs
        if: always()
        uses: actions/upload-artifact@v3
        with:
          name: agent-events
          path: agent-events.jsonl
```

### Docker Container

```dockerfile
FROM node:20-alpine

WORKDIR /app
COPY . .

# Copy Cedar policies
COPY policies/prod-policy.cedar .cedar/

# Install dependencies
RUN npm install

# Run agent with standalone interceptor
ENV TRUSERA_POLICY_FILE=.cedar/prod-policy.cedar
ENV TRUSERA_ENFORCEMENT=block
ENV TRUSERA_LOG_FILE=/var/log/agent-events.jsonl

CMD ["node", "agent.js"]
```

## API Reference

### Class: `StandaloneInterceptor`

#### Constructor
```typescript
new StandaloneInterceptor(options?: StandaloneInterceptorOptions)
```

#### Methods

**`install(): void`**
Installs the interceptor and monkey-patches `globalThis.fetch`.

**`uninstall(): void`**
Uninstalls the interceptor and restores original `fetch`.

### Class: `CedarEvaluator`

#### Constructor
```typescript
new CedarEvaluator(policyText: string)
```

#### Methods

**`evaluate(context: PolicyContext): PolicyDecision`**
Evaluates a request context against loaded policies.

**`getRuleCount(): number`**
Returns the number of loaded policy rules.

### Types

```typescript
interface StandaloneInterceptorOptions {
  policyFile?: string;
  enforcement?: "block" | "warn" | "log";
  logFile?: string;
  excludePatterns?: string[];
  debug?: boolean;
}

interface PolicyContext {
  url: string;
  method: string;
  hostname: string;
  path?: string;
  [key: string]: unknown;
}

interface PolicyDecision {
  decision: "Allow" | "Deny";
  reasons: string[];
}
```

## FAQ

**Q: Can I use both TruseraClient and StandaloneInterceptor?**
A: No, only one interceptor can be active at a time.

**Q: What happens if the policy file is invalid?**
A: The interceptor logs an error but continues without policy enforcement (fail-open).

**Q: Can I update policies without restarting?**
A: No, policies are loaded once at install(). Uninstall and reinstall to reload.

**Q: What's the performance impact?**
A: Minimal. Cedar evaluation is in-memory with no network calls.

**Q: Can I use this in production?**
A: Yes! It's designed for production use in air-gapped or offline scenarios.

## License

MIT - See LICENSE file for details.
