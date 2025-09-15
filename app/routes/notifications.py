from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app import db, socketio
from app.models.user import User
from app.models.notification import Notification
from app.models.campaign_recipient import CampaignRecipient
from app.models.action_log import ActionLog
from datetime import datetime

notifications_bp = Blueprint("notifications", __name__)

# 📌 Get user notifications (in-app)
@notifications_bp.route("/", methods=["GET"])
@jwt_required()
def get_notifications():
    ident = get_jwt_identity()
    notes = Notification.query.filter_by(user_id=ident["id"]).all()
    return jsonify([{
        "id": n.id,
        "message": n.message,
        "delivered_at": n.delivered_at,
        "created_at": n.created_at.isoformat()
    } for n in notes])

# 📌 Take action on a campaign
@notifications_bp.route("/<int:recipient_id>/action", methods=["POST"])
@jwt_required()
def take_action(recipient_id):
    from app.tasks import send_email_task
    ident = get_jwt_identity()
    data = request.get_json(force=True)
    action = data.get("action")
    hold_until = data.get("hold_until")
    source_name = data.get("source_name")

    # Update campaign recipient status
    recipient = CampaignRecipient.query.get_or_404(recipient_id)
    recipient.status = action
    recipient.acted_at = datetime.utcnow()
    db.session.add(recipient)

    # Log the action
    log = ActionLog(
        recipient_id=recipient.id,
        action=action,
        actor_id=ident["id"],
        source_name=source_name,
        hold_until=datetime.fromisoformat(hold_until) if hold_until else None
    )
    db.session.add(log)
    db.session.commit()

    # Notify campaign creator via socket (in-app)
    creator = User.query.get(recipient.campaign.creator_id)
    socketio.emit(
        "notification",
        {"message": f"{recipient.user.name} {action} the campaign"},
        room=f"user_{creator.id}"
    )

    # Send email to campaign creator
    if creator:
        send_email_task.delay(
            subject=f"Campaign {recipient.campaign.title}",
            recipients=[creator.email],
            body=f"{recipient.user.name} has {action} the campaign."
        )

    return jsonify({"message": "Action recorded"})

# 📌 Send notification to one user
@notifications_bp.route("/send/<int:user_id>", methods=["POST"])
@jwt_required()
def send_notification_to_user(user_id):
    from app.tasks import send_email_task
    data = request.get_json(force=True)
    msg = str(data.get("message", ""))
    email_subject = str(data.get("subject", "New Notification"))

    # Save in-app notification
    note = Notification(
        user_id=user_id,
        message=msg,
        delivered_at=datetime.utcnow()
    )
    db.session.add(note)
    db.session.commit()

    # Socket notification (in-app)
    socketio.emit("notification", {"message": msg}, room=f"user_{user_id}")

    # Send email
    user = User.query.get(user_id)
    if user:
        send_email_task.delay(
            subject=email_subject,
            recipients=[user.email],
            body=msg
        )

    return jsonify({"message": "Notification sent"})

# 📌 Send bulk email notifications (no in-app)
@notifications_bp.route("/send", methods=["POST"])
@jwt_required()
def send_bulk_notification():
    from app.tasks import send_email_task
    data = request.get_json(force=True)
    subject = str(data.get("subject", "No subject"))
    recipients = data.get("recipients", [])
    body = str(data.get("body", ""))

    if not recipients:
        return jsonify({"error": "Recipients required"}), 400

    # Queue email task
    send_email_task.delay(subject=subject, recipients=recipients, body=body)
    return jsonify({"message": "Email queued"}), 200
