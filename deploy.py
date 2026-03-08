#!/usr/bin/env python3
"""
AWS Deployment Script for Krishi Application

This script orchestrates the deployment of the Krishi agricultural decision support
application to AWS using a serverless architecture. It handles repository cloning,
backend packaging, frontend building, infrastructure deployment, and asset uploads.

"""

import argparse
import logging
import sys
from pathlib import Path
from typing import Dict, Optional
import json


class Deployer:
    """
    Main deployment orchestrator for the Krishi application.
    
    This class manages the complete deployment workflow including:
    - Repository cloning for isolation
    - Backend packaging for Lambda
    - Frontend building with Vite
    - Infrastructure provisioning with SAM
    - Asset uploads to S3
    - CloudFront cache invalidation
    """
    
    def __init__(self, environment: str = "prototype", region: str = "ap-south-1"):
        """
        Initialize the deployer.
        
        Args:
            environment: Deployment environment (prototype, staging, prod)
            region: AWS region for deployment
        """
        self.environment = environment
        self.region = region
        self.deployment_dir = Path("deployment")
        self.logger = logging.getLogger(__name__)
        
        self.logger.info(
            f"Initialized deployer for environment '{environment}' in region '{region}'"
        )
    
    def clone_repository(self) -> None:
        """
        Step 1: Clone repository to deployment directory.
        
        Creates an isolated copy of the local repository for deployment,
        preserving the working codebase unchanged.
        
        Requirements: 1.1, 1.2, 1.3, 1.4, 1.5
        """
        import shutil
        
        self.logger.info("📦 Cloning repository...")
        
        # Get source path (current directory)
        source_path = Path.cwd()
        
        # Define exclusion patterns
        exclusions = {
            'node_modules',
            'venv',
            '.venv',
            '__pycache__',
            '.pytest_cache'
        }
        
        def ignore_patterns(directory: str, contents: list) -> set:
            """
            Filter function for shutil.copytree to exclude specific patterns.
            
            Args:
                directory: Current directory being processed
                contents: List of items in the directory
                
            Returns:
                Set of items to exclude from copying
            """
            ignored = set()
            for item in contents:
                # Exclude items matching exclusion patterns
                if item in exclusions:
                    ignored.add(item)
                # Special handling: exclude deployment directory only if it's the target
                if item == 'deployment' and directory == str(source_path):
                    ignored.add(item)
            return ignored
        
        try:
            # Remove existing deployment directory if it exists
            if self.deployment_dir.exists():
                self.logger.info(f"Removing existing deployment directory: {self.deployment_dir}")
                shutil.rmtree(self.deployment_dir)
            
            # Clone repository using copytree with ignore function
            self.logger.info(f"Copying repository from {source_path} to {self.deployment_dir}")
            shutil.copytree(
                source_path,
                self.deployment_dir,
                ignore=ignore_patterns,
                symlinks=False,  # Don't follow symlinks
                dirs_exist_ok=False
            )
            
            # Verify .git directory was preserved
            git_dir = self.deployment_dir / '.git'
            if git_dir.exists():
                self.logger.info("✓ Git history preserved in deployment repository")
            else:
                self.logger.warning("⚠ No .git directory found - git history not preserved")
            
            self.logger.info(f"✓ Repository cloned successfully to {self.deployment_dir}")
            
        except Exception as e:
            self.logger.error(f"Failed to clone repository: {e}")
            raise
    
    def package_backend(self) -> None:
        """
        Package backend application for Lambda deployment.
        
        Installs all dependencies from requirements.txt, adds Mangum adapter,
        and copies application code to the package directory.
        
        Requirements: 2.1, 2.2
        """
        import subprocess
        import shutil
        
        self.logger.info("📦 Packaging backend for Lambda...")
        
        # Define paths
        backend_source = self.deployment_dir / "backend"
        package_dir = self.deployment_dir / "backend_package"
        requirements_file = backend_source / "requirements.txt"
        
        # Verify backend directory exists
        if not backend_source.exists():
            raise FileNotFoundError(f"Backend directory not found: {backend_source}")
        
        if not requirements_file.exists():
            raise FileNotFoundError(f"Requirements file not found: {requirements_file}")
        
        try:
            # Create package directory
            if package_dir.exists():
                self.logger.info(f"Removing existing package directory: {package_dir}")
                shutil.rmtree(package_dir)
            
            package_dir.mkdir(parents=True, exist_ok=True)
            self.logger.info(f"Created package directory: {package_dir}")
            
            # Install requirements.txt dependencies
            self.logger.info("Installing dependencies from requirements.txt...")
            subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "pip",
                    "install",
                    "-r",
                    str(requirements_file),
                    "-t",
                    str(package_dir),
                    "--upgrade"
                ],
                check=True,
                capture_output=True,
                text=True
            )
            self.logger.info("✓ Dependencies installed successfully")
            
            # Install Mangum adapter
            self.logger.info("Installing mangum>=0.17.0...")
            subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "pip",
                    "install",
                    "mangum>=0.17.0",
                    "-t",
                    str(package_dir),
                    "--upgrade"
                ],
                check=True,
                capture_output=True,
                text=True
            )
            self.logger.info("✓ Mangum adapter installed successfully")
            
            # Copy application code to package directory
            self.logger.info("Copying application code to package...")
            app_source = backend_source / "app"
            app_dest = package_dir / "app"
            
            if app_source.exists():
                shutil.copytree(
                    app_source,
                    app_dest,
                    dirs_exist_ok=True,
                    ignore=shutil.ignore_patterns('__pycache__', '*.pyc', '*.pyo', '.pytest_cache')
                )
                self.logger.info(f"✓ Application code copied to {app_dest}")
            else:
                raise FileNotFoundError(f"Application directory not found: {app_source}")
            
            # Calculate package size
            total_size = sum(
                f.stat().st_size for f in package_dir.rglob('*') if f.is_file()
            )
            size_mb = total_size / (1024 * 1024)
            
            self.logger.info(f"✓ Backend package created successfully")
            self.logger.info(f"  Package size: {size_mb:.2f} MB")
            
            # Warn if package is large
            if size_mb > 200:
                self.logger.warning(
                    f"⚠️  Package size ({size_mb:.2f} MB) is approaching Lambda limit (250 MB unzipped)"
                )
            
        except subprocess.CalledProcessError as e:
            self.logger.error(f"Failed to install dependencies: {e}")
            if e.stderr:
                self.logger.error(f"Error output: {e.stderr}")
            raise
        except Exception as e:
            self.logger.error(f"Failed to package backend: {e}")
            raise
    
    def setup_backend(self) -> None:
        """
        Step 2: Setup backend package for Lambda deployment.
        
        Installs dependencies, adds Mangum adapter, and creates Lambda handler.
        
        Requirements: 2.1, 2.2, 2.5
        """
        self.logger.info("🔧 Setting up backend...")
        
        # Package the backend
        self.package_backend()
        
        # Note: Lambda handler creation is handled in task 3.1
        # The handler should already exist in the deployment repository
        self.logger.info("✓ Backend setup complete")
    
    def build_frontend(self, api_endpoint: str) -> None:
        """
        Step 3: Build frontend application for production.
        
        Runs Vite build with API endpoint configuration.
        
        Args:
            api_endpoint: API Gateway endpoint URL
            
        Requirements: 3.1, 3.6
        """
        import subprocess
        import os
        
        self.logger.info("🎨 Building frontend...")
        
        # Define paths
        frontend_dir = self.deployment_dir / "frontend"
        dist_dir = frontend_dir / "dist"
        
        # Verify frontend directory exists
        if not frontend_dir.exists():
            raise FileNotFoundError(f"Frontend directory not found: {frontend_dir}")
        
        # Verify package.json exists
        package_json = frontend_dir / "package.json"
        if not package_json.exists():
            raise FileNotFoundError(f"package.json not found: {package_json}")
        
        try:
            # Set API endpoint environment variable for Vite
            env = os.environ.copy()
            env['VITE_API_BASE_URL'] = api_endpoint
            
            self.logger.info(f"Setting VITE_API_BASE_URL={api_endpoint}")
            
            # Install dependencies if node_modules doesn't exist
            node_modules = frontend_dir / "node_modules"
            if not node_modules.exists():
                self.logger.info("Installing frontend dependencies...")
                subprocess.run(
                    ["npm", "install"],
                    cwd=str(frontend_dir),
                    check=True,
                    capture_output=True,
                    text=True
                )
                self.logger.info("✓ Dependencies installed successfully")
            else:
                self.logger.info("✓ Dependencies already installed")
            
            # Run Vite production build
            self.logger.info("Running Vite production build...")
            result = subprocess.run(
                ["npm", "run", "build"],
                cwd=str(frontend_dir),
                env=env,
                check=True,
                capture_output=True,
                text=True
            )
            
            # Log build output if verbose
            if result.stdout:
                self.logger.debug(f"Build output:\n{result.stdout}")
            
            # Verify dist directory was created
            if not dist_dir.exists():
                raise FileNotFoundError(f"Build output directory not found: {dist_dir}")
            
            # Count files in dist directory
            dist_files = list(dist_dir.rglob('*'))
            file_count = sum(1 for f in dist_files if f.is_file())
            
            self.logger.info(f"✓ Frontend build complete")
            self.logger.info(f"  Output directory: {dist_dir}")
            self.logger.info(f"  Files generated: {file_count}")
            
        except subprocess.CalledProcessError as e:
            self.logger.error(f"Failed to build frontend: {e}")
            if e.stdout:
                self.logger.error(f"Build output:\n{e.stdout}")
            if e.stderr:
                self.logger.error(f"Build errors:\n{e.stderr}")
            raise
        except Exception as e:
            self.logger.error(f"Failed to build frontend: {e}")
            raise
    
    def deploy_infrastructure(self) -> Dict[str, str]:
        """
        Step 4: Deploy AWS infrastructure using SAM template.
        
        Creates Lambda functions, API Gateway, S3 buckets, CloudFront distribution,
        and all supporting resources.
        
        Returns:
            Dictionary containing stack outputs (API endpoint, CloudFront URL, etc.)
            
        Requirements: 7.1, 7.5, 8.4
        """
        import subprocess
        
        self.logger.info("☁️  Deploying infrastructure...")
        
        # Define paths
        template_path = self.deployment_dir / "template.yaml"
        
        # Verify template exists
        if not template_path.exists():
            raise FileNotFoundError(f"SAM template not found: {template_path}")
        
        # Define stack name
        stack_name = f"krishi-{self.environment}"
        
        try:
            # Run SAM deploy
            self.logger.info(f"Deploying stack '{stack_name}' using SAM...")
            self.logger.info(f"Template: {template_path}")
            self.logger.info(f"Region: {self.region}")
            
            result = subprocess.run(
                [
                    "sam", "deploy",
                    "--template-file", "template.yaml",
                    "--stack-name", stack_name,
                    "--capabilities", "CAPABILITY_IAM",
                    "--region", self.region,
                    "--parameter-overrides",
                    f"Environment={self.environment}",
                    "--resolve-s3",
                    "--no-confirm-changeset",
                    "--no-fail-on-empty-changeset"
                ],
                cwd=str(self.deployment_dir),
                check=True,
                capture_output=True,
                text=True
            )
            
            # Log deployment output
            if result.stdout:
                self.logger.debug(f"Deployment output:\n{result.stdout}")
            
            self.logger.info("✓ Infrastructure deployed successfully")
            
            # Parse and return stack outputs
            outputs = self._parse_stack_outputs(stack_name)
            
            self.logger.info("Stack outputs:")
            for key, value in outputs.items():
                self.logger.info(f"  {key}: {value}")
            
            return outputs
            
        except subprocess.CalledProcessError as e:
            self.logger.error(f"Failed to deploy infrastructure: {e}")
            if e.stdout:
                self.logger.error(f"Deployment output:\n{e.stdout}")
            if e.stderr:
                self.logger.error(f"Deployment errors:\n{e.stderr}")
            
            # Provide helpful error messages
            if "Unable to locate credentials" in str(e.stderr):
                self.logger.error("AWS credentials not configured")
                self.logger.error("Run 'aws configure' to set up credentials")
            elif "Invalid template" in str(e.stderr):
                self.logger.error("SAM template validation failed")
                self.logger.error("Check template.yaml for syntax errors")
            
            raise
        except Exception as e:
            self.logger.error(f"Failed to deploy infrastructure: {e}")
            raise
    
    def deploy_chromadb(self, chromadb_path: str, s3_bucket: str, s3_prefix: str = "chromadb/") -> None:
        """
        Upload ChromaDB data to S3.
        
        Uploads all files from the local ChromaDB directory to S3, preserving
        the directory structure with the specified prefix.
        
        Args:
            chromadb_path: Path to local ChromaDB directory
            s3_bucket: Target S3 bucket name
            s3_prefix: S3 key prefix (default: "chromadb/")
            
        Requirements: 5.1, 5.2
        """
        import boto3
        from botocore.exceptions import ClientError
        
        self.logger.info(f"💾 Uploading ChromaDB from {chromadb_path} to s3://{s3_bucket}/{s3_prefix}")
        
        # Verify ChromaDB directory exists
        chromadb_dir = Path(chromadb_path)
        if not chromadb_dir.exists():
            raise FileNotFoundError(f"ChromaDB directory not found: {chromadb_path}")
        
        if not chromadb_dir.is_dir():
            raise ValueError(f"ChromaDB path is not a directory: {chromadb_path}")
        
        try:
            # Initialize S3 client
            s3_client = boto3.client('s3', region_name=self.region)
            
            # Get all files in ChromaDB directory recursively
            files_to_upload = []
            for file_path in chromadb_dir.rglob('*'):
                if file_path.is_file():
                    files_to_upload.append(file_path)
            
            if not files_to_upload:
                self.logger.warning(f"⚠️  No files found in ChromaDB directory: {chromadb_path}")
                return
            
            self.logger.info(f"Found {len(files_to_upload)} files to upload")
            
            # Upload each file to S3, preserving directory structure
            uploaded_count = 0
            for file_path in files_to_upload:
                # Calculate relative path from ChromaDB directory
                relative_path = file_path.relative_to(chromadb_dir)
                
                # Construct S3 key with prefix and relative path
                s3_key = s3_prefix + str(relative_path).replace('\\', '/')
                
                # Upload file to S3
                try:
                    self.logger.debug(f"Uploading {file_path} to s3://{s3_bucket}/{s3_key}")
                    s3_client.upload_file(
                        str(file_path),
                        s3_bucket,
                        s3_key
                    )
                    uploaded_count += 1
                    
                except ClientError as e:
                    self.logger.error(f"Failed to upload {file_path}: {e}")
                    raise
            
            self.logger.info(f"✓ Successfully uploaded {uploaded_count} files to S3")
            self.logger.info(f"  S3 location: s3://{s3_bucket}/{s3_prefix}")
            
        except ClientError as e:
            error_code = e.response.get('Error', {}).get('Code', 'Unknown')
            error_message = e.response.get('Error', {}).get('Message', str(e))
            
            if error_code == 'NoSuchBucket':
                self.logger.error(f"S3 bucket does not exist: {s3_bucket}")
            elif error_code == 'AccessDenied':
                self.logger.error(f"Access denied to S3 bucket: {s3_bucket}")
                self.logger.error("Check IAM permissions for S3 PutObject operation")
            else:
                self.logger.error(f"S3 error ({error_code}): {error_message}")
            
            raise
        except Exception as e:
            self.logger.error(f"Failed to upload ChromaDB: {e}")
            raise
    
    def upload_chromadb(self, bucket: str) -> None:
        """
        Step 5: Upload ChromaDB data to S3.
        
        Uploads vector database files for Lambda to load at runtime.
        
        Args:
            bucket: S3 bucket name for ChromaDB storage
            
        Requirements: 5.1, 5.2
        """
        self.logger.info("💾 Uploading ChromaDB...")
        
        # Determine ChromaDB path in deployment directory
        chromadb_path = self.deployment_dir / "backend" / "chroma_db"
        
        # Upload using deploy_chromadb function
        self.deploy_chromadb(
            chromadb_path=str(chromadb_path),
            s3_bucket=bucket,
            s3_prefix="chromadb/"
        )
    def setup_configuration(
        self,
        config_values: Dict[str, str],
        secret_values: Dict[str, str]
    ) -> Dict[str, str]:
        """
        Store configuration in Parameter Store and Secrets Manager.

        Stores non-sensitive configuration values in AWS Systems Manager Parameter Store
        and sensitive credentials in AWS Secrets Manager, both under the path
        /krishi/{environment}/.

        Args:
            config_values: Non-sensitive configuration (URLs, feature flags, model names)
            secret_values: Sensitive credentials (API keys, tokens)

        Returns:
            Dictionary containing parameter and secret ARNs

        Requirements: 4.1, 4.2
        """
        import boto3
        from botocore.exceptions import ClientError

        self.logger.info(f"🔐 Setting up configuration for environment '{self.environment}'...")

        result = {
            'parameters': {},
            'secrets': {}
        }

        try:
            # Initialize AWS clients
            ssm_client = boto3.client('ssm', region_name=self.region)
            secrets_client = boto3.client('secretsmanager', region_name=self.region)

            # Store non-sensitive configuration in Parameter Store
            if config_values:
                self.logger.info(f"Storing {len(config_values)} parameters in Parameter Store...")

                for key, value in config_values.items():
                    parameter_name = f"/krishi/{self.environment}/{key}"

                    try:
                        self.logger.debug(f"Storing parameter: {parameter_name}")

                        response = ssm_client.put_parameter(
                            Name=parameter_name,
                            Value=str(value),
                            Type='String',
                            Overwrite=True,
                            Description=f"Configuration for Krishi {self.environment} environment"
                        )

                        result['parameters'][key] = parameter_name
                        self.logger.debug(f"✓ Stored parameter: {parameter_name}")

                    except ClientError as e:
                        self.logger.error(f"Failed to store parameter {parameter_name}: {e}")
                        raise

                self.logger.info(f"✓ Successfully stored {len(config_values)} parameters")
            else:
                self.logger.info("No configuration parameters to store")

            # Store sensitive credentials in Secrets Manager
            if secret_values:
                self.logger.info(f"Storing {len(secret_values)} secrets in Secrets Manager...")

                for key, value in secret_values.items():
                    secret_name = f"/krishi/{self.environment}/{key}"

                    try:
                        self.logger.debug(f"Storing secret: {secret_name}")

                        # Try to create the secret first
                        try:
                            response = secrets_client.create_secret(
                                Name=secret_name,
                                Description=f"Secret for Krishi {self.environment} environment",
                                SecretString=str(value)
                            )
                            result['secrets'][key] = response['ARN']
                            self.logger.debug(f"✓ Created secret: {secret_name}")

                        except ClientError as e:
                            # If secret already exists, update it instead
                            if e.response['Error']['Code'] == 'ResourceExistsException':
                                self.logger.debug(f"Secret exists, updating: {secret_name}")
                                response = secrets_client.update_secret(
                                    SecretId=secret_name,
                                    SecretString=str(value)
                                )
                                # Get the ARN
                                describe_response = secrets_client.describe_secret(
                                    SecretId=secret_name
                                )
                                result['secrets'][key] = describe_response['ARN']
                                self.logger.debug(f"✓ Updated secret: {secret_name}")
                            else:
                                raise

                    except ClientError as e:
                        self.logger.error(f"Failed to store secret {secret_name}: {e}")
                        raise

                self.logger.info(f"✓ Successfully stored {len(secret_values)} secrets")
            else:
                self.logger.info("No secrets to store")

            # Log summary
            self.logger.info("✓ Configuration setup complete")
            self.logger.info(f"  Parameters stored: {len(result['parameters'])}")
            self.logger.info(f"  Secrets stored: {len(result['secrets'])}")

            return result

        except ClientError as e:
            error_code = e.response.get('Error', {}).get('Code', 'Unknown')
            error_message = e.response.get('Error', {}).get('Message', str(e))

            if error_code == 'AccessDeniedException':
                self.logger.error("Access denied to AWS services")
                self.logger.error("Check IAM permissions for SSM Parameter Store and Secrets Manager")
            else:
                self.logger.error(f"AWS error ({error_code}): {error_message}")

            raise
        except Exception as e:
            self.logger.error(f"Failed to setup configuration: {e}")
            raise
    def setup_configuration_from_env_example(
        self,
        env_example_path: Optional[str] = None,
        override_values: Optional[Dict[str, str]] = None
    ) -> Dict[str, str]:
        """
        Setup configuration from .env.example file.

        Reads the .env.example file, categorizes values as sensitive or non-sensitive,
        and stores them in the appropriate AWS service.

        Args:
            env_example_path: Path to .env.example file (default: backend/.env.example)
            override_values: Dictionary of values to override from .env.example

        Returns:
            Dictionary containing parameter and secret ARNs

        Requirements: 4.1, 4.2
        """
        self.logger.info("📋 Setting up configuration from .env.example...")

        # Default path to .env.example
        if env_example_path is None:
            env_example_path = self.deployment_dir / "backend" / ".env.example"
        else:
            env_example_path = Path(env_example_path)

        if not env_example_path.exists():
            raise FileNotFoundError(f".env.example file not found: {env_example_path}")

        # Parse .env.example file
        env_vars = {}
        with open(env_example_path, 'r') as f:
            for line in f:
                line = line.strip()
                # Skip comments and empty lines
                if not line or line.startswith('#'):
                    continue

                # Parse KEY=VALUE format
                if '=' in line:
                    key, value = line.split('=', 1)
                    key = key.strip()
                    value = value.strip().strip('"').strip("'")
                    env_vars[key] = value

        self.logger.info(f"Parsed {len(env_vars)} environment variables from .env.example")

        # Apply overrides
        if override_values:
            env_vars.update(override_values)
            self.logger.info(f"Applied {len(override_values)} override values")

        # Categorize as sensitive (secrets) or non-sensitive (parameters)
        # Sensitive: API keys, tokens, passwords, secrets
        sensitive_keywords = ['key', 'token', 'password', 'secret', 'credential']

        config_values = {}
        secret_values = {}

        for key, value in env_vars.items():
            key_lower = key.lower()
            is_sensitive = any(keyword in key_lower for keyword in sensitive_keywords)

            if is_sensitive:
                secret_values[key.lower()] = value
            else:
                config_values[key.lower()] = value

        self.logger.info(f"Categorized: {len(config_values)} parameters, {len(secret_values)} secrets")

        # Store configuration
        return self.setup_configuration(config_values, secret_values)


    
    def upload_frontend(self, bucket: str) -> None:
        """
        Step 6: Upload frontend assets to S3.
        
        Syncs built frontend files to S3 bucket for CloudFront distribution.
        
        Args:
            bucket: S3 bucket name for frontend hosting
            
        Requirements: 3.2
        """
        import subprocess
        
        self.logger.info("🚀 Uploading frontend...")
        
        # Define paths
        frontend_dir = self.deployment_dir / "frontend"
        dist_dir = frontend_dir / "dist"
        
        # Verify dist directory exists
        if not dist_dir.exists():
            raise FileNotFoundError(
                f"Frontend build output not found: {dist_dir}. "
                "Run build_frontend() first."
            )
        
        try:
            # Use AWS CLI to sync dist directory to S3
            # --delete flag removes files in S3 that don't exist locally
            self.logger.info(f"Syncing {dist_dir} to s3://{bucket}/")
            
            result = subprocess.run(
                [
                    "aws", "s3", "sync",
                    str(dist_dir) + "/",  # Trailing slash to sync contents
                    f"s3://{bucket}/",
                    "--delete",
                    "--region", self.region
                ],
                check=True,
                capture_output=True,
                text=True
            )
            
            # Log sync output
            if result.stdout:
                self.logger.debug(f"Sync output:\n{result.stdout}")
            
            # Count uploaded files
            dist_files = list(dist_dir.rglob('*'))
            file_count = sum(1 for f in dist_files if f.is_file())
            
            self.logger.info(f"✓ Frontend uploaded successfully")
            self.logger.info(f"  S3 location: s3://{bucket}/")
            self.logger.info(f"  Files uploaded: {file_count}")
            
        except subprocess.CalledProcessError as e:
            self.logger.error(f"Failed to upload frontend: {e}")
            if e.stdout:
                self.logger.error(f"Upload output:\n{e.stdout}")
            if e.stderr:
                self.logger.error(f"Upload errors:\n{e.stderr}")
            
            # Provide helpful error messages
            if "NoSuchBucket" in str(e.stderr):
                self.logger.error(f"S3 bucket does not exist: {bucket}")
            elif "AccessDenied" in str(e.stderr):
                self.logger.error(f"Access denied to S3 bucket: {bucket}")
                self.logger.error("Check IAM permissions for S3 PutObject operation")
            
            raise
        except Exception as e:
            self.logger.error(f"Failed to upload frontend: {e}")
            raise
    
    def invalidate_cloudfront(self, distribution_id: str) -> None:
        """
        Step 7: Invalidate CloudFront cache.
        
        Clears cached content to ensure users get the latest version.
        
        Args:
            distribution_id: CloudFront distribution ID
            
        Requirements: 3.7
        """
        import subprocess
        import time
        
        self.logger.info("🔄 Invalidating CloudFront cache...")
        
        try:
            # Create invalidation for all paths
            self.logger.info(f"Creating invalidation for distribution: {distribution_id}")
            
            result = subprocess.run(
                [
                    "aws", "cloudfront", "create-invalidation",
                    "--distribution-id", distribution_id,
                    "--paths", "/*",
                    "--region", self.region
                ],
                check=True,
                capture_output=True,
                text=True
            )
            
            # Parse invalidation ID from output
            if result.stdout:
                self.logger.debug(f"Invalidation output:\n{result.stdout}")
                
                # Try to extract invalidation ID
                try:
                    import json
                    output_data = json.loads(result.stdout)
                    invalidation_id = output_data.get('Invalidation', {}).get('Id', 'unknown')
                    self.logger.info(f"✓ Invalidation created: {invalidation_id}")
                except json.JSONDecodeError:
                    self.logger.info("✓ Invalidation created successfully")
            else:
                self.logger.info("✓ Invalidation created successfully")
            
            self.logger.info("Note: Invalidation may take several minutes to complete")
            
        except subprocess.CalledProcessError as e:
            self.logger.error(f"Failed to invalidate CloudFront cache: {e}")
            if e.stdout:
                self.logger.error(f"Invalidation output:\n{e.stdout}")
            if e.stderr:
                self.logger.error(f"Invalidation errors:\n{e.stderr}")
            
            # Provide helpful error messages
            if "NoSuchDistribution" in str(e.stderr):
                self.logger.error(f"CloudFront distribution not found: {distribution_id}")
            elif "AccessDenied" in str(e.stderr):
                self.logger.error("Access denied to CloudFront")
                self.logger.error("Check IAM permissions for CloudFront CreateInvalidation")
            elif "TooManyInvalidationsInProgress" in str(e.stderr):
                self.logger.warning("Too many invalidations in progress")
                self.logger.warning("Wait for existing invalidations to complete")
            
            # Don't fail deployment for invalidation errors
            self.logger.warning("⚠️  Continuing despite invalidation failure")
            self.logger.warning("You may need to manually invalidate the CloudFront cache")
    
    def _parse_stack_outputs(self, stack_name: str) -> Dict[str, str]:
        """
        Parse CloudFormation stack outputs.
        
        Args:
            stack_name: Name of the CloudFormation stack
        
        Returns:
            Dictionary of output keys and values
        """
        import boto3
        from botocore.exceptions import ClientError
        
        try:
            # Initialize CloudFormation client
            cfn_client = boto3.client('cloudformation', region_name=self.region)
            
            # Describe stack to get outputs
            response = cfn_client.describe_stacks(StackName=stack_name)
            
            if not response.get('Stacks'):
                raise ValueError(f"Stack not found: {stack_name}")
            
            stack = response['Stacks'][0]
            outputs = stack.get('Outputs', [])
            
            # Convert outputs list to dictionary
            output_dict = {}
            for output in outputs:
                key = output.get('OutputKey')
                value = output.get('OutputValue')
                if key and value:
                    output_dict[key] = value
            
            return output_dict
            
        except ClientError as e:
            self.logger.error(f"Failed to parse stack outputs: {e}")
            raise
        except Exception as e:
            self.logger.error(f"Failed to parse stack outputs: {e}")
            raise
    
    def _get_distribution_id(self, cloudfront_url: str) -> str:
        """
        Extract CloudFront distribution ID from URL.
        
        Args:
            cloudfront_url: CloudFront distribution domain name
            
        Returns:
            Distribution ID
        """
        import boto3
        from botocore.exceptions import ClientError
        
        try:
            # Initialize CloudFront client
            cf_client = boto3.client('cloudfront', region_name=self.region)
            
            # List distributions and find matching domain name
            self.logger.debug(f"Looking up distribution ID for domain: {cloudfront_url}")
            
            paginator = cf_client.get_paginator('list_distributions')
            for page in paginator.paginate():
                distributions = page.get('DistributionList', {}).get('Items', [])
                
                for dist in distributions:
                    domain_name = dist.get('DomainName', '')
                    dist_id = dist.get('Id', '')
                    
                    # Match domain name (case-insensitive)
                    if domain_name.lower() == cloudfront_url.lower():
                        self.logger.debug(f"Found distribution ID: {dist_id}")
                        return dist_id
            
            # If not found, raise error
            raise ValueError(
                f"CloudFront distribution not found for domain: {cloudfront_url}"
            )
            
        except ClientError as e:
            self.logger.error(f"Failed to get distribution ID: {e}")
            raise
        except Exception as e:
            self.logger.error(f"Failed to get distribution ID: {e}")
            raise
    
    def deploy(self) -> None:
        """
        Execute complete deployment workflow.
        
        Orchestrates all deployment steps in the correct order with error handling.
        
        Requirements: 8.1, 8.2, 8.3, 8.4, 8.5, 8.6, 8.7
        """
        deployment_state = {
            'clone_repository': False,
            'setup_backend': False,
            'deploy_infrastructure': False,
            'build_frontend': False,
            'upload_chromadb': False,
            'upload_frontend': False,
            'invalidate_cloudfront': False
        }
        
        try:
            self.logger.info("🚀 Starting deployment workflow...")
            self.logger.info(f"Environment: {self.environment}")
            self.logger.info(f"Region: {self.region}")
            
            # Step 1: Clone repository
            self.logger.info("\n" + "="*60)
            self.logger.info("Step 1: Cloning repository")
            self.logger.info("="*60)
            try:
                self.clone_repository()
                deployment_state['clone_repository'] = True
            except Exception as e:
                self.logger.error(f"❌ Failed at step 1 (clone repository): {e}")
                raise
            
            # Step 2: Setup backend
            self.logger.info("\n" + "="*60)
            self.logger.info("Step 2: Setting up backend")
            self.logger.info("="*60)
            try:
                self.setup_backend()
                deployment_state['setup_backend'] = True
            except Exception as e:
                self.logger.error(f"❌ Failed at step 2 (setup backend): {e}")
                self.logger.error("Hint: Check that requirements.txt exists and dependencies are valid")
                raise
            
            # Step 3: Deploy infrastructure first to get API endpoint
            self.logger.info("\n" + "="*60)
            self.logger.info("Step 3: Deploying infrastructure")
            self.logger.info("="*60)
            try:
                outputs = self.deploy_infrastructure()
                deployment_state['deploy_infrastructure'] = True
                
                api_endpoint = outputs.get('ApiEndpoint')
                frontend_bucket = outputs.get('FrontendBucket')
                chromadb_bucket = outputs.get('ChromaDBBucket')
                cloudfront_url = outputs.get('CloudFrontURL')
                
                if not all([api_endpoint, frontend_bucket, chromadb_bucket, cloudfront_url]):
                    missing = []
                    if not api_endpoint: missing.append('ApiEndpoint')
                    if not frontend_bucket: missing.append('FrontendBucket')
                    if not chromadb_bucket: missing.append('ChromaDBBucket')
                    if not cloudfront_url: missing.append('CloudFrontURL')
                    
                    raise ValueError(
                        f"Missing required stack outputs: {', '.join(missing)}. "
                        "Check that template.yaml defines all required outputs."
                    )
                
            except Exception as e:
                self.logger.error(f"❌ Failed at step 3 (deploy infrastructure): {e}")
                self.logger.error("Hint: Check AWS credentials, SAM CLI installation, and template.yaml")
                raise
            
            # Step 4: Build frontend with API endpoint
            self.logger.info("\n" + "="*60)
            self.logger.info("Step 4: Building frontend")
            self.logger.info("="*60)
            try:
                self.build_frontend(api_endpoint)
                deployment_state['build_frontend'] = True
            except Exception as e:
                self.logger.error(f"❌ Failed at step 4 (build frontend): {e}")
                self.logger.error("Hint: Check that Node.js and npm are installed, and package.json is valid")
                raise
            
            # Step 5: Upload ChromaDB data
            self.logger.info("\n" + "="*60)
            self.logger.info("Step 5: Uploading ChromaDB")
            self.logger.info("="*60)
            try:
                self.upload_chromadb(chromadb_bucket)
                deployment_state['upload_chromadb'] = True
            except Exception as e:
                self.logger.error(f"❌ Failed at step 5 (upload ChromaDB): {e}")
                self.logger.error("Hint: Check that ChromaDB directory exists and S3 bucket is accessible")
                # Don't fail deployment if ChromaDB upload fails
                self.logger.warning("⚠️  Continuing without ChromaDB upload")
            
            # Step 6: Upload frontend assets
            self.logger.info("\n" + "="*60)
            self.logger.info("Step 6: Uploading frontend")
            self.logger.info("="*60)
            try:
                self.upload_frontend(frontend_bucket)
                deployment_state['upload_frontend'] = True
            except Exception as e:
                self.logger.error(f"❌ Failed at step 6 (upload frontend): {e}")
                self.logger.error("Hint: Check that frontend build completed and S3 bucket is accessible")
                raise
            
            # Step 7: Invalidate CloudFront cache
            self.logger.info("\n" + "="*60)
            self.logger.info("Step 7: Invalidating CloudFront cache")
            self.logger.info("="*60)
            try:
                distribution_id = self._get_distribution_id(cloudfront_url)
                self.invalidate_cloudfront(distribution_id)
                deployment_state['invalidate_cloudfront'] = True
            except Exception as e:
                self.logger.error(f"❌ Failed at step 7 (invalidate CloudFront): {e}")
                # Don't fail deployment for invalidation errors
                self.logger.warning("⚠️  Continuing despite invalidation failure")
                self.logger.warning("You may need to manually invalidate the CloudFront cache")
            
            # Success!
            self.logger.info("\n" + "="*60)
            self.logger.info("✅ DEPLOYMENT COMPLETE!")
            self.logger.info("="*60)
            self.logger.info(f"🌐 Application URL: https://{cloudfront_url}")
            self.logger.info(f"🔌 API Endpoint: {api_endpoint}")
            self.logger.info(f"📦 Frontend Bucket: {frontend_bucket}")
            self.logger.info(f"💾 ChromaDB Bucket: {chromadb_bucket}")
            self.logger.info("\nNext steps:")
            self.logger.info("1. Wait a few minutes for CloudFront distribution to deploy")
            self.logger.info("2. Access your application at the URL above")
            self.logger.info("3. Check CloudWatch Logs for backend logs")
            
        except Exception as e:
            self.logger.error("\n" + "="*60)
            self.logger.error("❌ DEPLOYMENT FAILED")
            self.logger.error("="*60)
            self.logger.error(f"Error: {e}")
            
            # Show deployment state
            self.logger.error("\nDeployment progress:")
            for step, completed in deployment_state.items():
                status = "✓" if completed else "✗"
                self.logger.error(f"  {status} {step.replace('_', ' ').title()}")
            
            # Cleanup suggestions
            self.logger.error("\nCleanup suggestions:")
            if deployment_state['deploy_infrastructure']:
                self.logger.error(f"- Delete CloudFormation stack: aws cloudformation delete-stack --stack-name krishi-{self.environment}")
            if deployment_state['clone_repository']:
                self.logger.error(f"- Remove deployment directory: rm -rf {self.deployment_dir}")
            
            sys.exit(1)


