# Implementation Plan: AWS Deployment

## Overview

This plan implements the AWS deployment infrastructure for the Krishi agricultural decision support application. The implementation creates a serverless architecture using AWS Lambda for the FastAPI backend, S3 and CloudFront for the React frontend, with supporting services for configuration management, persistence, and monitoring. The deployment preserves the local development environment by working in a cloned repository.

## Tasks

- [x] 1. Create deployment automation script structure
  - Create `deploy.py` script in project root with Deployer class
  - Implement command-line argument parsing for environment and region
  - Add logging configuration for deployment progress tracking
  - _Requirements: 8.1, 8.2, 8.3, 8.4, 8.5, 8.6, 8.7_

- [ ] 2. Implement repository cloning module
  - [x] 2.1 Create repository cloning function
    - Implement `clone_repository()` function using `shutil.copytree()`
    - Configure exclusion patterns for node_modules, venv, .venv, __pycache__, .pytest_cache
    - Preserve .git directory to maintain version history
    - _Requirements: 1.1, 1.2, 1.5_
  
  - [ ]* 2.2 Write property test for repository cloning completeness
    - **Property 1: Repository Cloning Completeness**
    - **Validates: Requirements 1.1, 1.2**
  
  - [ ]* 2.3 Write property test for repository isolation
    - **Property 2: Repository Isolation**
    - **Validates: Requirements 1.3, 1.4**
  
  - [ ]* 2.4 Write property test for git history preservation
    - **Property 3: Git History Preservation**
    - **Validates: Requirements 1.5**

- [ ] 3. Implement backend packaging module
  - [x] 3.1 Create Lambda handler wrapper with Mangum
    - Create `lambda_handler.py` in deployment backend directory
    - Import FastAPI app and wrap with Mangum adapter
    - Set lifespan="off" for Lambda compatibility
    - _Requirements: 2.1, 2.5_
  
  - [x] 3.2 Implement backend packaging function
    - Create `package_backend()` function to install dependencies to package directory
    - Install requirements.txt dependencies using pip with -t flag
    - Add mangum>=0.17.0 to package
    - Copy application code to package directory
    - _Requirements: 2.1, 2.2_
  
  - [ ]* 3.3 Write property test for Lambda package structure validity
    - **Property 4: Lambda Package Structure Validity**
    - **Validates: Requirements 2.1**
  
  - [ ]* 3.4 Write property test for dependency inclusion completeness
    - **Property 5: Dependency Inclusion Completeness**
    - **Validates: Requirements 2.2**
  
  - [ ]* 3.5 Write unit tests for backend packaging
    - Test handler creation and validity
    - Test package size within Lambda limits
    - Test all dependencies included

- [ ] 4. Implement ChromaDB persistence module
  - [x] 4.1 Create ChromaDB S3 upload function
    - Implement `deploy_chromadb()` function to upload ChromaDB files to S3
    - Use boto3 to upload all files from local ChromaDB directory
    - Preserve directory structure in S3 with prefix
    - _Requirements: 5.1, 5.2_
  
  - [x] 4.2 Create Lambda ChromaDB loading function
    - Implement `load_chromadb_from_s3()` function in Lambda handler
    - Download ChromaDB files from S3 to /tmp directory
    - Initialize ChromaDB PersistentClient with downloaded data
    - Use global variable for Lambda container reuse
    - _Requirements: 5.2, 5.3_
  
  - [ ]* 4.3 Write property test for ChromaDB file inclusion
    - **Property 13: ChromaDB File Inclusion**
    - **Validates: Requirements 5.1**
  
  - [ ]* 4.4 Write property test for ChromaDB data integrity
    - **Property 15: ChromaDB Data Integrity**
    - **Validates: Requirements 5.4**
  
  - [ ]* 4.5 Write unit tests for ChromaDB persistence
    - Test S3 upload completes successfully
    - Test Lambda loads ChromaDB from S3
    - Test collection counts match between local and deployed

- [x] 5. Checkpoint - Verify core modules
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 6. Implement configuration management module
  - [x] 6.1 Create configuration setup function
    - Implement `setup_configuration()` function using boto3
    - Store non-sensitive config in Parameter Store under /krishi/{environment}/
    - Store sensitive credentials in Secrets Manager under /krishi/{environment}/
    - _Requirements: 4.1, 4.2_
  
  - [x] 6.2 Create Lambda configuration loading function
    - Implement `load_config()` function to retrieve parameters from Parameter Store
    - Retrieve secrets from Secrets Manager
    - Set environment variables for application use
    - _Requirements: 4.3, 4.5_
  
  - [ ]* 6.3 Write property test for configuration template completeness
    - **Property 9: Configuration Template Completeness**
    - **Validates: Requirements 4.1**
  
  - [ ]* 6.4 Write property test for secret storage verification
    - **Property 10: Secret Storage Verification**
    - **Validates: Requirements 4.2**
  
  - [ ]* 6.5 Write property test for secret exclusion from code
    - **Property 12: Secret Exclusion from Code**
    - **Validates: Requirements 4.6**
  
  - [ ]* 6.6 Write unit tests for configuration management
    - Test parameters stored in Parameter Store
    - Test secrets stored in Secrets Manager
    - Test Lambda loads configuration at runtime

