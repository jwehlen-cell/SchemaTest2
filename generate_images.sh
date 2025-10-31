#!/bin/bash

# Script to generate PNG images from Mermaid diagrams
# Requires: Mermaid CLI (mmdc) to be installed
# Install with: npm install -g @mermaid-js/mermaid-cli

set -e  # Exit on any error

echo "🎨 Generating PNG images from Mermaid diagrams..."
echo "================================================"

# Check if Mermaid CLI is installed
if ! command -v mmdc &> /dev/null; then
    echo "❌ Mermaid CLI (mmdc) is not installed."
    echo "📦 Install it with: npm install -g @mermaid-js/mermaid-cli"
    echo "📚 More info: https://mermaid.js.org/ecosystem/mermaid-cli.html"
    exit 1
fi

echo "✅ Mermaid CLI found"

# Create images directory if it doesn't exist
mkdir -p images

# Generate Legacy schema PNG
echo "🏛️ Generating Legacy schema diagram..."
if mmdc -i Legacy_schema.mmd -o images/legacy_schema.png -w 1920 -H 1080 --backgroundColor white; then
    echo "✅ Legacy schema PNG generated: images/legacy_schema.png"
else
    echo "❌ Failed to generate Legacy schema PNG"
    exit 1
fi

# Generate NDC PLUS schema PNG
echo "🚀 Generating NDC PLUS schema diagram..."
if mmdc -i NDC_PLUS_schema.mmd -o images/ndc_plus_schema.png -w 1920 -H 1080 --backgroundColor white; then
    echo "✅ NDC PLUS schema PNG generated: images/ndc_plus_schema.png"
else
    echo "❌ Failed to generate NDC PLUS schema PNG"
    exit 1
fi

# Copy images to deployment folder for website
echo "📤 Copying images to deployment folder..."
mkdir -p deploy/images
cp images/legacy_schema.png deploy/images/
cp images/ndc_plus_schema.png deploy/images/

echo ""
echo "🎉 PNG Generation Complete!"
echo "==========================="
echo "📁 Repository images:"
echo "   • images/legacy_schema.png"
echo "   • images/ndc_plus_schema.png"
echo ""
echo "🌐 Website images:"
echo "   • deploy/images/legacy_schema.png"
echo "   • deploy/images/ndc_plus_schema.png"
echo ""
echo "💡 Next steps:"
echo "   • Review the generated images"
echo "   • Update documentation to reference the images"
echo "   • Commit the new images to the repository"
echo "   • Redeploy the website to include the images"