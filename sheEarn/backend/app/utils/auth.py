"""JWT Auth helpers and role-based access decorators"""
from functools import wraps
from flask import jsonify
from flask_jwt_extended import verify_jwt_in_request, get_jwt_identity

from app import db
from app.models.user import User


def get_current_user():
    """Return the currently authenticated User object."""
    user_id = get_jwt_identity()
    return db.session.get(User, int(user_id))


def role_required(*roles):
    """Decorator that restricts access to users with specific roles."""
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            verify_jwt_in_request()
            user = get_current_user()
            if not user or not user.is_active:
                return jsonify({"error": "Account not found or inactive"}), 401
            if user.role not in roles:
                return jsonify({"error": "Access forbidden: insufficient privileges"}), 403
            return fn(*args, **kwargs)
        return wrapper
    return decorator


def provider_required(fn):
    """Shortcut: only providers and admins."""
    @wraps(fn)
    def wrapper(*args, **kwargs):
        verify_jwt_in_request()
        user = get_current_user()
        if not user or not user.is_active:
            return jsonify({"error": "Account not found or inactive"}), 401
        if user.role not in ("provider", "admin"):
            return jsonify({"error": "Only service providers can perform this action"}), 403
        return fn(*args, **kwargs)
    return wrapper


def admin_required(fn):
    """Shortcut: only admins."""
    @wraps(fn)
    def wrapper(*args, **kwargs):
        verify_jwt_in_request()
        user = get_current_user()
        if not user or not user.is_active:
            return jsonify({"error": "Account not found or inactive"}), 401
        if user.role != "admin":
            return jsonify({"error": "Admin access required"}), 403
        return fn(*args, **kwargs)
    return wrapper
