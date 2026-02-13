package trusera

import (
	"strings"
	"testing"
)

func TestParseCedarPolicy(t *testing.T) {
	policy := `
// Block all requests to untrusted providers
forbid ( principal, action == Action::"deploy", resource )
when {
    resource.hostname == "untrusted.example.com";
};

// Block POST requests
forbid ( principal, action == Action::"deploy", resource )
when {
    resource.method == "POST";
};

// Permit GET requests
permit ( principal, action == Action::"deploy", resource )
when {
    resource.method == "GET";
};
`

	rules, err := ParseCedarPolicy(policy)
	if err != nil {
		t.Fatalf("failed to parse policy: %v", err)
	}

	if len(rules) != 3 {
		t.Errorf("expected 3 rules, got %d", len(rules))
	}

	// Check first rule
	if rules[0].Action != ActionForbid {
		t.Errorf("expected ActionForbid, got %s", rules[0].Action)
	}

	if rules[0].Field != "hostname" {
		t.Errorf("expected field 'hostname', got '%s'", rules[0].Field)
	}

	if rules[0].Operator != OpEqual {
		t.Errorf("expected operator '==', got '%s'", rules[0].Operator)
	}

	if rules[0].Value != "untrusted.example.com" {
		t.Errorf("expected value 'untrusted.example.com', got '%v'", rules[0].Value)
	}

	// Check third rule (permit)
	if rules[2].Action != ActionPermit {
		t.Errorf("expected ActionPermit, got %s", rules[2].Action)
	}
}

func TestParseCedarPolicyNumericConditions(t *testing.T) {
	policy := `
forbid ( principal, action == Action::"deploy", resource )
when {
    resource.port > 8080;
};

forbid ( principal, action == Action::"deploy", resource )
when {
    resource.score >= 75.5;
};
`

	rules, err := ParseCedarPolicy(policy)
	if err != nil {
		t.Fatalf("failed to parse policy: %v", err)
	}

	if len(rules) != 2 {
		t.Errorf("expected 2 rules, got %d", len(rules))
	}

	// Check integer value
	if portVal, ok := rules[0].Value.(int); !ok || portVal != 8080 {
		t.Errorf("expected integer value 8080, got %v (type %T)", rules[0].Value, rules[0].Value)
	}

	// Check float value
	if scoreVal, ok := rules[1].Value.(float64); !ok || scoreVal != 75.5 {
		t.Errorf("expected float value 75.5, got %v (type %T)", rules[1].Value, rules[1].Value)
	}
}

func TestEvaluatePolicyForbid(t *testing.T) {
	policy := `
forbid ( principal, action == Action::"deploy", resource )
when {
    resource.hostname == "blocked.example.com";
};
`

	rules, err := ParseCedarPolicy(policy)
	if err != nil {
		t.Fatalf("failed to parse policy: %v", err)
	}

	ctx := RequestContext{
		URL:      "https://blocked.example.com/api/data",
		Method:   "GET",
		Hostname: "blocked.example.com",
		Path:     "/api/data",
	}

	decision := EvaluatePolicy(ctx, rules)

	if decision.Decision != "Deny" {
		t.Errorf("expected Deny decision, got %s", decision.Decision)
	}

	if len(decision.Reasons) == 0 {
		t.Error("expected at least one reason for denial")
	}

	if !strings.Contains(decision.Reasons[0], "blocked.example.com") {
		t.Errorf("expected reason to mention hostname, got: %s", decision.Reasons[0])
	}

	if len(decision.Matched) == 0 {
		t.Error("expected matched rules")
	}
}

func TestEvaluatePolicyPermit(t *testing.T) {
	policy := `
permit ( principal, action == Action::"deploy", resource )
when {
    resource.method == "GET";
};
`

	rules, err := ParseCedarPolicy(policy)
	if err != nil {
		t.Fatalf("failed to parse policy: %v", err)
	}

	ctx := RequestContext{
		URL:      "https://api.example.com/data",
		Method:   "GET",
		Hostname: "api.example.com",
		Path:     "/data",
	}

	decision := EvaluatePolicy(ctx, rules)

	if decision.Decision != "Allow" {
		t.Errorf("expected Allow decision, got %s", decision.Decision)
	}

	if len(decision.Reasons) == 0 {
		t.Error("expected at least one reason for permit")
	}
}

func TestEvaluatePolicyForbidOverridesPermit(t *testing.T) {
	policy := `
permit ( principal, action == Action::"deploy", resource )
when {
    resource.method == "GET";
};

forbid ( principal, action == Action::"deploy", resource )
when {
    resource.hostname == "blocked.example.com";
};
`

	rules, err := ParseCedarPolicy(policy)
	if err != nil {
		t.Fatalf("failed to parse policy: %v", err)
	}

	ctx := RequestContext{
		URL:      "https://blocked.example.com/data",
		Method:   "GET",
		Hostname: "blocked.example.com",
		Path:     "/data",
	}

	decision := EvaluatePolicy(ctx, rules)

	// Forbid should override permit
	if decision.Decision != "Deny" {
		t.Errorf("expected Deny (forbid overrides permit), got %s", decision.Decision)
	}
}

