"""Government Schemes model"""
import json
from datetime import datetime
from app import db


class GovernmentScheme(db.Model):
    __tablename__ = "government_schemes"

    CATEGORY_FINANCIAL = "financial_inclusion"
    CATEGORY_ENTREPRENEURSHIP = "entrepreneurship"
    CATEGORY_HEALTH = "health_maternity"
    CATEGORY_SAFETY = "safety_education"

    CATEGORIES = [CATEGORY_FINANCIAL, CATEGORY_ENTREPRENEURSHIP, CATEGORY_HEALTH, CATEGORY_SAFETY]

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(300), nullable=False)
    category = db.Column(db.String(100), nullable=False, index=True)
    eligibility = db.Column(db.Text, nullable=True)
    benefits = db.Column(db.Text, nullable=True)
    _application_steps = db.Column("application_steps", db.Text, nullable=True, default="[]")
    _documents_required = db.Column("documents_required", db.Text, nullable=True, default="[]")
    documents_required_hi = db.Column(db.Text, nullable=True)   # Hindi
    documents_required_kn = db.Column(db.Text, nullable=True)   # Kannada
    eligibility_hi = db.Column(db.Text, nullable=True)
    eligibility_kn = db.Column(db.Text, nullable=True)
    scheme_url = db.Column(db.String(500), nullable=True)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    @property
    def application_steps(self):
        try:
            return json.loads(self._application_steps) if self._application_steps else []
        except (json.JSONDecodeError, TypeError):
            return []

    @application_steps.setter
    def application_steps(self, value):
        if isinstance(value, list):
            self._application_steps = json.dumps(value)
        else:
            self._application_steps = "[]"

    @property
    def documents_required(self):
        try:
            return json.loads(self._documents_required) if self._documents_required else []
        except (json.JSONDecodeError, TypeError):
            return []

    @documents_required.setter
    def documents_required(self, value):
        if isinstance(value, list):
            self._documents_required = json.dumps(value, ensure_ascii=False)
        else:
            self._documents_required = "[]"

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "category": self.category,
            "eligibility": self.eligibility,
            "eligibility_hi": self.eligibility_hi,
            "eligibility_kn": self.eligibility_kn,
            "benefits": self.benefits,
            "application_steps": self.application_steps,
            "documents_required": self.documents_required,
            "documents_required_hi": self.documents_required_hi,
            "documents_required_kn": self.documents_required_kn,
            "scheme_url": self.scheme_url,
            "is_active": self.is_active,
        }
