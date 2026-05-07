"""Profile model"""
import json
from datetime import datetime
from app import db


class Profile(db.Model):
    __tablename__ = "profiles"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, unique=True)
    location = db.Column(db.String(300), nullable=True)
    latitude = db.Column(db.Float, nullable=True)
    longitude = db.Column(db.Float, nullable=True)
    _skills = db.Column("skills", db.Text, nullable=True, default="[]")
    description = db.Column(db.Text, nullable=True)
    profile_image = db.Column(db.String(500), nullable=True)
    upi_id = db.Column(db.String(100), nullable=True)  # e.g. name@paytm, name@ybl
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    @property
    def skills(self):
        try:
            return json.loads(self._skills) if self._skills else []
        except (json.JSONDecodeError, TypeError):
            return []

    @skills.setter
    def skills(self, value):
        if isinstance(value, list):
            self._skills = json.dumps(value)
        elif isinstance(value, str):
            self._skills = value
        else:
            self._skills = "[]"

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "location": self.location,
            "latitude": self.latitude,
            "longitude": self.longitude,
            "skills": self.skills,
            "description": self.description,
            "profile_image": self.profile_image,
            "upi_id": self.upi_id,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
