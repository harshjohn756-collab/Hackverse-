"""
WebSocket (SocketIO) real-time chat events.

Events:
  Client → Server:
    join_room   { token }           — authenticate and join personal room
    send_message { receiver_id, message }
    mark_read   { sender_id }

  Server → Client:
    new_message  { message_dict }
    error        { message }
    ack          { message }
"""
from flask import request as flask_request
from flask_socketio import emit, join_room, disconnect
from flask_jwt_extended import decode_token
from jwt.exceptions import ExpiredSignatureError, DecodeError

from app import socketio, db
from app.models.chat import ChatMessage
from app.models.user import User

# Map user_id → socket session id for presence
connected_users: dict[int, str] = {}  # user_id → sid


def _auth_socket(token: str):
    """Decode JWT and return User or None."""
    try:
        data = decode_token(token)
        user_id = int(data["sub"])
        return User.query.get(user_id)
    except (ExpiredSignatureError, DecodeError, KeyError, ValueError):
        return None


@socketio.on("join_room")
def handle_join(data):
    token = data.get("token", "")
    user = _auth_socket(token)
    if not user:
        emit("error", {"message": "Unauthorized"})
        disconnect()
        return

    room = f"user_{user.id}"
    join_room(room)
    connected_users[user.id] = flask_request.sid  # store actual socket session id
    emit("ack", {"message": f"Joined room as {user.name}"})


@socketio.on("send_message")
def handle_send_message(data):
    token = data.get("token", "")
    user = _auth_socket(token)
    if not user:
        emit("error", {"message": "Unauthorized"})
        return

    receiver_id = data.get("receiver_id")
    message_text = (data.get("message") or "").strip()

    if not receiver_id or not message_text:
        emit("error", {"message": "receiver_id and message are required"})
        return

    receiver = User.query.get(receiver_id)
    if not receiver:
        emit("error", {"message": "Recipient not found"})
        return

    msg = ChatMessage(sender_id=user.id, receiver_id=receiver_id, message=message_text)
    db.session.add(msg)
    db.session.commit()

    payload = msg.to_dict(include_users=True)

    # Echo back to sender
    emit("new_message", payload)

    # Push to receiver's room if online
    receiver_room = f"user_{receiver_id}"
    emit("new_message", payload, room=receiver_room)


@socketio.on("mark_read")
def handle_mark_read(data):
    token = data.get("token", "")
    user = _auth_socket(token)
    if not user:
        emit("error", {"message": "Unauthorized"})
        return

    sender_id = data.get("sender_id")
    if not sender_id:
        return

    ChatMessage.query.filter_by(
        sender_id=sender_id, receiver_id=user.id, is_read=False
    ).update({"is_read": True})
    db.session.commit()
    emit("ack", {"message": "Messages marked as read"})


@socketio.on("disconnect")
def handle_disconnect():
    """Remove only the user whose socket disconnected."""
    sid = flask_request.sid
    to_remove = [uid for uid, stored_sid in connected_users.items() if stored_sid == sid]
    for uid in to_remove:
        connected_users.pop(uid, None)
