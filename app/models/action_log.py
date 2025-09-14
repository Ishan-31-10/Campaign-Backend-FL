from app import db
from datetime import datetime
from sqlalchemy.dialects.postgresql import JSON

class ActionLog(db.Model):
    __tablename__ = "action_logs"
    id = db.Column(db.Integer, primary_key=True)
    campaign_recipient_id = db.Column(db.Integer, db.ForeignKey('campaign_recipients.id'))
    action = db.Column(db.String(50))
    actor_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    actor_role = db.Column(db.String(50))
    reason = db.Column(db.Text, nullable=True)
    hold_until = db.Column(db.DateTime, nullable=True)
    source_name = db.Column(db.String(120), nullable=True)
    meta_data = db.Column("metadata", JSON, default={})

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
