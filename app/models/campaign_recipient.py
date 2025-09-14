from app import db
from datetime import datetime
from sqlalchemy.dialects.postgresql import JSON

class CampaignRecipient(db.Model):
    __tablename__ = "campaign_recipients"
    id = db.Column(db.Integer, primary_key=True)
    campaign_id = db.Column(db.Integer, db.ForeignKey('campaigns.id'))
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    team_snapshot = db.Column(JSON, nullable=True)  # snapshot of team at share time
    status = db.Column(db.String(50), default='pending')
    status_meta = db.Column(JSON, default={})
    assigned_role = db.Column(db.String(50), nullable=True)  # sales/delivery/both
    source_name = db.Column(db.String(120), nullable=True)
    acted_at = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    campaign = db.relationship("Campaign", back_populates="recipients")
