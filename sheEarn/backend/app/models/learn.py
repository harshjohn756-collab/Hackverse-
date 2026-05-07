"""Financial Literacy Content model"""
from datetime import datetime
from app import db


class FinancialContent(db.Model):
    __tablename__ = "financial_content"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(300), nullable=False)
    video_link = db.Column(db.String(500), nullable=True)
    description = db.Column(db.Text, nullable=True)
    thumbnail = db.Column(db.String(500), nullable=True)
    duration_minutes = db.Column(db.Integer, nullable=True)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "title": self.title,
            "video_link": self.video_link,
            "description": self.description,
            "thumbnail": self.thumbnail,
            "duration_minutes": self.duration_minutes,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
