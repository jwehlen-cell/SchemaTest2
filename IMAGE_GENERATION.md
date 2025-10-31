# 🎨 Mermaid Diagram Image Generation

This directory contains tools and scripts for generating PNG images from Mermaid diagrams and including them in both the repository and website deployment.

## 📁 Generated Files

### Mermaid Source Files
- `Legacy_schema.mmd` - Legacy database schema Entity Relationship Diagram
- `NDC_PLUS_schema.mmd` - NDC PLUS database schema Entity Relationship Diagram  
- `Cross_Schema_Mapping.mmd` - Cross-schema relationship mapping diagram

### PNG Output Files

#### Repository Images (`images/`)
- `legacy_schema.png` - Legacy schema ER diagram (1920x1080)
- `ndc_plus_schema.png` - NDC PLUS schema ER diagram (1920x1080)
- `cross_schema_mapping.png` - Cross-schema relationship diagram (1920x1080)

#### Website Images (`deploy/images/`)
- `legacy_schema.png` - Legacy schema for website display
- `ndc_plus_schema.png` - NDC PLUS schema for website display
- `cross_schema_mapping.png` - Cross-schema mapping for website display

### Scripts
- **`generate_images.sh`** - Main script to generate PNG images from .mmd files
- **`update_deployment_with_images.sh`** - Updates website deployment with images

## 🚀 Quick Start

### 1. Install Mermaid CLI

```bash
# Install Mermaid CLI globally
npm install -g @mermaid-js/mermaid-cli

# Verify installation
mmdc --version
```

### 2. Generate PNG Images

```bash
# Generate both Legacy and NDC PLUS schema PNGs
./generate_images.sh
```

This will create:
- `images/legacy_schema.png` (1920x1080, white background)
- `images/ndc_plus_schema.png` (1920x1080, white background)
- Copies in `deploy/images/` for website deployment

### 3. Update Website (Optional)

```bash
# Create enhanced HTML template with image viewing capability
./update_deployment_with_images.sh
```

## 📊 Image Specifications

- **Format**: PNG
- **Resolution**: 1920x1080 pixels
- **Background**: White
- **Quality**: High resolution for documentation and presentations

## 🔧 Customization

### Modify Image Settings

Edit `generate_images.sh` to change image parameters:

```bash
# Change resolution
mmdc -i Legacy_schema.mmd -o images/legacy_schema.png -w 2560 -H 1440

# Change background color
mmdc -i Legacy_schema.mmd -o images/legacy_schema.png --backgroundColor "#f8f9fa"

# Generate SVG instead of PNG
mmdc -i Legacy_schema.mmd -o images/legacy_schema.svg
```

### Add New Diagrams

1. Create new `.mmd` file with your Mermaid code
2. Add generation command to `generate_images.sh`
3. Update deployment scripts as needed

## 🌐 Website Integration

The images can be integrated into your website in several ways:

### Option 1: Image Gallery Tab
Add a "Diagrams" tab to the existing schema browser to display the ERD images alongside the interactive table browser.

### Option 2: Inline Documentation
Embed images directly in the markdown documentation for static viewing.

### Option 3: Download Links
Provide direct download links to high-resolution images for use in presentations.

## 📝 Usage Tips

### For Documentation
- Use the PNG images in README files, wikis, or presentations
- High resolution makes them suitable for printing
- White background works well in most documentation contexts

### For Development
- Images provide a visual overview of schema relationships
- Useful for onboarding new team members
- Can be embedded in code documentation tools

### For Presentations
- 1920x1080 resolution is perfect for most presentation software
- Images can be easily imported into PowerPoint, Keynote, etc.
- Consider generating SVG versions for scalable graphics

## 🛠️ Troubleshooting

### Mermaid CLI Issues
```bash
# If mmdc command not found
npm install -g @mermaid-js/mermaid-cli

# If permission issues on macOS
sudo npm install -g @mermaid-js/mermaid-cli

# Alternative: Use local installation
npx @mermaid-js/mermaid-cli -i diagram.mmd -o diagram.png
```

### Image Quality Issues
- Increase resolution with `-w` and `-H` parameters
- For very large diagrams, consider generating SVG format
- Adjust background color if needed for your documentation theme

### Browser/Platform Compatibility
- PNG format is universally supported
- Consider generating multiple formats (PNG, SVG, PDF) for different use cases

## 📚 Resources

- [Mermaid Documentation](https://mermaid.js.org/)
- [Mermaid CLI Documentation](https://mermaid.js.org/ecosystem/mermaid-cli.html)
- [Entity Relationship Diagram Syntax](https://mermaid.js.org/syntax/entityRelationshipDiagram.html)