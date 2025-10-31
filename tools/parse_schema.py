#!/usr/bin/env python3
"""
NDC PLUS and Legacy Schema Parser and Documentation Generator

Parses both NDC_PLUS_tables.txt and Legacy_tables.txt files and generates:
1. JSON Schema documentation for both systems
2. Markdown documentation with Mermaid diagrams showing relationships
3. Cross-schema relationship mapping
4. Interactive HTML viewer with dual-schema support
"""

import re
import json
from pathlib import Path
from collections import defaultdict


def parse_legacy_schema_file(filepath):
    """Parse the Legacy_tables.txt schema file with different format."""
    with open(filepath, 'r') as f:
        content = f.read()
    
    tables = {}
    current_table = None
    current_columns = []
    
    lines = content.split('\n')
    i = 0
    
    while i < len(lines):
        line = lines[i].strip()
        
        # Check for table definition (Legacy format: "TABLENAME TABLE:" with possible extra spaces)
        if re.match(r'^[A-Z_]+\s+TABLE:$', line):
            # Save previous table if exists
            if current_table and current_columns:
                tables[current_table] = current_columns
            
            # Start new table - extract table name by removing " TABLE:" and extra spaces
            current_table = re.sub(r'\s+TABLE:$', '', line).strip()
            current_columns = []
            i += 1
            continue
        
        # Skip empty lines
        if not line:
            i += 1
            continue
        
        # Parse column line (Legacy format: " COLUMN_NAME    TYPE")
        original_line = lines[i]  # Get the original line without stripping
        if current_table and original_line.startswith(' '):
            # Split by multiple spaces to get column parts
            parts = re.split(r'\s{2,}', line)  # line is already stripped
            
            if len(parts) >= 2:
                column_name = parts[0].strip()
                col_type = parts[1].strip()
                
                # Legacy tables don't explicitly mark NOT NULL, infer from common patterns
                is_primary = column_name in ['EVID', 'ORID', 'ARID', 'AMPID', 'MAGID', 'COMMID', 'TAGID', 'WFID', 'QCMASKID']
                
                current_columns.append({
                    'name': column_name,
                    'type': col_type,
                    'nullable': not is_primary,
                    'primary_key': is_primary
                })
        
        i += 1
    
    # Save last table
    if current_table and current_columns:
        tables[current_table] = current_columns
    
    return tables


def parse_ndc_plus_schema_file(filepath):
    """Parse the NDC_PLUS_tables.txt schema file."""
    with open(filepath, 'r') as f:
        content = f.read()
    
    tables = {}
    current_table = None
    current_columns = []
    
    lines = content.split('\n')
    i = 0
    
    while i < len(lines):
        line = lines[i].strip()
        
        # Check for table definition
        if line.startswith('TABLE:'):
            # Save previous table if exists
            if current_table and current_columns:
                tables[current_table] = current_columns
            
            # Start new table
            current_table = line.replace('TABLE:', '').strip()
            current_columns = []
            i += 1
            continue
        
        # Skip header and separator lines
        if line.startswith('Column') or line.startswith('---') or not line:
            i += 1
            continue
        
        # Parse column line
        if current_table and len(line) > 0:
            # Split by multiple spaces to get column parts
            parts = re.split(r'\s{2,}', line)
            
            if len(parts) >= 2:
                column_name = parts[0].strip()
                
                # Determine nullable and type
                if len(parts) == 3:
                    nullable = parts[1].strip()
                    col_type = parts[2].strip()
                elif len(parts) == 2:
                    nullable = 'NULL'
                    col_type = parts[1].strip()
                else:
                    i += 1
                    continue
                
                current_columns.append({
                    'name': column_name,
                    'type': col_type,
                    'nullable': nullable != 'NOT NULL',
                    'primary_key': nullable == 'NOT NULL' and column_name == 'UUID' or column_name in ['INID', 'STA_GRP_NAME']
                })
        
        i += 1
    
    # Save last table
    if current_table and current_columns:
        tables[current_table] = current_columns
    
    return tables


