from flask import Blueprint, request, jsonify, current_app
from app import db
from app.models.user import User
from app.models.admin_otp import AdminOTP
from werkzeug.security import generate_password_hash, check_password_hash
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from datetime import datetime, timedelta
import bcrypt, os, hmac, hashlib
import random

bp = Blueprint("auth", __name__, url_prefix="/api/auth")

# in app/routes/auth.py (replace register and login functions)

@bp.route("/register", methods=["POST"])
def register():
    data = request.json or {}
    email = data.get("email")
    password = data.get("password")
    name = data.get("name")
    roles = data.get("roles", [])  # expect list, e.g. ["sales"] or ["delivery"]
    if not email or not password:
        return jsonify(msg="email and password required"), 400
    if User.query.filter_by(email=email).first():
        return jsonify(msg="user exists"), 400
    pw_hash = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
    user = User(email=email, password_hash=pw_hash, roles=roles, name=name)
    db.session.add(user)
    db.session.commit()
    return jsonify(msg="registered", id=user.id), 201

@bp.route("/login", methods=["POST"])
def login():
    data = request.json or {}
    email = data.get("email")
    password = data.get("password")
    if not email or not password:
        return jsonify(msg="email and password required"), 400
    user = User.query.filter_by(email=email).first()
    if not user or not user.password_hash:
        return jsonify(msg="invalid credentials"), 401
    if not bcrypt.checkpw(password.encode(), user.password_hash.encode()):
        return jsonify(msg="invalid credentials"), 401
    # IMPORTANT: store only user_id (string) as identity — simpler & safer
    access = create_access_token(identity=str(user.id), expires_delta=timedelta(hours=8))
    return jsonify(access_token=access, user={"id": user.id, "email": user.email, "roles": user.roles or []})

# Admin OTP flow
def _hash_otp(otp):
    # simple HMAC with secret for storage
    key = os.getenv("SECRET_KEY", "devsecret").encode()
    return hmac.new(key, otp.encode(), hashlib.sha256).hexdigest()

@bp.route("/admin/request-otp", methods=["POST"])
def admin_request_otp():
    data = request.json or {}
    identifier = data.get("identifier")
    if not identifier:
        return jsonify(msg="identifier required"), 400
    # rate limiting not implemented here; rely on flask-limiter in production
    otp = f"{random.randint(100000,999999)}"
    otp_hash = _hash_otp(otp)
    expires_at = datetime.utcnow() + timedelta(seconds=int(current_app.config.get('OTP_EXPIRY_SECONDS', 600)))
    rec = AdminOTP(identifier=identifier, otp_hash=otp_hash, expires_at=expires_at)
    db.session.add(rec)
    db.session.commit()
    # Send OTP: in dev we print to console (in production hook SMS/email)
    print(f"[DEV OTP for {identifier}]: {otp}")
    return jsonify(msg="otp_sent", expires_at=expires_at.isoformat()), 200

@bp.route("/admin/verify-otp", methods=["POST"])
def admin_verify_otp():
    data = request.json or {}
    identifier = data.get("identifier")
    otp = data.get("otp")
    if not identifier or not otp:
        return jsonify(msg="identifier and otp required"), 400
    rec = AdminOTP.query.filter_by(identifier=identifier, used=False).order_by(AdminOTP.created_at.desc()).first()
    if not rec:
        return jsonify(msg="no pending otp"), 404
    if rec.expires_at < datetime.utcnow():
        return jsonify(msg="otp expired"), 400
    if _hash_otp(otp) != rec.otp_hash:
        return jsonify(msg="invalid otp"), 400
    rec.used = True
    db.session.add(rec)
    # find or create admin user with this identifier (email)
    user = User.query.filter_by(email=identifier).first()
    if not user:
        user = User(email=identifier, roles=['admin'])
        db.session.add(user)
    else:
        roles = user.roles or []
        if 'admin' not in roles:
            roles.append('admin')
            user.roles = roles
    db.session.commit()
    access = create_access_token(identity={"user_id": user.id, "email": user.email, "roles": user.roles}, expires_delta=timedelta(hours=8))
    return jsonify(access_token=access, user={"id": user.id, "email": user.email, "roles": user.roles})

@bp.route('/me', methods=['GET'])
@jwt_required()
def me():
    ident = get_jwt_identity()
    return jsonify(ident)
