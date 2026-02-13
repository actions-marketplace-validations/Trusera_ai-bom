/**
 * Cedar-like policy evaluator for TypeScript.
 *
 * Evaluates simplified Cedar policy rules against HTTP request contexts.
 * Supports forbid/permit rules with conditions on URL, method, hostname, path.
 *
 * @example
 * ```typescript
 * const policy = `
 *   forbid (principal, action == Action::"http.get", resource)
 *   when { resource.hostname == "malicious.com" };
 * `;
 *
 * const evaluator = new CedarEvaluator(policy);
 * const result = evaluator.evaluate({
 *   url: "https://malicious.com/api",
 *   method: "GET",
 *   hostname: "malicious.com"
 * });
 *
 * console.log(result.decision); // "Deny"
 * console.log(result.reasons);  // ["Policy violation: hostname == malicious.com"]
 * ```
 */

/**
 * Request context for policy evaluation.
 */
export interface PolicyContext {
  /** Full URL being accessed */
  url: string;
  /** HTTP method (GET, POST, etc.) */
  method: string;
  /** Hostname extracted from URL */
  hostname: string;
  /** Path extracted from URL */
  path?: string;
  /** Custom context fields */
  [key: string]: unknown;
}

/**
 * Policy evaluation result.
 */
export interface PolicyDecision {
  /** Allow or Deny */
  decision: "Allow" | "Deny";
  /** Reasons for the decision (policy rules that matched) */
  reasons: string[];
}

/**
 * Parsed policy rule.
 */
interface PolicyRule {
  /** forbid or permit */
  effect: "forbid" | "permit";
  /** Action pattern (e.g., "http.get", "*") */
  action: string;
  /** Field name being checked (e.g., "hostname", "path") */
  field: string;
  /** Comparison operator (==, !=, contains, startsWith, etc.) */
  operator: string;
  /** Value to compare against */
  value: string;
  /** Raw rule text for debugging */
  raw: string;
}

/**
 * Cedar-like policy evaluator.
 *
 * Parses and evaluates simplified Cedar policies for HTTP requests.
 * Supports basic forbid/permit rules with string matching conditions.
 */
export class CedarEvaluator {
  private rules: PolicyRule[] = [];

  /**
   * Creates a new Cedar evaluator with the given policy text.
   *
   * @param policyText - Cedar-like policy rules
   */
  constructor(policyText: string) {
    this.rules = this.parsePolicy(policyText);
  }

  /**
   * Evaluates a request context against loaded policies.
   *
   * @param context - Request context to evaluate
   * @returns Policy decision with reasons
   */
  evaluate(context: PolicyContext): PolicyDecision {
    const matchedRules: PolicyRule[] = [];

    for (const rule of this.rules) {
      if (this.evaluateRule(rule, context)) {
        matchedRules.push(rule);
      }
    }

    // If any forbid rules matched, deny the request
    const forbidMatches = matchedRules.filter((r) => r.effect === "forbid");
    if (forbidMatches.length > 0) {
      return {
        decision: "Deny",
        reasons: forbidMatches.map(
          (r) => `Policy violation: ${r.field} ${r.operator} ${r.value}`
        ),
      };
    }

    // Otherwise allow
    return {
      decision: "Allow",
      reasons: [],
    };
  }

  /**
   * Parses Cedar-like policy text into rule objects.
   *
   * Supported syntax:
   * ```
   * forbid (principal, action == Action::"http.get", resource)
   * when { resource.hostname == "malicious.com" };
   *
   * forbid (principal, action == Action::"*", resource)
   * when { resource.url contains "blocked-domain.com" };
   * ```
   */
  private parsePolicy(policyText: string): PolicyRule[] {
    const rules: PolicyRule[] = [];

    // Strip comments (// style)
    const cleaned = policyText.replace(/\/\/[^\n]*/g, "");

    // Regex to match forbid/permit rules
    // Matches: (forbid|permit) ( ... ) when { resource.field operator "value" };
    const rulePattern = /\b(forbid|permit)\s*\(\s*principal\s*,\s*action\s*==\s*Action::"([^"]+)"\s*,\s*resource\s*\)\s*when\s*\{([^}]+)\}\s*;/gim;

    let match;
    while ((match = rulePattern.exec(cleaned)) !== null) {
      const effect = match[1]?.toLowerCase() as "forbid" | "permit";
      const action = match[2];
      const conditionBody = match[3];

      if (!effect || !action || !conditionBody) {
        continue;
      }

      // Parse condition (resource.field operator value)
      const conditionPattern = /resource\.(\w+)\s*(==|!=|contains|startsWith|endsWith)\s*"([^"]+)"/gi;
      let condMatch;
      while ((condMatch = conditionPattern.exec(conditionBody)) !== null) {
        const field = condMatch[1];
        const operator = condMatch[2];
        const value = condMatch[3];

        if (!field || !operator || !value) {
          continue;
        }

        rules.push({
          effect,
          action,
          field,
          operator,
          value,
          raw: match[0] ?? "",
        });
      }
    }

    return rules;
  }

  /**
   * Evaluates a single rule against a context.
   */
  private evaluateRule(rule: PolicyRule, context: PolicyContext): boolean {
    // Check if action matches
    if (!this.matchesAction(rule.action, context.method)) {
      return false;
    }

    // Get the field value from context
    const fieldValue = this.getFieldValue(rule.field, context);
    if (fieldValue === undefined) {
      return false;
    }

    // Evaluate the condition
    return this.evaluateCondition(
      String(fieldValue),
      rule.operator,
      rule.value
    );
  }

  /**
   * Checks if an action pattern matches the HTTP method.
   */
  private matchesAction(actionPattern: string, method: string): boolean {
    if (actionPattern === "*") {
      return true;
    }

    // Action format: "http.get", "http.post", etc.
    const normalizedPattern = actionPattern.toLowerCase();
    const normalizedMethod = method.toLowerCase();

    if (normalizedPattern === `http.${normalizedMethod}`) {
      return true;
    }

    // Check for wildcard patterns
    if (normalizedPattern.endsWith("*")) {
      const prefix = normalizedPattern.slice(0, -1);
      return normalizedMethod.startsWith(prefix);
    }

    return false;
  }

  /**
   * Extracts a field value from the context.
   */
  private getFieldValue(field: string, context: PolicyContext): unknown {
    // Direct context access
    if (field in context) {
      return context[field];
    }

    // Special handling for common fields
    if (field === "hostname") {
      return context.hostname;
    }

    if (field === "path") {
      if (context.path !== undefined) {
        return context.path;
      }
      // Try to extract from URL
      try {
        const url = new URL(context.url);
        return url.pathname;
      } catch {
        return undefined;
      }
    }

    if (field === "method") {
      return context.method;
    }

    if (field === "url") {
      return context.url;
    }

    return undefined;
  }

  /**
   * Evaluates a condition operator.
   */
  private evaluateCondition(
    actual: string,
    operator: string,
    expected: string
  ): boolean {
    const actualLower = actual.toLowerCase();
    const expectedLower = expected.toLowerCase();

    switch (operator.toLowerCase()) {
      case "==":
        return actualLower === expectedLower;
      case "!=":
        return actualLower !== expectedLower;
      case "contains":
        return actualLower.includes(expectedLower);
      case "startswith":
        return actualLower.startsWith(expectedLower);
      case "endswith":
        return actualLower.endsWith(expectedLower);
      default:
        return false;
    }
  }

  /**
   * Returns the number of loaded rules.
   */
  getRuleCount(): number {
    return this.rules.length;
  }
}