def identify_cross_schema_relationships(legacy_tables, ndc_plus_tables):
    """Identify relationships between Legacy and NDC PLUS schemas."""
    cross_relationships = []
    
    # Mapping patterns for cross-schema relationships
    legacy_to_ndc_mappings = {
        'EVENT': 'EVENT',
        'ARRIVAL': 'FEATURE_MEASUREMENT_ARRIVAL_TIME',
        'AMPLITUDE': 'FEATURE_MEASUREMENT_AMPLITUDE', 
        'ORIGIN': 'LOCATION_SOLUTION',
        'ASSOC': 'SIGNAL_DETECTION_HYPOTHESIS',
        'STAMAG': 'STATION_MAGNITUDE_SOLUTION',
        'NETMAG': 'NETWORK_MAGNITUDE_SOLUTION',
        'REMARK': 'REMARK'
    }
    
    for legacy_table, ndc_table in legacy_to_ndc_mappings.items():
        if legacy_table in legacy_tables and ndc_table in ndc_plus_tables:
            cross_relationships.append({
                'legacy_table': legacy_table,
                'ndc_plus_table': ndc_table,
                'relationship_type': 'conceptual_mapping',
                'description': f'Legacy {legacy_table} conceptually maps to NDC PLUS {ndc_table}'
            })
    
    return cross_relationships


def generate_dual_schema_json(legacy_tables, ndc_plus_tables, cross_relationships):
    """Generate JSON schema from both parsed table sets."""
    schema = {
        "$schema": "http://json-schema.org/draft-07/schema#",
        "title": "NDC PLUS and Legacy Database Schemas",
        "description": "Combined schema documentation for Legacy and NDC PLUS seismic monitoring systems",
        "version": "2.0.0",
        "schemas": {
            "legacy": {
                "database_type": "Oracle",
                "description": "Legacy seismic monitoring database schema",
                "table_count": len(legacy_tables),
                "tables": {}
            },
            "ndc_plus": {
                "database_type": "Oracle", 
                "description": "NDC PLUS modern seismic monitoring database schema",
                "table_count": len(ndc_plus_tables),
                "tables": {}
            }
        },
        "cross_schema_relationships": cross_relationships
    }
    
    # Process Legacy tables
    for table_name, columns in legacy_tables.items():
        table_schema = {
            "description": get_legacy_table_description(table_name),
            "columns": {}
        }
        
        for col in columns:
            table_schema["columns"][col['name']] = {
                "type": map_oracle_type_to_json(col['type']),
                "oracle_type": col['type'],
                "nullable": col['nullable'],
                "primary_key": col['primary_key']
            }
        
        schema["schemas"]["legacy"]["tables"][table_name] = table_schema
    
    # Process NDC PLUS tables
    for table_name, columns in ndc_plus_tables.items():
        table_schema = {
            "description": get_table_description(table_name),
            "columns": {}
        }
        
        for col in columns:
            table_schema["columns"][col['name']] = {
                "type": map_oracle_type_to_json(col['type']),
                "oracle_type": col['type'],
                "nullable": col['nullable'],
                "primary_key": col['primary_key']
            }
        
        schema["schemas"]["ndc_plus"]["tables"][table_name] = table_schema
    
    return schema


def get_legacy_table_description(table_name):
    """Get description for Legacy tables."""
    descriptions = {
        'ACTIVE_ID': 'Active identification tags and metadata',
        'AMPLITUDE': 'Seismic signal amplitude measurements',
        'AMPLITUDE_DYN_PARS_INT': 'Dynamic parameters for amplitude calculations',
        'ARRIVAL': 'Seismic phase arrival information', 
        'ARRIVAL_DYN_PARS_INT': 'Dynamic parameters for arrival calculations',
        'AR_INFO': 'Autoregressive model information',
        'ASSOC': 'Associations between arrivals and origins',
        'EVENT': 'Seismic event master records',
        'EVENT_CONTROL': 'Event processing control parameters',
        'EVENT_CORRELATION': 'Cross-correlation analysis of events',
        'NETMAG': 'Network magnitude calculations',
        'ORIGERR': 'Origin location error estimates',
        'ORIGIN': 'Seismic event origin solutions',
        'QCMASKINFO': 'Quality control mask information',
        'REMARK': 'Comments and annotations',
        'STAMAG': 'Station magnitude calculations',
        'WFTAG': 'Waveform tag associations'
    }
    
    return descriptions.get(table_name, f'Legacy database table: {table_name}')


