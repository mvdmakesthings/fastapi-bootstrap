#!/bin/bash
# Interactive setup script for FastAPI Bootstrap

set -e

# Get the directory of this script
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# ASCII art banner
echo "
███████╗░█████╗░░██████╗████████╗░█████╗░██████╗░██╗  ██████╗░░█████╗░░█████╗░████████╗░██████╗████████╗██████╗░░█████╗░██████╗░
██╔════╝██╔══██╗██╔════╝╚══██╔══╝██╔══██╗██╔══██╗██║  ██╔══██╗██╔══██╗██╔══██╗╚══██╔══╝██╔════╝╚══██╔══╝██╔══██╗██╔══██╗██╔══██╗
█████╗░░███████║╚█████╗░░░░██║░░░███████║██████╔╝██║  ██████╦╝██║░░██║██║░░██║░░░██║░░░╚█████╗░░░░██║░░░██████╔╝███████║██████╔╝
██╔══╝░░██╔══██║░╚═══██╗░░░██║░░░██╔══██║██╔═══╝░██║  ██╔══██╗██║░░██║██║░░██║░░░██║░░░░╚═══██╗░░░██║░░░██╔══██╗██╔══██║██╔═══╝░
██║░░░░░██║░░██║██████╔╝░░░██║░░░██║░░██║██║░░░░░██║  ██████╦╝╚█████╔╝╚█████╔╝░░░██║░░░██████╔╝░░░██║░░░██║░░██║██║░░██║██║░░░░░
╚═╝░░░░░╚═╝░░╚═╝╚═════╝░░░░╚═╝░░░╚═╝░░╚═╝╚═╝░░░░░╚═╝  ╚═════╝░░╚════╝░░╚════╝░░░░╚═╝░░░╚═════╝░░░░╚═╝░░░╚═╝░░╚═╝╚═╝░░╚═╝╚═╝░░░░░
"
echo "Interactive Setup for FastAPI Bootstrap"
echo "--------------------------------------"
echo "This script will guide you through setting up your FastAPI Bootstrap project."
echo ""

# Check for required tools
echo "Checking for required tools..."
for tool in aws terraform docker jq curl; do
  if ! command -v $tool &> /dev/null; then
    echo "Error: $tool is not installed. Please install it and try again."
    exit 1
  fi
done
echo "✅ All required tools are installed."
echo ""

# Check AWS credentials
echo "Checking AWS credentials..."
if ! aws sts get-caller-identity &> /dev/null; then
  echo "Error: AWS credentials not configured or invalid."
  echo "Please run 'aws configure' to set up your AWS credentials."
  exit 1
fi

AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
echo "✅ AWS credentials are valid. Account ID: $AWS_ACCOUNT_ID"
echo ""

# Get organization name
read -p "Enter your organization name (used for S3 bucket naming): " ORG_NAME
while [[ -z "$ORG_NAME" ]]; do
  echo "Organization name cannot be empty."
  read -p "Enter your organization name: " ORG_NAME
done
ORG_NAME=$(echo "$ORG_NAME" | tr '[:upper:]' '[:lower:]' | tr ' ' '-')
echo ""

# Get AWS region
DEFAULT_REGION="us-east-1"
read -p "Enter AWS region [$DEFAULT_REGION]: " AWS_REGION
AWS_REGION=${AWS_REGION:-$DEFAULT_REGION}
echo ""

# Get environment
DEFAULT_ENV="dev"
read -p "Enter deployment environment (dev/test/prod) [$DEFAULT_ENV]: " ENVIRONMENT
ENVIRONMENT=${ENVIRONMENT:-$DEFAULT_ENV}
if [[ ! "$ENVIRONMENT" =~ ^(dev|test|prod)$ ]]; then
  echo "Error: Environment must be one of: dev, test, prod"
  exit 1
fi
echo ""

# Get domain name (optional)
read -p "Enter domain name for SSL certificate (leave blank for self-signed): " DOMAIN_NAME
echo ""

# Confirm settings
echo "Please confirm your settings:"
echo "----------------------------"
echo "Organization name: $ORG_NAME"
echo "AWS Account ID: $AWS_ACCOUNT_ID"
echo "AWS Region: $AWS_REGION"
echo "Environment: $ENVIRONMENT"
if [[ -n "$DOMAIN_NAME" ]]; then
  echo "Domain name: $DOMAIN_NAME"
else
  echo "Domain name: [Self-signed certificate will be used]"
fi
echo ""

read -p "Are these settings correct? (y/n): " CONFIRM
if [[ ! "$CONFIRM" =~ ^[Yy]$ ]]; then
  echo "Setup cancelled. Please run the script again with the correct settings."
  exit 0
fi
echo ""

# Setup Terraform backend
echo "Setting up Terraform backend..."
"$SCRIPT_DIR/setup-terraform-backend.sh" --org-name "$ORG_NAME" --region "$AWS_REGION"
echo "✅ Terraform backend setup complete."
echo ""

# Deploy infrastructure
echo "Deploying infrastructure..."
DEPLOY_CMD="$SCRIPT_DIR/deploy.sh --environment $ENVIRONMENT --account-id $AWS_ACCOUNT_ID --region $AWS_REGION"
if [[ -n "$DOMAIN_NAME" ]]; then
  DEPLOY_CMD="$DEPLOY_CMD --domain $DOMAIN_NAME"
fi
$DEPLOY_CMD
echo "✅ Infrastructure deployment complete."
echo ""

# Setup GitHub Actions (if applicable)
if command -v gh &> /dev/null; then
  read -p "Would you like to set up GitHub Actions secrets? (y/n): " SETUP_GH
  if [[ "$SETUP_GH" =~ ^[Yy]$ ]]; then
    echo "Setting up GitHub Actions secrets..."
    
    # Check if we're in a GitHub repo
    if gh repo view &> /dev/null; then
      gh secret set AWS_ACCESS_KEY_ID
      gh secret set AWS_SECRET_ACCESS_KEY
      gh secret set AWS_REGION --body "$AWS_REGION"
      gh secret set AWS_ACCOUNT_ID --body "$AWS_ACCOUNT_ID"
      echo "✅ GitHub Actions secrets set up successfully."
    else
      echo "Not in a GitHub repository. Skipping GitHub Actions setup."
    fi
  fi
fi
echo ""

# Generate a sample .env file
echo "Generating sample .env file..."
if [[ ! -f "$PROJECT_ROOT/.env" ]]; then
  cp "$PROJECT_ROOT/.env.example" "$PROJECT_ROOT/.env"
  echo "✅ Sample .env file created."
else
  echo "⚠️ .env file already exists. Skipping."
fi
echo ""

echo "🎉 FastAPI Bootstrap setup complete! 🎉"
echo ""
echo "Next steps:"
echo "1. Push an initial image to the ECR repository:"
ECR_REPOSITORY_URL="${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com/fastapi-bootstrap"
echo "   aws ecr get-login-password --region $AWS_REGION | docker login --username AWS --password-stdin $ECR_REPOSITORY_URL"
echo "   docker build -t $ECR_REPOSITORY_URL:latest ."
echo "   docker push $ECR_REPOSITORY_URL:latest"
echo ""
echo "2. Access your API at the URL shown above"
echo ""
echo "3. For local development, run:"
echo "   docker-compose up -d"
echo ""
echo "Documentation:"
echo "- Infrastructure: $PROJECT_ROOT/docs/infrastructure.md"
echo "- Blue/Green Deployment: $PROJECT_ROOT/docs/blue-green-deployment.md"
echo ""