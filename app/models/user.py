from app import db
from datetime import datetime
from sqlalchemy.dialects.postgresql import JSON

class User(db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120))
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128))
    roles = db.Column(JSON, default=[])
    team_id = db.Column(db.Integer, db.ForeignKey('teams.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    team = db.relationship("Team", back_populates="members")
