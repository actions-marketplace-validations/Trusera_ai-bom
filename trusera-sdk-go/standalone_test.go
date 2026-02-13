package trusera

import (
	"bufio"
	"encoding/json"
	"net/http"
	"net/http/httptest"
	"os"
	"path/filepath"
	"strings"
	"sync"
	"testing"
	"time"
)

func TestNewStandaloneInterceptor(t *testing.T) {
	tmpDir := t.TempDir()
	policyPath := filepath.Join(tmpDir, "policy.cedar")
	logPath := filepath.Join(tmpDir, "events.jsonl")

	policy := `
forbid ( principal, action == Action::"deploy", resource )
when {
    resource.hostname == "blocked.example.com";
};
`

	if err := os.WriteFile(policyPath, []byte(policy), 0644); err != nil {
		t.Fatalf("failed to write policy file: %v", err)
	}

	si, err := NewStandaloneInterceptor(
		WithPolicyFile(policyPath),
		WithEnforcement(EnforcementBlock),
		WithLogFile(logPath),
	)

	if err != nil {
		t.Fatalf("failed to create standalone interceptor: %v", err)
	}
	defer si.Close()

	if si.enforcement != EnforcementBlock {
		t.Errorf("expected enforcement mode block, got %s", si.enforcement)
	}

	if len(si.rules) != 1 {
		t.Errorf("expected 1 rule loaded, got %d", len(si.rules))
	}

	if si.logWriter == nil {
		t.Error("expected log writer to be initialized")
	}
}

func TestNewStandaloneInterceptorMissingPolicyFile(t *testing.T) {
	_, err := NewStandaloneInterceptor(
		WithPolicyFile("/nonexistent/policy.cedar"),
	)

	if err == nil {
		t.Error("expected error for missing policy file")
	}

	if !strings.Contains(err.Error(), "failed to read policy file") {
		t.Errorf("unexpected error message: %v", err)
	}
}

func TestStandaloneInterceptorBlockMode(t *testing.T) {
	tmpDir := t.TempDir()
	policyPath := filepath.Join(tmpDir, "policy.cedar")
	logPath := filepath.Join(tmpDir, "events.jsonl")

	policy := `
forbid ( principal, action == Action::"deploy", resource )
when {
    resource.hostname == "blocked.example.com";
};
`

	if err := os.WriteFile(policyPath, []byte(policy), 0644); err != nil {
		t.Fatalf("failed to write policy file: %v", err)
	}

	si, err := NewStandaloneInterceptor(
		WithPolicyFile(policyPath),
		WithEnforcement(EnforcementBlock),
		WithLogFile(logPath),
	)
	if err != nil {
		t.Fatalf("failed to create interceptor: %v", err)
	}
	defer si.Close()

	// Create backend that should NOT be called
	backend := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		t.Error("backend should not be called for blocked request")
		w.WriteHeader(http.StatusOK)
	}))
	defer backend.Close()

	// Replace backend URL with blocked hostname for testing
	client := si.WrapClient(&http.Client{})

	req, _ := http.NewRequest("GET", "https://blocked.example.com/api/data", nil)
	resp, err := client.Do(req)

	if err == nil {
		t.Error("expected error for blocked request")
	}

	if !strings.Contains(err.Error(), "blocked by Cedar policy") {
		t.Errorf("unexpected error message: %v", err)
	}

	if resp != nil {
		resp.Body.Close()
		t.Error("expected nil response for blocked request")
	}

	// Verify JSONL log was written
	time.Sleep(50 * time.Millisecond)

	logData, err := os.ReadFile(logPath)
	if err != nil {
		t.Fatalf("failed to read log file: %v", err)
	}

	var logEntry eventLog
	if err := json.Unmarshal(logData, &logEntry); err != nil {
		t.Fatalf("failed to parse log entry: %v", err)
	}

	if logEntry.PolicyDecision != "Deny" {
		t.Errorf("expected policy decision Deny, got %s", logEntry.PolicyDecision)
	}

	if logEntry.EnforcementAction != "blocked" {
		t.Errorf("expected enforcement action blocked, got %s", logEntry.EnforcementAction)
	}
}