def setup_logging(verbose: bool = False) -> None:
    """
    Configure logging for deployment progress tracking.
    
    Args:
        verbose: Enable verbose (DEBUG level) logging
        
    Requirements: 8.3
    """
    log_level = logging.DEBUG if verbose else logging.INFO
    
    # Configure root logger
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Reduce noise from boto3 and other libraries
    logging.getLogger('boto3').setLevel(logging.WARNING)
    logging.getLogger('botocore').setLevel(logging.WARNING)
    logging.getLogger('urllib3').setLevel(logging.WARNING)


def parse_arguments() -> argparse.Namespace:
    """
    Parse command-line arguments for deployment configuration.
    
    Returns:
        Parsed arguments namespace
        
    Requirements: 8.2
    """
    parser = argparse.ArgumentParser(
        description='Deploy Krishi application to AWS',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Deploy to prototype environment in ap-south-1 (default)
  python deploy.py
  
  # Deploy to staging environment in us-east-1
  python deploy.py --environment staging --region us-east-1
  
  # Deploy with verbose logging
  python deploy.py --verbose
        """
    )
    
    parser.add_argument(
        '--environment',
        '-e',
        type=str,
        default='prototype',
        choices=['prototype', 'staging', 'prod'],
        help='Deployment environment (default: prototype)'
    )
    
    parser.add_argument(
        '--region',
        '-r',
        type=str,
        default='ap-south-1',
        help='AWS region for deployment (default: ap-south-1)'
    )
    
    parser.add_argument(
        '--verbose',
        '-v',
        action='store_true',
        help='Enable verbose logging'
    )
    
    return parser.parse_args()


def main() -> None:
    """
    Main entry point for deployment script.
    
    Requirements: 8.1, 8.2, 8.3
    """
    # Parse command-line arguments
    args = parse_arguments()
    
    # Setup logging
    setup_logging(verbose=args.verbose)
    
    # Create deployer and execute deployment
    deployer = Deployer(
        environment=args.environment,
        region=args.region
    )
    
    deployer.deploy()


if __name__ == "__main__":
    main()
