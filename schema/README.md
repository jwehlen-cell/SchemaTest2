# Schema Documentation

This directory contains the NDC PLUS database schema documentation in multiple formats.

## Files

- **ndc_plus_schema.json** - Machine-readable JSON schema specification
- **docs/NDC_PLUS_SCHEMA.md** - Human-readable Markdown documentation with Mermaid diagrams
- **docs/schema-viewer.html** - Interactive HTML schema browser (Swagger-like interface)

## Viewing Options

### 1. Markdown (GitHub)
Simply click on [docs/NDC_PLUS_SCHEMA.md](docs/NDC_PLUS_SCHEMA.md) to view the schema documentation directly in GitHub with rendered Mermaid diagrams.

### 2. Interactive HTML Viewer
For the best experience, use the HTML viewer:

```bash
# Open the HTML file in your browser
cd docs
python3 -m http.server 8000
# Then visit: http://localhost:8000/schema-viewer.html
```

Or simply double-click `docs/schema-viewer.html` (may have CORS restrictions depending on browser).

### 3. JSON Schema
For programmatic access:

```python
import json

with open('ndc_plus_schema.json', 'r') as f:
    schema = json.load(f)

# Access table information
for table_name, table_info in schema['tables'].items():
    print(f"{table_name}: {table_info['description']}")
```

## Regenerating Documentation

If you modify the source schema file (`NDC_PLUS_tables.txt` in the repository root), regenerate the documentation:

```bash
# From repository root
python3 tools/parse_schema.py
```

This will automatically update all files in this directory.

## Schema Statistics

- **Total Tables**: 35
- **Database Type**: Oracle
- **Primary Key Type**: RAW(16) UUID
- **Table Categories**: 9 functional groups

## Quick Links

- [View Full Documentation](docs/NDC_PLUS_SCHEMA.md)
- [Interactive Viewer](docs/schema-viewer.html)
- [Usage Guide](../USAGE_GUIDE.md)
- [Main README](../README.md)