def map_oracle_type_to_json(oracle_type):
    """Map Oracle types to JSON schema types."""
    oracle_type_upper = oracle_type.upper()
    
    if 'VARCHAR' in oracle_type_upper or 'CHAR' in oracle_type_upper:
        return "string"
    elif 'NUMBER' in oracle_type_upper or 'FLOAT' in oracle_type_upper:
        return "number"
    elif 'DATE' in oracle_type_upper or 'TIMESTAMP' in oracle_type_upper:
        return "timestamp"
    elif 'RAW' in oracle_type_upper:
        return "binary"
    elif 'CLOB' in oracle_type_upper:
        return "string"
    else:
        return "string"


def generate_dual_schema_markdown(legacy_tables, ndc_plus_tables, legacy_relationships, ndc_plus_relationships, cross_relationships):
    """Generate comprehensive Markdown documentation for both schemas."""
    doc = []
    
    # Header
    doc.append("# NDC PLUS and Legacy Database Schema Documentation\n")
    doc.append("## Overview\n")
    doc.append("This documentation covers both the Legacy and NDC PLUS database schemas for seismic event monitoring, ")
    doc.append("waveform analysis, and location determination. Both are Oracle database schemas with distinct but related purposes.\n\n")
    
    # Schema Comparison
    doc.append("## Schema Comparison\n")
    doc.append("| Aspect | Legacy Schema | NDC PLUS Schema |\n")
    doc.append("|--------|---------------|------------------|\n")
    doc.append(f"| Tables | {len(legacy_tables)} tables | {len(ndc_plus_tables)} tables |\n")
    doc.append("| Focus | Traditional seismic analysis | Modern event processing |\n")
    doc.append("| Data Types | Standard Oracle types | Enhanced with RAW/UUID |\n")
    doc.append("| Relationships | ID-based foreign keys | UUID-based references |\n\n")
    
    # Cross-schema relationships overview
    doc.append("## Cross-Schema Integration\n")
    doc.append("The Legacy and NDC PLUS schemas are designed to work together, with conceptual mappings between related tables:\n\n")
    doc.append("```mermaid\n")
    doc.append("graph LR\n")
    doc.append("    subgraph Legacy[\"Legacy Schema\"]\n")
    doc.append("        L1[EVENT]\n")
    doc.append("        L2[ARRIVAL]\n")
    doc.append("        L3[AMPLITUDE]\n")
    doc.append("        L4[ORIGIN]\n")
    doc.append("        L5[STAMAG]\n")
    doc.append("        L6[NETMAG]\n")
    doc.append("    end\n")
    doc.append("    \n")
    doc.append("    subgraph NDC[\"NDC PLUS Schema\"]\n")
    doc.append("        N1[EVENT]\n")
    doc.append("        N2[FEATURE_MEASUREMENT_ARRIVAL_TIME]\n")
    doc.append("        N3[FEATURE_MEASUREMENT_AMPLITUDE]\n")
    doc.append("        N4[LOCATION_SOLUTION]\n")
    doc.append("        N5[STATION_MAGNITUDE_SOLUTION]\n")
    doc.append("        N6[NETWORK_MAGNITUDE_SOLUTION]\n")
    doc.append("    end\n")
    doc.append("    \n")
    doc.append("    L1 -.->|\"Maps to\"| N1\n")
    doc.append("    L2 -.->|\"Maps to\"| N2\n")
    doc.append("    L3 -.->|\"Maps to\"| N3\n")
    doc.append("    L4 -.->|\"Maps to\"| N4\n")
    doc.append("    L5 -.->|\"Maps to\"| N5\n")
    doc.append("    L6 -.->|\"Maps to\"| N6\n")
    doc.append("```\n\n")
    
    # Legacy Schema section
    doc.append("## Legacy Schema\n")
    doc.append("### Overview\n")
    doc.append("The Legacy schema represents the traditional seismic monitoring database design, ")
    doc.append("optimized for classical seismic analysis workflows.\n\n")
    
    # Legacy table categories
    legacy_categories = {
        'Event Management': ['EVENT', 'EVENT_CONTROL', 'EVENT_CORRELATION'],
        'Arrival & Measurements': ['ARRIVAL', 'ARRIVAL_DYN_PARS_INT', 'AMPLITUDE', 'AMPLITUDE_DYN_PARS_INT'],
        'Location Analysis': ['ORIGIN', 'ORIGERR', 'ASSOC'],
        'Magnitude Calculations': ['STAMAG', 'NETMAG'],
        'Quality Control': ['QCMASKINFO'],
        'Metadata & Tags': ['ACTIVE_ID', 'WFTAG', 'AR_INFO', 'REMARK']
    }
    
    doc.append("### Legacy Table Categories\n")
    for category, table_list in legacy_categories.items():
        doc.append(f"#### {category}\n")
        for tbl in table_list:
            if tbl in legacy_tables:
                doc.append(f"- **{tbl}**: {get_legacy_table_description(tbl)}\n")
        doc.append("\n")
    
    # Legacy relationships diagram
    doc.append("### Legacy Schema Relationships\n")
    doc.append("```mermaid\n")
    doc.append("graph TD\n")
    doc.append("    EVENT[EVENT] --> ORIGIN[ORIGIN]\n")
    doc.append("    ORIGIN --> ASSOC[ASSOC]\n")
    doc.append("    ASSOC --> ARRIVAL[ARRIVAL]\n")
    doc.append("    ARRIVAL --> AMPLITUDE[AMPLITUDE]\n")
    doc.append("    ORIGIN --> STAMAG[STAMAG]\n")
    doc.append("    STAMAG --> NETMAG[NETMAG]\n")
    doc.append("    ORIGIN --> ORIGERR[ORIGERR]\n")
    doc.append("```\n\n")
    
    # NDC PLUS Schema section
    doc.append("## NDC PLUS Schema\n")
    doc.append("### Overview\n")
    doc.append("The NDC PLUS schema represents the modern, enhanced seismic monitoring database design, ")
    doc.append("featuring UUID-based relationships and advanced processing capabilities.\n\n")
    
    # NDC PLUS table categories
    ndc_plus_categories = {
        'Channel & Waveform Data': ['CHANNEL_SEGMENT', 'CHANNEL_SEGMENT_CREATION', 'CHANNEL_SEGMENT_PROC_MASK_XREF', 'CHANNEL_SEGMENT_WAVEFORM', 'STATION_CHANNEL'],
        'Event Management': ['EVENT', 'EVENT_HYPOTHESIS', 'EVENT_HYPOTHESIS_TAG', 'EVENT_STATUS_INFO', 'EVENT_CORRELATION'],
        'Feature Measurements': ['FEATURE_MEASUREMENT_AMPLITUDE', 'FEATURE_MEASUREMENT_ARRIVAL_TIME', 'FEATURE_MEASUREMENT_ENUMERATED', 'FEATURE_MEASUREMENT_NUMERIC'],
        'Feature Predictions': ['FEATURE_PREDICTION_ARRIVAL_TIME', 'FEATURE_PREDICTION_COMPONENT', 'FEATURE_PREDICTION_NUMERIC'],
        'Location & Uncertainty': ['LOCATION_SOLUTION', 'LOCATION_BEHAVIOR', 'LOCATION_RESTRAINT', 'LOCATION_UNCERTAINTY', 'LOCATION_UNCERTAINTY_ELLIPSE', 'LOCATION_UNCERTAINTY_ELLIPSOID'],
        'Magnitude Calculations': ['NETWORK_MAGNITUDE_SOLUTION', 'STATION_MAGNITUDE_SOLUTION'],
        'Quality Control': ['PROCESSING_MASK', 'PROCESSING_MASK_QC_SEGMENT_VERSION', 'QC_SEGMENT_VERSION'],
        'Signal Detection': ['SIGNAL_DETECTION_HYPOTHESIS', 'INTERVAL'],
        'Metadata & Configuration': ['STATION_GROUP_VERSION', 'RESPONSE_TABLE', 'REMARK', 'STAGE_METRICS']
    }
    
    doc.append("### NDC PLUS Table Categories\n")
    for category, table_list in ndc_plus_categories.items():
        doc.append(f"#### {category}\n")
        for tbl in table_list:
            if tbl in ndc_plus_tables:
                doc.append(f"- **{tbl}**: {get_table_description(tbl)}\n")
        doc.append("\n")
    
    # NDC PLUS relationships diagram
    doc.append("### NDC PLUS Schema Relationships\n")
    doc.append("```mermaid\n")
    doc.append("graph TD\n")
    doc.append("    EVENT[EVENT] --> EVHYP[EVENT_HYPOTHESIS]\n")
    doc.append("    EVHYP --> LOCSOL[LOCATION_SOLUTION]\n")
    doc.append("    EVHYP --> SIGMAG[NETWORK_MAGNITUDE_SOLUTION]\n")
    doc.append("    SIGMAG --> STAMAG[STATION_MAGNITUDE_SOLUTION]\n")
    doc.append("    EVHYP --> SIGDET[SIGNAL_DETECTION_HYPOTHESIS]\n")
    doc.append("    SIGDET --> FEARR[FEATURE_MEASUREMENT_ARRIVAL_TIME]\n")
    doc.append("    SIGDET --> FEAMP[FEATURE_MEASUREMENT_AMPLITUDE]\n")
    doc.append("    CHANSEG[CHANNEL_SEGMENT] --> CHANWF[CHANNEL_SEGMENT_WAVEFORM]\n")
    doc.append("    STACHAN[STATION_CHANNEL] --> CHANSEG\n")
    doc.append("```\n\n")
    
    # Detailed table specifications
    doc.append("## Detailed Table Specifications\n\n")
    
    # Legacy tables first
    doc.append("### Legacy Schema Tables\n\n")
    for table_name in sorted(legacy_tables.keys()):
        columns = legacy_tables[table_name]
        doc.append(f"#### {table_name}\n")
        doc.append(f"**Description**: {get_legacy_table_description(table_name)}\n\n")
        doc.append(f"**Column Count**: {len(columns)}\n\n")
        
        doc.append("| Column | Type | Nullable | Primary Key |\n")
        doc.append("|--------|------|----------|-------------|\n")
        
        for col in columns:
            nullable = "Yes" if col['nullable'] else "No"
            primary = "Yes" if col['primary_key'] else "No"
            doc.append(f"| {col['name']} | {col['type']} | {nullable} | {primary} |\n")
        
        doc.append("\n---\n\n")
    
    # NDC PLUS tables
    doc.append("### NDC PLUS Schema Tables\n\n")
    for table_name in sorted(ndc_plus_tables.keys()):
        columns = ndc_plus_tables[table_name]
        doc.append(f"#### {table_name}\n")
        doc.append(f"**Description**: {get_table_description(table_name)}\n\n")
        doc.append(f"**Column Count**: {len(columns)}\n\n")
        
        doc.append("| Column | Type | Nullable | Primary Key |\n")
        doc.append("|--------|------|----------|-------------|\n")
        
        for col in columns:
            nullable = "Yes" if col['nullable'] else "No"
            primary = "Yes" if col['primary_key'] else "No"
            doc.append(f"| {col['name']} | {col['type']} | {nullable} | {primary} |\n")
        
        doc.append("\n---\n\n")
    
    return ''.join(doc)