func TestStandaloneInterceptorWarnMode(t *testing.T) {
	tmpDir := t.TempDir()
	policyPath := filepath.Join(tmpDir, "policy.cedar")
	logPath := filepath.Join(tmpDir, "events.jsonl")

	policy := `
forbid ( principal, action == Action::"deploy", resource )
when {
    resource.method == "DELETE";
};
`

	if err := os.WriteFile(policyPath, []byte(policy), 0644); err != nil {
		t.Fatalf("failed to write policy file: %v", err)
	}

	si, err := NewStandaloneInterceptor(
		WithPolicyFile(policyPath),
		WithEnforcement(EnforcementWarn),
		WithLogFile(logPath),
	)
	if err != nil {
		t.Fatalf("failed to create interceptor: %v", err)
	}
	defer si.Close()

	backendCalled := false
	backend := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		backendCalled = true
		w.WriteHeader(http.StatusOK)
	}))
	defer backend.Close()

	client := si.WrapClient(&http.Client{})

	req, _ := http.NewRequest("DELETE", backend.URL+"/resource/123", nil)
	resp, err := client.Do(req)
	if err != nil {
		t.Fatalf("request should succeed in warn mode: %v", err)
	}
	defer resp.Body.Close()

	if !backendCalled {
		t.Error("backend should be called in warn mode")
	}

	if resp.StatusCode != http.StatusOK {
		t.Errorf("expected status 200, got %d", resp.StatusCode)
	}

	// Verify log entry shows warned action
	time.Sleep(50 * time.Millisecond)

	logData, err := os.ReadFile(logPath)
	if err != nil {
		t.Fatalf("failed to read log file: %v", err)
	}

	var logEntry eventLog
	if err := json.Unmarshal(logData, &logEntry); err != nil {
		t.Fatalf("failed to parse log entry: %v", err)
	}

	if logEntry.EnforcementAction != "warned" {
		t.Errorf("expected enforcement action warned, got %s", logEntry.EnforcementAction)
	}
}

func TestStandaloneInterceptorLogMode(t *testing.T) {
	tmpDir := t.TempDir()
	policyPath := filepath.Join(tmpDir, "policy.cedar")
	logPath := filepath.Join(tmpDir, "events.jsonl")

	policy := `
forbid ( principal, action == Action::"deploy", resource )
when {
    resource.path == "/admin";
};
`

	if err := os.WriteFile(policyPath, []byte(policy), 0644); err != nil {
		t.Fatalf("failed to write policy file: %v", err)
	}

	si, err := NewStandaloneInterceptor(
		WithPolicyFile(policyPath),
		WithEnforcement(EnforcementLog),
		WithLogFile(logPath),
	)
	if err != nil {
		t.Fatalf("failed to create interceptor: %v", err)
	}
	defer si.Close()

	backendCalled := false
	backend := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		backendCalled = true
		w.WriteHeader(http.StatusOK)
	}))
	defer backend.Close()

	client := si.WrapClient(&http.Client{})

	resp, err := client.Get(backend.URL + "/admin")
	if err != nil {
		t.Fatalf("request should succeed in log mode: %v", err)
	}
	defer resp.Body.Close()

	if !backendCalled {
		t.Error("backend should be called in log mode")
	}

	// Verify log entry shows logged action
	time.Sleep(50 * time.Millisecond)

	logData, err := os.ReadFile(logPath)
	if err != nil {
		t.Fatalf("failed to read log file: %v", err)
	}

	var logEntry eventLog
	if err := json.Unmarshal(logData, &logEntry); err != nil {
		t.Fatalf("failed to parse log entry: %v", err)
	}

	if logEntry.EnforcementAction != "logged" {
		t.Errorf("expected enforcement action logged, got %s", logEntry.EnforcementAction)
	}
}

func TestStandaloneInterceptorExcludePatterns(t *testing.T) {
	tmpDir := t.TempDir()
	logPath := filepath.Join(tmpDir, "events.jsonl")

	si, err := NewStandaloneInterceptor(
		WithLogFile(logPath),
		WithExcludePatterns("localhost", "127.0.0.1", "api.trusera."),
	)
	if err != nil {
		t.Fatalf("failed to create interceptor: %v", err)
	}
	defer si.Close()

	backend := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		w.WriteHeader(http.StatusOK)
	}))
	defer backend.Close()

	client := si.WrapClient(&http.Client{})

	// Make request (will be excluded because httptest uses localhost)
	resp, err := client.Get(backend.URL + "/test")
	if err != nil {
		t.Fatalf("request failed: %v", err)
	}
	resp.Body.Close()

	time.Sleep(50 * time.Millisecond)

	// Log file should be empty (no events logged for excluded URLs)
	logData, err := os.ReadFile(logPath)
	if err != nil {
		t.Fatalf("failed to read log file: %v", err)
	}

	if len(logData) > 0 {
		t.Errorf("expected no log entries for excluded URL, got: %s", string(logData))
	}
}

