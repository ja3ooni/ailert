import os
import json
import boto3
import logging
from typing import Optional, Dict, Any
from dataclasses import dataclass
from botocore.exceptions import ClientError

logger = logging.getLogger(__name__)

@dataclass
class Config:
    """Application configuration with environment variable support"""
    sendgrid_api_key: str = os.getenv('SENDGRID_API_KEY', '')
    dynamo_region: str = os.getenv('AWS_REGION', 'us-east-1')
    jwt_secret: str = os.getenv('JWT_SECRET', 'default-secret-change-me')
    redis_url: str = os.getenv('REDIS_URL', 'redis://localhost:6379')
    max_email_concurrent: int = int(os.getenv('MAX_EMAIL_CONCURRENT', '10'))
    cache_ttl: int = int(os.getenv('CACHE_TTL', '3600'))
    db_pool_size: int = int(os.getenv('DB_POOL_SIZE', '10'))
    log_level: str = os.getenv('LOG_LEVEL', 'INFO')

class SecretManager:
    """AWS Secrets Manager integration"""
    def __init__(self, region_name: str):
        self.client = boto3.client('secretsmanager', region_name=region_name)
    
    def get_secret(self, secret_name: str) -> Dict[str, Any]:
        """Retrieve secret from AWS Secrets Manager"""
        try:
            response = self.client.get_secret_value(SecretId=secret_name)
            return json.loads(response['SecretString'])
        except ClientError as e:
            logger.error(f"Failed to retrieve secret {secret_name}: {e}")
            raise
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse secret {secret_name}: {e}")
            raise
    
    def update_secret(self, secret_name: str, secret_value: Dict[str, Any]):
        """Update secret in AWS Secrets Manager"""
        try:
            self.client.update_secret(
                SecretId=secret_name,
                SecretString=json.dumps(secret_value)
            )
            logger.info(f"Updated secret {secret_name}")
        except ClientError as e:
            logger.error(f"Failed to update secret {secret_name}: {e}")
            raise

def get_config() -> Config:
    """Get application configuration"""
    return Config()

def setup_logging(log_level: str = 'INFO'):
    """Setup structured logging"""
    logging.basicConfig(
        level=getattr(logging, log_level.upper()),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler('newsletter.log')
        ]
    )