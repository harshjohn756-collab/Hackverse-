"""Rating model"""
from datetime import datetime
from app import db


class Rating(db.Model):
    __tablename__ = "ratings"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    service_id = db.Column(db.Integer, db.ForeignKey("services.id"), nullable=False, index=True)
    booking_id = db.Column(db.Integer, db.ForeignKey("bookings.id"), nullable=True)
    stars = db.Column(db.Integer, nullable=False)  # 1-5
    comment = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    __table_args__ = (
        db.UniqueConstraint("user_id", "service_id", name="unique_user_service_rating"),
    )

    def to_dict(self, include_reviewer=False):
        data = {
            "id": self.id,
            "user_id": self.user_id,
            "service_id": self.service_id,
            "booking_id": self.booking_id,
            "stars": self.stars,
            "comment": self.comment,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
        if include_reviewer and self.reviewer:
            data["reviewer"] = {"id": self.reviewer.id, "name": self.reviewer.name}
        return data
