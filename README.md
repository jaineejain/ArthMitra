# ArthMitra — AI Finance Mentor

## Quick Start (5 minutes)

### Prerequisites
- Python 3.11+, Node 18+, PostgreSQL 15

### Backend
cd arthmitra/backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
# Add your GROQ_API_KEY to .env

# Create database + tables
createdb arthmitra
psql arthmitra < schema.sql

uvicorn main:app --reload --port 8000

### Frontend
cd arthmitra/frontend
npm install
cp .env.example .env
npm run dev

### Seed demo data
cd arthmitra/backend && python seed_demo.py

### Verify running
- Backend Swagger: http://localhost:8000/docs
- Frontend: http://localhost:5173

### AI Money Mentor Pro (v2)
- Premium chat UI: http://localhost:5173/mentor
- Structured advisor API: `POST /api/v2/mentor/chat` (JSON: safe / balanced / growth + risks + steps)
- Health: `GET /api/v2/mentor/health` — also `GET /api/health` lists service surfaces
- SIP illustration: `POST /api/v2/mentor/simulate/wealth` `{ "monthly_sip_rupees": 10000, "years": 10, "annual_return": 0.12 }`
- WebSocket (single-shot JSON reply): connect to `ws://localhost:8000/api/v2/mentor/ws` and send JSON `{ "user_id", "message", "history" }`

