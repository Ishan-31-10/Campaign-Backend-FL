# Flask Campaign Backend - Full Ready Scaffold

This repository contains a Flask + SQLAlchemy backend scaffold implementing:
- JWT auth (password login) and Admin OTP flow
- User, Team, Campaign, CampaignRecipient, Notification, ActionLog models
- Campaign creation, sharing, notification actions
- Socket.IO integration (server-side) for real-time events
- Celery tasks (deadline checker)
- Admin CSV export endpoint

## Quick start (development, using docker-compose)

1. Copy `.env.example` to `.env` and edit if needed.

2. Start services:
```bash
docker compose up --build
```

3. Initialize DB and migrations (in another terminal):
```bash
docker compose exec web flask db init
docker compose exec web flask db migrate -m "init"
docker compose exec web flask db upgrade
```

4. Create a user:
```bash
docker compose exec web flask shell -c "from app import db; from app.models.user import User; u=User(email='admin@example.com', roles=['admin']); db.session.add(u); db.session.commit()"
```

5. Request OTP for admin:
```bash
curl -X POST http://localhost:5000/api/auth/admin/request-otp -H "Content-Type: application/json" -d '{"identifier":"admin@example.com"}'
# Check web logs for OTP printed in console, then:
curl -X POST http://localhost:5000/api/auth/admin/verify-otp -H "Content-Type: application/json" -d '{"identifier":"admin@example.com","otp":"123456"}'
```

## Notes & next steps
- OTP sending in dev prints to server logs. Replace with real provider (Twilio, SMTP).
- Expand team sharing logic (current code expects expanded list of user_ids).
- Add more validations, tests, and production configurations (rate limiting, HTTPS, secrets, monitoring).

