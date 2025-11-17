# routes/decorators.py

from flask import request, jsonify, current_app
import jwt
from models.userModel import User

def token_required(f):
    from functools import wraps
    @wraps(f)
    def decorated(*args, **kwargs):
        # Accept token from Authorization header (Bearer ...) or fallback to access_token cookie
        token = request.headers.get('Authorization')
        if not token:
            token = request.cookies.get('access_token')
        if not token:
            return jsonify({'error': 'Token ausente'}), 401
        if isinstance(token, str) and token.startswith('Bearer '):
            token = token.split(' ', 1)[1]
        try:
            payload = jwt.decode(token, current_app.config['SECRET_KEY'], algorithms=['HS256'])
            user = User.query.get(payload['user_id'])
            if not user:
                return jsonify({'error': 'Usuário não encontrado'}), 401
            request.user = user
        except jwt.ExpiredSignatureError:
            return jsonify({'error': 'Token expirado'}), 401
        except jwt.InvalidTokenError:
            return jsonify({'error': 'Token inválido'}), 401
        return f(*args, **kwargs)
    return decorated

def role_required(required_role):
    def decorator(f):
        from functools import wraps
        @wraps(f)
        @token_required
        def wrapped(*args, **kwargs):
            user = getattr(request, 'user', None)
            # Support passing a single role (string) or a list/tuple of allowed roles
            if isinstance(required_role, (list, tuple, set)):
                allowed = {str(r).upper() for r in required_role}
            else:
                allowed = {str(required_role).upper()}

            # Normalize user's role value to a comparable string
            try:
                user_role_val = (user.role.value if hasattr(user.role, 'value') else user.role)
            except Exception:
                user_role_val = None

            user_role_norm = str(user_role_val).upper() if user_role_val else None

            # Alias groups: consider common synonyms between languages
            moderator_aliases = {'MODERADOR', 'MODERATOR', 'MOD'}
            admin_aliases = {'ADMIN'}

            allowed_match = False
            if user_role_norm and user_role_norm in allowed:
                allowed_match = True
            else:
                # Special-case: if allowed includes any moderator synonym, accept any moderator alias
                if allowed & moderator_aliases and user_role_norm in moderator_aliases:
                    allowed_match = True
                # Special-case: admin aliases
                if allowed & admin_aliases and user_role_norm in admin_aliases:
                    allowed_match = True

            if not user or not allowed_match:
                return jsonify({'error': 'Acesso restrito a {}'.format(required_role)}), 403
            return f(*args, **kwargs)
        return wrapped
    return decorator