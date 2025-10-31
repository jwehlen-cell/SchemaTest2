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
    doc.append("    subgraph Legacy[\"🏛️ Legacy Schema\"]\n")
    doc.append("        direction TB\n")
    doc.append("        subgraph LegacyEvent[\"Event Management\"]\n")
    doc.append("            L_EVENT[EVENT]\n")
    doc.append("            L_EVENT_CONTROL[EVENT_CONTROL]\n")
    doc.append("            L_EVENT_CORRELATION[EVENT_CORRELATION]\n")
    doc.append("        end\n")
    doc.append("        subgraph LegacyMeasure[\"Measurements\"]\n")
    doc.append("            L_ARRIVAL[ARRIVAL]\n")
    doc.append("            L_AMPLITUDE[AMPLITUDE]\n")
    doc.append("            L_AMPLITUDE_DYN[AMPLITUDE_DYN_PARS_INT]\n")
    doc.append("            L_ARRIVAL_DYN[ARRIVAL_DYN_PARS_INT]\n")
    doc.append("        end\n")
    doc.append("        subgraph LegacyLocation[\"Location Analysis\"]\n")
    doc.append("            L_ORIGIN[ORIGIN]\n")
    doc.append("            L_ORIGERR[ORIGERR]\n")
    doc.append("            L_ASSOC[ASSOC]\n")
    doc.append("        end\n")
    doc.append("        subgraph LegacyMagnitude[\"Magnitude\"]\n")
    doc.append("            L_STAMAG[STAMAG]\n")
    doc.append("            L_NETMAG[NETMAG]\n")
    doc.append("        end\n")
    doc.append("        subgraph LegacyMeta[\"Metadata\"]\n")
    doc.append("            L_ACTIVE_ID[ACTIVE_ID]\n")
    doc.append("            L_WFTAG[WFTAG]\n")
    doc.append("            L_AR_INFO[AR_INFO]\n")
    doc.append("            L_REMARK[REMARK]\n")
    doc.append("            L_QCMASKINFO[QCMASKINFO]\n")
    doc.append("        end\n")
    doc.append("    end\n")
    doc.append("    \n")
    doc.append("    subgraph NDC[\"🚀 NDC PLUS Schema\"]\n")
    doc.append("        direction TB\n")
    doc.append("        subgraph NDCChannel[\"Channel & Waveform\"]\n")
    doc.append("            N_CHANNEL_SEGMENT[CHANNEL_SEGMENT]\n")
    doc.append("            N_CHANNEL_CREATION[CHANNEL_SEGMENT_CREATION]\n")
    doc.append("            N_CHANNEL_PROC[CHANNEL_SEGMENT_PROC_MASK_XREF]\n")
    doc.append("            N_CHANNEL_WAVEFORM[CHANNEL_SEGMENT_WAVEFORM]\n")
    doc.append("            N_STATION_CHANNEL[STATION_CHANNEL]\n")
    doc.append("        end\n")
    doc.append("        subgraph NDCEvent[\"Event Management\"]\n")
    doc.append("            N_EVENT[EVENT]\n")
    doc.append("            N_EVENT_HYPOTHESIS[EVENT_HYPOTHESIS]\n")
    doc.append("            N_EVENT_HYPOTHESIS_TAG[EVENT_HYPOTHESIS_TAG]\n")
    doc.append("            N_EVENT_STATUS[EVENT_STATUS_INFO]\n")
    doc.append("            N_EVENT_CORRELATION[EVENT_CORRELATION]\n")
    doc.append("            N_EVENT_CORR_CHAN[EVENT_CORRELATION_CHANNEL_SEGMENT]\n")
    doc.append("        end\n")
    doc.append("        subgraph NDCFeatureMeas[\"Feature Measurements\"]\n")
    doc.append("            N_FEAT_AMP[FEATURE_MEASUREMENT_AMPLITUDE]\n")
    doc.append("            N_FEAT_ARR[FEATURE_MEASUREMENT_ARRIVAL_TIME]\n")
    doc.append("            N_FEAT_ENUM[FEATURE_MEASUREMENT_ENUMERATED]\n")
    doc.append("            N_FEAT_NUM[FEATURE_MEASUREMENT_NUMERIC]\n")
    doc.append("        end\n")
    doc.append("        subgraph NDCFeaturePred[\"Feature Predictions\"]\n")
    doc.append("            N_PRED_ARR[FEATURE_PREDICTION_ARRIVAL_TIME]\n")
    doc.append("            N_PRED_COMP[FEATURE_PREDICTION_COMPONENT]\n")
    doc.append("            N_PRED_NUM[FEATURE_PREDICTION_NUMERIC]\n")
    doc.append("        end\n")
    doc.append("        subgraph NDCLocation[\"Location & Uncertainty\"]\n")
    doc.append("            N_LOC_SOL[LOCATION_SOLUTION]\n")
    doc.append("            N_LOC_BEHAV[LOCATION_BEHAVIOR]\n")
    doc.append("            N_LOC_RESTRAINT[LOCATION_RESTRAINT]\n")
    doc.append("            N_LOC_UNCERT[LOCATION_UNCERTAINTY]\n")
    doc.append("            N_LOC_ELLIPSE[LOCATION_UNCERTAINTY_ELLIPSE]\n")
    doc.append("            N_LOC_ELLIPSOID[LOCATION_UNCERTAINTY_ELLIPSOID]\n")
    doc.append("        end\n")
    doc.append("        subgraph NDCMagnitude[\"Magnitude\"]\n")
    doc.append("            N_NET_MAG[NETWORK_MAGNITUDE_SOLUTION]\n")
    doc.append("            N_STA_MAG[STATION_MAGNITUDE_SOLUTION]\n")
    doc.append("        end\n")
    doc.append("        subgraph NDCQuality[\"Quality Control\"]\n")
    doc.append("            N_PROC_MASK[PROCESSING_MASK]\n")
    doc.append("            N_PROC_QC[PROCESSING_MASK_QC_SEGMENT_VERSION]\n")
    doc.append("            N_QC_SEGMENT[QC_SEGMENT_VERSION]\n")
    doc.append("        end\n")
    doc.append("        subgraph NDCSignal[\"Signal Detection\"]\n")
    doc.append("            N_SIGNAL_DET[SIGNAL_DETECTION_HYPOTHESIS]\n")
    doc.append("            N_INTERVAL[INTERVAL]\n")
    doc.append("        end\n")
    doc.append("        subgraph NDCMeta[\"Metadata & Config\"]\n")
    doc.append("            N_STATION_GROUP[STATION_GROUP_VERSION]\n")
    doc.append("            N_RESPONSE[RESPONSE_TABLE]\n")
    doc.append("            N_REMARK[REMARK]\n")
    doc.append("            N_STAGE_METRICS[STAGE_METRICS]\n")
    doc.append("        end\n")
    doc.append("    end\n")
    doc.append("    \n")
    doc.append("    %% Cross-schema conceptual mappings\n")
    doc.append("    L_EVENT -.->|\"Conceptual Mapping\"| N_EVENT\n")
    doc.append("    L_ARRIVAL -.->|\"Enhanced Measurement\"| N_FEAT_ARR\n")
    doc.append("    L_AMPLITUDE -.->|\"Enhanced Measurement\"| N_FEAT_AMP\n")
    doc.append("    L_ORIGIN -.->|\"Enhanced Location\"| N_LOC_SOL\n")
    doc.append("    L_ASSOC -.->|\"Advanced Detection\"| N_SIGNAL_DET\n")
    doc.append("    L_STAMAG -.->|\"Enhanced Magnitude\"| N_STA_MAG\n")
    doc.append("    L_NETMAG -.->|\"Enhanced Magnitude\"| N_NET_MAG\n")
    doc.append("    L_REMARK -.->|\"Direct Mapping\"| N_REMARK\n")
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
    doc.append("    %% Event Management Flow\n")
    doc.append("    EVENT[\"📊 EVENT<br/>Master Records\"] --> ORIGIN[\"🌍 ORIGIN<br/>Location Solutions\"]\n")
    doc.append("    EVENT_CONTROL[\"⚙️ EVENT_CONTROL<br/>Processing Control\"] --> EVENT\n")
    doc.append("    EVENT_CORRELATION[\"🔗 EVENT_CORRELATION<br/>Cross-correlation\"] --> EVENT\n")
    doc.append("    \n")
    doc.append("    %% Location and Association\n")
    doc.append("    ORIGIN --> ASSOC[\"🔗 ASSOC<br/>Arrival Associations\"]\n")
    doc.append("    ORIGIN --> ORIGERR[\"❌ ORIGERR<br/>Location Errors\"]\n")
    doc.append("    ASSOC --> ARRIVAL[\"📡 ARRIVAL<br/>Phase Arrivals\"]\n")
    doc.append("    \n")
    doc.append("    %% Amplitude and Magnitude\n")
    doc.append("    ARRIVAL --> AMPLITUDE[\"📈 AMPLITUDE<br/>Signal Measurements\"]\n")
    doc.append("    AMPLITUDE --> AMPLITUDE_DYN_PARS_INT[\"⚙️ AMPLITUDE_DYN_PARS_INT<br/>Dynamic Parameters\"]\n")
    doc.append("    ARRIVAL --> ARRIVAL_DYN_PARS_INT[\"⚙️ ARRIVAL_DYN_PARS_INT<br/>Dynamic Parameters\"]\n")
    doc.append("    \n")
    doc.append("    %% Magnitude Calculations\n")
    doc.append("    AMPLITUDE --> STAMAG[\"📏 STAMAG<br/>Station Magnitude\"]\n")
    doc.append("    STAMAG --> NETMAG[\"🌐 NETMAG<br/>Network Magnitude\"]\n")
    doc.append("    \n")
    doc.append("    %% Metadata and Quality Control\n")
    doc.append("    ACTIVE_ID[\"🏷️ ACTIVE_ID<br/>Active Tags\"] -.-> EVENT\n")
    doc.append("    WFTAG[\"🏷️ WFTAG<br/>Waveform Tags\"] -.-> AMPLITUDE\n")
    doc.append("    AR_INFO[\"ℹ️ AR_INFO<br/>AR Model Info\"] -.-> ARRIVAL\n")
    doc.append("    REMARK[\"💬 REMARK<br/>Comments\"] -.-> EVENT\n")
    doc.append("    QCMASKINFO[\"✅ QCMASKINFO<br/>Quality Control\"] -.-> ARRIVAL\n")
    doc.append("    \n")
    doc.append("    %% Styling\n")
    doc.append("    classDef eventClass fill:#e1f5fe,stroke:#01579b,stroke-width:2px\n")
    doc.append("    classDef measureClass fill:#f3e5f5,stroke:#4a148c,stroke-width:2px\n")
    doc.append("    classDef locationClass fill:#e8f5e8,stroke:#1b5e20,stroke-width:2px\n")
    doc.append("    classDef metaClass fill:#fff3e0,stroke:#e65100,stroke-width:2px\n")
    doc.append("    \n")
    doc.append("    class EVENT,EVENT_CONTROL,EVENT_CORRELATION eventClass\n")
    doc.append("    class ARRIVAL,AMPLITUDE,ARRIVAL_DYN_PARS_INT,AMPLITUDE_DYN_PARS_INT,STAMAG,NETMAG measureClass\n")
    doc.append("    class ORIGIN,ORIGERR,ASSOC locationClass\n")
    doc.append("    class ACTIVE_ID,WFTAG,AR_INFO,REMARK,QCMASKINFO metaClass\n")
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
    doc.append("    %% Core Event Processing\n")
    doc.append("    SCENARIO[\"📋 SCENARIO<br/>Analysis Contexts\"] --> SCENARIO_REVISION[\"🔄 SCENARIO_REVISION<br/>Version Control\"]\n")
    doc.append("    SCENARIO_REVISION --> SCENARIO_EVENTS[\"🔗 SCENARIO_EVENTS<br/>Event Associations\"]\n")
    doc.append("    SCENARIO_EVENTS --> SCENARIO_ORIGINS[\"📍 SCENARIO_ORIGINS<br/>Location Solutions\"]\n")
    doc.append("    \n")
    doc.append("    %% Detection Processing\n")
    doc.append("    DETECTION_IDC[\"🔍 DETECTION_IDC<br/>IDC Detections\"] --> CHANNEL_RESPONSE[\"📡 CHANNEL_RESPONSE<br/>Instrument Response\"]\n")
    doc.append("    DETECTION_IDC --> WAVEFORM_SEGMENT[\"🌊 WAVEFORM_SEGMENT<br/>Data Segments\"]\n")
    doc.append("    \n")
    doc.append("    %% Station and Network Data\n")
    doc.append("    STATION[\"🏠 STATION<br/>Site Information\"] --> SITE[\"📍 SITE<br/>Geographic Locations\"]\n")
    doc.append("    STATION --> CHANNEL[\"📊 CHANNEL<br/>Recording Channels\"]\n")
    doc.append("    CHANNEL --> SENSOR[\"🔧 SENSOR<br/>Physical Sensors\"]\n")
    doc.append("    CHANNEL --> CHANNEL_RESPONSE\n")
    doc.append("    \n")
    doc.append("    %% Magnitude Processing\n")
    doc.append("    MAGNITUDE_IDC[\"📏 MAGNITUDE_IDC<br/>IDC Magnitudes\"] --> MAGNITUDE_METHOD_REFERENCE[\"📋 MAGNITUDE_METHOD_REFERENCE<br/>Calculation Methods\"]\n")
    doc.append("    MAGNITUDE_IDC --> STATION_MAGNITUDE_IDC[\"📊 STATION_MAGNITUDE_IDC<br/>Station Values\"]\n")
    doc.append("    \n")
    doc.append("    %% Observation and Analysis\n")
    doc.append("    OBSERVATION[\"👁️ OBSERVATION<br/>Analyst Observations\"] --> PHASE_MEASUREMENT[\"⏱️ PHASE_MEASUREMENT<br/>Timing Measurements\"]\n")
    doc.append("    OBSERVATION --> OBSERVATION_MAGNITUDE[\"📈 OBSERVATION_MAGNITUDE<br/>Magnitude Estimates\"]\n")
    doc.append("    \n")
    doc.append("    %% Waveform Processing\n")
    doc.append("    WAVEFORM_SUMMARY[\"📊 WAVEFORM_SUMMARY<br/>Summary Statistics\"] --> WAVEFORM_SEGMENT\n")
    doc.append("    FK_SPECTRUM_DEFINITION[\"🔄 FK_SPECTRUM_DEFINITION<br/>FK Analysis Setup\"] --> FK_SPECTRA[\"🌈 FK_SPECTRA<br/>FK Results\"]\n")
    doc.append("    \n")
    doc.append("    %% Calibration and Response\n")
    doc.append("    CALIBRATION[\"⚖️ CALIBRATION<br/>Instrument Calibration\"] --> INSTRUMENT[\"🔧 INSTRUMENT<br/>Recording Equipment\"]\n")
    doc.append("    INSTRUMENT --> SENSOR\n")
    doc.append("    RESPONSE[\"📈 RESPONSE<br/>Frequency Response\"] --> CHANNEL_RESPONSE\n")
    doc.append("    \n")
    doc.append("    %% Reference Data\n")
    doc.append("    EARTH_MODEL[\"🌍 EARTH_MODEL<br/>Velocity Models\"] -.-> SCENARIO\n")
    doc.append("    FILTER_DEFINITION[\"🔍 FILTER_DEFINITION<br/>Signal Filters\"] -.-> WAVEFORM_SEGMENT\n")
    doc.append("    BEAM_RECIPE[\"📡 BEAM_RECIPE<br/>Array Processing\"] -.-> CHANNEL\n")
    doc.append("    \n")
    doc.append("    %% Quality and Metadata\n")
    doc.append("    GIS_CONTINENT[\"🗺️ GIS_CONTINENT<br/>Geographic Regions\"] -.-> SITE\n")
    doc.append("    QUALITY_SUMMARY[\"✅ QUALITY_SUMMARY<br/>Data Quality\"] -.-> WAVEFORM_SEGMENT\n")
    doc.append("    \n")
    doc.append("    %% Styling\n")
    doc.append("    classDef scenarioClass fill:#e3f2fd,stroke:#0277bd,stroke-width:2px\n")
    doc.append("    classDef detectionClass fill:#f1f8e9,stroke:#33691e,stroke-width:2px\n")
    doc.append("    classDef stationClass fill:#fce4ec,stroke:#ad1457,stroke-width:2px\n")
    doc.append("    classDef magnitudeClass fill:#f3e5f5,stroke:#7b1fa2,stroke-width:2px\n")
    doc.append("    classDef observationClass fill:#fff8e1,stroke:#f57f17,stroke-width:2px\n")
    doc.append("    classDef waveformClass fill:#e8f5e8,stroke:#2e7d32,stroke-width:2px\n")
    doc.append("    classDef referenceClass fill:#fafafa,stroke:#616161,stroke-width:2px\n")
    doc.append("    \n")
    doc.append("    class SCENARIO,SCENARIO_REVISION,SCENARIO_EVENTS,SCENARIO_ORIGINS scenarioClass\n")
    doc.append("    class DETECTION_IDC,OBSERVATION,PHASE_MEASUREMENT,OBSERVATION_MAGNITUDE detectionClass\n")
    doc.append("    class STATION,SITE,CHANNEL,SENSOR,INSTRUMENT stationClass\n")
    doc.append("    class MAGNITUDE_IDC,MAGNITUDE_METHOD_REFERENCE,STATION_MAGNITUDE_IDC magnitudeClass\n")
    doc.append("    class WAVEFORM_SUMMARY,WAVEFORM_SEGMENT,FK_SPECTRUM_DEFINITION,FK_SPECTRA waveformClass\n")
    doc.append("    class EARTH_MODEL,FILTER_DEFINITION,BEAM_RECIPE,GIS_CONTINENT,QUALITY_SUMMARY,CALIBRATION,RESPONSE,CHANNEL_RESPONSE referenceClass\n")
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
