// Trusera Cedar Policy Example
// This file demonstrates Cedar-like policy rules for AI agent HTTP request governance

// ============================================================================
// SECURITY POLICIES - Block untrusted or malicious endpoints
// ============================================================================

// Block requests to known data exfiltration services
forbid ( principal, action == Action::"deploy", resource )
when {
    resource.hostname == "pastebin.com";
};

forbid ( principal, action == Action::"deploy", resource )
when {
    resource.hostname == "transfer.sh";
};

// Block requests to untrusted LLM providers
forbid ( principal, action == Action::"deploy", resource )
when {
    resource.hostname == "api.deepseek.com";
};

// ============================================================================
// COMPLIANCE POLICIES - Enforce organizational standards
// ============================================================================

// Block all DELETE operations (require manual approval)
forbid ( principal, action == Action::"deploy", resource )
when {
    resource.method == "DELETE";
};

// Block access to admin endpoints
forbid ( principal, action == Action::"deploy", resource )
when {
    resource.path == "/admin";
};

forbid ( principal, action == Action::"deploy", resource )
when {
    resource.path == "/api/admin";
};

// ============================================================================
// ALLOWLIST POLICIES - Explicitly permit trusted operations
// ============================================================================

// Allow GET requests (read-only operations)
permit ( principal, action == Action::"deploy", resource )
when {
    resource.method == "GET";
};

// Allow POST to approved API endpoints
permit ( principal, action == Action::"deploy", resource )
when {
    resource.method == "POST";
    resource.hostname == "api.openai.com";
};

permit ( principal, action == Action::"deploy", resource )
when {
    resource.method == "POST";
    resource.hostname == "api.anthropic.com";
};

// ============================================================================
// USAGE NOTES
// ============================================================================

// Policy Evaluation Order:
// 1. All rules are evaluated against the request
// 2. If ANY forbid rule matches → Request is DENIED
// 3. If ONLY permit rules match → Request is ALLOWED
// 4. If NO rules match → Request is ALLOWED (default allow)
//
// This follows the principle: "forbid always wins over permit"

// Supported Resource Fields:
// - resource.url       (full URL string)
// - resource.method    (HTTP method: GET, POST, DELETE, etc.)
// - resource.hostname  (domain from URL)
// - resource.path      (URL path)

// Supported Operators:
// - ==  (equal)
// - !=  (not equal)
// - >   (greater than)
// - >=  (greater than or equal)
// - <   (less than)
// - <=  (less than or equal)
