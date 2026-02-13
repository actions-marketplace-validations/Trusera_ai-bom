package main

import (
	"fmt"
	"log"
	"net/http"
	"os"

	trusera "github.com/Trusera/ai-bom/trusera-sdk-go"
)

func main() {
	// Create a sample Cedar policy file
	policyContent := `
// Block requests to untrusted domains
forbid ( principal, action == Action::"deploy", resource )
when {
    resource.hostname == "untrusted-api.example.com";
};

// Block DELETE requests
forbid ( principal, action == Action::"deploy", resource )
when {
    resource.method == "DELETE";
};

// Allow GET requests
permit ( principal, action == Action::"deploy", resource )
when {
    resource.method == "GET";
};
`

	// Write policy to temp file
	if err := os.WriteFile("policy.cedar", []byte(policyContent), 0644); err != nil {
		log.Fatalf("Failed to write policy file: %v", err)
	}
	defer os.Remove("policy.cedar")

	// Create standalone interceptor with Cedar policy
	interceptor, err := trusera.NewStandaloneInterceptor(
		trusera.WithPolicyFile("policy.cedar"),
		trusera.WithEnforcement(trusera.EnforcementBlock), // Block violations
		trusera.WithLogFile("agent-events.jsonl"),
		trusera.WithExcludePatterns("api.trusera."), // Don't intercept Trusera API calls
	)
	if err != nil {
		log.Fatalf("Failed to create interceptor: %v", err)
	}
	defer interceptor.Close()

	// Wrap the HTTP client
	client := interceptor.WrapClient(&http.Client{})

	fmt.Println("=== Standalone Interceptor Demo ===")
	fmt.Println()

	// Example 1: Allowed request (GET to trusted domain)
	fmt.Println("1. Making GET request to httpbin.org (should be allowed)...")
	resp, err := client.Get("https://httpbin.org/get")
	if err != nil {
		fmt.Printf("   Error: %v\n", err)
	} else {
		fmt.Printf("   Success! Status: %s\n", resp.Status)
		resp.Body.Close()
	}
	fmt.Println()

	// Example 2: Blocked request (DELETE method)
	fmt.Println("2. Making DELETE request (should be blocked by policy)...")
	req, _ := http.NewRequest("DELETE", "https://httpbin.org/delete", nil)
	resp, err = client.Do(req)
	if err != nil {
		fmt.Printf("   Blocked! Error: %v\n", err)
	} else {
		fmt.Printf("   Unexpected success: %s\n", resp.Status)
		resp.Body.Close()
	}
	fmt.Println()

	// Example 3: Blocked request (untrusted hostname)
	fmt.Println("3. Making request to untrusted domain (should be blocked)...")
	resp, err = client.Get("https://untrusted-api.example.com/data")
	if err != nil {
		fmt.Printf("   Blocked! Error: %v\n", err)
	} else {
		fmt.Printf("   Unexpected success: %s\n", resp.Status)
		resp.Body.Close()
	}
	fmt.Println()

	fmt.Println("=== Event Log ===")
	fmt.Println("Events written to agent-events.jsonl:")
	logData, err := os.ReadFile("agent-events.jsonl")
	if err != nil {
		log.Fatalf("Failed to read log file: %v", err)
	}
	fmt.Println(string(logData))

	// Clean up log file
	os.Remove("agent-events.jsonl")
}

// Example output:
//
// === Standalone Interceptor Demo ===
//
// 1. Making GET request to httpbin.org (should be allowed)...
//    Success! Status: 200 OK
//
// 2. Making DELETE request (should be blocked by policy)...
//    Blocked! Error: request blocked by Cedar policy: forbid: resource.method == DELETE (actual: DELETE)
//
// 3. Making request to untrusted domain (should be blocked)...
//    Blocked! Error: request blocked by Cedar policy: forbid: resource.hostname == untrusted-api.example.com (actual: untrusted-api.example.com)
//
// === Event Log ===
// Events written to agent-events.jsonl:
// {"timestamp":"2024-01-15T10:30:00Z","method":"GET","url":"https://httpbin.org/get","hostname":"httpbin.org","path":"/get","status":200,"duration_ms":245.3,"policy_decision":"Allow","enforcement_action":"allowed","reasons":"permit: resource.method == GET (actual: GET)"}
// {"timestamp":"2024-01-15T10:30:01Z","method":"DELETE","url":"https://httpbin.org/delete","hostname":"httpbin.org","path":"/delete","duration_ms":0.1,"policy_decision":"Deny","enforcement_action":"blocked","reasons":"forbid: resource.method == DELETE (actual: DELETE)"}
// {"timestamp":"2024-01-15T10:30:01Z","method":"GET","url":"https://untrusted-api.example.com/data","hostname":"untrusted-api.example.com","path":"/data","duration_ms":0.1,"policy_decision":"Deny","enforcement_action":"blocked","reasons":"forbid: resource.hostname == untrusted-api.example.com (actual: untrusted-api.example.com)"}
