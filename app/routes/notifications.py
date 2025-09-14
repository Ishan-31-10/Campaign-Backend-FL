from flask import Blueprint, request, jsonify
from app import db, socketio
from app.models.notification import Notification
from app.models.campaign_recipient import CampaignRecipient
from app.models.action_log import ActionLog
from datetime import datetime
from flask_jwt_extended import jwt_required, get_jwt_identity

bp = Blueprint('notifications', __name__, url_prefix='/api/notifications')

@bp.route('/', methods=['GET'])
@jwt_required()
def list_notifications():
    ident = get_jwt_identity()
    user_id = ident.get('user_id')
    # naive pagination
    page = int(request.args.get('page', 1))
    per = int(request.args.get('per', 20))
    q = Notification.query.join(CampaignRecipient, Notification.campaign_recipient_id==CampaignRecipient.id).filter(CampaignRecipient.user_id==user_id)
    total = q.count()
    items = q.order_by(Notification.created_at.desc()).offset((page-1)*per).limit(per).all()
    out = []
    for n in items:
        out.append({'id': n.id, 'campaign_recipient_id': n.campaign_recipient_id, 'payload': n.payload, 'delivered_at': n.delivered_at.isoformat() if n.delivered_at else None})
    return jsonify(total=total, items=out)

@bp.route('/<int:notification_id>/action', methods=['POST'])
@jwt_required()
def action_notification(notification_id):
    ident = get_jwt_identity()
    user_id = ident.get('user_id')
    data = request.json or {}
    action = data.get('action')
    reason = data.get('reason')
    hold_until = data.get('hold_until')
    source_name = data.get('source_name')
    notif = Notification.query.get_or_404(notification_id)
    rec = CampaignRecipient.query.get_or_404(notif.campaign_recipient_id)
    # simple permission check
    if rec.user_id != user_id:
        return jsonify(msg='forbidden'), 403
    # update recipient status
    rec.status = action
    rec.acted_at = datetime.utcnow()
    db.session.add(rec)
    # write action log
    log = ActionLog(campaign_recipient_id=rec.id, action=action, actor_id=user_id, actor_role=ident.get('roles',[]), reason=reason, source_name=source_name)
    db.session.add(log)
    db.session.commit()
    # emit socket to campaign creator / sales
    socketio.emit('notification_action', {'campaign_recipient_id': rec.id, 'action': action}, room=f'user_{rec.campaign.created_by}')
    return jsonify(msg='ok')

