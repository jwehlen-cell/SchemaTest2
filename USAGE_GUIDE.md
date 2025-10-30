# Schema Management Guide

This guide explains how to use and maintain the NDC PLUS database schema documentation.

## Table of Contents

1. [Viewing the Schema](#viewing-the-schema)
2. [Updating the Schema](#updating-the-schema)
3. [Automated Documentation](#automated-documentation)
4. [Schema Validation](#schema-validation)
5. [Integration Examples](#integration-examples)

## Viewing the Schema

### Option 1: Markdown Documentation

The primary documentation is in `schema/docs/NDC_PLUS_SCHEMA.md`. This includes:
- Table categorization
- Mermaid relationship diagrams (rendered automatically in GitHub)
- Detailed column specifications
- Foreign key relationships

**View online**: [NDC_PLUS_SCHEMA.md](schema/docs/NDC_PLUS_SCHEMA.md)

### Option 2: Interactive HTML Viewer

For a Swagger-like browsing experience, open the HTML viewer:

```bash
# Option A: Open directly in browser
open schema/docs/schema-viewer.html

# Option B: Serve with Python
cd schema/docs
python3 -m http.server 8000
# Then visit: http://localhost:8000/schema-viewer.html
```

Features of the HTML viewer:
- ✅ Categorized table navigation
- ✅ Search functionality
- ✅ Detailed column information
- ✅ Interactive UI similar to Swagger
- ✅ No external dependencies

### Option 3: JSON Schema

For programmatic access, use the JSON schema file:

```python
import json

with open('schema/ndc_plus_schema.json', 'r') as f:
    schema = json.load(f)

# Get all table names
tables = list(schema['tables'].keys())
print(f"Total tables: {len(tables)}")

# Get columns for a specific table
event_table = schema['tables']['EVENT']
print(f"EVENT table description: {event_table['description']}")
print(f"Columns: {list(event_table['columns'].keys())}")
```

## Updating the Schema

### Step 1: Edit Source File

Edit the `NDC_PLUS_tables.txt` file with your schema changes:

```bash
nano NDC_PLUS_tables.txt
```

The file format should follow this pattern:
```
TABLE: TABLE_NAME
 Column                                    Null?    Type
 ----------------------------------------- -------- ----------------------------
 COLUMN_NAME                               NOT NULL TYPE
 OTHER_COLUMN                                       TYPE
```

### Step 2: Regenerate Documentation

Run the schema parser to regenerate all documentation:

```bash
python3 tools/parse_schema.py
```

This will update:
- `schema/ndc_plus_schema.json`
- `schema/docs/NDC_PLUS_SCHEMA.md`

### Step 3: Review Changes

```bash
# View what changed
git diff schema/

# Check the generated files
cat schema/ndc_plus_schema.json | jq '.tables | keys'
head -50 schema/docs/NDC_PLUS_SCHEMA.md
```

### Step 4: Commit Changes

```bash
git add NDC_PLUS_tables.txt schema/
git commit -m "Update schema: Add new table XYZ"
git push
```

## Automated Documentation

### GitHub Actions Workflow

The repository includes a GitHub Actions workflow that automatically regenerates documentation when changes are detected.

**Trigger conditions**:
- Push to `NDC_PLUS_tables.txt`
- Push to `tools/parse_schema.py`
- Manual trigger via workflow_dispatch

**Workflow file**: `.github/workflows/regenerate-docs.yml`

To manually trigger:
1. Go to Actions tab in GitHub
2. Select "Regenerate Schema Documentation"
3. Click "Run workflow"

## Schema Validation

### Basic Validation

The parser includes basic validation:

```bash
# Run parser (validates automatically)
python3 tools/parse_schema.py

# Check for parsing errors in output
# ✓ = Success
# ❌ = Error
```

### Custom Validation Script

Create a validation script for your specific requirements:

```python
#!/usr/bin/env python3
import json
from pathlib import Path

def validate_schema():
    """Validate schema against business rules."""
    with open('schema/ndc_plus_schema.json', 'r') as f:
        schema = json.load(f)
    
    errors = []
    
    # Example: Ensure all tables have descriptions
    for table_name, table_data in schema['tables'].items():
        if not table_data.get('description'):
            errors.append(f"Table {table_name} missing description")
    
    # Example: Check for UUID primary keys
    for table_name, table_data in schema['tables'].items():
        has_pk = any(col.get('primary_key') for col in table_data['columns'].values())
        if not has_pk:
            errors.append(f"Table {table_name} has no primary key")
    
    if errors:
        print("Validation errors:")
        for error in errors:
            print(f"  - {error}")
        return False
    
    print("✅ Schema validation passed")
    return True

if __name__ == '__main__':
    validate_schema()
```

## Integration Examples

### 1. Generate Database DDL

```python
#!/usr/bin/env python3
import json

def generate_ddl(schema_file, output_file):
    """Generate Oracle DDL from JSON schema."""
    with open(schema_file, 'r') as f:
        schema = json.load(f)
    
    ddl = []
    
    for table_name, table_data in schema['tables'].items():
        ddl.append(f"-- {table_data['description']}")
        ddl.append(f"CREATE TABLE {table_name} (")
        
        columns = []
        for col_name, col_data in table_data['columns'].items():
            null_clause = "NOT NULL" if not col_data['nullable'] else ""
            columns.append(f"    {col_name} {col_data['oracle_type']} {null_clause}".strip())
        
        ddl.append(",\n".join(columns))
        ddl.append(");\n")
    
    with open(output_file, 'w') as f:
        f.write("\n".join(ddl))

generate_ddl('schema/ndc_plus_schema.json', 'output/schema.sql')
```

### 2. Generate API Models

```python
#!/usr/bin/env python3
import json

def generate_python_models(schema_file):
    """Generate Python SQLAlchemy models."""
    with open(schema_file, 'r') as f:
        schema = json.load(f)
    
    for table_name, table_data in schema['tables'].items():
        class_name = ''.join(word.capitalize() for word in table_name.split('_'))
        
        print(f"class {class_name}(Base):")
        print(f"    __tablename__ = '{table_name}'")
        print()
        
        for col_name, col_data in table_data['columns'].items():
            python_type = map_to_sqlalchemy_type(col_data['type'])
            pk = ", primary_key=True" if col_data['primary_key'] else ""
            nullable = ", nullable=True" if col_data['nullable'] else ""
            print(f"    {col_name.lower()} = Column({python_type}{pk}{nullable})")
        print()

def map_to_sqlalchemy_type(json_type):
    mapping = {
        'string': 'String',
        'number': 'Float',
        'timestamp': 'DateTime',
        'binary': 'LargeBinary'
    }
    return mapping.get(json_type, 'String')

generate_python_models('schema/ndc_plus_schema.json')
```

### 3. Documentation Website

Deploy the schema documentation as a static website:

```bash
# Option 1: GitHub Pages
# 1. Enable GitHub Pages in repository settings
# 2. Set source to main branch, /docs folder
# 3. Copy schema-viewer.html to docs/index.html

# Option 2: Custom hosting
# Upload these files to your web server:
# - schema/docs/schema-viewer.html
# - schema/ndc_plus_schema.json

# Option 3: Local server
cd schema/docs
python3 -m http.server 8000
# Access at: http://localhost:8000/schema-viewer.html
```

### 4. Schema Comparison

Compare schema versions:

```bash
# Compare with previous version
git diff HEAD~1 schema/ndc_plus_schema.json

# Compare with specific version
git diff v1.0.0 schema/ndc_plus_schema.json

# Show only table names that changed
git diff HEAD~1 schema/ndc_plus_schema.json | grep '".*":' | grep tables
```

## Best Practices

1. **Version Control**
   - Always commit schema changes with descriptive messages
   - Tag major schema versions: `git tag -a v1.0 -m "Initial schema release"`

2. **Documentation**
   - Update table descriptions when changing functionality
   - Document breaking changes in commit messages
   - Keep the README.md in sync with actual schema

3. **Testing**
   - Test schema changes in a development database first
   - Validate generated DDL before applying to production
   - Review HTML viewer after regenerating docs

4. **Collaboration**
   - Use pull requests for schema changes
   - Get review from DBAs before merging
   - Communicate breaking changes to dependent teams

## Troubleshooting

### Parser Issues

**Problem**: Parser fails to read schema file
```bash
# Check file encoding
file -I NDC_PLUS_tables.txt

# Should output: text/plain; charset=us-ascii or utf-8
```

**Problem**: Tables not appearing in output
```bash
# Check file format
head -20 NDC_PLUS_tables.txt

# Ensure it follows the pattern:
# TABLE: TABLE_NAME
#  Column ...
```

### HTML Viewer Issues

**Problem**: Schema not loading in HTML viewer
```bash
# Check file path
cd schema/docs
ls -la
# Should show: schema-viewer.html and ../ndc_plus_schema.json

# Test JSON validity
python3 -m json.tool ../ndc_plus_schema.json > /dev/null
```

**Problem**: CORS errors when opening HTML file
```bash
# Use a local server instead of file://
python3 -m http.server 8000
# Then access via http://localhost:8000/schema-viewer.html
```

## Additional Resources

- [Oracle Data Types](https://docs.oracle.com/en/database/oracle/oracle-database/19/sqlrf/Data-Types.html)
- [JSON Schema](https://json-schema.org/)
- [Mermaid Diagrams](https://mermaid.js.org/)
- [GitHub Markdown](https://guides.github.com/features/mastering-markdown/)

## Support

For issues or questions:
1. Check this guide first
2. Review existing GitHub issues
3. Create a new issue with:
   - Description of the problem
   - Steps to reproduce
   - Expected vs actual behavior
   - Schema file version
