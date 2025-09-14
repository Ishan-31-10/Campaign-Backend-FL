from flask import Blueprint, request, jsonify, current_app
from app import db, socketio
from app.models.campaign import Campaign
from app.models.campaign_recipient import CampaignRecipient
from app.models.user import User
from datetime import datetime
import json

bp = Blueprint("campaigns", __name__, url_prefix="/api/campaigns")

@bp.route("/", methods=["POST"])
def create_campaign():
    data = request.json or {}
    title = data.get("title")
    if not title:
        return jsonify(msg="title required"), 400
    campaign = Campaign(
        title=title,
        description=data.get("description"),
        assets_link=data.get("assets_link"),
        priority=data.get("priority"),
        created_by=data.get("created_by"),
        due_at=datetime.fromisoformat(data.get("due_at")) if data.get("due_at") else None,
        duration_hours=data.get("duration_hours"),
    )
    db.session.add(campaign)
    db.session.commit()
    return jsonify(msg="created", id=campaign.id), 201

@bp.route("/<int:cid>/share", methods=["POST"])
def share_campaign(cid):
    data = request.json or {}
    campaign = Campaign.query.get_or_404(cid)
    user_ids = data.get("user_ids", [])
    team_user_ids = data.get("team_user_ids", [])  # expanded by frontend or server-side expansion logic
    source_name = data.get("source_name")
    created_recipients = []
    for uid in set(user_ids + team_user_ids):
        user = User.query.get(uid)
        if not user:
            continue
        rec = CampaignRecipient(campaign_id=campaign.id, user_id=user.id, status='pending', assigned_role=data.get('assigned_role'), source_name=source_name)
        db.session.add(rec)
        db.session.flush()
        created_recipients.append({'id': rec.id, 'user_id': user.id})
        # emit socket event to user-specific channel
        socketio.emit('campaign_shared', {'campaign_id': campaign.id, 'recipient_id': rec.id}, room=f'user_{user.id}')
    db.session.commit()
    return jsonify(msg="shared", recipients=created_recipients), 201

@bp.route("/<int:cid>", methods=["GET"])
def get_campaign(cid):
    campaign = Campaign.query.get_or_404(cid)
    recs = []
    for r in campaign.recipients:
        recs.append({
            'id': r.id,
            'user_id': r.user_id,
            'status': r.status,
            'assigned_role': r.assigned_role,
            'source_name': r.source_name,
            'acted_at': r.acted_at.isoformat() if r.acted_at else None
        })
    return jsonify({
        'id': campaign.id,
        'title': campaign.title,
        'description': campaign.description,
        'due_at': campaign.due_at.isoformat() if campaign.due_at else None,
        'recipients': recs
    })
