"""Chat REST routes — message history and unread counts"""
from flask import Blueprint, request
from flask_jwt_extended import jwt_required
from sqlalchemy import or_, and_

from app import db
from app.models.chat import ChatMessage
from app.models.user import User
from app.utils.auth import get_current_user
from app.utils.responses import success, error

chat_bp = Blueprint("chat", __name__)


@chat_bp.route("/conversations", methods=["GET"])
@jwt_required()
def list_conversations():
    """Return a list of users the current user has chatted with."""
    user = get_current_user()
    uid = user.id

    subq = db.session.query(
        db.func.max(ChatMessage.id).label("last_msg_id")
    ).filter(
        or_(ChatMessage.sender_id == uid, ChatMessage.receiver_id == uid)
    ).group_by(
        db.case(
            (ChatMessage.sender_id == uid, ChatMessage.receiver_id),
            else_=ChatMessage.sender_id,
        )
    ).subquery()

    messages = ChatMessage.query.join(subq, ChatMessage.id == subq.c.last_msg_id).all()

    convs = []
    for msg in messages:
        other_id = msg.receiver_id if msg.sender_id == uid else msg.sender_id
        other = db.session.get(User, other_id)
        if not other:          # skip conversations with deleted users
            continue
        unread = ChatMessage.query.filter_by(sender_id=other_id, receiver_id=uid, is_read=False).count()
        convs.append({
            "user": {"id": other.id, "name": other.name, "profile_image": other.profile.profile_image if other.profile else None},
            "last_message": msg.to_dict(),
            "unread_count": unread,
        })
    convs.sort(key=lambda x: x["last_message"]["created_at"], reverse=True)
    return success(convs)


@chat_bp.route("/messages/<int:other_user_id>", methods=["GET"])
@jwt_required()
def get_messages(other_user_id):
    """Fetch conversation history between current user and another user."""
    user = get_current_user()
    uid = user.id
    page = request.args.get("page", 1, type=int)
    per_page = 30

    query = ChatMessage.query.filter(
        or_(
            and_(ChatMessage.sender_id == uid, ChatMessage.receiver_id == other_user_id),
            and_(ChatMessage.sender_id == other_user_id, ChatMessage.receiver_id == uid),
        )
    ).order_by(ChatMessage.created_at.desc())

    pagination = query.paginate(page=page, per_page=per_page, error_out=False)

    # Mark received messages as read
    ChatMessage.query.filter_by(sender_id=other_user_id, receiver_id=uid, is_read=False).update({"is_read": True})
    db.session.commit()

    messages = list(reversed(pagination.items))
    return success({
        "messages": [m.to_dict(include_users=True) for m in messages],
        "has_more": pagination.has_next,
        "page": page,
    })


@chat_bp.route("/send", methods=["POST"])
@jwt_required()
def send_message():
    """Send a chat message via REST (fallback when WebSocket unavailable)."""
    user = get_current_user()
    data = request.get_json(silent=True) or {}
    receiver_id = data.get("receiver_id")
    message = (data.get("message") or "").strip()

    if not receiver_id or not message:
        return error("receiver_id and message are required")

    receiver = User.query.get(receiver_id)
    if not receiver:
        return error("Recipient not found", 404)

    msg = ChatMessage(sender_id=user.id, receiver_id=receiver_id, message=message)
    db.session.add(msg)
    db.session.commit()
    return success(msg.to_dict(include_users=True), "Message sent", 201)


@chat_bp.route("/unread-count", methods=["GET"])
@jwt_required()
def unread_count():
    user = get_current_user()
    count = ChatMessage.query.filter_by(receiver_id=user.id, is_read=False).count()
    return success({"unread_count": count})


@chat_bp.route("/messages/<int:msg_id>", methods=["DELETE"])
@jwt_required()
def delete_message(msg_id):
    """Delete a chat message. Only sender can delete their own message."""
    user = get_current_user()
    msg = ChatMessage.query.get_or_404(msg_id)
    
    if msg.sender_id != user.id and user.role != "admin":
        return error("Only the sender can delete this message", 403)
        
    db.session.delete(msg)
    db.session.commit()
    return success(message="Message deleted successfully")


@chat_bp.route("/search-users", methods=["GET"])
@jwt_required()
def search_users():
    """Search users to start a chat."""
    q = request.args.get("q", "").strip()
    if not q or len(q) < 2:
        return success([])
        
    users = User.query.filter(
        User.is_active == True,
        or_(
            User.name.ilike(f"%{q}%"),
            User.email.ilike(f"%{q}%"),
            User.phone.ilike(f"%{q}%"),
            User.username.ilike(f"%{q}%")
        )
    ).limit(10).all()
    
    return success([
        {
            "id": u.id,
            "name": u.name,
            "username": u.username,
            "role": u.role,
            "profile_image": u.profile.profile_image if u.profile else None
        } for u in users
    ])