def generate_json_schema(tables):
    """Generate JSON schema from parsed tables."""
    schema = {
        "$schema": "http://json-schema.org/draft-07/schema#",
        "title": "NDC PLUS Database Schema",
        "description": "National Data Center PLUS system database schema for seismic event monitoring and analysis",
        "version": "1.0.0",
        "database_type": "Oracle",
        "tables": {}
    }
    
    for table_name, columns in tables.items():
        table_schema = {
            "description": get_table_description(table_name),
            "columns": {}
        }
        
        for col in columns:
            table_schema["columns"][col['name']] = {
                "type": map_oracle_to_json_type(col['type']),
                "oracle_type": col['type'],
                "nullable": col['nullable'],
                "primary_key": col['primary_key']
            }
        
        schema["tables"][table_name] = table_schema
    
    return schema


def map_oracle_to_json_type(oracle_type):
    """Map Oracle data types to JSON schema types."""
    oracle_type = oracle_type.upper()
    
    if 'VARCHAR' in oracle_type or 'CHAR' in oracle_type or 'CLOB' in oracle_type:
        return "string"
    elif 'NUMBER' in oracle_type or 'FLOAT' in oracle_type:
        return "number"
    elif 'TIMESTAMP' in oracle_type or 'DATE' in oracle_type:
        return "timestamp"
    elif 'RAW' in oracle_type:
        return "binary"
    else:
        return "string"


