from app import db
from datetime import datetime
from sqlalchemy.dialects.postgresql import JSON

class Campaign(db.Model):
    __tablename__ = "campaigns"
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text)
    assets_link = db.Column(db.String(1024))
    priority = db.Column(db.String(50))
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    due_at = db.Column(db.DateTime, nullable=True)
    duration_hours = db.Column(db.Integer, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    recipients = db.relationship("CampaignRecipient", back_populates="campaign")
