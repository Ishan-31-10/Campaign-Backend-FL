from app import db
from datetime import datetime

class AdminOTP(db.Model):
    __tablename__ = "admin_otps"
    id = db.Column(db.Integer, primary_key=True)
    identifier = db.Column(db.String(255), nullable=False)  # email or phone
    otp_hash = db.Column(db.String(255), nullable=False)
    expires_at = db.Column(db.DateTime, nullable=False)
    used = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
