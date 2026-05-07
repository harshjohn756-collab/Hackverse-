"""Standardized JSON response helpers"""
from flask import jsonify


def success(data=None, message="Success", status=200):
    resp = {"success": True, "message": message}
    if data is not None:
        resp["data"] = data
    return jsonify(resp), status


def error(message="An error occurred", status=400, details=None):
    resp = {"success": False, "error": message}
    if details:
        resp["details"] = details
    return jsonify(resp), status


def paginate(query, page: int, per_page: int, serializer):
    """Helper to paginate a SQLAlchemy query and return structured response."""
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    return success({
        "items": [serializer(item) for item in pagination.items],
        "total": pagination.total,
        "page": pagination.page,
        "pages": pagination.pages,
        "per_page": pagination.per_page,
        "has_next": pagination.has_next,
        "has_prev": pagination.has_prev,
    })
