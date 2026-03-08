#!/bin/bash

# AWS Deployment Script for Krishi Application
# This script handles deployment to AWS using SAM

set -e  # Exit on any error

# Configuration
STACK_NAME="krishi-app"
REGION="ap-south-1"
ENVIRONMENT="${1:-dev}"
TEMPLATE_FILE="template.yaml"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Logging function
log() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')] $1${NC}"
}

error() {
    echo -e "${RED}[$(date +'%Y-%m-%d %H:%M:%S')] ERROR: $1${NC}"
    exit 1
}

warning() {
    echo -e "${YELLOW}[$(date +'%Y-%m-%d %H:%M:%S')] WARNING: $1${NC}"
}

# Check prerequisites
check_prerequisites() {
    log "Checking prerequisites..."
    
    # Check AWS CLI
    if ! command -v aws &> /dev/null; then
        error "AWS CLI is not installed or not in PATH"
    fi
    
    # Check SAM CLI
    if ! command -v sam &> /dev/null; then
        error "AWS SAM CLI is not installed or not in PATH"
    fi
    
    # Check Docker
    if ! command -v docker &> /dev/null; then
        error "Docker is not installed or not in PATH"
    fi
    
    # Check AWS credentials
    if ! aws sts get-caller-identity &> /dev/null; then
        error "AWS credentials are not configured properly"
    fi
    
    log "Prerequisites check passed"
}

# Validate template
validate_template() {
    log "Validating SAM template..."
    
    if ! sam validate -t "$TEMPLATE_FILE"; then
        error "SAM template validation failed"
    fi
    
    log "Template validation passed"
}

# Build application
build_application() {
    log "Building application..."
    
    # Use build arguments for environment-specific configuration
    sam build \
        --template-file "$TEMPLATE_FILE" \
        --parameter-overrides \
            Environment="$ENVIRONMENT" \
            UseAWSAI="true" \
        --build-dir ".aws-sam/build-$ENVIRONMENT"
    
    log "Application build completed"
}

# Deploy application
deploy_application() {
    log "Deploying application to AWS..."
    
    # Generate unique stack name with environment
    STACK_NAME_ENV="${STACK_NAME}-${ENVIRONMENT}"
    
    # Deploy with capabilities
    sam deploy \
        --template-file ".aws-sam/build-$ENVIRONMENT/template.yaml" \
        --stack-name "$STACK_NAME_ENV" \
        --capabilities CAPABILITY_IAM CAPABILITY_NAMED_IAM \
        --parameter-overrides \
            Environment="$ENVIRONMENT" \
            UseAWSAI="true" \
        --region "$REGION" \
        --no-confirm-changeset \
        --no-fail-on-empty-changeset
    
    log "Application deployment completed"
}

# Get deployment outputs
get_outputs() {
    log "Retrieving deployment outputs..."
    
    STACK_NAME_ENV="${STACK_NAME}-${ENVIRONMENT}"
    
    # Get API Gateway URL
    API_URL=$(aws cloudformation describe-stacks \
        --stack-name "$STACK_NAME_ENV" \
        --region "$REGION" \
        --query 'Stacks[0].Outputs[?OutputKey==`ApiUrl`].OutputValue' \
        --output text)
    
    # Get Lambda function ARN
    LAMBDA_ARN=$(aws cloudformation describe-stacks \
        --stack-name "$STACK_NAME_ENV" \
        --region "$REGION" \
        --query 'Stacks[0].Outputs[?OutputKey==`BackendFunctionArn`].OutputValue' \
        --output text)
    
    # Get S3 bucket name
    S3_BUCKET=$(aws cloudformation describe-stacks \
        --stack-name "$STACK_NAME_ENV" \
        --region "$REGION" \
        --query 'Stacks[0].Outputs[?OutputKey==`FrontendBucketName`].OutputValue' \
        --output text)
    
    log "Deployment outputs:"
    log "API Gateway URL: $API_URL"
    log "Lambda Function ARN: $LAMBDA_ARN"
    log "S3 Bucket: $S3_BUCKET"
    
    # Save outputs to file
    cat > "deployment-outputs-$ENVIRONMENT.json" << EOF
{
    "environment": "$ENVIRONMENT",
    "api_url": "$API_URL",
    "lambda_arn": "$LAMBDA_ARN",
    "s3_bucket": "$S3_BUCKET",
    "region": "$REGION",
    "deployment_time": "$(date -u +%Y-%m-%dT%H:%M:%SZ)"
}
EOF
    
    log "Deployment outputs saved to deployment-outputs-$ENVIRONMENT.json"
}

# Run post-deployment tests
run_tests() {
    log "Running post-deployment tests..."
    
    # Load deployment outputs
    if [ -f "deployment-outputs-$ENVIRONMENT.json" ]; then
        API_URL=$(jq -r '.api_url' "deployment-outputs-$ENVIRONMENT.json")
        
        # Test health endpoint
        if curl -f -s "$API_URL/api/v1/health" > /dev/null; then
            log "Health check passed"
        else
            warning "Health check failed - API may still be starting"
        fi
        
        # Test API documentation
        if curl -f -s "$API_URL/docs" > /dev/null; then
            log "API documentation accessible"
        else
            warning "API documentation not accessible"
        fi
    else
        warning "Deployment outputs file not found - skipping tests"
    fi
}

# Setup monitoring
setup_monitoring() {
    log "Setting up monitoring..."
    
    STACK_NAME_ENV="${STACK_NAME}-${ENVIRONMENT}"
    
    # Create CloudWatch dashboard
    aws cloudformation create-stack \
        --stack-name "${STACK_NAME_ENV}-monitoring" \
        --template-body file://monitoring-dashboard.yaml \
        --parameters \
            ParameterKey=Environment,ParameterValue="$ENVIRONMENT" \
            ParameterKey=LambdaFunctionName,ParameterValue="${STACK_NAME_ENV}-BackendFunction" \
        --region "$REGION" \
        --capabilities CAPABILITY_IAM || warning "Monitoring stack may already exist"
    
    log "Monitoring setup completed"
}

# Main deployment function
main() {
    log "Starting AWS deployment for environment: $ENVIRONMENT"
    
    # Run deployment steps
    check_prerequisites
    validate_template
    build_application
    deploy_application
    get_outputs
    run_tests
    setup_monitoring
    
    log "AWS deployment completed successfully!"
    log "API URL: $(jq -r '.api_url' "deployment-outputs-$ENVIRONMENT.json")"
    log "Environment: $ENVIRONMENT"
    log "Region: $REGION"
}

# Handle script arguments
case "${1:-deploy}" in
    "deploy")
        main
        ;;
    "build")
        check_prerequisites
        validate_template
        build_application
        ;;
    "outputs")
        get_outputs
        ;;
    "test")
        run_tests
        ;;
    "monitoring")
        setup_monitoring
        ;;
    *)
        echo "Usage: $0 [deploy|build|outputs|test|monitoring] [environment]"
        echo "  deploy    - Full deployment (default)"
        echo "  build     - Build application only"
        echo "  outputs   - Get deployment outputs"
        echo "  test      - Run post-deployment tests"
        echo "  monitoring - Setup monitoring"
        exit 1
        ;;
esac