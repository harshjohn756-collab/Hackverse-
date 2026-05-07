"""Profile routes — view and update user profiles"""
from flask import Blueprint, request
from flask_jwt_extended import jwt_required

from app import db
from app.models.profile import Profile
from app.models.user import User
from app.utils.auth import get_current_user
from app.utils.responses import success, error
from app.utils.upload import save_file

profile_bp = Blueprint("profile", __name__)


@profile_bp.route("/", methods=["GET"])
@jwt_required()
def get_my_profile():
    user = get_current_user()
    if not user:
        return error("User not found", 401)
    data = user.to_dict()
    data["profile"] = user.profile.to_dict() if user.profile else None
    data["wallet"] = user.wallet.to_dict() if user.wallet else None
    return success(data)


@profile_bp.route("/", methods=["PUT"])
@jwt_required()
def update_profile():
    user = get_current_user()
    if not user:
        return error("User not found", 401)
    data = request.get_json(silent=True) or {}

    # Update user fields
    if "name" in data:
        user.name = data["name"].strip()
    if "language" in data:
        user.language = data["language"]

    # Update/create profile
    profile = user.profile
    if not profile:
        profile = Profile(user_id=user.id)
        db.session.add(profile)

    if "location" in data:
        profile.location = data["location"]
    if "latitude" in data:
        profile.latitude = float(data["latitude"])
    if "longitude" in data:
        profile.longitude = float(data["longitude"])
    if "skills" in data:
        profile.skills = data["skills"]
    if "description" in data:
        profile.description = data["description"]
    if "upi_id" in data:
        profile.upi_id = data["upi_id"].strip() if data["upi_id"] else None

    db.session.commit()

    result = user.to_dict()
    result["profile"] = profile.to_dict()
    return success(result, "Profile updated")


@profile_bp.route("/upload-image", methods=["POST"])
@jwt_required()
def upload_profile_image():
    user = get_current_user()
    if not user:
        return error("User not found", 401)
    file = request.files.get("image")
    url = save_file(file)
    if not url:
        return error("Invalid or missing image file")

    profile = user.profile
    if not profile:
        profile = Profile(user_id=user.id)
        db.session.add(profile)

    profile.profile_image = url
    db.session.commit()
    return success({"profile_image": url}, "Profile image updated")


@profile_bp.route("/remove-image", methods=["DELETE"])
@jwt_required()
def remove_profile_image():
    user = get_current_user()
    if not user:
        return error("User not found", 401)
    profile = user.profile
    if profile and profile.profile_image:
        profile.profile_image = None
        db.session.commit()
        return success(message="Profile image removed")
    return error("No profile image found", 404)


@profile_bp.route("/<int:user_id>", methods=["GET"])
def get_public_profile(user_id):
    user = User.query.get_or_404(user_id)
    data = {
        "id": user.id,
        "name": user.name,
        "role": user.role,
        "profile": user.profile.to_dict() if user.profile else None,
    }
    if user.role == "provider":
        data["services"] = [s.to_dict() for s in user.services.filter_by(is_active=True, is_approved=True).all()]
    return success(data)
