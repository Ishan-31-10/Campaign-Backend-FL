from app import db
from datetime import datetime
from sqlalchemy.dialects.postgresql import JSON

class Notification(db.Model):
    __tablename__ = "notifications"
    id = db.Column(db.Integer, primary_key=True)
    campaign_recipient_id = db.Column(db.Integer, db.ForeignKey('campaign_recipients.id'))
    payload = db.Column(JSON, default={})
    delivered_at = db.Column(db.DateTime, nullable=True)
    read_at = db.Column(db.DateTime, nullable=True)
    source_name = db.Column(db.String(120), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
