import jwt
import configparser
from functools import wraps
from flask import request, jsonify
from datetime import datetime, timedelta

config = configparser.ConfigParser()
config.read('db_handler/vault/secrets.ini')
JWT_SECRET_KEY = config["JWT"]["token"]


def create_token(user_id):
    payload = {
        'exp': datetime.now() + timedelta(days=1),
        'iat': datetime.now(),
        'sub': user_id
    }

    token = jwt.encode(
        payload,
        JWT_SECRET_KEY,
        algorithm='HS256'
    )
    return token


def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None

        # Check for token in headers
        if 'Authorization' in request.headers:
            token = request.headers['Authorization'].split(" ")[1]

        if not token:
            return jsonify({
                'message': 'Token is missing',
                'status': 'error'
            }), 401

        try:
            # Decode token
            data = jwt.decode(token, JWT_SECRET_KEY, algorithms=["HS256"])
            current_user = data['user']
        except:
            return jsonify({
                'message': 'Token is invalid',
                'status': 'error'
            }), 401

        return f(current_user, *args, **kwargs)

    return decorated
