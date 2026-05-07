"""User model"""
import json
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from app import db


class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(200), unique=True, nullable=True, index=True)
    phone = db.Column(db.String(20), unique=True, nullable=True, index=True)
    username = db.Column(db.String(50), unique=True, nullable=True, index=True)
    password_hash = db.Column(db.String(256), nullable=False)
    role = db.Column(db.String(20), nullable=False, default="customer")  # provider / customer / admin
    language = db.Column(db.String(5), nullable=False, default="kn")  # en / hi / kn
    gender = db.Column(db.String(10), nullable=True, default="female")
    is_active = db.Column(db.Boolean, default=True)
    kyc_status = db.Column(db.String(20), default="pending")  # pending / approved / declined
    kyc_session_id = db.Column(db.String(120), nullable=True)   # Didit session reference
    security_question = db.Column(db.String(255), nullable=True)
    security_answer_hash = db.Column(db.String(256), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    profile = db.relationship("Profile", backref="user", uselist=False, cascade="all, delete-orphan")
    services = db.relationship("Service", backref="provider", lazy="dynamic", foreign_keys="Service.provider_id")
    bookings_as_customer = db.relationship("Booking", backref="customer", lazy="dynamic", foreign_keys="Booking.customer_id")
    bookings_as_provider = db.relationship("Booking", backref="provider", lazy="dynamic", foreign_keys="Booking.provider_id")
    ratings = db.relationship("Rating", backref="reviewer", lazy="dynamic", foreign_keys="Rating.user_id")
    wallet = db.relationship("Wallet", backref="user", uselist=False, cascade="all, delete-orphan")

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def set_security_answer(self, answer):
        self.security_answer_hash = generate_password_hash(answer.lower().strip())

    def check_security_answer(self, answer):
        if not self.security_answer_hash:
            return False
        return check_password_hash(self.security_answer_hash, answer.lower().strip())

    def to_dict(self, include_sensitive=False):
        data = {
            "id": self.id,
            "name": self.name,
            "username": self.username,
            "email": self.email,
            "phone": self.phone,
            "role": self.role,
            "language": self.language,
            "gender": self.gender,
            "kyc_status": self.kyc_status,
            "kyc_session_id": self.kyc_session_id,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
        if include_sensitive:
            data["password_hash"] = self.password_hash
        return data

    def __repr__(self):
        return f"<User {self.name} ({self.role})>"
