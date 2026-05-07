"""Government Schemes routes"""
from flask import Blueprint, request

from app import db
from app.models.scheme import GovernmentScheme
from app.utils.auth import admin_required
from app.utils.responses import success, error, paginate

scheme_bp = Blueprint("schemes", __name__)


@scheme_bp.route("/", methods=["GET"])
def list_schemes():
    category = request.args.get("category")
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 10, type=int)

    query = GovernmentScheme.query.filter_by(is_active=True)
    if category:
        query = query.filter_by(category=category)
    query = query.order_by(GovernmentScheme.created_at.desc())
    return paginate(query, page, per_page, lambda s: s.to_dict())


@scheme_bp.route("/<int:scheme_id>", methods=["GET"])
def get_scheme(scheme_id):
    scheme = GovernmentScheme.query.get_or_404(scheme_id)
    return success(scheme.to_dict())


@scheme_bp.route("/categories", methods=["GET"])
def list_categories():
    return success(GovernmentScheme.CATEGORIES)


@scheme_bp.route("/", methods=["POST"])
@admin_required
def create_scheme():
    data = request.get_json(silent=True) or {}
    name = (data.get("name") or "").strip()
    category = data.get("category", "")

    if not name:
        return error("Scheme name is required")
    if category not in GovernmentScheme.CATEGORIES:
        return error(f"Category must be one of: {', '.join(GovernmentScheme.CATEGORIES)}")

    scheme = GovernmentScheme(
        name=name,
        category=category,
        eligibility=data.get("eligibility"),
        benefits=data.get("benefits"),
        scheme_url=data.get("scheme_url"),
    )
    if "application_steps" in data:
        scheme.application_steps = data["application_steps"]

    db.session.add(scheme)
    db.session.commit()
    return success(scheme.to_dict(), "Scheme created", 201)


@scheme_bp.route("/<int:scheme_id>", methods=["PUT"])
@admin_required
def update_scheme(scheme_id):
    scheme = GovernmentScheme.query.get_or_404(scheme_id)
    data = request.get_json(silent=True) or {}

    for field in ("name", "eligibility", "benefits", "scheme_url"):
        if field in data:
            setattr(scheme, field, data[field])
    if "category" in data:
        if data["category"] not in GovernmentScheme.CATEGORIES:
            return error("Invalid category")
        scheme.category = data["category"]
    if "application_steps" in data:
        scheme.application_steps = data["application_steps"]
    if "is_active" in data:
        scheme.is_active = bool(data["is_active"])

    db.session.commit()
    return success(scheme.to_dict(), "Scheme updated")


@scheme_bp.route("/<int:scheme_id>", methods=["DELETE"])
@admin_required
def delete_scheme(scheme_id):
    scheme = GovernmentScheme.query.get_or_404(scheme_id)
    scheme.is_active = False
    db.session.commit()
    return success(message="Scheme deactivated")
