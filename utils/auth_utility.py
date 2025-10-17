import jwt
import logging
from datetime import datetime, timedelta
from functools import wraps
from flask import request, jsonify
import configparser

logger = logging.getLogger(__name__)

# Load JWT secret from config
config = configparser.ConfigParser()
config.read('db_handler/vault/secrets.ini')

try:
    JWT_SECRET = config["JWT"]["secret"]
except KeyError:
    JWT_SECRET = "default-secret-change-me"
    logger.warning("JWT secret not found in config, using default")

def create_token(user_id: str) -> str:
    """Create JWT token for user"""
    try:
        payload = {
            'user_id': user_id,
            'exp': datetime.utcnow() + timedelta(hours=24),
            'iat': datetime.utcnow()
        }
        token = jwt.encode(payload, JWT_SECRET, algorithm='HS256')
        return token
    except Exception as e:
        logger.error(f"Failed to create token: {e}")
        raise

def validate_token(token: str) -> dict:
    """Validate JWT token"""
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=['HS256'])
        return payload
    except jwt.ExpiredSignatureError:
        raise ValueError("Token expired")
    except jwt.InvalidTokenError:
        raise ValueError("Invalid token")

def token_required(f):
    """Decorator to require valid JWT token"""
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        
        # Get token from Authorization header
        if 'Authorization' in request.headers:
            auth_header = request.headers['Authorization']
            try:
                token = auth_header.split(" ")[1]  # Bearer <token>
            except IndexError:
                return jsonify({'message': 'Invalid token format'}), 401
        
        if not token:
            return jsonify({'message': 'Token is missing'}), 401
        
        try:
            payload = validate_token(token)
            request.current_user = payload
        except ValueError as e:
            return jsonify({'message': str(e)}), 401
        except Exception as e:
            logger.error(f"Token validation error: {e}")
            return jsonify({'message': 'Token validation failed'}), 401
        
        return f(*args, **kwargs)
    
    return decorated