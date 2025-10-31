#!/bin/bash

# Update deployment with PNG images
# This script updates the website deployment to include the generated PNG images

set -e

echo "🖼️ Updating website deployment with PNG images..."
echo "==============================================="

# Check if images exist
if [ ! -f "images/legacy_schema.png" ] || [ ! -f "images/ndc_plus_schema.png" ]; then
    echo "❌ PNG images not found. Please run ./generate_images.sh first."
    exit 1
fi

echo "✅ PNG images found"

# Copy images to deployment
mkdir -p deploy/images
cp images/legacy_schema.png deploy/images/
cp images/ndc_plus_schema.png deploy/images/

echo "✅ Images copied to deployment folder"

# Create updated HTML with image tabs
cat > deploy/index_with_images.html << 'EOF'
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>NDC PLUS & Legacy Database Schema Browser</title>
    <meta name="description" content="Interactive browser for NDC PLUS and Legacy seismic monitoring database schemas with visual diagrams.">
    <style>
        /* Include all the existing styles from index.html */
        /* ... styles would be copied from the main index.html ... */
        
        .diagram-section {
            background-color: white;
            border-radius: 8px;
            margin: 20px 0;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        
        .diagram-header {
            background: linear-gradient(135deg, #3498db, #2c3e50);
            color: white;
            padding: 20px;
            border-radius: 8px 8px 0 0;
        }
        
        .diagram-content {
            padding: 20px;
            text-align: center;
        }
        
        .diagram-image {
            max-width: 100%;
            height: auto;
            border: 1px solid #ddd;
            border-radius: 4px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        }
        
        .view-tabs {
            display: flex;
            background-color: #f8f9fa;
            border-radius: 8px;
            padding: 4px;
            margin-bottom: 20px;
        }
        
        .view-tab {
            flex: 1;
            padding: 12px 20px;
            text-align: center;
            background: none;
            border: none;
            border-radius: 6px;
            cursor: pointer;
            transition: all 0.3s ease;
            font-size: 14px;
            font-weight: 500;
        }
        
        .view-tab.active {
            background-color: #3498db;
            color: white;
        }
        
        .view-tab:hover:not(.active) {
            background-color: #e9ecef;
        }
        
        .view-content {
            display: none;
        }
        
        .view-content.active {
            display: block;
        }
    </style>
</head>
<body>
    <!-- Copy sidebar and basic structure from index.html -->
    
    <div class="main-content">
        <!-- Copy header from index.html -->
        
        <div class="view-tabs">
            <button class="view-tab active" onclick="switchView('browser')">📊 Table Browser</button>
            <button class="view-tab" onclick="switchView('diagrams')">🎨 Schema Diagrams</button>
        </div>
        
        <div id="browserView" class="view-content active">
            <!-- Copy existing browser content from index.html -->
        </div>
        
        <div id="diagramsView" class="view-content">
            <div class="diagram-section">
                <div class="diagram-header">
                    <h2>🏛️ Legacy Schema Entity Relationship Diagram</h2>
                    <p>Traditional seismic analysis database design (17 tables)</p>
                </div>
                <div class="diagram-content">
                    <img src="images/legacy_schema.png" alt="Legacy Schema ERD" class="diagram-image">
                </div>
            </div>
            
            <div class="diagram-section">
                <div class="diagram-header">
                    <h2>🚀 NDC PLUS Schema Entity Relationship Diagram</h2>
                    <p>Modern event processing database design (35 tables)</p>
                </div>
                <div class="diagram-content">
                    <img src="images/ndc_plus_schema.png" alt="NDC PLUS Schema ERD" class="diagram-image">
                </div>
            </div>
        </div>
    </div>
    
    <script>
        function switchView(view) {
            // Hide all views
            document.querySelectorAll('.view-content').forEach(content => {
                content.classList.remove('active');
            });
            
            // Remove active class from all tabs
            document.querySelectorAll('.view-tab').forEach(tab => {
                tab.classList.remove('active');
            });
            
            // Show selected view
            document.getElementById(view + 'View').classList.add('active');
            
            // Activate selected tab
            event.target.classList.add('active');
        }
        
        // Copy existing JavaScript from index.html
    </script>
</body>
</html>
EOF

echo "✅ Created enhanced HTML template with image support"

echo ""
echo "🎯 Next Steps:"
echo "1. Run ./generate_images.sh to create PNG files"
echo "2. Customize deploy/index_with_images.html as needed"
echo "3. Replace deploy/index.html with the enhanced version"
echo "4. Deploy to AWS with the new images"