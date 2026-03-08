"""
Lambda handler for Krishi FastAPI application.

This module wraps the FastAPI application with the Mangum ASGI adapter
to enable deployment on AWS Lambda. The handler is configured for Lambda
compatibility with lifespan="off" to prevent lifecycle management issues.

It also handles loading ChromaDB from S3 at cold start for RAG functionality.

Requirements: 2.1, 2.5, 5.2, 5.3
"""

import os
import logging
from pathlib import Path
from typing import Optional

from mangum import Mangum
from app.main import app
from config_loader import load_config

# Configure logging
logger = logging.getLogger(__name__)

# Global variable for Lambda container reuse
chroma_client = None
chroma_loaded = False


def load_chromadb_from_s3() -> Optional[Path]:
    """
    Download ChromaDB files from S3 to Lambda /tmp directory.
    
    This function is called at Lambda cold start to load the ChromaDB
    vector database from S3 persistent storage. The database is downloaded
    to /tmp and can be used by the RAG service.
    
    The function uses a global variable to cache the ChromaDB path across
    Lambda invocations within the same container, avoiding redundant downloads.
    
    Returns:
        Path to the downloaded ChromaDB directory, or None if loading fails
        
    Requirements: 5.2, 5.3
    """
    global chroma_client, chroma_loaded
    
    # Return cached path if already loaded
    if chroma_loaded:
        logger.info("ChromaDB already loaded in this Lambda container")
        return Path("/tmp/chroma_db")
    
    try:
        import boto3
        
        # Get S3 bucket from environment variable
        bucket = os.environ.get('CHROMADB_BUCKET')
        if not bucket:
            logger.warning("CHROMADB_BUCKET environment variable not set, skipping ChromaDB loading")
            return None
        
        prefix = 'chromadb/'
        temp_dir = Path("/tmp/chroma_db")
        
        logger.info(f"Loading ChromaDB from s3://{bucket}/{prefix} to {temp_dir}")
        
        # Create temp directory if it doesn't exist
        temp_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize S3 client
        s3 = boto3.client('s3')
        
        # Download ChromaDB files
        paginator = s3.get_paginator('list_objects_v2')
        file_count = 0
        
        for page in paginator.paginate(Bucket=bucket, Prefix=prefix):
            for obj in page.get('Contents', []):
                key = obj['Key']
                
                # Skip directory markers
                if key.endswith('/'):
                    continue
                
                # Calculate local path (remove prefix)
                relative_path = key.replace(prefix, '', 1)
                local_path = temp_dir / relative_path
                
                # Create parent directories
                local_path.parent.mkdir(parents=True, exist_ok=True)
                
                # Download file
                logger.debug(f"Downloading {key} to {local_path}")
                s3.download_file(bucket, key, str(local_path))
                file_count += 1
        
        logger.info(f"Successfully downloaded {file_count} ChromaDB files to {temp_dir}")
        
        # Mark as loaded
        chroma_loaded = True
        
        return temp_dir
        
    except Exception as e:
        logger.error(f"Failed to load ChromaDB from S3: {e}", exc_info=True)
        return None


# Load configuration at module initialization (cold start)
# This happens once per Lambda container, before any requests are processed
config_values = load_config()

if config_values:
    logger.info(f"Configuration loaded successfully with {len(config_values)} values")
else:
    logger.warning("Configuration loading returned empty - using defaults")

# Load ChromaDB at module initialization (cold start)
# This happens once per Lambda container
chromadb_path = load_chromadb_from_s3()

if chromadb_path:
    # Update the RAG service to use the downloaded ChromaDB
    # This is done by setting an environment variable that the RAG service can read
    os.environ['CHROMA_DB_PATH'] = str(chromadb_path)
    logger.info(f"ChromaDB loaded and available at {chromadb_path}")
else:
    logger.warning("ChromaDB not loaded - RAG functionality may be limited")

# Create Lambda handler with Mangum adapter
# lifespan="off" is required for Lambda compatibility to prevent
# startup/shutdown event handling issues in the Lambda environment
handler = Mangum(app, lifespan="off")
