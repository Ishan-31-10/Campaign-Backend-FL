from app import db
from datetime import datetime
from sqlalchemy.dialects.postgresql import JSON

class Notification(db.Model):
    __tablename__ = "notifications"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))  # required for send_notification
    campaign_recipient_id = db.Column(db.Integer, db.ForeignKey('campaign_recipients.id'))
    message = db.Column(db.String(255), nullable=False)         # ← add this
    payload = db.Column(JSON, default={})
    delivered_at = db.Column(db.DateTime, nullable=True)
    read_at = db.Column(db.DateTime, nullable=True)
    subject = db.Column(db.String(255), nullable=True)
    source_name = db.Column(db.String(120), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

