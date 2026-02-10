# Output Formats

AI-BOM supports 9 output formats for different use cases.

| Format | Flag | Best For |
|--------|------|----------|
| Table | `table` | Terminal display |
| CycloneDX 1.6 | `cyclonedx` / `json` | SBOM standard |
| SARIF | `sarif` | GitHub Code Scanning |
| SPDX 3.0 | `spdx3` | SBOM standard |
| HTML | `html` | Shareable reports |
| CSV | `csv` | Spreadsheet analysis |
| JUnit XML | `junit` | CI/CD test results |
| Markdown | `markdown` | Documentation |

## Usage

```bash
ai-bom scan . --format <format> -o <output-file>
```