def get_table_description(table_name):
    """Generate description for table based on name."""
    descriptions = {
        'CHANNEL_SEGMENT': 'Stores time series channel segment information for waveform data',
        'CHANNEL_SEGMENT_CREATION': 'Tracks creation metadata for channel segments',
        'CHANNEL_SEGMENT_PROC_MASK_XREF': 'Cross-reference between channel segments and processing masks',
        'CHANNEL_SEGMENT_WAVEFORM': 'Links channel segments to waveform IDs',
        'EVENT': 'Seismic event master table',
        'EVENT_CORRELATION': 'Correlation analysis between seismic events',
        'EVENT_CORRELATION_CHANNEL_SEGMENT': 'Channel segments used in event correlation',
        'EVENT_HYPOTHESIS': 'Hypotheses about seismic event characteristics',
        'EVENT_HYPOTHESIS_TAG': 'Tags and classifications for event hypotheses',
        'EVENT_STATUS_INFO': 'Status and workflow information for events',
        'FEATURE_MEASUREMENT_AMPLITUDE': 'Amplitude measurements from seismic signals',
        'FEATURE_MEASUREMENT_ARRIVAL_TIME': 'Arrival time measurements for seismic phases',
        'FEATURE_MEASUREMENT_ENUMERATED': 'Categorical feature measurements',
        'FEATURE_MEASUREMENT_NUMERIC': 'Numeric feature measurements',
        'FEATURE_PREDICTION_ARRIVAL_TIME': 'Predicted arrival times for seismic phases',
        'FEATURE_PREDICTION_COMPONENT': 'Component-specific feature predictions',
        'FEATURE_PREDICTION_NUMERIC': 'Numeric feature predictions',
        'INTERVAL': 'Time intervals for processing and analysis',
        'LOCATION_BEHAVIOR': 'Location calculation behavior and parameters',
        'LOCATION_RESTRAINT': 'Constraints and restraints for location calculations',
        'LOCATION_SOLUTION': 'Calculated geographic locations for events',
        'LOCATION_UNCERTAINTY': 'Uncertainty estimates for event locations',
        'LOCATION_UNCERTAINTY_ELLIPSE': 'Elliptical uncertainty representation',
        'LOCATION_UNCERTAINTY_ELLIPSOID': 'Ellipsoidal 3D uncertainty representation',
        'NETWORK_MAGNITUDE_SOLUTION': 'Network-level magnitude calculations',
        'PROCESSING_MASK': 'Data quality masks and processing intervals',
        'PROCESSING_MASK_QC_SEGMENT_VERSION': 'Links processing masks to QC segments',
        'QC_SEGMENT_VERSION': 'Quality control segment versions',
        'REMARK': 'Comments and annotations',
        'SIGNAL_DETECTION_HYPOTHESIS': 'Signal detection hypotheses and picks',
        'STAGE_METRICS': 'Performance metrics for processing stages',
        'STATION_MAGNITUDE_SOLUTION': 'Station-level magnitude calculations',
        'RESPONSE_TABLE': 'Instrument response specifications',
        'STATION_CHANNEL': 'Station and channel configuration metadata',
        'STATION_GROUP_VERSION': 'Station group definitions and versions'
    }
    
    return descriptions.get(table_name, f'Database table: {table_name}')


