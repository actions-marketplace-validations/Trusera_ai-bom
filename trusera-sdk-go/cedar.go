package trusera

import (
	"bufio"
	"fmt"
	"regexp"
	"strconv"
	"strings"
)

// PolicyAction represents the effect of a policy rule
type PolicyAction string

const (
	ActionForbid PolicyAction = "forbid"
	ActionPermit PolicyAction = "permit"
)

// PolicyOperator represents comparison operators in conditions
type PolicyOperator string

const (
	OpEqual              PolicyOperator = "=="
	OpNotEqual           PolicyOperator = "!="
	OpGreaterThan        PolicyOperator = ">"
	OpGreaterThanOrEqual PolicyOperator = ">="
	OpLessThan           PolicyOperator = "<"
	OpLessThanOrEqual    PolicyOperator = "<="
)

// PolicyRule represents a parsed Cedar-like policy rule
type PolicyRule struct {
	Action   PolicyAction
	Field    string
	Operator PolicyOperator
	Value    any // string, int, or float64
	Raw      string
}

// PolicyDecision represents the result of policy evaluation
type PolicyDecision struct {
	Decision string   // "Allow" or "Deny"
	Reasons  []string // Human-readable reasons for the decision
	Matched  []string // Raw policy rules that matched
}

// RequestContext contains information about an HTTP request for policy evaluation
type RequestContext struct {
	URL      string
	Method   string
	Hostname string
	Path     string
}

var (
	// Match: forbid ( principal, action == Action::"deploy", resource ) when { ... };
	rulePattern = regexp.MustCompile(
		`(?s)(forbid|permit)\s*\(\s*principal\s*,\s*action\s*==\s*Action::"(\w+)"\s*,\s*resource\s*\)\s*when\s*\{([^}]+)\}\s*;`,
	)

	// Match conditions: resource.field operator "value" or resource.field operator value
	conditionPattern = regexp.MustCompile(
		`resource\.(\w+)\s*(==|!=|>=|>|<=|<)\s*(?:"([^"]+)"|([^;"\s]+))`,
	)

	// Match comments
	commentPattern = regexp.MustCompile(`//[^\n]*`)
)

// ParseCedarPolicy parses a Cedar-like policy file into rules
func ParseCedarPolicy(policyText string) ([]PolicyRule, error) {
	var rules []PolicyRule

	// Strip comments
	cleaned := commentPattern.ReplaceAllString(policyText, "")

	// Find all rule blocks
	matches := rulePattern.FindAllStringSubmatch(cleaned, -1)

	for _, match := range matches {
		if len(match) < 4 {
			continue
		}

		action := PolicyAction(match[1])
		// actionType := match[2] // e.g., "deploy" - not currently used
		conditionBlock := strings.TrimSpace(match[3])
		rawRule := strings.TrimSpace(match[0])

		// Parse conditions within the when block
		scanner := bufio.NewScanner(strings.NewReader(conditionBlock))
		for scanner.Scan() {
			line := strings.TrimSpace(scanner.Text())
			if line == "" {
				continue
			}

			condMatches := conditionPattern.FindStringSubmatch(line)
			if len(condMatches) < 3 {
				continue
			}

			field := condMatches[1]
			operator := PolicyOperator(condMatches[2])

			// Get value from either quoted (group 3) or unquoted (group 4)
			var rawValue string
			if condMatches[3] != "" {
				rawValue = condMatches[3] // quoted value
			} else if len(condMatches) > 4 && condMatches[4] != "" {
				rawValue = condMatches[4] // unquoted value
			} else {
				continue
			}

			rawValue = strings.TrimSpace(rawValue)

			// Parse value type
			var value any
			if intVal, err := strconv.ParseInt(rawValue, 10, 64); err == nil {
				value = int(intVal)
			} else if floatVal, err := strconv.ParseFloat(rawValue, 64); err == nil {
				value = floatVal
			} else {
				value = rawValue
			}

			rules = append(rules, PolicyRule{
				Action:   action,
				Field:    field,
				Operator: operator,
				Value:    value,
				Raw:      rawRule,
			})
		}
	}

	return rules, nil
}

