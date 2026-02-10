# Troubleshooting

## Common Issues

### No components detected

- Ensure your project uses AI libraries that AI-BOM can detect
- Run `ai-bom list-scanners` to see available scanners
- Use `--verbose` to see which scanners ran
- Use `--deep` for Python AST analysis

### Permission errors

AI-BOM skips files it can't read. Use `--verbose` to see skipped files.

### Large repositories are slow

- Use `.ai-bomignore` to exclude directories
- Use `--cache` for incremental scanning
- Default excludes already skip `node_modules/`, `.git/`, etc.

### SARIF upload fails

Ensure your workflow has `security-events: write` permission.

### Encoding errors

AI-BOM uses a fallback chain: UTF-8 -> Latin-1 -> skip. Files with unknown encodings are safely skipped.
