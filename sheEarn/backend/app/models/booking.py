"""Booking model"""
from datetime import datetime
from app import db


class Booking(db.Model):
    __tablename__ = "bookings"

    STATUS_PENDING = "pending"
    STATUS_ACCEPTED = "accepted"
    STATUS_CONFIRMED = "confirmed"
    STATUS_PACKED = "packed"
    STATUS_OUT_FOR_DELIVERY = "out_for_delivery"
    STATUS_REJECTED = "rejected"
    STATUS_COMPLETED = "completed"
    STATUS_CANCELLED = "cancelled"

    STATUSES = [STATUS_PENDING, STATUS_ACCEPTED, STATUS_CONFIRMED, STATUS_PACKED, STATUS_OUT_FOR_DELIVERY, STATUS_REJECTED, STATUS_COMPLETED, STATUS_CANCELLED]

    id = db.Column(db.Integer, primary_key=True)
    service_id = db.Column(db.Integer, db.ForeignKey("services.id"), nullable=False, index=True)
    customer_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    provider_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    scheduled_at = db.Column(db.DateTime, nullable=False)
    status = db.Column(db.String(20), nullable=False, default=STATUS_PENDING, index=True)
    notes = db.Column(db.Text, nullable=True)
    address = db.Column(db.String(300), nullable=True)
    contact_number = db.Column(db.String(20), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationship
    payment = db.relationship("Payment", backref="booking", uselist=False)

    def to_dict(self, include_details=False):
        data = {
            "id": self.id,
            "service_id": self.service_id,
            "customer_id": self.customer_id,
            "provider_id": self.provider_id,
            "scheduled_at": self.scheduled_at.isoformat() + "Z" if self.scheduled_at else None,
            "status": self.status,
            "notes": self.notes,
            "address": self.address,
            "contact_number": self.contact_number,
            "created_at": self.created_at.isoformat() + "Z" if self.created_at else None,
        }
        if include_details:
            if self.service:
                data["service"] = self.service.to_dict()
            if self.customer:
                data["customer"] = {"id": self.customer.id, "name": self.customer.name}
            if self.provider:
                data["provider"] = {"id": self.provider.id, "name": self.provider.name}
            if self.payment:
                data["payment"] = self.payment.to_dict()
        return data
