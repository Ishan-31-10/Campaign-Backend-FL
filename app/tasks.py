from celery import Celery
from flask_mail import Message
from datetime import datetime
from app import create_app, db, mail
from app.models.campaign import Campaign

# Flask app + celery init
flask_app = create_app()
celery = Celery(__name__)
celery.conf.update(flask_app.config)

# -----------------------
# ⏰ Campaign deadline check task
# -----------------------
@celery.task
def check_campaign_deadlines():
    with flask_app.app_context():
        now = datetime.utcnow()
        campaigns = Campaign.query.filter(
            Campaign.due_at.isnot(None),
            Campaign.due_at <= now
        ).all()

        for c in campaigns:
            for r in c.recipients:
                if r.status == "pending":
                    r.status = "expired"
                    r.acted_at = now
                    db.session.add(r)

        db.session.commit()
        return f"✅ Checked deadlines at {now}, updated {len(campaigns)} campaigns."


# -----------------------
# 📧 Async email task
# -----------------------
@celery.task
def send_email_task(subject, recipients, body):
    """
    Send email asynchronously using Flask-Mail.
    Args:
        subject (str): Email subject
        recipients (list[str]): List of recipients
        body (str): Email body
    """
    with flask_app.app_context():
        try:
            msg = Message(
                subject=subject,
                recipients=recipients,
                body=body
            )
            mail.send(msg)
            return f"✅ Email sent to {recipients}"
        except Exception as e:
            return f"❌ Email send failed: {str(e)}"
