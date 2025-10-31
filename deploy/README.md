# 🚀 AWS S3 Deployment Guide - NDC Schema Browser

This guide will help you deploy your schema browser to AWS S3 as a public website.

## 📋 Prerequisites

Before you begin, ensure you have:

1. **AWS Account**: An active AWS account with appropriate permissions
2. **AWS CLI**: Installed and configured on your machine
3. **Permissions**: IAM permissions for S3 bucket operations

## 🛠️ Setup Instructions

### Step 1: Install AWS CLI (if not already installed)

**macOS (using Homebrew):**
```bash
brew install awscli
```

**macOS/Linux (using pip):**
```bash
pip install awscli
```

**Windows:**
Download from: https://aws.amazon.com/cli/

### Step 2: Configure AWS CLI

Run the configuration command and enter your credentials:

```bash
aws configure
```

You'll need to provide:
- **AWS Access Key ID**: Your AWS access key
- **AWS Secret Access Key**: Your secret key
- **Default region**: `us-east-1`
- **Default output format**: `json`

### Step 3: Verify AWS Configuration

Test your configuration:
```bash
aws sts get-caller-identity
```

You should see your account details if configured correctly.

## 🚀 Deployment Process

### Option 1: Automated Deployment (Recommended)

Simply run the deployment script:

```bash
cd /Users/josephwehlen/dev/SchemaTest2
./deploy/deploy.sh
```

The script will:
1. ✅ Create the S3 bucket `ndc-schematest`
2. ✅ Configure it for website hosting
3. ✅ Set public read permissions
4. ✅ Upload your files
5. ✅ Provide the website URL

### Option 2: Manual Deployment

If you prefer manual control, follow these steps:

#### 1. Create S3 Bucket
```bash
aws s3api create-bucket --bucket ndc-schematest --region us-east-1
```

#### 2. Enable Website Hosting
```bash
aws s3 website s3://ndc-schematest --index-document index.html --error-document index.html
```

#### 3. Set Bucket Policy
```bash
aws s3api put-bucket-policy --bucket ndc-schematest --policy file://deploy/bucket-policy.json
```

#### 4. Upload Files
```bash
aws s3 cp deploy/index.html s3://ndc-schematest/index.html --content-type "text/html"
aws s3 cp deploy/schema_data.json s3://ndc-schematest/schema_data.json --content-type "application/json"
```

## 🌐 Your Website

After successful deployment, your schema browser will be available at:

**🔗 http://ndc-schematest.s3-website-us-east-1.amazonaws.com**

## 📊 What's Deployed

Your deployment includes:

- **`index.html`**: The main schema browser application
- **`schema_data.json`**: Complete schema data for both Legacy and NDC PLUS
- **Public Access**: Anyone can view the website
- **Responsive Design**: Works on desktop and mobile devices

## 🔧 Updating Your Site

To update the website after making changes:

1. Regenerate the schema data (if needed):
   ```bash
   python tools/parse_schema.py
   cp schema/dual_schema.json deploy/schema_data.json
   ```

2. Re-run the deployment script:
   ```bash
   ./deploy/deploy.sh
   ```

## 💰 Cost Information

**S3 Website Hosting Costs:**
- **Storage**: ~$0.02 per month (for a few KB of files)
- **Requests**: ~$0.0004 per 1,000 requests
- **Data Transfer**: First 1 GB free per month

Total estimated cost: **Less than $1 per month** for typical usage.

## 🔒 Security Considerations

- ✅ **Read-Only Access**: The bucket policy only allows public read access
- ✅ **No Sensitive Data**: Schema documentation contains no sensitive information
- ✅ **HTTPS Available**: AWS provides HTTPS access automatically
- ⚠️ **Public Website**: Anyone with the URL can access the site

## 🛠️ Troubleshooting

### Common Issues:

**❌ "Bucket name already exists"**
- Solution: Change `BUCKET_NAME` in `deploy.sh` to something unique

**❌ "Access Denied"**
- Solution: Check your AWS credentials and permissions

**❌ "AWS CLI not found"**
- Solution: Install AWS CLI following the setup instructions above

**❌ "Website shows 404"**
- Solution: Wait a few minutes for DNS propagation, or check the exact URL

### Support Commands:

**Check bucket status:**
```bash
aws s3api head-bucket --bucket ndc-schematest
```

**List bucket contents:**
```bash
aws s3 ls s3://ndc-schematest/
```

**Delete bucket (if needed):**
```bash
aws s3 rm s3://ndc-schematest --recursive
aws s3api delete-bucket --bucket ndc-schematest
```

## 🎯 Next Steps

After deployment, you can:

1. **Share the URL** with your team and stakeholders
2. **Bookmark** the site for easy access
3. **Update content** by re-running the deployment script
4. **Monitor usage** through AWS CloudWatch (optional)
5. **Add a custom domain** using Route 53 (optional)

## 📞 Need Help?

If you encounter issues:

1. Check the troubleshooting section above
2. Verify your AWS credentials and permissions
3. Ensure the deployment files are in the correct location
4. Review AWS S3 documentation for additional help

---

**🎉 Congratulations!** Your NDC Schema Browser is now live and accessible worldwide!