func TestStandaloneInterceptorJSONLFormat(t *testing.T) {
	tmpDir := t.TempDir()
	policyPath := filepath.Join(tmpDir, "policy.cedar")
	logPath := filepath.Join(tmpDir, "events.jsonl")

	policy := `
permit ( principal, action == Action::"deploy", resource )
when {
    resource.method == "GET";
};
`

	if err := os.WriteFile(policyPath, []byte(policy), 0644); err != nil {
		t.Fatalf("failed to write policy file: %v", err)
	}

	si, err := NewStandaloneInterceptor(
		WithPolicyFile(policyPath),
		WithEnforcement(EnforcementLog),
		WithLogFile(logPath),
	)
	if err != nil {
		t.Fatalf("failed to create interceptor: %v", err)
	}
	defer si.Close()

	backend := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		w.WriteHeader(http.StatusOK)
	}))
	defer backend.Close()

	client := si.WrapClient(&http.Client{})

	// Make multiple requests
	for i := 0; i < 3; i++ {
		resp, err := client.Get(backend.URL + "/api/test")
		if err != nil {
			t.Fatalf("request %d failed: %v", i, err)
		}
		resp.Body.Close()
		time.Sleep(10 * time.Millisecond)
	}

	time.Sleep(100 * time.Millisecond)

	// Read and verify JSONL format
	file, err := os.Open(logPath)
	if err != nil {
		t.Fatalf("failed to open log file: %v", err)
	}
	defer file.Close()

	scanner := bufio.NewScanner(file)
	lineCount := 0

	for scanner.Scan() {
		lineCount++
		line := scanner.Text()

		var entry eventLog
		if err := json.Unmarshal([]byte(line), &entry); err != nil {
			t.Fatalf("line %d: failed to parse JSON: %v", lineCount, err)
		}

		// Verify required fields
		if entry.Timestamp == "" {
			t.Errorf("line %d: missing timestamp", lineCount)
		}

		if entry.Method != "GET" {
			t.Errorf("line %d: expected method GET, got %s", lineCount, entry.Method)
		}

		if entry.URL == "" {
			t.Errorf("line %d: missing URL", lineCount)
		}

		if entry.PolicyDecision == "" {
			t.Errorf("line %d: missing policy decision", lineCount)
		}

		if entry.EnforcementAction == "" {
			t.Errorf("line %d: missing enforcement action", lineCount)
		}

		if entry.DurationMs < 0 {
			t.Errorf("line %d: invalid duration: %f", lineCount, entry.DurationMs)
		}
	}

	if lineCount != 3 {
		t.Errorf("expected 3 log entries, got %d", lineCount)
	}
}

func TestStandaloneInterceptorConcurrentRequests(t *testing.T) {
	tmpDir := t.TempDir()
	logPath := filepath.Join(tmpDir, "events.jsonl")

	si, err := NewStandaloneInterceptor(
		WithLogFile(logPath),
		WithEnforcement(EnforcementLog),
	)
	if err != nil {
		t.Fatalf("failed to create interceptor: %v", err)
	}
	defer si.Close()

	backend := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		time.Sleep(10 * time.Millisecond)
		w.WriteHeader(http.StatusOK)
	}))
	defer backend.Close()

	client := si.WrapClient(&http.Client{})

	var wg sync.WaitGroup
	for i := 0; i < 20; i++ {
		wg.Add(1)
		go func() {
			defer wg.Done()
			resp, err := client.Get(backend.URL + "/concurrent")
			if err != nil {
				t.Errorf("concurrent request failed: %v", err)
				return
			}
			resp.Body.Close()
		}()
	}

	wg.Wait()
	time.Sleep(100 * time.Millisecond)

	// Count log entries
	logData, err := os.ReadFile(logPath)
	if err != nil {
		t.Fatalf("failed to read log file: %v", err)
	}

	lines := strings.Split(strings.TrimSpace(string(logData)), "\n")
	if len(lines) != 20 {
		t.Errorf("expected 20 log entries, got %d", len(lines))
	}
}

