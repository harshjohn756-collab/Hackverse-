"""Admin routes — dashboard stats, user/service/booking management"""
from flask import Blueprint, request

from app import db
from app.models.user import User
from app.models.service import Service
from app.models.booking import Booking
from app.models.payment import Payment, Wallet
from app.utils.auth import admin_required
from app.utils.responses import success, error, paginate

admin_bp = Blueprint("admin", __name__)


# ─── Dashboard ────────────────────────────────────────────────────────────────

@admin_bp.route("/stats", methods=["GET"])
@admin_required
def dashboard_stats():
    stats = {
        "users": {
            "total": User.query.count(),
            "providers": User.query.filter_by(role="provider").count(),
            "customers": User.query.filter_by(role="customer").count(),
            "active": User.query.filter_by(is_active=True).count(),
        },
        "services": {
            "total": Service.query.count(),
            "approved": Service.query.filter_by(is_approved=True).count(),
            "pending": Service.query.filter_by(is_approved=False, is_active=True).count(),
        },
        "bookings": {
            "total": Booking.query.count(),
            "pending": Booking.query.filter_by(status=Booking.STATUS_PENDING).count(),
            "completed": Booking.query.filter_by(status=Booking.STATUS_COMPLETED).count(),
            "cancelled": Booking.query.filter_by(status=Booking.STATUS_CANCELLED).count(),
        },
        "revenue": {
            "total_payments": Payment.query.filter_by(status=Payment.STATUS_SUCCESS).count(),
            "total_amount": db.session.query(
                db.func.sum(Payment.amount)
            ).filter_by(status=Payment.STATUS_SUCCESS).scalar() or 0,
        },
    }
    return success(stats)


# ─── Users ────────────────────────────────────────────────────────────────────

@admin_bp.route("/users", methods=["GET"])
@admin_required
def list_users():
    role = request.args.get("role")
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 20, type=int)

    query = User.query
    if role:
        query = query.filter_by(role=role)
    query = query.order_by(User.created_at.desc())
    return paginate(query, page, per_page, lambda u: u.to_dict())


@admin_bp.route("/users/<int:user_id>", methods=["GET"])
@admin_required
def get_user(user_id):
    user = User.query.get_or_404(user_id)
    data = user.to_dict()
    data["profile"] = user.profile.to_dict() if user.profile else None
    data["wallet"] = user.wallet.to_dict() if user.wallet else None
    return success(data)


@admin_bp.route("/users/<int:user_id>/toggle-active", methods=["POST"])
@admin_required
def toggle_user_active(user_id):
    user = User.query.get_or_404(user_id)
    if user.role == "admin":
        return error("Cannot deactivate an admin account", 403)
    user.is_active = not user.is_active
    db.session.commit()
    state = "activated" if user.is_active else "deactivated"
    return success(user.to_dict(), f"User {state}")


@admin_bp.route("/users/<int:user_id>/make-admin", methods=["POST"])
@admin_required
def make_admin(user_id):
    user = User.query.get_or_404(user_id)
    user.role = "admin"
    db.session.commit()
    return success(user.to_dict(), "User promoted to admin")


# ─── Services ─────────────────────────────────────────────────────────────────

@admin_bp.route("/services/pending", methods=["GET"])
@admin_required
def pending_services():
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 20, type=int)
    query = Service.query.filter_by(is_approved=False, is_active=True).order_by(Service.created_at.asc())
    return paginate(query, page, per_page, lambda s: s.to_dict(include_provider=True))


@admin_bp.route("/services/<int:service_id>/approve", methods=["POST"])
@admin_required
def approve_service(service_id):
    service = Service.query.get_or_404(service_id)
    service.is_approved = True
    db.session.commit()
    return success(service.to_dict(include_provider=True), "Service approved")


@admin_bp.route("/services/<int:service_id>/reject", methods=["POST"])
@admin_required
def reject_service(service_id):
    service = Service.query.get_or_404(service_id)
    service.is_approved = False
    service.is_active = False
    db.session.commit()
    return success(service.to_dict(), "Service rejected and deactivated")


@admin_bp.route("/services", methods=["GET"])
@admin_required
def list_all_services():
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 20, type=int)
    approved = request.args.get("approved")
    query = Service.query
    if approved is not None:
        query = query.filter_by(is_approved=approved.lower() == "true")
    query = query.order_by(Service.created_at.desc())
    return paginate(query, page, per_page, lambda s: s.to_dict(include_provider=True))


# ─── Bookings ─────────────────────────────────────────────────────────────────

@admin_bp.route("/bookings", methods=["GET"])
@admin_required
def list_all_bookings():
    status = request.args.get("status")
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 20, type=int)
    query = Booking.query
    if status:
        query = query.filter_by(status=status)
    query = query.order_by(Booking.created_at.desc())
    return paginate(query, page, per_page, lambda b: b.to_dict(include_details=True))


# ─── Payments ─────────────────────────────────────────────────────────────────

@admin_bp.route("/payments", methods=["GET"])
@admin_required
def list_all_payments():
    status = request.args.get("status")
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 20, type=int)
    query = Payment.query
    if status:
        query = query.filter_by(status=status)
    query = query.order_by(Payment.created_at.desc())
    return paginate(query, page, per_page, lambda p: p.to_dict())


# ─── Wallet credit (admin manual credit) ─────────────────────────────────────

@admin_bp.route("/wallet/credit", methods=["POST"])
@admin_required
def admin_credit_wallet():
    data = request.get_json(silent=True) or {}
    user_id = data.get("user_id")
    amount = data.get("amount", 0)

    if not user_id or float(amount) <= 0:
        return error("user_id and positive amount required")

    wallet = Wallet.query.filter_by(user_id=user_id).first()
    if not wallet:
        wallet = Wallet(user_id=user_id)
        db.session.add(wallet)

    wallet.credit(float(amount))
    db.session.commit()
    return success(wallet.to_dict(), f"₹{amount} credited to user {user_id}'s wallet")