// EvaluatePolicy evaluates a request context against Cedar policy rules
func EvaluatePolicy(ctx RequestContext, rules []PolicyRule) PolicyDecision {
	var forbidReasons []string
	var forbidMatched []string
	var permitReasons []string
	var permitMatched []string

	for _, rule := range rules {
		if matches := evaluateCondition(rule, ctx); matches {
			reason := fmt.Sprintf("%s: resource.%s %s %v (actual: %s)",
				rule.Action, rule.Field, rule.Operator, rule.Value, getFieldValue(ctx, rule.Field))

			if rule.Action == ActionForbid {
				forbidReasons = append(forbidReasons, reason)
				forbidMatched = append(forbidMatched, rule.Raw)
			} else if rule.Action == ActionPermit {
				permitReasons = append(permitReasons, reason)
				permitMatched = append(permitMatched, rule.Raw)
			}
		}
	}

	// Cedar semantics: any forbid overrides permit
	if len(forbidReasons) > 0 {
		return PolicyDecision{
			Decision: "Deny",
			Reasons:  forbidReasons,
			Matched:  forbidMatched,
		}
	}

	// If we have explicit permits, allow
	if len(permitReasons) > 0 {
		return PolicyDecision{
			Decision: "Allow",
			Reasons:  permitReasons,
			Matched:  permitMatched,
		}
	}

	// Default: allow if no rules matched
	return PolicyDecision{
		Decision: "Allow",
		Reasons:  []string{"No matching policy rules"},
		Matched:  []string{},
	}
}

// evaluateCondition checks if a rule condition matches the request context
func evaluateCondition(rule PolicyRule, ctx RequestContext) bool {
	actual := getFieldValue(ctx, rule.Field)
	if actual == "" {
		return false
	}

	// Try numeric comparison if rule value is numeric
	switch v := rule.Value.(type) {
	case int:
		actualNum, err := strconv.ParseFloat(actual, 64)
		if err != nil {
			return false
		}
		return compareNumeric(actualNum, float64(v), rule.Operator)

	case float64:
		actualNum, err := strconv.ParseFloat(actual, 64)
		if err != nil {
			return false
		}
		return compareNumeric(actualNum, v, rule.Operator)

	case string:
		return compareString(actual, v, rule.Operator)
	}

	return false
}

// getFieldValue extracts field value from request context
func getFieldValue(ctx RequestContext, field string) string {
	switch field {
	case "url":
		return ctx.URL
	case "method":
		return ctx.Method
	case "hostname":
		return ctx.Hostname
	case "path":
		return ctx.Path
	default:
		return ""
	}
}

// compareNumeric performs numeric comparison
func compareNumeric(actual, target float64, op PolicyOperator) bool {
	switch op {
	case OpEqual:
		return actual == target
	case OpNotEqual:
		return actual != target
	case OpGreaterThan:
		return actual > target
	case OpGreaterThanOrEqual:
		return actual >= target
	case OpLessThan:
		return actual < target
	case OpLessThanOrEqual:
		return actual <= target
	}
	return false
}

// compareString performs string comparison (case-insensitive)
func compareString(actual, target string, op PolicyOperator) bool {
	actualLower := strings.ToLower(actual)
	targetLower := strings.ToLower(target)

	switch op {
	case OpEqual:
		return actualLower == targetLower
	case OpNotEqual:
		return actualLower != targetLower
	}

	// For other operators on strings, do lexicographic comparison
	switch op {
	case OpGreaterThan:
		return actualLower > targetLower
	case OpGreaterThanOrEqual:
		return actualLower >= targetLower
	case OpLessThan:
		return actualLower < targetLower
	case OpLessThanOrEqual:
		return actualLower <= targetLower
	}

	return false
}
