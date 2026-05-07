"""Service routes — CRUD + location-based discovery"""
from flask import Blueprint, request
from flask_jwt_extended import jwt_required

from app import db
from app.models.service import Service
from app.models.profile import Profile
from app.utils.auth import get_current_user, provider_required
from app.utils.geo import filter_by_radius
from app.utils.responses import success, error, paginate
from app.utils.upload import save_file

service_bp = Blueprint("services", __name__)


@service_bp.route("/", methods=["GET"])
def list_services():
    """Public endpoint — browse/search approved services with optional location filter."""
    category = request.args.get("category")
    q = request.args.get("q", "").strip()
    lat = request.args.get("lat", type=float)
    lon = request.args.get("lon", type=float)
    radius = request.args.get("radius", 20.0, type=float)
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 10, type=int)

    query = Service.query.filter_by(is_approved=True, is_active=True)
    if category:
        query = query.filter_by(category=category)
    if q:
        query = query.filter(Service.title.ilike(f"%{q}%"))

    if lat and lon:
        # Load all filtered services with provider profiles for geo filtering
        services = query.all()
        pairs = [(s, s.provider.profile if s.provider else None) for s in services]
        geo_results = filter_by_radius(pairs, lat, lon, radius)
        items = []
        for s, profile, dist in geo_results:
            d = s.to_dict(include_provider=True)
            d["distance_km"] = dist
            items.append(d)
        return success({
            "items": items,
            "total": len(items),
            "page": 1,
            "pages": 1,
        })

    return paginate(query.order_by(Service.created_at.desc()), page, per_page,
                    lambda s: s.to_dict(include_provider=True))


@service_bp.route("/<int:service_id>", methods=["GET"])
def get_service(service_id):
    service = Service.query.get_or_404(service_id)
    data = service.to_dict(include_provider=True)
    data["ratings"] = [r.to_dict(include_reviewer=True) for r in service.ratings.order_by(None).limit(10).all()]
    return success(data)


@service_bp.route("/", methods=["POST"])
@provider_required
def create_service():
    user = get_current_user()
    
    if request.is_json:
        data = request.get_json(silent=True) or {}
    else:
        data = request.form

    title = (data.get("title") or "").strip()
    category = data.get("category", "")
    price = data.get("price")

    if not title:
        return error("Title is required")
    if category not in Service.CATEGORIES:
        return error(f"Category must be one of: {', '.join(Service.CATEGORIES)}")
    if price is None or float(price) < 0:
        return error("Valid price is required")

    service = Service(
        provider_id=user.id,
        title=title,
        category=category,
        price=float(price),
        description=data.get("description", ""),
        is_approved=True  # Auto-approve services so they appear immediately
    )
    db.session.add(service)

    # Handle image if provided
    file = request.files.get("image")
    if file:
        url = save_file(file)
        if url:
            service.images = [url]

    db.session.commit()
    return success(service.to_dict(), "Service created successfully", 201)


@service_bp.route("/<int:service_id>", methods=["PUT"])
@provider_required
def update_service(service_id):
    user = get_current_user()
    service = Service.query.get_or_404(service_id)

    if service.provider_id != user.id and user.role != "admin":
        return error("Not your service", 403)

    data = request.get_json(silent=True) or {}
    if "title" in data:
        service.title = data["title"].strip()
    if "category" in data:
        if data["category"] not in Service.CATEGORIES:
            return error("Invalid category")
        service.category = data["category"]
    if "price" in data:
        service.price = float(data["price"])
    if "description" in data:
        service.description = data["description"]
    if "is_active" in data:
        service.is_active = bool(data["is_active"])

    db.session.commit()
    return success(service.to_dict(), "Service updated")


@service_bp.route("/<int:service_id>/images", methods=["POST"])
@provider_required
def upload_service_images(service_id):
    user = get_current_user()
    service = Service.query.get_or_404(service_id)

    if service.provider_id != user.id:
        return error("Not your service", 403)

    files = request.files.getlist("images")
    if not files:
        return error("No images provided")

    urls = []
    for f in files[:5]:  # max 5 images
        url = save_file(f)
        if url:
            urls.append(url)

    service.images = service.images + urls
    db.session.commit()
    return success({"images": service.images}, "Images uploaded")


@service_bp.route("/<int:service_id>", methods=["DELETE"])
@provider_required
def delete_service(service_id):
    user = get_current_user()
    service = Service.query.get_or_404(service_id)

    if service.provider_id != user.id and user.role != "admin":
        return error("Not your service", 403)

    service.is_active = False
    db.session.commit()
    return success(message="Service deleted")


@service_bp.route("/my", methods=["GET"])
@provider_required
def my_services():
    user = get_current_user()
    services = Service.query.filter_by(provider_id=user.id, is_active=True).order_by(Service.created_at.desc()).all()
    return success([s.to_dict() for s in services])


@service_bp.route("/categories", methods=["GET"])
def get_categories():
    return success(Service.CATEGORIES)