- [ ] 7. Create AWS SAM infrastructure template
  - [x] 7.1 Create SAM template with Lambda function definition
    - Create `template.yaml` with AWS::Serverless::Function resource
    - Configure Python 3.11 runtime, 1024 MB memory, 60 second timeout
    - Set CodeUri to backend package directory
    - Set Handler to lambda_handler.handler
    - _Requirements: 2.6, 2.7, 7.1, 7.2_
  
  - [x] 7.2 Add API Gateway configuration to SAM template
    - Define AWS::Serverless::Api resource with CORS enabled
    - Configure API Gateway events for Lambda function with /{proxy+} path
    - Enable CloudWatch logging and tracing
    - _Requirements: 2.3, 2.4, 7.2_
  
  - [x] 7.3 Add S3 buckets to SAM template
    - Define frontend S3 bucket with static website hosting
    - Define ChromaDB S3 bucket with versioning and lifecycle policies
    - Configure bucket policies for CloudFront and Lambda access
    - _Requirements: 3.2, 3.3, 5.2, 7.2_
  
  - [x] 7.4 Add CloudFront distribution to SAM template
    - Define AWS::CloudFront::Distribution resource
    - Configure origin as frontend S3 bucket with OAC
    - Set cache behaviors and custom error responses for SPA routing
    - Enable HTTPS with redirect-to-https policy
    - _Requirements: 3.4, 3.5, 3.7, 7.2_
  
  - [x] 7.5 Add IAM roles and policies to SAM template
    - Configure Lambda execution role with S3 read access for ChromaDB bucket
    - Add Parameter Store and Secrets Manager read permissions
    - Add Bedrock invoke permissions (conditional on USE_AWS_AI parameter)
    - Add CloudWatch Logs write permissions
    - Follow least-privilege principle
    - _Requirements: 7.3, 10.4, 11.1_
  
  - [x] 7.6 Add parameters and outputs to SAM template
    - Define parameters for Environment and UseAWSAI
    - Add outputs for ApiEndpoint, CloudFrontURL, FrontendBucket, ChromaDBBucket
    - _Requirements: 7.6, 8.6, 9.1_
  
  - [ ]* 7.7 Write property test for infrastructure resource completeness
    - **Property 19: Infrastructure Resource Completeness**
    - **Validates: Requirements 7.2**
  
  - [ ]* 7.8 Write property test for infrastructure parameterization
    - **Property 20: Infrastructure Parameterization**
    - **Validates: Requirements 7.6**

- [ ] 8. Implement frontend build module
  - [ ] 8.1 Create frontend build function
    - Implement `build_frontend()` function to run Vite production build
    - Set VITE_API_BASE_URL environment variable to API Gateway endpoint
    - Execute npm run build command
    - Verify dist/ directory created with assets
    - _Requirements: 3.1, 3.6_
  
  - [x] 8.2 Create S3 upload function for frontend
    - Implement `upload_frontend()` function using AWS CLI or boto3
    - Sync dist/ directory to S3 bucket with --delete flag
    - Set appropriate content types for assets
    - _Requirements: 3.2_
  
  - [ ]* 8.3 Write property test for frontend asset synchronization
    - **Property 7: Frontend Asset Synchronization**
    - **Validates: Requirements 3.2**
  
  - [ ]* 8.4 Write unit tests for frontend build
    - Test build completes successfully
    - Test API endpoint configured in build
    - Test dist/ directory contains expected files

