"""Payment routes — Real UPI payments (hackathon-ready)
Generates UPI deep links & QR codes for real money transfer.
No API keys or business registration needed.
"""
import logging
from flask import Blueprint, request
from flask_jwt_extended import jwt_required
from urllib.parse import quote

from app import db
from app.models.booking import Booking
from app.models.payment import Payment, Wallet
from app.models.profile import Profile
from app.utils.auth import get_current_user
from app.utils.responses import success, error

payment_bp = Blueprint("payments", __name__)
logger = logging.getLogger(__name__)


@payment_bp.route("/initiate", methods=["POST"])
@jwt_required()
def initiate_payment():
    """
    Step 1: Customer initiates payment → returns UPI deep link + provider info.
    The frontend shows a QR code and/or opens UPI app for REAL money transfer.
    """
    user = get_current_user()
    data = request.get_json(silent=True) or {}
    booking_id = data.get("booking_id")

    if not booking_id:
        return error("booking_id is required")

    booking = Booking.query.get(booking_id)
    if not booking:
        return error("Booking not found", 404)
    if booking.customer_id != user.id:
        return error("Not your booking", 403)
    if booking.status not in (Booking.STATUS_ACCEPTED, Booking.STATUS_COMPLETED,
                               Booking.STATUS_CONFIRMED, Booking.STATUS_PACKED,
                               Booking.STATUS_OUT_FOR_DELIVERY):
        return error("Can only pay for accepted or active bookings")

    # Check if already paid
    existing = Payment.query.filter_by(booking_id=booking.id).first()
    if existing and existing.status == Payment.STATUS_SUCCESS:
        return error("Payment already completed for this booking")

    service = booking.service
    amount = service.price

    # Get provider's UPI ID
    provider_profile = Profile.query.filter_by(user_id=booking.provider_id).first()
    provider_upi = provider_profile.upi_id if provider_profile else None
    provider_name = booking.provider.name if booking.provider else "Provider"

    if not provider_upi:
        return error("Provider has not set their UPI ID yet. Ask them to update their profile.", 400)

    # Create or reuse payment record
    if existing:
        payment = existing
        payment.status = Payment.STATUS_PENDING
    else:
        payment = Payment(
            booking_id=booking.id,
            amount=amount,
            provider_id=booking.provider_id,
            customer_id=user.id,
            upi_id=provider_upi,
            status=Payment.STATUS_PENDING,
        )
        db.session.add(payment)

    db.session.commit()

    # Build UPI deep link (works with Google Pay, PhonePe, Paytm, etc.)
    txn_note = f"SheEarn Booking #{booking.id} - {service.title}"
    upi_link = (
        f"upi://pay?"
        f"pa={quote(provider_upi)}"
        f"&pn={quote(provider_name)}"
        f"&am={amount}"
        f"&cu=INR"
        f"&tn={quote(txn_note)}"
        f"&tr={payment.transaction_id}"
    )

    return success({
        "payment": payment.to_dict(),
        "upi_link": upi_link,
        "provider_upi": provider_upi,
        "provider_name": provider_name,
        "amount": amount,
        "transaction_id": payment.transaction_id,
        "booking_id": booking.id,
        "service_title": service.title,
    }, "Payment initiated — scan QR or tap to pay via UPI", 201)


@payment_bp.route("/confirm/<int:payment_id>", methods=["POST"])
@jwt_required()
def confirm_payment(payment_id):
    """
    Step 2: Customer confirms they've paid via UPI.
    Marks payment as success and credits provider's internal wallet.
    """
    user = get_current_user()
    payment = Payment.query.get_or_404(payment_id)

    if payment.customer_id != user.id and user.role != "admin":
        return error("Access denied", 403)
    if payment.status == Payment.STATUS_SUCCESS:
        return success(payment.to_dict(), "Payment already confirmed")

    data = request.get_json(silent=True) or {}
    payment_method = data.get("payment_method", "upi")
    upi_ref = data.get("upi_ref", "")  # Optional: customer can enter UPI ref number

    # Mark payment as success
    payment.status = Payment.STATUS_SUCCESS
    payment.payment_method = payment_method
    if upi_ref:
        payment.upi_id = f"{payment.upi_id} (Ref: {upi_ref})"

    # Credit provider wallet (full amount)
    provider_credit = payment.amount

    provider_wallet = Wallet.query.filter_by(user_id=payment.provider_id).first()
    if not provider_wallet:
        provider_wallet = Wallet(user_id=payment.provider_id)
        db.session.add(provider_wallet)
    provider_wallet.credit(provider_credit)

    # Track customer spending
    customer_wallet = Wallet.query.filter_by(user_id=payment.customer_id).first()
    if not customer_wallet:
        customer_wallet = Wallet(user_id=payment.customer_id)
        db.session.add(customer_wallet)
    customer_wallet.total_spent += payment.amount

    # Auto-complete booking if still active
    booking = payment.booking
    if booking.status in (Booking.STATUS_ACCEPTED, Booking.STATUS_CONFIRMED,
                          Booking.STATUS_PACKED, Booking.STATUS_OUT_FOR_DELIVERY):
        booking.status = Booking.STATUS_COMPLETED

    db.session.commit()

    logger.info(f"Payment {payment.transaction_id}: ₹{payment.amount} → provider {payment.provider_id} via {payment_method}")

    return success({
        "payment": payment.to_dict(),
        "provider_credited": provider_credit,
    }, f"✅ Payment of ₹{payment.amount} confirmed! Provider credited ₹{provider_credit}.")


@payment_bp.route("/wallet", methods=["GET"])
@jwt_required()
def get_wallet():
    user = get_current_user()
    wallet = user.wallet
    if not wallet:
        wallet = Wallet(user_id=user.id)
        db.session.add(wallet)
        db.session.commit()
    return success(wallet.to_dict())


@payment_bp.route("/wallet/add", methods=["POST"])
@jwt_required()
def add_money():
    """Add money to wallet (hackathon demo — instant top-up)."""
    user = get_current_user()
    data = request.get_json(silent=True) or {}
    amount = data.get("amount", 0)

    if not amount or amount <= 0:
        return error("Amount must be positive")
    if amount > 100000:
        return error("Max top-up is ₹1,00,000")

    wallet = Wallet.query.filter_by(user_id=user.id).first()
    if not wallet:
        wallet = Wallet(user_id=user.id)
        db.session.add(wallet)

    wallet.balance += amount
    db.session.commit()

    return success(wallet.to_dict(), f"₹{amount} added to wallet!")


@payment_bp.route("/history", methods=["GET"])
@jwt_required()
def payment_history():
    user = get_current_user()
    if user.role == "customer":
        payments = Payment.query.filter_by(customer_id=user.id).order_by(Payment.created_at.desc()).all()
    elif user.role == "provider":
        payments = Payment.query.filter_by(provider_id=user.id).order_by(Payment.created_at.desc()).all()
    else:
        payments = Payment.query.order_by(Payment.created_at.desc()).limit(100).all()

    return success([p.to_dict() for p in payments])
