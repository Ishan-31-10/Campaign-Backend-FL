import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_jwt_extended import JWTManager
from flask_socketio import SocketIO
from celery import Celery
from dotenv import load_dotenv

load_dotenv()

db = SQLAlchemy()
migrate = Migrate()
jwt = JWTManager()
socketio = SocketIO(cors_allowed_origins='*', async_mode='eventlet')
celery = Celery(__name__)

def make_celery(app):
    celery.conf.update(
        broker_url=app.config.get("CELERY_BROKER_URL") or os.getenv("CELERY_BROKER_URL"),
        result_backend=app.config.get("CELERY_RESULT_BACKEND") or os.getenv("CELERY_RESULT_BACKEND"),
        task_serializer='json',
        accept_content=['json'],
        result_serializer='json',
        timezone='UTC',
        enable_utc=True,
    )
    class ContextTask(celery.Task):
        def __call__(self, *args, **kwargs):
            with app.app_context():
                return self.run(*args, **kwargs)
    celery.Task = ContextTask
    return celery

def create_app():
    app = Flask(__name__, instance_relative_config=False)
    app.config.from_mapping(
        SECRET_KEY=os.getenv("SECRET_KEY", "devsecret"),
        SQLALCHEMY_DATABASE_URI=os.getenv("DATABASE_URL", "sqlite:///data.db"),
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
        JWT_SECRET_KEY=os.getenv("JWT_SECRET_KEY", "jwtsecret"),
        REDIS_URL=os.getenv("REDIS_URL", "redis://localhost:6379/0"),
        CELERY_BROKER_URL=os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/1"),
        CELERY_RESULT_BACKEND=os.getenv("CELERY_RESULT_BACKEND", "redis://localhost:6379/2"),
        OTP_EXPIRY_SECONDS=int(os.getenv("OTP_EXPIRY_SECONDS", "600")),
        OTP_RESEND_LIMIT_PER_HOUR=int(os.getenv("OTP_RESEND_LIMIT_PER_HOUR", "5")),
    )
    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)
    socketio.init_app(app, message_queue=app.config['REDIS_URL'])

    from app.routes.auth import bp as auth_bp
    from app.routes.campaigns import bp as campaigns_bp
    from app.routes.notifications import bp as notifications_bp
    from app.routes.admin import bp as admin_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(campaigns_bp)
    app.register_blueprint(notifications_bp)
    app.register_blueprint(admin_bp)

    # register socket events
    from app.sockets import socket_events
    socket_events.register(socketio)

    # initialize celery
    global celery
    celery = make_celery(app)
    from app import tasks  # noqa

    return app

# expose celery for command-line
from app import celery as celery