- [ ] 9. Implement infrastructure deployment orchestration
  - [x] 9.1 Create SAM deployment function
    - Implement `deploy_infrastructure()` function using subprocess to call sam deploy
    - Pass template path, stack name, capabilities, region, and parameters
    - Capture and parse CloudFormation stack outputs
    - Return outputs as dictionary
    - _Requirements: 7.1, 7.5, 8.4_
  
  - [x] 9.2 Create CloudFront invalidation function
    - Implement `invalidate_cloudfront()` function using AWS CLI or boto3
    - Create invalidation for /* path
    - _Requirements: 3.7_
  
  - [ ]* 9.3 Write property test for deployment error reporting
    - **Property 21: Deployment Error Reporting**
    - **Validates: Requirements 8.7**

- [ ] 10. Checkpoint - Verify infrastructure and deployment modules
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 11. Implement monitoring and logging enhancements
  - [x] 11.1 Add CloudWatch custom metrics for external API calls
    - Create `log_external_api_call()` function using boto3 CloudWatch client
    - Emit metrics for API call count and latency by service
    - Integrate with existing circuit breaker and retry logic
    - _Requirements: 6.6, 11.6_
  
  - [ ]* 11.2 Write property test for CloudWatch log delivery
    - **Property 22: CloudWatch Log Delivery**
    - **Validates: Requirements 11.1**
  
  - [ ]* 11.3 Write property test for structured log format preservation
    - **Property 23: Structured Log Format Preservation**
    - **Validates: Requirements 11.2**
  
  - [ ]* 11.4 Write property test for external API call logging
    - **Property 24: External API Call Logging**
    - **Validates: Requirements 11.6**

- [ ] 12. Implement complete deployment workflow
  - [x] 12.1 Wire deployment steps in main deploy() method
    - Call clone_repository() to create deployment copy
    - Call setup_backend() to package Lambda function
    - Call deploy_infrastructure() to create AWS resources
    - Extract API endpoint from stack outputs
    - Call build_frontend() with API endpoint
    - Call upload_chromadb() to S3
    - Call upload_frontend() to S3
    - Call invalidate_cloudfront() to clear cache
    - Print success message with URLs
    - _Requirements: 8.1, 8.2, 8.3, 8.4, 8.5, 8.6_
  
  - [x] 12.2 Add error handling and recovery to deployment workflow
    - Wrap each step in try-except blocks
    - Provide clear error messages identifying failure point
    - Clean up partial deployments on failure
    - _Requirements: 8.7_
  
  - [ ]* 12.3 Write unit test for full deployment workflow
    - Test complete deployment from start to finish (integration test)
    - Verify all resources created
    - Verify endpoints accessible

- [ ] 13. Implement external API integration verification
  - [ ]* 13.1 Write property test for circuit breaker failure handling
    - **Property 16: Circuit Breaker Failure Handling**
    - **Validates: Requirements 6.4**
  
  - [ ]* 13.2 Write property test for retry logic with exponential backoff
    - **Property 17: Retry Logic with Exponential Backoff**
    - **Validates: Requirements 6.5**
  
  - [ ]* 13.3 Write property test for external API error logging
    - **Property 18: External API Error Logging**
    - **Validates: Requirements 6.6**
  
  - [ ]* 13.4 Write unit tests for external API integration
    - Test backend calls CEDA API successfully
    - Test circuit breaker opens after failures
    - Test retry logic with backoff

- [ ] 14. Implement API endpoint and connectivity verification
  - [ ]* 14.1 Write property test for API endpoint routing
    - **Property 6: API Endpoint Routing**
    - **Validates: Requirements 2.3, 2.4**
  
  - [ ]* 14.2 Write property test for frontend-backend connectivity
    - **Property 8: Frontend-Backend Connectivity**
    - **Validates: Requirements 3.6, 9.5**
  
  - [ ]* 14.3 Write unit test for frontend-backend integration
    - Test frontend can call backend through API Gateway
    - Test API responses received correctly

- [ ] 15. Create deployment documentation
  - [ ] 15.1 Create deployment guide document
    - Create `DEPLOYMENT.md` in deployment repository
    - Document prerequisites (AWS account, CLI, SAM CLI, Node.js, Python)
    - Provide step-by-step deployment instructions
    - Document configuration management (Parameter Store/Secrets Manager)
    - Document redeployment process for code changes
    - Document CloudWatch logs access for troubleshooting
    - _Requirements: 13.1, 13.2, 13.3, 13.4, 13.5, 13.6_
  
  - [ ] 15.2 Add architecture diagram to documentation
    - Create architecture diagram showing all AWS components
    - Document data flow from user to frontend to backend to external APIs
    - _Requirements: 13.7_
  
  - [ ] 15.3 Document cost optimization and estimates
    - Document Lambda scaling to zero configuration
    - Document S3 storage class recommendations
    - Document CloudFront cache TTL settings
    - Provide estimated monthly cost breakdown
    - _Requirements: 12.1, 12.2, 12.3, 12.4, 12.5_
  
  - [ ] 15.4 Document AI service configuration options
    - Document USE_AWS_AI parameter usage
    - Document Bedrock configuration for AWS AI
    - Document Ollama endpoint configuration for external AI
    - _Requirements: 10.1, 10.2, 10.3, 10.5_

- [ ] 16. Final checkpoint - Complete deployment verification
  - Ensure all tests pass, ask the user if questions arise.

## Notes

- Tasks marked with `*` are optional and can be skipped for faster MVP
- Each task references specific requirements for traceability
- Checkpoints ensure incremental validation at key milestones
- Property tests validate universal correctness properties across all inputs
- Unit tests validate specific examples, edge cases, and integration points
- The deployment script should be idempotent where possible
- All AWS resources should be tagged with Environment and Project tags
- Consider using AWS SAM local testing before deploying to AWS
- Monitor Lambda cold start times and optimize ChromaDB loading if needed
- Test with actual API keys in a non-production AWS account first
