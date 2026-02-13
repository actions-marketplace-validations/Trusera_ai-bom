// Example Cedar policy for AI agent HTTP request filtering
//
// This policy demonstrates common security patterns for LLM-based agents:
// 1. Block requests to risky AI providers
// 2. Block destructive operations
// 3. Block access to sensitive endpoints

// Block requests to DeepSeek API
forbid (
    principal,
    action == Action::"http",
    resource
) when {
    request.hostname contains "deepseek.com"
};

forbid (
    principal,
    action == Action::"http",
    resource
) when {
    request.url contains "api.deepseek.com"
};

// Block all DELETE requests (destructive operations)
forbid (
    principal,
    action == Action::"http",
    resource
) when {
    request.method == "DELETE"
};

// Block access to admin endpoints
forbid (
    principal,
    action == Action::"http",
    resource
) when {
    request.path contains "/admin"
};

// Block file uploads to external services
forbid (
    principal,
    action == Action::"http",
    resource
) when {
    request.path contains "/upload"
};

// Block requests to internal network ranges (example)
forbid (
    principal,
    action == Action::"http",
    resource
) when {
    request.hostname startswith "192.168."
};

forbid (
    principal,
    action == Action::"http",
    resource
) when {
    request.hostname startswith "10."
};

// Explicitly permit OpenAI API (if needed with other blocking rules)
permit (
    principal,
    action == Action::"http",
    resource
) when {
    request.hostname == "api.openai.com"
};

// Explicitly permit Anthropic API
permit (
    principal,
    action == Action::"http",
    resource
) when {
    request.hostname == "api.anthropic.com"
};
