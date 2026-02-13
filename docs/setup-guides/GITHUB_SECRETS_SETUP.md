# GitHub Secrets Setup for Vercel Deployment

## Required Secrets

Configure these secrets in GitHub Actions before deployment:

### 1. VERCEL_TOKEN
- **What**: Vercel API authentication token
- **Get it**: https://vercel.com/account/tokens
- Click "Create Token", name it "GitHub Actions BBBot", click "Create"

### 2. VERCEL_ORG_ID  
- **What**: Your Vercel organization/team ID
- **Get it**: Vercel Dashboard → Settings → Organization ID

### 3. VERCEL_PROJECT_ID
- **What**: Your specific Vercel project ID  
- **Get it**: Project → Settings → Project ID

### 4. VERCEL_SCOPE
- **What**: Team name or username for deployment scope
- **Get it**: Personal account use username, Team use team slug from URL

## How to Add

1. Go to: https://github.com/winstonwilliamsiii/BBBot/settings/secrets/actions
2. Click "New repository secret"
3. Add each secret with exact name (case-sensitive)
4. Verify all 4 secrets are listed

## Next Steps

After adding secrets:
