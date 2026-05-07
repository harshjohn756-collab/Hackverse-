"""Translation model for multilingual support"""
from datetime import datetime
from app import db


class Translation(db.Model):
    __tablename__ = "translations"

    LANGUAGES = ["en", "hi", "kn"]

    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(200), nullable=False, index=True)
    language = db.Column(db.String(5), nullable=False, index=True)
    text = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    __table_args__ = (
        db.UniqueConstraint("key", "language", name="unique_key_language"),
    )

    def to_dict(self):
        return {
            "id": self.id,
            "key": self.key,
            "language": self.language,
            "text": self.text,
        }
