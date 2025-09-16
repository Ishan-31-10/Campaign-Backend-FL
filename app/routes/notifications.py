from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app import db, socketio, celery  # 'celery' is now imported here
from app.models.user import User
from app.models.notification import Notification
from app.models.campaign_recipient import CampaignRecipient
from app.models.action_log import ActionLog
from datetime import datetime

notifications_bp = Blueprint("notifications", __name__, url_prefix="/api/notifications")

# helper to get current user object
def current_user():
    ident = get_jwt_identity()
    try:
        uid = int(ident)
    except Exception:
        if isinstance(ident, dict):
            uid = int(ident.get("user_id"))
        else:
            return None
    return User.query.get(uid)

@notifications_bp.route("/", methods=["GET"])
@jwt_required()
def get_notifications():
    user = current_user()
    if not user:
        return jsonify({"error": "invalid token"}), 401
    notes = Notification.query.filter_by(user_id=user.id).order_by(Notification.created_at.desc()).all()
    return jsonify([{
        "id": n.id,
        "message": n.message,
        "subject": n.subject,
        "delivered_at": n.delivered_at.isoformat() if n.delivered_at else None,
        "created_at": n.created_at.isoformat()
    } for n in notes])


@notifications_bp.route("/<int:recipient_id>/action", methods=["POST"])
@jwt_required()
def take_action(recipient_id):
    user = current_user()
    if not user:
        return jsonify({"error": "invalid token"}), 401

    data = request.get_json(force=True)
    action = data.get("action")
    hold_until = data.get("hold_until")
    source_name = data.get("source_name")

    recipient = CampaignRecipient.query.get_or_404(recipient_id)
    if recipient.user_id and recipient.user_id != user.id and 'admin' not in (user.roles or []):
        return jsonify({"error": "forbidden"}), 403

    recipient.status = action
    recipient.acted_at = datetime.utcnow()
    db.session.add(recipient)

    log = ActionLog(
        campaign_recipient_id=recipient.id,
        action=action,
        actor_id=user.id,
        actor_role=",".join(user.roles or []),
        reason=data.get("reason"),
        hold_until=datetime.fromisoformat(hold_until) if hold_until else None,
        source_name=source_name
    )
    db.session.add(log)
    db.session.commit()

    creator = User.query.get(recipient.campaign.created_by)
    socketio.emit("notification", {"message": f"{recipient.user_id} {action} the campaign"}, room=f"user_{creator.id}" if creator else None)

    if creator and creator.email:
        celery.send_email_task.delay(subject=f"Campaign {recipient.campaign.title}", recipients=[creator.email], body=f"Recipient {recipient.user_id} has {action} the campaign.")

    return jsonify({"message": "Action recorded"})


@notifications_bp.route("/send/<int:user_id>", methods=["POST"])
@jwt_required()
def send_notification_to_user(user_id):
    sender = current_user()
    if not sender:
        return jsonify({"error": "invalid token"}), 401

    data = request.get_json(force=True)
    msg = str(data.get("message", ""))
    subject = str(data.get("subject", "New Notification"))

    note = Notification(user_id=user_id, message=msg, subject=subject, delivered_at=datetime.utcnow())
    db.session.add(note)
    db.session.commit()

    socketio.emit("notification", {"message": msg}, room=f"user_{user_id}")

    receiver = User.query.get(user_id)
    if receiver and receiver.email:
        celery.send_email_task.delay(subject=subject, recipients=[receiver.email], body=msg)

    return jsonify({"message": "Notification sent"})


@notifications_bp.route("/send", methods=["POST"])
@jwt_required()
def send_bulk_notification():
    data = request.get_json(force=True)
    subject = str(data.get("subject", "No subject"))
    recipients = data.get("recipients", [])
    body = str(data.get("body", ""))

    if not recipients or not isinstance(recipients, list):
        return jsonify({"error": "Recipients required as list"}), 400

    celery.send_email_task.delay(subject=subject, recipients=recipients, body=body)
    return jsonify({"message": "Email queued"}), 200