def identify_relationships(tables):
    """Identify foreign key relationships based on naming conventions."""
    relationships = []
    
    for table_name, columns in tables.items():
        for col in columns:
            col_name = col['name']
            
            # UUID pattern matching
            if col_name.endswith('_UUID') and col_name != 'UUID':
                ref_table = col_name.replace('_UUID', '')
                if ref_table in tables:
                    relationships.append({
                        'from_table': table_name,
                        'from_column': col_name,
                        'to_table': ref_table,
                        'to_column': 'UUID'
                    })
            
            # GID pattern matching
            if col_name.endswith('_GID') and col_name != 'GID':
                ref_table = col_name.replace('_GID', '')
                if ref_table in tables:
                    relationships.append({
                        'from_table': table_name,
                        'from_column': col_name,
                        'to_table': ref_table,
                        'to_column': 'UUID'
                    })
            
            # Special cases
            if col_name == 'WFID':
                relationships.append({
                    'from_table': table_name,
                    'from_column': col_name,
                    'to_table': 'WAVEFORM',
                    'to_column': 'WFID',
                    'note': 'External reference'
                })
    
    return relationships


def generate_markdown_docs(tables, relationships):
    """Generate comprehensive Markdown documentation."""
    doc = []
    
    # Header
    doc.append("# NDC PLUS Database Schema Documentation\n")
    doc.append("## Overview\n")
    doc.append("The NDC (National Data Center) PLUS database schema supports seismic event monitoring, ")
    doc.append("waveform analysis, and location determination. This is an Oracle database schema with ")
    doc.append(f"{len(tables)} tables organized into functional groups.\n")
    
    # Table groups
    doc.append("## Table Categories\n")
    
    categories = {
        'Channel & Waveform Data': [
            'CHANNEL_SEGMENT', 'CHANNEL_SEGMENT_CREATION', 
            'CHANNEL_SEGMENT_PROC_MASK_XREF', 'CHANNEL_SEGMENT_WAVEFORM',
            'STATION_CHANNEL'
        ],
        'Event Management': [
            'EVENT', 'EVENT_HYPOTHESIS', 'EVENT_HYPOTHESIS_TAG', 
            'EVENT_STATUS_INFO', 'EVENT_CORRELATION', 
            'EVENT_CORRELATION_CHANNEL_SEGMENT'
        ],
        'Feature Measurements': [
            'FEATURE_MEASUREMENT_AMPLITUDE', 'FEATURE_MEASUREMENT_ARRIVAL_TIME',
            'FEATURE_MEASUREMENT_ENUMERATED', 'FEATURE_MEASUREMENT_NUMERIC'
        ],
        'Feature Predictions': [
            'FEATURE_PREDICTION_ARRIVAL_TIME', 'FEATURE_PREDICTION_COMPONENT',
            'FEATURE_PREDICTION_NUMERIC'
        ],
        'Location & Uncertainty': [
            'LOCATION_SOLUTION', 'LOCATION_BEHAVIOR', 'LOCATION_RESTRAINT',
            'LOCATION_UNCERTAINTY', 'LOCATION_UNCERTAINTY_ELLIPSE',
            'LOCATION_UNCERTAINTY_ELLIPSOID'
        ],
        'Magnitude Calculations': [
            'NETWORK_MAGNITUDE_SOLUTION', 'STATION_MAGNITUDE_SOLUTION'
        ],
        'Quality Control': [
            'PROCESSING_MASK', 'PROCESSING_MASK_QC_SEGMENT_VERSION',
            'QC_SEGMENT_VERSION'
        ],
        'Signal Detection': [
            'SIGNAL_DETECTION_HYPOTHESIS', 'INTERVAL'
        ],
        'Metadata & Configuration': [
            'STATION_GROUP_VERSION', 'RESPONSE_TABLE', 'REMARK',
            'STAGE_METRICS'
        ]
    }
    
    for category, table_list in categories.items():
        doc.append(f"### {category}\n")
        for tbl in table_list:
            if tbl in tables:
                doc.append(f"- **{tbl}**: {get_table_description(tbl)}\n")
        doc.append("\n")
    
    # Entity Relationship Overview
    doc.append("## Key Relationships\n")
    doc.append("```mermaid\n")
    doc.append("graph TD\n")
    doc.append("    EVENT[EVENT] --> EVHYP[EVENT_HYPOTHESIS]\n")
    doc.append("    EVHYP --> LOCSOL[LOCATION_SOLUTION]\n")
    doc.append("    EVHYP --> SIGMAG[NETWORK_MAGNITUDE_SOLUTION]\n")
    doc.append("    SIGMAG --> STAMAG[STATION_MAGNITUDE_SOLUTION]\n")
    doc.append("    EVHYP --> SIGDET[SIGNAL_DETECTION_HYPOTHESIS]\n")
    doc.append("    SIGDET --> FEARR[FEATURE_MEASUREMENT_ARRIVAL_TIME]\n")
    doc.append("    SIGDET --> FEAMP[FEATURE_MEASUREMENT_AMPLITUDE]\n")
    doc.append("    CHANSEG[CHANNEL_SEGMENT] --> CHANWF[CHANNEL_SEGMENT_WAVEFORM]\n")
    doc.append("    STACHAN[STATION_CHANNEL] --> CHANSEG\n")
    doc.append("```\n\n")
    
    # Detailed table documentation
    doc.append("## Detailed Table Specifications\n")
    
    for table_name in sorted(tables.keys()):
        columns = tables[table_name]
        doc.append(f"### {table_name}\n")
        doc.append(f"**Description**: {get_table_description(table_name)}\n\n")
        doc.append(f"**Column Count**: {len(columns)}\n\n")
        
        # Columns table
        doc.append("| Column | Type | Nullable | Primary Key |\n")
        doc.append("|--------|------|----------|-------------|\n")
        
        for col in columns:
            pk_mark = "✓" if col['primary_key'] else ""
            nullable_mark = "Yes" if col['nullable'] else "No"
            doc.append(f"| {col['name']} | {col['type']} | {nullable_mark} | {pk_mark} |\n")
        
        doc.append("\n")
        
        # Related tables
        related = [r for r in relationships if r['from_table'] == table_name or r['to_table'] == table_name]
        if related:
            doc.append("**Relationships**:\n")
            for rel in related:
                if rel['from_table'] == table_name:
                    doc.append(f"- References **{rel['to_table']}**.{rel['to_column']} via {rel['from_column']}\n")
                else:
                    doc.append(f"- Referenced by **{rel['from_table']}**.{rel['from_column']}\n")
            doc.append("\n")
        
        doc.append("---\n\n")
    
    return ''.join(doc)


