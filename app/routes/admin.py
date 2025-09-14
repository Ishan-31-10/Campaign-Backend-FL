from flask import Blueprint, request, jsonify, Response, current_app
from app import db
from app.models.action_log import ActionLog
import csv
from io import StringIO
from flask_jwt_extended import jwt_required, get_jwt_identity

bp = Blueprint('admin', __name__, url_prefix='/api/admin')

def admin_required():
    ident = get_jwt_identity()
    roles = ident.get('roles', []) if ident else []
    return 'admin' in roles

@bp.route('/exports', methods=['GET'])
@jwt_required()
def exports():
    if not admin_required():
        return jsonify(msg='forbidden'), 403
    # simple export of action logs
    q = ActionLog.query.order_by(ActionLog.created_at.desc()).limit(1000)
    si = StringIO()
    cw = csv.writer(si)
    cw.writerow(['id','campaign_recipient_id','action','actor_id','actor_role','reason','source_name','created_at'])
    for r in q:
        cw.writerow([r.id, r.campaign_recipient_id, r.action, r.actor_id, r.actor_role, r.reason, r.source_name, r.created_at.isoformat()])
    output = si.getvalue()
    return Response(output, mimetype='text/csv', headers={'Content-Disposition':'attachment;filename=action_logs.csv'})
