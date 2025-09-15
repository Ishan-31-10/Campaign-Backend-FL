# migrate_script.py
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate, upgrade, migrate

app = Flask(__name__)
app.config.from_object("app.config.Config")  # ya apka config
db = SQLAlchemy(app)
migrate_obj = Migrate(app, db)

# import your models here
from app.models.notification import Notification
from app.models.campaign import Campaign
from app.models.campaign_recipient import CampaignRecipient

with app.app_context():
    # 1️⃣ Generate migration (like flask db migrate)
    migrate(message="Add subject column to notifications")

    # 2️⃣ Apply migration (like flask db upgrade)
    upgrade()
    print("✅ Migration applied successfully!")