def main():
    """Main execution function."""
    print("🔍 NDC PLUS and Legacy Schema Parser\n")
    
    # Paths
    base_dir = Path(__file__).parent.parent
    ndc_plus_file = base_dir / 'NDC_PLUS_tables.txt'
    legacy_file = base_dir / 'Legacy_tables.txt'
    output_dir = base_dir / 'schema'
    docs_dir = output_dir / 'docs'
    
    # Create output directories
    output_dir.mkdir(exist_ok=True)
    docs_dir.mkdir(exist_ok=True)
    
    # Parse both schemas
    print(f"📄 Parsing {ndc_plus_file.name}...")
    ndc_plus_tables = parse_ndc_plus_schema_file(ndc_plus_file)
    print(f"✓ Found {len(ndc_plus_tables)} NDC PLUS tables")
    
    print(f"📄 Parsing {legacy_file.name}...")
    legacy_tables = parse_legacy_schema_file(legacy_file)
    print(f"✓ Found {len(legacy_tables)} Legacy tables")
    
    # Identify relationships
    print("🔗 Identifying relationships...")
    legacy_relationships = identify_relationships(legacy_tables)
    ndc_plus_relationships = identify_relationships(ndc_plus_tables)
    cross_relationships = identify_cross_schema_relationships(legacy_tables, ndc_plus_tables)
    print(f"✓ Found {len(legacy_relationships)} Legacy relationships")
    print(f"✓ Found {len(ndc_plus_relationships)} NDC PLUS relationships")
    print(f"✓ Found {len(cross_relationships)} cross-schema mappings")
    
    # Generate dual JSON schema
    print("📝 Generating dual JSON schema...")
    json_schema = generate_dual_schema_json(legacy_tables, ndc_plus_tables, cross_relationships)
    json_output = output_dir / 'dual_schema.json'
    with open(json_output, 'w') as f:
        json.dump(json_schema, f, indent=2)
    print(f"✓ Saved to {json_output}")
    
    # Generate Markdown documentation
    print("📖 Generating dual Markdown documentation...")
    markdown_docs = generate_dual_schema_markdown(legacy_tables, ndc_plus_tables, legacy_relationships, ndc_plus_relationships, cross_relationships)
    md_output = docs_dir / 'DUAL_SCHEMA.md'
    with open(md_output, 'w') as f:
        f.write(markdown_docs)
    print(f"✓ Saved to {md_output}")
    
    print("\n✅ Dual schema documentation generated successfully!")
    print(f"\nView the documentation:")
    print(f"  - Dual JSON Schema: {json_output.relative_to(base_dir)}")
    print(f"  - Dual Markdown Docs: {md_output.relative_to(base_dir)}")


if __name__ == '__main__':
    main()
