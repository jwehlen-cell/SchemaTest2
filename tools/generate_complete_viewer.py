#!/usr/bin/env python3
"""
Generate complete dual-schema HTML viewer with all tables embedded
"""

import json
from pathlib import Path

def generate_complete_html_viewer():
    """Generate HTML viewer with all tables from dual_schema.json"""
    
    # Load the complete schema
    schema_file = Path(__file__).parent.parent / 'schema' / 'dual_schema.json'
    with open(schema_file, 'r') as f:
        schema_data = json.load(f)
    
    # Generate JavaScript object string
    js_schema_data = json.dumps(schema_data, indent=2)
    
    # Read the current HTML template
    html_file = Path(__file__).parent.parent / 'schema' / 'docs' / 'dual-schema-viewer.html'
    with open(html_file, 'r') as f:
        html_content = f.read()
    
    # Replace the embedded schema data section
    start_marker = "const schemaData = {"
    end_marker = "};"
    
    start_idx = html_content.find(start_marker)
    if start_idx == -1:
        print("Could not find schema data section in HTML file")
        return
    
    # Find the end of the schema data object
    brace_count = 0
    current_idx = start_idx + len("const schemaData = ")
    in_string = False
    escape_next = False
    
    while current_idx < len(html_content):
        char = html_content[current_idx]
        
        if escape_next:
            escape_next = False
            current_idx += 1
            continue
            
        if char == '\\':
            escape_next = True
            current_idx += 1
            continue
            
        if char == '"' and not escape_next:
            in_string = not in_string
        elif not in_string:
            if char == '{':
                brace_count += 1
            elif char == '}':
                brace_count -= 1
                if brace_count == 0:
                    end_idx = current_idx + 1
                    break
        
        current_idx += 1
    
    # Replace the schema data
    new_html_content = (
        html_content[:start_idx] + 
        f"const schemaData = {js_schema_data};" +
        html_content[end_idx:]
    )
    
    # Write the updated HTML file
    with open(html_file, 'w') as f:
        f.write(new_html_content)
    
    print(f"✅ Updated HTML viewer with all {schema_data['schemas']['legacy']['table_count']} Legacy tables")
    print(f"✅ Updated HTML viewer with all {schema_data['schemas']['ndc_plus']['table_count']} NDC PLUS tables")
    print(f"✅ Included {len(schema_data['cross_schema_relationships'])} cross-schema relationships")
    print(f"📁 Updated file: {html_file}")

if __name__ == '__main__':
    generate_complete_html_viewer()