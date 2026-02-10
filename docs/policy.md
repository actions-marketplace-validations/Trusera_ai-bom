# Policy Enforcement

## Severity Threshold

Fail CI if findings meet a severity threshold:

```bash
ai-bom scan . --fail-on critical --quiet
```

## Policy File

Create a YAML policy file for fine-grained control:

```yaml
# policy.yml
max_risk_score: 75
blocked_providers:
  - "DeepSeek"
require_declared: true
max_components: 50
```

```bash
ai-bom scan . --policy policy.yml
```
