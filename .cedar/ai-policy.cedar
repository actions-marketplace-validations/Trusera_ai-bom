// AI-BOM Cedar Policy — Example Rules
//
// This file defines fine-grained rules for the AI-BOM Cedar policy gate.
// The gate evaluates discovered AI components against these rules and
// fails the CI pipeline if any component violates a "forbid" rule.
//
// Syntax (simplified Cedar-like):
//   permit|forbid (principal, action, resource) when { conditions };
//
// Supported condition fields:
//   resource.severity   — "critical", "high", "medium", "low", "info"
//   resource.provider   — e.g. "OpenAI", "Anthropic", "HuggingFace"
//   resource.component_type — "api_key", "model", "endpoint", "sdk", "framework"
//   resource.risk_score — integer 0-100
//   resource.name       — component name string
//
// Operators: ==, !=, >, >=, <, <=

// ── Block critical and high-severity findings ──────────────────────
forbid (principal, action, resource)
when { resource.severity == "critical" };

forbid (principal, action, resource)
when { resource.severity == "high" };

// ── Block exposed API keys (any severity) ──────────────────────────
forbid (principal, action, resource)
when { resource.component_type == "api_key" };

// ── Block components with risk score above 70 ──────────────────────
forbid (principal, action, resource)
when { resource.risk_score > 70 };

// ── Allow everything else ──────────────────────────────────────────
permit (principal, action, resource);
