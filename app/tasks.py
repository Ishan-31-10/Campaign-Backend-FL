from app import celery, create_app, db
from app.models.campaign import Campaign
from datetime import datetime, timezone
from sqlalchemy import and_

app = create_app()

@celery.task
def check_campaign_deadlines():
    with app.app_context():
        now = datetime.now(timezone.utc)
        campaigns = Campaign.query.filter(Campaign.due_at != None).all()
        for c in campaigns:
            if c.due_at and c.due_at <= now:
                # mark pending recipients as expired
                for r in c.recipients:
                    if r.status == 'pending':
                        r.status = 'expired'
                        r.acted_at = datetime.utcnow()
                        db.session.add(r)
                db.session.commit()
