"""Booking routes — create, view, accept/reject/complete/cancel"""
from datetime import datetime
from flask import Blueprint, request
from flask_jwt_extended import jwt_required

from app import db
from app.models.booking import Booking
from app.models.service import Service
from app.utils.auth import get_current_user
from app.utils.responses import success, error, paginate

booking_bp = Blueprint("bookings", __name__)


@booking_bp.route("/", methods=["POST"])
@jwt_required()
def create_booking():
    user = get_current_user()
    # User role check is removed so providers can book services from others.
    # We will check if they are booking their own service below.

    data = request.get_json(silent=True) or {}
    service_id = data.get("service_id")
    scheduled_at = data.get("scheduled_at")
    notes = data.get("notes", "")
    address = data.get("address", "")
    contact_number = data.get("contact_number", "")

    if not service_id:
        return error("service_id is required")
    if not scheduled_at:
        return error("scheduled_at is required (ISO format)")
    if not address:
        return error("address is required")
    if not contact_number:
        return error("contact_number is required")
    if not notes:
        return error("notes is required")

    service = Service.query.get(service_id)
    if not service or not service.is_active or not service.is_approved:
        return error("Service not found or unavailable", 404)

    if service.provider_id == user.id:
        return error("You cannot book your own service", 403)

    try:
        scheduled_dt = datetime.fromisoformat(scheduled_at.replace("Z", "+00:00"))
    except ValueError:
        return error("Invalid date format. Use ISO 8601 (e.g. 2024-06-01T10:00:00Z)")

    if scheduled_dt.tzinfo is not None:
        scheduled_dt = scheduled_dt.replace(tzinfo=None)

    if scheduled_dt < datetime.utcnow():
        return error("Scheduled time must be in the future")

    booking = Booking(
        service_id=service.id,
        customer_id=user.id,
        provider_id=service.provider_id,
        scheduled_at=scheduled_dt,
        notes=notes,
        address=address,
        contact_number=contact_number,
    )
    db.session.add(booking)
    db.session.commit()
    return success(booking.to_dict(include_details=True), "Booking created", 201)


@booking_bp.route("/", methods=["GET"])
@jwt_required()
def list_bookings():
    user = get_current_user()
    status = request.args.get("status")
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 10, type=int)

    if user.role == "customer":
        query = Booking.query.filter_by(customer_id=user.id)
    elif user.role == "provider":
        query = Booking.query.filter_by(provider_id=user.id)
    else:  # admin
        query = Booking.query

    if status == "active":
        query = query.filter(Booking.status.in_([
            Booking.STATUS_ACCEPTED, 
            Booking.STATUS_CONFIRMED, 
            Booking.STATUS_PACKED, 
            Booking.STATUS_OUT_FOR_DELIVERY
        ]))
    elif status and status in Booking.STATUSES:
        query = query.filter_by(status=status)

    query = query.order_by(Booking.created_at.desc())
    return paginate(query, page, per_page, lambda b: b.to_dict(include_details=True))


@booking_bp.route("/<int:booking_id>", methods=["GET"])
@jwt_required()
def get_booking(booking_id):
    user = get_current_user()
    booking = Booking.query.get_or_404(booking_id)

    if user.role not in ("admin",) and booking.customer_id != user.id and booking.provider_id != user.id:
        return error("Access denied", 403)

    return success(booking.to_dict(include_details=True))



@booking_bp.route("/<int:booking_id>/accept", methods=["POST"])
@jwt_required()
def accept_booking(booking_id):
    user = get_current_user()
    booking = Booking.query.get_or_404(booking_id)

    if booking.provider_id != user.id and user.role != "admin":
        return error("Only the provider can accept this booking", 403)
    if booking.status != Booking.STATUS_PENDING:
        return error("Can only accept pending bookings")

    booking.status = Booking.STATUS_ACCEPTED
    db.session.commit()
    return success(booking.to_dict(include_details=True), "Booking accepted")


@booking_bp.route("/<int:booking_id>/reject", methods=["POST"])
@jwt_required()
def reject_booking(booking_id):
    user = get_current_user()
    booking = Booking.query.get_or_404(booking_id)

    if booking.provider_id != user.id and user.role != "admin":
        return error("Only the provider can reject this booking", 403)
    if booking.status != Booking.STATUS_PENDING:
        return error("Can only reject pending bookings")

    booking.status = Booking.STATUS_REJECTED
    db.session.commit()
    return success(booking.to_dict(include_details=True), "Booking rejected")


@booking_bp.route("/<int:booking_id>/complete", methods=["POST"])
@jwt_required()
def complete_booking(booking_id):
    user = get_current_user()
    booking = Booking.query.get_or_404(booking_id)

    if booking.provider_id != user.id and user.role != "admin":
        return error("Only the provider can mark as complete", 403)
    if booking.status not in (Booking.STATUS_ACCEPTED, Booking.STATUS_CONFIRMED, Booking.STATUS_PACKED, Booking.STATUS_OUT_FOR_DELIVERY):
        return error("Can only complete active bookings")

    booking.status = Booking.STATUS_COMPLETED
    db.session.commit()
    return success(booking.to_dict(include_details=True), "Booking completed")


@booking_bp.route("/<int:booking_id>/cancel", methods=["POST"])
@jwt_required()
def cancel_booking(booking_id):
    user = get_current_user()
    booking = Booking.query.get_or_404(booking_id)

    if booking.customer_id != user.id and booking.provider_id != user.id and user.role != "admin":
        return error("Access denied", 403)
    if booking.status in (Booking.STATUS_COMPLETED, Booking.STATUS_CANCELLED):
        return error(f"Cannot cancel a {booking.status} booking")

    booking.status = Booking.STATUS_CANCELLED
    db.session.commit()
    return success(booking.to_dict(include_details=True), "Booking cancelled")


@booking_bp.route("/<int:booking_id>/status", methods=["PUT"])
@jwt_required()
def update_booking_status(booking_id):
    user = get_current_user()
    booking = Booking.query.get_or_404(booking_id)

    if booking.provider_id != user.id and user.role != "admin":
        return error("Only the provider can update this booking status", 403)
        
    data = request.get_json(silent=True) or {}
    new_status = data.get("status")
    
    if not new_status or new_status not in Booking.STATUSES:
        return error("Invalid status")
        
    booking.status = new_status
    db.session.commit()
    return success(booking.to_dict(include_details=True), f"Booking status updated to {new_status}")
