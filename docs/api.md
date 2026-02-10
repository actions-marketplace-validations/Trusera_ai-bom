# REST API

Start the API server:

```bash
ai-bom serve --port 8080
```

## Endpoints

### `GET /health`

Health check.

**Response:** `{"status": "ok", "version": "3.0.0"}`

### `GET /version`

Version info.

**Response:** `{"version": "3.0.0", "name": "ai-bom"}`

### `POST /scan`

Scan a directory path.

**Request:**
```json
{
  "path": "/path/to/scan",
  "deep": false,
  "severity": null
}
```

**Response:** Full scan result JSON with components, summary, and risk assessments.

### `GET /scanners`

List available scanners.

**Response:**
```json
[
  {"name": "code", "description": "...", "enabled": true},
  ...
]
```
