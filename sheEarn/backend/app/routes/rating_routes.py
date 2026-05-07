"""Rating routes — submit and list ratings"""
from flask import Blueprint, request
from flask_jwt_extended import jwt_required
from sqlalchemy.exc import IntegrityError

from app import db
from app.models.booking import Booking
from app.models.rating import Rating
from app.models.service import Service
from app.utils.auth import get_current_user
from app.utils.responses import success, error

rating_bp = Blueprint("ratings", __name__)


@rating_bp.route("/", methods=["POST"])
@jwt_required()
def submit_rating():
    user = get_current_user()
    data = request.get_json(silent=True) or {}

    service_id = data.get("service_id")
    booking_id = data.get("booking_id")
    stars = data.get("stars")
    comment = data.get("comment", "").strip()

    if not service_id:
        return error("service_id is required")
    if stars is None or int(stars) not in range(1, 6):
        return error("Stars must be an integer between 1 and 5")

    service = Service.query.get(service_id)
    if not service:
        return error("Service not found", 404)

    # Verify the user actually had a completed booking for this service
    if booking_id:
        booking = Booking.query.get(booking_id)
        if not booking or booking.customer_id != user.id or booking.service_id != service_id:
            return error("Invalid booking reference", 400)
        if booking.status != Booking.STATUS_COMPLETED:
            return error("You can only rate after the booking is completed")
    else:
        # Check any completed booking
        existing_booking = Booking.query.filter_by(
            customer_id=user.id,
            service_id=service_id,
            status=Booking.STATUS_COMPLETED,
        ).first()
        if not existing_booking:
            return error("You must complete a booking before rating this service")

    rating = Rating(
        user_id=user.id,
        service_id=service_id,
        booking_id=booking_id,
        stars=int(stars),
        comment=comment or None,
    )
    db.session.add(rating)

    try:
        db.session.flush()
        service.recalculate_rating()
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return error("You have already rated this service", 409)

    return success(rating.to_dict(include_reviewer=True), "Rating submitted", 201)


@rating_bp.route("/service/<int:service_id>", methods=["GET"])
def service_ratings(service_id):
    service = Service.query.get_or_404(service_id)
    ratings = Rating.query.filter_by(service_id=service_id).order_by(Rating.created_at.desc()).all()
    return success({
        "avg_rating": service.avg_rating,
        "rating_count": service.rating_count,
        "ratings": [r.to_dict(include_reviewer=True) for r in ratings],
    })