func TestStandaloneInterceptorWithNilClient(t *testing.T) {
	tmpDir := t.TempDir()
	logPath := filepath.Join(tmpDir, "events.jsonl")

	si, err := NewStandaloneInterceptor(
		WithLogFile(logPath),
	)
	if err != nil {
		t.Fatalf("failed to create interceptor: %v", err)
	}
	defer si.Close()

	// WrapClient should handle nil client
	client := si.WrapClient(nil)

	if client == nil {
		t.Error("expected non-nil client")
	}

	if client.Transport == nil {
		t.Error("expected non-nil transport")
	}
}

func TestMustNewStandaloneInterceptor(t *testing.T) {
	tmpDir := t.TempDir()
	logPath := filepath.Join(tmpDir, "events.jsonl")

	// Should not panic with valid options
	si := MustNewStandaloneInterceptor(
		WithLogFile(logPath),
		WithEnforcement(EnforcementLog),
	)

	if si == nil {
		t.Error("expected non-nil interceptor")
	}

	si.Close()
}

func TestMustNewStandaloneInterceptorPanic(t *testing.T) {
	defer func() {
		if r := recover(); r == nil {
			t.Error("expected panic for invalid policy file")
		}
	}()

	// Should panic with invalid policy file
	MustNewStandaloneInterceptor(
		WithPolicyFile("/nonexistent/policy.cedar"),
	)
}

func TestParseURL(t *testing.T) {
	tests := []struct {
		url      string
		hostname string
		path     string
	}{
		{"https://api.example.com/v1/data", "api.example.com", "/v1/data"},
		{"http://localhost:8080/test", "localhost", "/test"},
		{"https://example.com", "example.com", ""},
		{"https://example.com/", "example.com", "/"},
	}

	for _, tt := range tests {
		hostname, path := ParseURL(tt.url)
		if hostname != tt.hostname {
			t.Errorf("ParseURL(%s) hostname = %s, want %s", tt.url, hostname, tt.hostname)
		}
		if path != tt.path {
			t.Errorf("ParseURL(%s) path = %s, want %s", tt.url, path, tt.path)
		}
	}
}

func TestStandaloneInterceptorAllowedRequest(t *testing.T) {
	tmpDir := t.TempDir()
	policyPath := filepath.Join(tmpDir, "policy.cedar")
	logPath := filepath.Join(tmpDir, "events.jsonl")

	policy := `
forbid ( principal, action == Action::"deploy", resource )
when {
    resource.hostname == "blocked.example.com";
};
`

	if err := os.WriteFile(policyPath, []byte(policy), 0644); err != nil {
		t.Fatalf("failed to write policy file: %v", err)
	}

	si, err := NewStandaloneInterceptor(
		WithPolicyFile(policyPath),
		WithEnforcement(EnforcementBlock),
		WithLogFile(logPath),
	)
	if err != nil {
		t.Fatalf("failed to create interceptor: %v", err)
	}
	defer si.Close()

	backend := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		w.WriteHeader(http.StatusOK)
	}))
	defer backend.Close()

	client := si.WrapClient(&http.Client{})

	resp, err := client.Get(backend.URL + "/api/data")
	if err != nil {
		t.Fatalf("allowed request failed: %v", err)
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		t.Errorf("expected status 200, got %d", resp.StatusCode)
	}

	// Verify log shows allowed
	time.Sleep(50 * time.Millisecond)

	logData, err := os.ReadFile(logPath)
	if err != nil {
		t.Fatalf("failed to read log file: %v", err)
	}

	var logEntry eventLog
	if err := json.Unmarshal(logData, &logEntry); err != nil {
		t.Fatalf("failed to parse log entry: %v", err)
	}

	if logEntry.EnforcementAction != "allowed" {
		t.Errorf("expected enforcement action allowed, got %s", logEntry.EnforcementAction)
	}

	if logEntry.Status != 200 {
		t.Errorf("expected status 200, got %d", logEntry.Status)
	}
}
