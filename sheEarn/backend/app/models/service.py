"""Service model"""
import json
from datetime import datetime
from app import db


class Service(db.Model):
    __tablename__ = "services"

    id = db.Column(db.Integer, primary_key=True)
    provider_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    title = db.Column(db.String(200), nullable=False)
    category = db.Column(db.String(100), nullable=False, index=True)
    price = db.Column(db.Float, nullable=False)
    description = db.Column(db.Text, nullable=True)
    _images = db.Column("images", db.Text, nullable=True, default="[]")
    is_approved = db.Column(db.Boolean, default=False, index=True)
    is_active = db.Column(db.Boolean, default=True)
    avg_rating = db.Column(db.Float, default=0.0)
    rating_count = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    bookings = db.relationship("Booking", backref="service", lazy="dynamic")
    ratings = db.relationship("Rating", backref="service", lazy="dynamic")

    CATEGORIES = ["cooking", "stitching", "tutoring", "handmade_crafts", "beauty", "cleaning", "other"]

    @property
    def images(self):
        try:
            return json.loads(self._images) if self._images else []
        except (json.JSONDecodeError, TypeError):
            return []

    @images.setter
    def images(self, value):
        if isinstance(value, list):
            self._images = json.dumps(value)
        elif isinstance(value, str):
            self._images = value
        else:
            self._images = "[]"

    def recalculate_rating(self):
        from app.models.rating import Rating
        ratings = Rating.query.filter_by(service_id=self.id).all()
        if ratings:
            self.avg_rating = round(sum(r.stars for r in ratings) / len(ratings), 2)
            self.rating_count = len(ratings)
        else:
            self.avg_rating = 0.0
            self.rating_count = 0

    def to_dict(self, include_provider=False):
        data = {
            "id": self.id,
            "provider_id": self.provider_id,
            "title": self.title,
            "category": self.category,
            "price": self.price,
            "description": self.description,
            "images": self.images,
            "is_approved": self.is_approved,
            "is_active": self.is_active,
            "avg_rating": self.avg_rating,
            "rating_count": self.rating_count,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
        if include_provider and self.provider:
            data["provider"] = {
                "id": self.provider.id,
                "name": self.provider.name,
                "profile": self.provider.profile.to_dict() if self.provider.profile else None,
            }
        return data
