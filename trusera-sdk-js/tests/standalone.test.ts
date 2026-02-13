import { describe, it, expect, beforeEach, afterEach, vi } from "vitest";
import * as fs from "node:fs";
import * as path from "node:path";
import { StandaloneInterceptor } from "../src/standalone.js";
import { CedarEvaluator } from "../src/cedar.js";

// Save original fetch
const originalFetch = globalThis.fetch;
let mockFetch: ReturnType<typeof vi.fn>;
let interceptor: StandaloneInterceptor | undefined;

// Temp files for testing
const testLogFile = path.join(__dirname, "test-events.jsonl");
const testPolicyFile = path.join(__dirname, "test-policy.cedar");

// Cleanup helper
function cleanupTestFiles(): void {
  try {
    if (fs.existsSync(testLogFile)) {
      fs.unlinkSync(testLogFile);
    }
    if (fs.existsSync(testPolicyFile)) {
      fs.unlinkSync(testPolicyFile);
    }
  } catch {
    // Ignore cleanup errors
  }
}

beforeEach(() => {
  cleanupTestFiles();
  mockFetch = vi.fn();
  interceptor = undefined;
  // Reset to original fetch before each test
  globalThis.fetch = originalFetch;
});

afterEach(() => {
  if (interceptor) {
    interceptor.uninstall();
  }
  globalThis.fetch = originalFetch;
  cleanupTestFiles();
});

describe("CedarEvaluator", () => {
  describe("policy parsing", () => {
    it("should parse forbid rules", () => {
      const policy = `
        forbid (principal, action == Action::"http.get", resource)
        when { resource.hostname == "malicious.com" };
      `;

      const evaluator = new CedarEvaluator(policy);
      expect(evaluator.getRuleCount()).toBe(1);
    });

    it("should parse multiple rules", () => {
      const policy = `
        forbid (principal, action == Action::"http.get", resource)
        when { resource.hostname == "malicious.com" };

        forbid (principal, action == Action::"*", resource)
        when { resource.url contains "blocked-domain.com" };
      `;

      const evaluator = new CedarEvaluator(policy);
      expect(evaluator.getRuleCount()).toBe(2);
    });

    it("should ignore comments", () => {
      const policy = `
        // This is a comment
        forbid (principal, action == Action::"http.get", resource)
        when { resource.hostname == "malicious.com" }; // inline comment
      `;

      const evaluator = new CedarEvaluator(policy);
      expect(evaluator.getRuleCount()).toBe(1);
    });

    it("should handle empty policy", () => {
      const evaluator = new CedarEvaluator("");
      expect(evaluator.getRuleCount()).toBe(0);
    });
  });

  describe("policy evaluation", () => {
    it("should deny matching hostname", () => {
      const policy = `
        forbid (principal, action == Action::"http.get", resource)
        when { resource.hostname == "malicious.com" };
      `;

      const evaluator = new CedarEvaluator(policy);
      const result = evaluator.evaluate({
        url: "https://malicious.com/api",
        method: "GET",
        hostname: "malicious.com",
      });

      expect(result.decision).toBe("Deny");
      expect(result.reasons).toHaveLength(1);
      expect(result.reasons[0]).toContain("hostname == malicious.com");
    });

    it("should allow non-matching hostname", () => {
      const policy = `
        forbid (principal, action == Action::"http.get", resource)
        when { resource.hostname == "malicious.com" };
      `;

      const evaluator = new CedarEvaluator(policy);
      const result = evaluator.evaluate({
        url: "https://safe.com/api",
        method: "GET",
        hostname: "safe.com",
      });

      expect(result.decision).toBe("Allow");
      expect(result.reasons).toHaveLength(0);
    });

    it("should support contains operator", () => {
      const policy = `
        forbid (principal, action == Action::"*", resource)
        when { resource.url contains "blocked-domain" };
      `;

      const evaluator = new CedarEvaluator(policy);
      const result = evaluator.evaluate({
        url: "https://api.blocked-domain.com/test",
        method: "GET",
        hostname: "api.blocked-domain.com",
      });

      expect(result.decision).toBe("Deny");
    });

    it("should support startsWith operator", () => {
      const policy = `
        forbid (principal, action == Action::"http.post", resource)
        when { resource.path startsWith "/admin" };
      `;

      const evaluator = new CedarEvaluator(policy);
      const result = evaluator.evaluate({
        url: "https://example.com/admin/users",
        method: "POST",
        hostname: "example.com",
        path: "/admin/users",
      });

      expect(result.decision).toBe("Deny");
    });

    it("should support endsWith operator", () => {
      const policy = `
        forbid (principal, action == Action::"*", resource)
        when { resource.url endsWith ".exe" };
      `;

      const evaluator = new CedarEvaluator(policy);
      const result = evaluator.evaluate({
        url: "https://downloads.com/malware.exe",
        method: "GET",
        hostname: "downloads.com",
      });

      expect(result.decision).toBe("Deny");
    });

    it("should support != operator", () => {
      const policy = `
        forbid (principal, action == Action::"*", resource)
        when { resource.hostname != "trusted.com" };
      `;

      const evaluator = new CedarEvaluator(policy);
      const result = evaluator.evaluate({
        url: "https://untrusted.com/api",
        method: "GET",
        hostname: "untrusted.com",
      });

      expect(result.decision).toBe("Deny");
    });

    it("should match wildcard actions", () => {
      const policy = `
        forbid (principal, action == Action::"*", resource)
        when { resource.hostname == "blocked.com" };
      `;

      const evaluator = new CedarEvaluator(policy);

      // Should match GET
      let result = evaluator.evaluate({
        url: "https://blocked.com/api",
        method: "GET",
        hostname: "blocked.com",
      });
      expect(result.decision).toBe("Deny");

      // Should match POST
      result = evaluator.evaluate({
        url: "https://blocked.com/api",
        method: "POST",
        hostname: "blocked.com",
      });
      expect(result.decision).toBe("Deny");
    });

    it("should be case-insensitive", () => {
      const policy = `
        forbid (principal, action == Action::"http.get", resource)
        when { resource.hostname == "BLOCKED.COM" };
      `;

      const evaluator = new CedarEvaluator(policy);
      const result = evaluator.evaluate({
        url: "https://blocked.com/api",
        method: "GET",
        hostname: "blocked.com",
      });

      expect(result.decision).toBe("Deny");
    });
  });
});

