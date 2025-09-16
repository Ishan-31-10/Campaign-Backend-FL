import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_jwt_extended import JWTManager
from flask_socketio import SocketIO
from celery import Celery
from dotenv import load_dotenv
from flask_mail import Mail

load_dotenv()

db = SQLAlchemy()
migrate = Migrate()
jwt = JWTManager()
socketio = SocketIO(cors_allowed_origins="*", async_mode="eventlet")
mail = Mail()

# Initialize Celery here without passing the app object yet
celery = Celery(
    __name__,
    broker=os.getenv("CELERY_BROKER_URL"),
    backend=os.getenv("CELERY_RESULT_BACKEND"),
)


def make_celery(app):
    """Factory to create a Celery app instance."""
    celery.conf.update(
        broker_url=app.config["CELERY_BROKER_URL"],
        result_backend=app.config["CELERY_RESULT_BACKEND"],
        task_serializer="json",
        accept_content=["json"],
        result_serializer="json",
        timezone="UTC",
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
        CELERY_RESULT_BACKEND=os.getenv(
            "CELERY_RESULT_BACKEND", "redis://localhost:6379/2"
        ),
        MAIL_SERVER=os.getenv("MAIL_SERVER", "smtp.gmail.com"),
        MAIL_PORT=int(os.getenv("MAIL_PORT", 587)),
        MAIL_USE_TLS=True,
        MAIL_USERNAME=os.getenv("MAIL_USERNAME"),
        MAIL_PASSWORD=os.getenv("MAIL_PASSWORD"),
        MAIL_DEFAULT_SENDER=os.getenv(
            "MAIL_DEFAULT_SENDER", os.getenv("MAIL_USERNAME")
        ),
    )
      
    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)
    mail.init_app(app)
    socketio.init_app(app, message_queue=app.config["REDIS_URL"])

    # register blueprints
    from app.routes.auth import bp as auth_bp
    from app.routes.campaigns import bp as campaigns_bp
    from app.routes.admin import bp as admin_bp
    from app.routes.notifications import notifications_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(campaigns_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(notifications_bp, url_prefix="/api/notifications")

    # register socket events
    from app.sockets import socket_events
    socket_events.register(socketio)

    # setup celery
    global celery
    celery = make_celery(app)
    
    # This is the correct place for autodiscover
    celery.autodiscover_tasks(['app.tasks'])

    return app