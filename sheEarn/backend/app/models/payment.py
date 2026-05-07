"""Payment and Wallet models"""
import uuid
from datetime import datetime
from app import db


class Payment(db.Model):
    __tablename__ = "payments"

    STATUS_PENDING = "pending"
    STATUS_SUCCESS = "success"
    STATUS_FAILED = "failed"
    STATUS_REFUNDED = "refunded"

    METHOD_UPI = "upi"
    METHOD_CARD = "card"
    METHOD_WALLET = "wallet"

    id = db.Column(db.Integer, primary_key=True)
    booking_id = db.Column(db.Integer, db.ForeignKey("bookings.id"), nullable=False, unique=True)
    transaction_id = db.Column(db.String(100), unique=True, nullable=False, default=lambda: f"TXN{uuid.uuid4().hex[:12].upper()}")
    amount = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(20), nullable=False, default=STATUS_PENDING)
    payment_method = db.Column(db.String(20), nullable=True, default=METHOD_UPI)
    upi_id = db.Column(db.String(200), nullable=True)
    provider_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    customer_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "booking_id": self.booking_id,
            "transaction_id": self.transaction_id,
            "amount": self.amount,
            "status": self.status,
            "payment_method": self.payment_method,
            "upi_id": self.upi_id,
            "provider_id": self.provider_id,
            "customer_id": self.customer_id,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class Wallet(db.Model):
    __tablename__ = "wallets"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, unique=True)
    balance = db.Column(db.Float, nullable=False, default=0.0)
    total_earned = db.Column(db.Float, nullable=False, default=0.0)
    total_spent = db.Column(db.Float, nullable=False, default=0.0)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def credit(self, amount):
        self.balance += amount
        self.total_earned += amount

    def debit(self, amount):
        if self.balance < amount:
            return False
        self.balance -= amount
        self.total_spent += amount
        return True

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "balance": round(self.balance, 2),
            "total_earned": round(self.total_earned, 2),
            "total_spent": round(self.total_spent, 2),
        }
