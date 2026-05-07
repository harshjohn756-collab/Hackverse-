"""Chat Message model"""
from datetime import datetime
from app import db


class ChatMessage(db.Model):
    __tablename__ = "chat_messages"

    id = db.Column(db.Integer, primary_key=True)
    sender_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    receiver_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    message = db.Column(db.Text, nullable=False)
    is_read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    sender = db.relationship("User", foreign_keys=[sender_id], backref=db.backref("sent_messages", lazy="dynamic"))
    receiver = db.relationship("User", foreign_keys=[receiver_id], backref=db.backref("received_messages", lazy="dynamic"))

    def to_dict(self, include_users=False):
        data = {
            "id": self.id,
            "sender_id": self.sender_id,
            "receiver_id": self.receiver_id,
            "message": self.message,
            "is_read": self.is_read,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
        if include_users:
            if self.sender:
                data["sender"] = {"id": self.sender.id, "name": self.sender.name}
            if self.receiver:
                data["receiver"] = {"id": self.receiver.id, "name": self.receiver.name}
        return data
