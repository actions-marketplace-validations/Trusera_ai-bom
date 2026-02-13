/**
 * Example: Using StandaloneInterceptor without API key
 *
 * This demonstrates the standalone mode that works WITHOUT any connection
 * to the Trusera platform. Perfect for local development and testing.
 */

import { StandaloneInterceptor } from "../src/standalone.js";

// Example 1: Basic usage with local logging
console.log("\n=== Example 1: Basic Standalone Interceptor ===\n");

const interceptor1 = new StandaloneInterceptor({
  logFile: "./agent-events.jsonl",
  debug: true,
});

interceptor1.install();

// Make some HTTP calls - they'll be logged to agent-events.jsonl
await fetch("https://api.github.com/repos/trusera/ai-bom");
await fetch("https://api.github.com/users/octocat");

interceptor1.uninstall();

// Example 2: With Cedar policy enforcement
console.log("\n=== Example 2: With Cedar Policy ===\n");

// Create a simple Cedar policy
import * as fs from "node:fs";

const policyContent = `
// Block requests to untrusted domains
forbid (principal, action == Action::"*", resource)
when { resource.hostname == "malicious.com" };

// Block all DELETE requests
forbid (principal, action == Action::"http.delete", resource)
when { resource.method == "DELETE" };
`;

fs.writeFileSync("./example-policy.cedar", policyContent);

const interceptor2 = new StandaloneInterceptor({
  policyFile: "./example-policy.cedar",
  enforcement: "block",
  logFile: "./agent-events.jsonl",
  debug: true,
});

interceptor2.install();

// This will succeed
try {
  await fetch("https://api.github.com/users/octocat");
  console.log("✓ Request to trusted domain succeeded");
} catch (error) {
  console.error("✗ Request failed:", (error as Error).message);
}

// This will be blocked by policy
try {
  await fetch("https://malicious.com/api");
  console.log("✓ Request succeeded");
} catch (error) {
  console.error("✗ Policy blocked request:", (error as Error).message);
}

interceptor2.uninstall();

// Example 3: Warn mode (log violations but allow)
console.log("\n=== Example 3: Warn Mode ===\n");

const interceptor3 = new StandaloneInterceptor({
  policyFile: "./example-policy.cedar",
  enforcement: "warn", // Just warn, don't block
  logFile: "./agent-events.jsonl",
});

interceptor3.install();

// This will warn but still succeed
await fetch("https://malicious.com/api");

interceptor3.uninstall();

// Cleanup
fs.unlinkSync("./example-policy.cedar");

console.log("\n=== Done! Check agent-events.jsonl for logs ===\n");
