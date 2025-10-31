#!/bin/bash

# NDC Schema Browser - AWS S3 Deployment Script
# This script deploys the schema browser to AWS S3 as a static website

set -e  # Exit on any error

# Configuration
BUCKET_NAME="ndc-schematest"
REGION="us-east-1"
DEPLOY_DIR="deploy"

echo "🚀 NDC Schema Browser - AWS S3 Deployment"
echo "==========================================="
echo "Bucket: $BUCKET_NAME"
echo "Region: $REGION"
echo ""

# Check if AWS CLI is installed
if ! command -v aws &> /dev/null; then
    echo "❌ AWS CLI is not installed. Please install it first:"
    echo "   https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html"
    exit 1
fi

# Check if AWS CLI is configured
if ! aws sts get-caller-identity &> /dev/null; then
    echo "❌ AWS CLI is not configured. Please run 'aws configure' first."
    exit 1
fi

echo "✅ AWS CLI is installed and configured"

# Check if deployment directory exists
if [ ! -d "$DEPLOY_DIR" ]; then
    echo "❌ Deployment directory '$DEPLOY_DIR' not found"
    exit 1
fi

echo "✅ Deployment directory found"

# Step 1: Create S3 bucket
echo ""
echo "📦 Step 1: Creating S3 bucket..."
if aws s3api head-bucket --bucket "$BUCKET_NAME" 2>/dev/null; then
    echo "⚠️  Bucket '$BUCKET_NAME' already exists"
else
    if aws s3api create-bucket --bucket "$BUCKET_NAME" --region "$REGION"; then
        echo "✅ Bucket '$BUCKET_NAME' created successfully"
    else
        echo "❌ Failed to create bucket. The name might be taken globally."
        echo "   Try using a different bucket name by editing this script."
        exit 1
    fi
fi

# Step 2: Configure bucket for website hosting
echo ""
echo "🌐 Step 2: Configuring bucket for website hosting..."
aws s3 website "s3://$BUCKET_NAME" --index-document index.html --error-document index.html

echo "✅ Website hosting configured"

# Step 3: Apply bucket policy for public access
echo ""
echo "🔓 Step 3: Setting bucket policy for public access..."
aws s3api put-bucket-policy --bucket "$BUCKET_NAME" --policy file://"$DEPLOY_DIR/bucket-policy.json"

echo "✅ Bucket policy applied"

# Step 4: Upload files
echo ""
echo "📤 Step 4: Uploading files to S3..."

# Upload HTML file with proper content type
aws s3 cp "$DEPLOY_DIR/index.html" "s3://$BUCKET_NAME/index.html" \
    --content-type "text/html" \
    --cache-control "max-age=300"

# Upload JSON file with proper content type
aws s3 cp "$DEPLOY_DIR/schema_data.json" "s3://$BUCKET_NAME/schema_data.json" \
    --content-type "application/json" \
    --cache-control "max-age=3600"

# Upload images directory if it exists
if [ -d "$DEPLOY_DIR/images" ]; then
    echo "📸 Uploading diagram images..."
    aws s3 cp "$DEPLOY_DIR/images/" "s3://$BUCKET_NAME/images/" \
        --recursive \
        --content-type "image/png" \
        --cache-control "max-age=86400"
fi

echo "✅ Files uploaded successfully"

# Step 5: Get website URL
echo ""
echo "🌍 Step 5: Getting website URL..."
WEBSITE_URL="http://$BUCKET_NAME.s3-website-$REGION.amazonaws.com"

echo ""
echo "🎉 Deployment Complete!"
echo "======================="
echo "Your schema browser is now live at:"
echo "🔗 $WEBSITE_URL"
echo ""
echo "📊 Deployment Summary:"
echo "   • Bucket: $BUCKET_NAME"
echo "   • Region: $REGION"
echo "   • Files: index.html, schema_data.json"
echo "   • Access: Public (read-only)"
echo ""
echo "💡 Tips:"
echo "   • Bookmark the URL for easy access"
echo "   • Share the URL with your team"
echo "   • To update, re-run this script after making changes"
echo ""

# Optional: Open in browser (macOS only)
if [[ "$OSTYPE" == "darwin"* ]]; then
    read -p "🌐 Open website in browser? (y/n): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        open "$WEBSITE_URL"
    fi
fi

echo "✨ Deployment script completed successfully!"