describe("StandaloneInterceptor", () => {
  describe("install/uninstall", () => {
    it("should install interceptor", () => {
      interceptor = new StandaloneInterceptor();
      interceptor.install();
      expect(globalThis.fetch).not.toBe(originalFetch);
    });

    it("should uninstall interceptor", () => {
      interceptor = new StandaloneInterceptor();
      interceptor.install();
      interceptor.uninstall();
      expect(globalThis.fetch).toBe(originalFetch);
    });

    it("should prevent multiple interceptors", () => {
      interceptor = new StandaloneInterceptor();
      interceptor.install();

      const interceptor2 = new StandaloneInterceptor();
      expect(() => {
        interceptor2.install();
      }).toThrow("Another StandaloneInterceptor is already installed");

      interceptor2.uninstall(); // Cleanup
    });

    it("should allow reinstalling same interceptor", () => {
      interceptor = new StandaloneInterceptor();
      interceptor.install();
      interceptor.install(); // Should not throw
    });
  });

  describe("fetch interception", () => {
    it("should intercept fetch calls", async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        status: 200,
        statusText: "OK",
        headers: new Headers(),
      } as Response);

      // Set mock BEFORE install so it becomes the "original" fetch
      globalThis.fetch = mockFetch as unknown as typeof fetch;

      interceptor = new StandaloneInterceptor();
      interceptor.install();

      await globalThis.fetch("https://api.example.com/test");

      expect(mockFetch).toHaveBeenCalledWith(
        "https://api.example.com/test",
        undefined
      );
    });

    it("should handle URL object input", async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        status: 200,
        statusText: "OK",
        headers: new Headers(),
      } as Response);

      globalThis.fetch = mockFetch as unknown as typeof fetch;
      interceptor = new StandaloneInterceptor();
      interceptor.install();

      const url = new URL("https://api.example.com/test");
      await globalThis.fetch(url);

      expect(mockFetch).toHaveBeenCalledWith(url, undefined);
    });

    it("should handle Request object input", async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        status: 200,
        statusText: "OK",
        headers: new Headers(),
      } as Response);

      globalThis.fetch = mockFetch as unknown as typeof fetch;
      interceptor = new StandaloneInterceptor();
      interceptor.install();

      const request = new Request("https://api.example.com/test", {
        method: "POST",
      });
      await globalThis.fetch(request);

      expect(mockFetch).toHaveBeenCalledWith(request, undefined);
    });
  });

  describe("exclude patterns", () => {
    it("should exclude matching URLs", async () => {
      mockFetch.mockResolvedValue({
        ok: true,
        status: 200,
        statusText: "OK",
        headers: new Headers(),
      } as Response);

      globalThis.fetch = mockFetch as unknown as typeof fetch;

      // Create interceptor AFTER setting mock fetch
      interceptor = new StandaloneInterceptor({
        logFile: testLogFile,
        excludePatterns: ["^https://api\\.trusera\\."],
      });

      interceptor.install();

      // This should be excluded (no log entry)
      await globalThis.fetch("https://api.trusera.io/events/batch");

      // This should be tracked (log entry)
      await globalThis.fetch("https://api.example.com/test");

      interceptor.uninstall();

      // Check log file
      const logContent = fs.readFileSync(testLogFile, "utf-8");
      const lines = logContent.trim().split("\n").filter(Boolean);

      // Only one event logged (the non-excluded one)
      expect(lines.length).toBe(1);
      const event = JSON.parse(lines[0] ?? "{}");
      expect(event.url).toBe("https://api.example.com/test");
    });

    it("should support multiple exclude patterns", async () => {
      mockFetch.mockResolvedValue({
        ok: true,
        status: 200,
        statusText: "OK",
        headers: new Headers(),
      } as Response);

      globalThis.fetch = mockFetch as unknown as typeof fetch;

      interceptor = new StandaloneInterceptor({
        logFile: testLogFile,
        excludePatterns: [
          "^https://api\\.trusera\\.",
          "^https://internal\\.example\\.com",
        ],
      });

      interceptor.install();

      await globalThis.fetch("https://api.trusera.io/test");
      await globalThis.fetch("https://internal.example.com/health");
      await globalThis.fetch("https://external.example.com/api");

      interceptor.uninstall();

      const logContent = fs.readFileSync(testLogFile, "utf-8");
      const lines = logContent.trim().split("\n").filter(Boolean);

      // Only external.example.com should be logged
      expect(lines.length).toBe(1);
      const event = JSON.parse(lines[0] ?? "{}");
      expect(event.url).toBe("https://external.example.com/api");
    });
  });

  describe("enforcement modes", () => {
    it("should log violations in log mode (default)", async () => {
      // Create policy that blocks all requests
      const policy = `
        forbid (principal, action == Action::"*", resource)
        when { resource.hostname == "blocked.com" };
      `;
      fs.writeFileSync(testPolicyFile, policy);

      mockFetch.mockResolvedValueOnce({
        ok: true,
        status: 200,
        statusText: "OK",
        headers: new Headers(),
      } as Response);

      globalThis.fetch = mockFetch as unknown as typeof fetch;

      interceptor = new StandaloneInterceptor({
        policyFile: testPolicyFile,
        logFile: testLogFile,
        enforcement: "log",
      });

      interceptor.install();

      // Request should succeed despite policy violation
      const response = await globalThis.fetch("https://blocked.com/api");
      expect(response.ok).toBe(true);

      interceptor.uninstall();

      // Check log file
      const logContent = fs.readFileSync(testLogFile, "utf-8");
      const lines = logContent.trim().split("\n").filter(Boolean);
      expect(lines.length).toBe(2); // violation log + success log

      const violationEvent = JSON.parse(lines[0] ?? "{}");
      expect(violationEvent.policy_decision).toBe("Deny");
      expect(violationEvent.enforcement_action).toBe("warned");
    });

    it("should warn but allow in warn mode", async () => {
      const consoleWarnSpy = vi.spyOn(console, "warn").mockImplementation(() => {});

      const policy = `
        forbid (principal, action == Action::"*", resource)
        when { resource.hostname == "blocked.com" };
      `;
      fs.writeFileSync(testPolicyFile, policy);

      mockFetch.mockResolvedValueOnce({
        ok: true,
        status: 200,
        statusText: "OK",
        headers: new Headers(),
      } as Response);

      globalThis.fetch = mockFetch as unknown as typeof fetch;

      interceptor = new StandaloneInterceptor({
        policyFile: testPolicyFile,
        enforcement: "warn",
      });

      interceptor.install();

      const response = await globalThis.fetch("https://blocked.com/api");

      expect(response.ok).toBe(true);
      expect(consoleWarnSpy).toHaveBeenCalledWith(
        expect.stringContaining("[Trusera] Policy violation")
      );

      consoleWarnSpy.mockRestore();
    });

    it("should block requests in block mode", async () => {
      const policy = `
        forbid (principal, action == Action::"*", resource)
        when { resource.hostname == "blocked.com" };
      `;
      fs.writeFileSync(testPolicyFile, policy);

      globalThis.fetch = mockFetch as unknown as typeof fetch;

      interceptor = new StandaloneInterceptor({
        policyFile: testPolicyFile,
        enforcement: "block",
      });

      interceptor.install();

      await expect(
        globalThis.fetch("https://blocked.com/api")
      ).rejects.toThrow("[Trusera] Policy violation");
    });

    it("should allow requests when policy check passes", async () => {
      const policy = `
        forbid (principal, action == Action::"*", resource)
        when { resource.hostname == "blocked.com" };
      `;
      fs.writeFileSync(testPolicyFile, policy);

      mockFetch.mockResolvedValueOnce({
        ok: true,
        status: 200,
        statusText: "OK",
        headers: new Headers(),
      } as Response);

      globalThis.fetch = mockFetch as unknown as typeof fetch;

      interceptor = new StandaloneInterceptor({
        policyFile: testPolicyFile,
        enforcement: "block",
      });

      interceptor.install();

      // Different hostname, should pass
      const response = await globalThis.fetch("https://allowed.com/api");
      expect(response.ok).toBe(true);
    });
  });

  describe("event logging", () => {
    it("should log events to JSONL file", async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        status: 200,
        statusText: "OK",
        headers: new Headers(),
      } as Response);

      globalThis.fetch = mockFetch as unknown as typeof fetch;

      interceptor = new StandaloneInterceptor({
        logFile: testLogFile,
      });

      interceptor.install();

      await globalThis.fetch("https://api.example.com/users", {
        method: "POST",
      });

      interceptor.uninstall();

      // Check log file exists and has content
      expect(fs.existsSync(testLogFile)).toBe(true);
      const logContent = fs.readFileSync(testLogFile, "utf-8");
      const lines = logContent.trim().split("\n").filter(Boolean);

      expect(lines.length).toBeGreaterThan(0);

      const event = JSON.parse(lines[0] ?? "{}");
      expect(event.method).toBe("POST");
      expect(event.url).toBe("https://api.example.com/users");
      expect(event.status).toBe(200);
      expect(event.policy_decision).toBe("Allow");
      expect(event.enforcement_action).toBe("allowed");
      expect(typeof event.duration_ms).toBe("number");
      expect(event.timestamp).toBeDefined();
    });

    it("should log errors", async () => {
      mockFetch.mockRejectedValueOnce(new Error("Network error"));

      globalThis.fetch = mockFetch as unknown as typeof fetch;

      interceptor = new StandaloneInterceptor({
        logFile: testLogFile,
      });

      interceptor.install();

      await expect(
        globalThis.fetch("https://api.example.com/test")
      ).rejects.toThrow("Network error");

      interceptor.uninstall();

      const logContent = fs.readFileSync(testLogFile, "utf-8");
      const lines = logContent.trim().split("\n").filter(Boolean);

      expect(lines.length).toBe(1);
      const event = JSON.parse(lines[0] ?? "{}");
      expect(event.error).toBe("Network error");
      expect(event.url).toBe("https://api.example.com/test");
    });

    it("should handle missing log directory", async () => {
      const nestedLogFile = path.join(__dirname, "nested", "dir", "events.jsonl");

      mockFetch.mockResolvedValueOnce({
        ok: true,
        status: 200,
        statusText: "OK",
        headers: new Headers(),
      } as Response);

      globalThis.fetch = mockFetch as unknown as typeof fetch;

      interceptor = new StandaloneInterceptor({
        logFile: nestedLogFile,
      });

      interceptor.install();

      await globalThis.fetch("https://api.example.com/test");

      interceptor.uninstall();

      // Directory should be created automatically
      expect(fs.existsSync(nestedLogFile)).toBe(true);

      // Cleanup
      fs.unlinkSync(nestedLogFile);
      fs.rmdirSync(path.dirname(nestedLogFile));
      fs.rmdirSync(path.dirname(path.dirname(nestedLogFile)));
    });

    it("should append to existing log file", async () => {
      // Create initial log entry
      fs.writeFileSync(
        testLogFile,
        JSON.stringify({ initial: "entry" }) + "\n"
      );

      mockFetch.mockResolvedValueOnce({
        ok: true,
        status: 200,
        statusText: "OK",
        headers: new Headers(),
      } as Response);

      globalThis.fetch = mockFetch as unknown as typeof fetch;

      interceptor = new StandaloneInterceptor({
        logFile: testLogFile,
      });

      interceptor.install();

      await globalThis.fetch("https://api.example.com/test");

      interceptor.uninstall();

      const logContent = fs.readFileSync(testLogFile, "utf-8");
      const lines = logContent.trim().split("\n").filter(Boolean);

      // Should have 2 entries (initial + new)
      expect(lines.length).toBe(2);
      expect(JSON.parse(lines[0] ?? "{}").initial).toBe("entry");
      expect(JSON.parse(lines[1] ?? "{}").url).toBe("https://api.example.com/test");
    });
  });

  describe("policy file loading", () => {
    it("should load policy from file", async () => {
      const policy = `
        forbid (principal, action == Action::"http.get", resource)
        when { resource.hostname == "blocked.com" };
      `;
      fs.writeFileSync(testPolicyFile, policy);

      globalThis.fetch = mockFetch as unknown as typeof fetch;

      interceptor = new StandaloneInterceptor({
        policyFile: testPolicyFile,
        enforcement: "block",
      });

      interceptor.install();

      await expect(
        globalThis.fetch("https://blocked.com/api")
      ).rejects.toThrow("[Trusera] Policy violation");
    });

    it("should handle missing policy file gracefully", async () => {
      const consoleErrorSpy = vi.spyOn(console, "error").mockImplementation(() => {});

      mockFetch.mockResolvedValueOnce({
        ok: true,
        status: 200,
        statusText: "OK",
        headers: new Headers(),
      } as Response);

      globalThis.fetch = mockFetch as unknown as typeof fetch;

      interceptor = new StandaloneInterceptor({
        policyFile: "/nonexistent/policy.cedar",
      });

      interceptor.install();

      // Should continue without policy (allow all)
      const response = await globalThis.fetch("https://api.example.com/test");
      expect(response.ok).toBe(true);
      expect(consoleErrorSpy).toHaveBeenCalled();

      consoleErrorSpy.mockRestore();
    });

    it("should work without policy file", async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        status: 200,
        statusText: "OK",
        headers: new Headers(),
      } as Response);

      globalThis.fetch = mockFetch as unknown as typeof fetch;

      interceptor = new StandaloneInterceptor({
        logFile: testLogFile,
      });

      interceptor.install();

      // Should allow all requests without policy
      const response = await globalThis.fetch("https://api.example.com/test");
      expect(response.ok).toBe(true);

      interceptor.uninstall();

      const logContent = fs.readFileSync(testLogFile, "utf-8");
      const lines = logContent.trim().split("\n").filter(Boolean);
      const event = JSON.parse(lines[0] ?? "{}");
      expect(event.policy_decision).toBe("Allow");
    });
  });
});
