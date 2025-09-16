from datetime import datetime
from flask_mail import Message
from app import db, mail, celery

@celery.task(name="app.tasks.check_campaign_deadlines")
def check_campaign_deadlines():
    try:
        from app.models.campaign import Campaign
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
    except Exception as e:
        db.session.rollback()
        print(f"Database transaction failed: {e}")
        raise
    return f"Checked deadlines at {now}, updated {len(campaigns)} campaigns."

@celery.task(name="app.tasks.send_email_task")
def send_email_task(subject, recipients, body):
    try:
        if isinstance(recipients, str):
            recipients = [recipients]
        msg = Message(subject=str(subject), recipients=recipients, body=str(body))
        mail.send(msg)
        return f"Email sent to {recipients}"
    except Exception as e:
        print("send_email_task error:", repr(e))
        return f"Email send failed: {str(e)}"