func TestEvaluatePolicyNoMatch(t *testing.T) {
	policy := `
forbid ( principal, action == Action::"deploy", resource )
when {
    resource.hostname == "blocked.example.com";
};
`

	rules, err := ParseCedarPolicy(policy)
	if err != nil {
		t.Fatalf("failed to parse policy: %v", err)
	}

	ctx := RequestContext{
		URL:      "https://allowed.example.com/data",
		Method:   "GET",
		Hostname: "allowed.example.com",
		Path:     "/data",
	}

	decision := EvaluatePolicy(ctx, rules)

	// No match = default allow
	if decision.Decision != "Allow" {
		t.Errorf("expected Allow (no match), got %s", decision.Decision)
	}
}

func TestCompareNumeric(t *testing.T) {
	tests := []struct {
		actual   float64
		target   float64
		operator PolicyOperator
		want     bool
	}{
		{10, 5, OpGreaterThan, true},
		{10, 10, OpGreaterThanOrEqual, true},
		{10, 15, OpLessThan, true},
		{10, 10, OpLessThanOrEqual, true},
		{10, 10, OpEqual, true},
		{10, 5, OpNotEqual, true},
		{10, 5, OpLessThan, false},
		{10, 15, OpGreaterThan, false},
	}

	for _, tt := range tests {
		got := compareNumeric(tt.actual, tt.target, tt.operator)
		if got != tt.want {
			t.Errorf("compareNumeric(%v, %v, %s) = %v, want %v",
				tt.actual, tt.target, tt.operator, got, tt.want)
		}
	}
}

func TestCompareStringCaseInsensitive(t *testing.T) {
	tests := []struct {
		actual   string
		target   string
		operator PolicyOperator
		want     bool
	}{
		{"GET", "get", OpEqual, true},
		{"GET", "POST", OpNotEqual, true},
		{"POST", "GET", OpGreaterThan, true}, // lexicographic
		{"api.example.com", "API.EXAMPLE.COM", OpEqual, true},
		{"GET", "POST", OpEqual, false},
	}

	for _, tt := range tests {
		got := compareString(tt.actual, tt.target, tt.operator)
		if got != tt.want {
			t.Errorf("compareString(%s, %s, %s) = %v, want %v",
				tt.actual, tt.target, tt.operator, got, tt.want)
		}
	}
}

func TestGetFieldValue(t *testing.T) {
	ctx := RequestContext{
		URL:      "https://api.example.com/v1/data",
		Method:   "GET",
		Hostname: "api.example.com",
		Path:     "/v1/data",
	}

	tests := []struct {
		field string
		want  string
	}{
		{"url", "https://api.example.com/v1/data"},
		{"method", "GET"},
		{"hostname", "api.example.com"},
		{"path", "/v1/data"},
		{"unknown", ""},
	}

	for _, tt := range tests {
		got := getFieldValue(ctx, tt.field)
		if got != tt.want {
			t.Errorf("getFieldValue(ctx, %s) = %s, want %s", tt.field, got, tt.want)
		}
	}
}

func TestParseCedarPolicyOperators(t *testing.T) {
	policy := `
forbid ( principal, action == Action::"deploy", resource )
when {
    resource.status != "ok";
    resource.count >= 100;
    resource.score <= 50;
};
`

	rules, err := ParseCedarPolicy(policy)
	if err != nil {
		t.Fatalf("failed to parse policy: %v", err)
	}

	if len(rules) != 3 {
		t.Errorf("expected 3 rules, got %d", len(rules))
	}

	expectedOps := []PolicyOperator{OpNotEqual, OpGreaterThanOrEqual, OpLessThanOrEqual}
	for i, expected := range expectedOps {
		if rules[i].Operator != expected {
			t.Errorf("rule %d: expected operator %s, got %s", i, expected, rules[i].Operator)
		}
	}
}

func TestEvaluatePolicyMethodBlocking(t *testing.T) {
	policy := `
forbid ( principal, action == Action::"deploy", resource )
when {
    resource.method == "DELETE";
};
`

	rules, err := ParseCedarPolicy(policy)
	if err != nil {
		t.Fatalf("failed to parse policy: %v", err)
	}

	// DELETE should be blocked
	ctxDelete := RequestContext{
		URL:      "https://api.example.com/user/123",
		Method:   "DELETE",
		Hostname: "api.example.com",
		Path:     "/user/123",
	}

	decision := EvaluatePolicy(ctxDelete, rules)
	if decision.Decision != "Deny" {
		t.Errorf("expected DELETE to be denied, got %s", decision.Decision)
	}

	// GET should be allowed
	ctxGet := RequestContext{
		URL:      "https://api.example.com/user/123",
		Method:   "GET",
		Hostname: "api.example.com",
		Path:     "/user/123",
	}

	decision = EvaluatePolicy(ctxGet, rules)
	if decision.Decision != "Allow" {
		t.Errorf("expected GET to be allowed, got %s", decision.Decision)
	}
}

func TestParseCedarPolicyEmptyFile(t *testing.T) {
	policy := `
// Just comments
// No actual rules
`

	rules, err := ParseCedarPolicy(policy)
	if err != nil {
		t.Fatalf("failed to parse empty policy: %v", err)
	}

	if len(rules) != 0 {
		t.Errorf("expected 0 rules, got %d", len(rules))
	}
}
