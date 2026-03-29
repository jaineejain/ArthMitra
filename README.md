<div align="center">

# 🪙 ArthMitra
**Your AI-Powered Personal Finance Mentor — Built for Bharat**

*"Arth" (अर्थ) = Money & Meaning — "Mitra" (मित्र) = Friend & Guide*

[![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=flat-square&logo=python&logoColor=white)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-latest-009688?style=flat-square&logo=fastapi)](https://fastapi.tiangolo.com)
[![React](https://img.shields.io/badge/React-18-61DAFB?style=flat-square&logo=react&logoColor=black)](https://react.dev)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15-336791?style=flat-square&logo=postgresql&logoColor=white)](https://postgresql.org)
[![Groq](https://img.shields.io/badge/Groq%20LLM-Powered-F55036?style=flat-square)](https://groq.com)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow?style=flat-square)](LICENSE)

</div>

---

## The Problem We're Solving

Only about 3% of Indians invest in mutual funds. In the US, that number is over 55%.

It's not because Indians don't want to invest — it's because real financial guidance has always been expensive and inaccessible. A Certified Financial Planner charges anywhere from ₹2,000 to ₹10,000 per session. Most working Indians never get that conversation.

The result? SIPs go unstarted. Tax savings get missed. Term insurance remains a mystery. Emergency funds don't exist. Financial anxiety quietly compounds alongside debt.

ArthMitra fixes this. It puts a structured, intelligent financial advisor in your pocket — one that speaks Hinglish, understands Indian tax law, and never judges you for asking "dumb" questions.

---

## What ArthMitra Actually Does

ArthMitra is a full-stack AI finance platform. It's not a chatbot that wraps a language model with a finance prompt — it has real calculation engines, real financial logic, and a proper backend built around Indian-specific rules.

Here is every feature currently in the codebase:

---

### 💬 AI Money Mentor Pro (v2)

The core of the product. A premium chat interface at `/mentor` that connects to Groq LLM through a multi-layer intelligence pipeline.

Every message goes through:

1. **Language auto-detection** — recognizes Hindi, Hinglish, Marathi, Gujarati from Devanagari Unicode ranges and vocabulary patterns. Responds in the same language the user typed in.
2. **Domain detection** — scans for 30+ finance-specific keywords (SIP, ELSS, 80C, ITR, LTCG, XIRR, FOIR, ₹) and routes accordingly.
3. **RAG retrieval** — pulls the most relevant snippets from a local financial knowledge base before every LLM call, scored by token overlap.
4. **Structured JSON response** — the LLM is forced to return a fixed schema every time: `answer`, `key_numbers`, `analysis`, `modes` (safe / balanced / growth), `action_steps`, `alternative_options`, `assumptions`, `pro_tip`, `risk_notes`. No freeform walls of text.
5. **Professional CA mode** — a toggle that switches to formal English output styled like a Chartered Accountant's advice note, with bullet-point sections and precise terminology.
6. **Expert / beginner toggle** — adjusts depth and jargon level per user preference.
7. **Planner section routing** — routes queries to specialized sub-prompts: `tax`, `investment`, `couple_family`, `debt_loan`, `general_finance`.
8. **In-process memory** — stores last topic, domain, and language per user for session continuity (designed for Redis upgrade in production).

The frontend renders the structured JSON as visual cards — not raw text — with separate sections for the summary, key numbers, action steps, and risk notes.

---

### 📊 Money Health Score (MHS)

A weighted composite score across 6 financial dimensions, each calculated with real formulas:

| Dimension | What It Measures | Weight |
|-----------|-----------------|--------|
| **Emergency** | Months of expenses + EMI covered by liquid fund (target: 6 months) | 20% |
| **Insurance** | Term cover ratio (15× annual income) + health cover adequacy + PA | 25% |
| **Debt** | FOIR (Fixed Obligation to Income Ratio) with credit card penalty | 15% |
| **Investment** | Equity % deviation from the 100-minus-age rule | 20% |
| **Tax** | 80C utilization, NPS, HRA, and regime selection | 10% |
| **Retirement** | Projected corpus vs FIRE target (25× annual expenses) | 10% |

Score bands: **Critical** (<50), **Poor** (50–69), **Fair** (70–84), **Good** (85+). The dashboard shows a circular ring chart and horizontal bars for each dimension.

---

### 🔥 FIRE Planner

Calculates your Financial Independence, Retire Early target using proper compounding math:

- Inflation-adjusted future corpus at **6.5% annual inflation**
- Conservative **Safe Withdrawal Rate of 3.5%** (India-appropriate, accounts for longer retirement horizon)
- SIP gap calculator — how much more per month you need to hit the target
- **5-year milestone chart** — projects both your current trajectory and required trajectory at years 5, 10, 15, 20, 25
- Checks whether the required SIP is actually achievable given income − expenses − EMI
- Returns `achievable: true/false` flag the UI uses to color the result

---

### 🧾 Tax Optimizer

Compares Old vs New regime using actual FY2024-25 slabs:

**New regime:** 0% up to ₹3L → 5% (₹3–7L) → 10% (₹7–10L) → 15% (₹10–12L) → 20% (₹12–15L) → 30% (₹15L+)

**Old regime:** 0% up to ₹2.5L → 5% (₹2.5–5L) → 20% (₹5–10L) → 30% (₹10L+)

Both include 4% cess. Also calculates:

- **HRA exemption** — min of: HRA received, rent paid minus 10% of basic, 50/40% of basic for metro/non-metro cities
- **Missed deductions** — NPS 80CCD(1B) gap, 80C gap, health insurance 80D for parents — each with ₹ saving estimate
- Recommends the better regime with exact annual ₹ savings
- **Form 16 PDF upload** — parses the PDF using `pdfplumber`, extracts gross salary, basic salary, and HRA, then pre-fills the entire tax form automatically

---

### 📈 SIP Wealth Simulator

Future value of a monthly SIP using standard compound interest:

```
FV = P × [((1 + r/12)^n − 1) / (r/12)]
```

Inputs: monthly SIP amount, duration in years, expected annual return. Returns future value with a clear disclaimer. Triggered automatically in the Mentor chat when the user types something like "invest ₹10,000 monthly for 10 years."

---

### 💑 Couple's Financial Optimizer

One of the more unusual features — genuinely optimizes tax decisions across two partners:

- Calculates each partner's tax individually under their optimal regime
- Determines **which partner should claim HRA** based on marginal tax rate — the higher-slab earner claims it for maximum exemption
- **Splits 80C / SIP allocation** inversely proportional to income — lower earner gets more 80C to maximize slab efficiency
- Handles cases where caps clip the allocation and redistributes the remainder by remaining headroom
- Returns annual combined tax saving from the optimized arrangement

---

### 📉 Loan Analyzer

Reducing-balance EMI calculator with prepayment analysis:

- Standard reducing-balance EMI formula with monthly compounding
- Total interest remaining over the loan tenure
- Prepayment penalty cost calculation
- Net saving from prepaying today (interest saved minus penalty)

---

### 📂 MF Portfolio X-Ray

Analyzes a mutual fund portfolio across:

- Fund type distribution — equity, debt, hybrid, ELSS, liquid, gold, international
- Overlap detection
- **XIRR calculation using Brent's numerical method** (`scipy.optimize.brentq`) for accurate annualized return across irregular investment and redemption cash flows
- Supports **CAMS / KFintech PDF statement upload** — `pdfplumber` extracts fund names, amounts, and dates directly from the PDF

---

### 🧮 Karma Score (0–1000)

A behavioral finance score, separate from MHS, that measures financial habits rather than current state:

| Dimension | What It Measures |
|-----------|-----------------|
| **Discipline** (25%) | Whether a SIP is active and whether it exceeds 20% of income |
| **Growth** (20%) | SIP-to-income ratio, scaled to 100 |
| **Protection** (20%) | Insurance dimension score from MHS |
| **Family Safety** (20%) | Term cover as percentage of 15× annual income |
| **Debt Health** (15%) | Debt dimension score from MHS |

Score is on 0–1000. Returns a percentile band: **Top 1% / 5% / 10% / 20% / 30%**. Shows as a floating card widget in the bottom-right of the dashboard.

---

### 🚨 Financial Watchdog

Proactive alert system with severity levels (currently demo-mode, wired for cron/scheduler integration):

- **Tax-saving window** alert — Feb–Mar, 80C gap check with action prompt
- **SIP mandate bounce** reminder — pre-debit day verification prompt
- Each alert carries a `severity` flag and an `action_prompt` string that pre-fills the Mentor chat with the right question

---

### 🧭 Onboarding Chat

A structured conversational onboarding flow using the full **Arth Protocol** — the AI collects your financial profile over a conversation before building your initial MHS and FIRE plan. The protocol defines a 7-level depth model:

1. Profile: income, expenses, EMI, savings
2. Debt: rate, tenure, type, prepayment situation
3. Protection: health + term insurance, nominees
4. Investments: MF, FD, PPF, NPS, stocks, gold
5. Tax: regime, 80C, HRA, home loan
6. Goals: retirement age, education, house, FIRE target
7. Behaviour: savings habit, credit card discipline

Hard rules in the protocol: won't finalize SIP advice before confirming emergency fund exists. Won't compare tax regimes without collecting both income and deduction data. Will never use flat-rate interest for a loan.

---

### 🗣️ Feature-Specific Chat Modules

Six dedicated modules, each with a tailored opening message and calculation context:

| Module | Opens With | Calculates |
|--------|-----------|------------|
| **FIRE** | Age + target retirement age | Corpus, SIP gap, milestone chart |
| **Tax** | Annual gross CTC | Regime comparison, HRA, deductions |
| **Life Event** | Which event (bonus/job/marriage/baby/house) | Impact analysis and action plan |
| **MF X-Ray** | Upload CAMS statement or use demo portfolio | Type split, XIRR, overlap |
| **Couple** | Both partners' income | Joint HRA + 80C optimization |
| **MHS** | Monthly income | Full 6-dimension health score |

All modules persist conversation history in PostgreSQL and reload on revisit.

---

### 🔐 Auth System

Full JWT-based authentication:

- Signup and login with bcrypt password hashing
- Email validation, password strength enforcement (8+ chars, must include letters and numbers)
- Token-based password reset with 15-minute TTL, SHA-256 hashed reset tokens stored in memory (database-ready)
- All protected routes use `Authorization: Bearer` header
- `ProtectedRoute` component on the frontend redirects unauthenticated users before any page renders

---

## Architecture

```
Browser (React 18 + Vite)
│
├── /login  /signup              → Auth pages
├── /onboarding                  → Conversational financial profile builder
├── /dashboard                   → MHS ring, dimension bars, karma widget, feature grid
├── /chat/fire                   → FIRE planner chat
├── /chat/tax                    → Tax optimizer chat
├── /chat/life_event             → Life event advisor chat
├── /chat/mf_xray                → MF portfolio X-Ray chat
├── /chat/couple                 → Couple financial optimizer chat
├── /chat/mhs                    → Money health score chat
└── /mentor                      → AI Money Mentor Pro
          │
          │  HTTP REST + WebSocket (?token= JWT auth)
          ▼
FastAPI Backend (Python 3.11)
│
├── Auth         /api/auth/*           signup, login, forgot-password, reset-password
├── Users        /api/users/*          profile CRUD, financial profile save/load
├── Feature Chat /api/chat/*           module-scoped chats with DB persistence
├── File Upload  /api/upload/form16    Form 16 PDF → pdfplumber → pre-filled tax data
│                /api/upload/cams      CAMS PDF → portfolio extraction + XIRR
├── Finance API  /api/finance/mhs      Money Health Score (6 dimensions)
│                /api/finance/tax      Tax old vs new + HRA + missed deductions
│                /api/finance/fire     FIRE corpus + SIP gap + milestone chart
│                /api/finance/portfolio MF type split + XIRR
│                /api/finance/couple   Joint tax + HRA + 80C optimization
│                /api/finance/life-event Life event impact analysis
│                /api/finance/what-if  What-if parameter simulation
│                /api/finance/risk-alerts Personalized risk alerts
├── Mentor v2    /api/v2/mentor/chat   LLM + RAG + domain detect + language detect
│                /api/v2/mentor/simulate/wealth SIP future value
│                /api/v2/mentor/watchdog/alerts Proactive alerts
│                WS /api/v2/mentor/ws  WebSocket real-time chat
└── Health       /api/health           Service surfaces status
          │
          ├── Groq LLM Service      (structured JSON responses via LLaMA 3)
          ├── RAG Service           (token-overlap retrieval from knowledge_base.json)
          ├── Finance Engine        (MHS, FIRE, Tax, Loan, XIRR, Couple, Karma — scipy)
          ├── PDF Parser            (pdfplumber: Form 16 + CAMS statement extraction)
          ├── Orchestrator Agent    (routes to mentor engine with full context)
          ├── Domain Detector       (regex: 30+ India finance keyword patterns)
          └── Language Detector     (Unicode range + Hinglish/Marathi/Gujarati hints)
          │
          ▼
PostgreSQL 15  (users, financial_profiles, chats, messages)
SQLite         (arthmitra.db — zero-config local dev fallback)
```

---

## Tech Stack

| Layer | Technology | Purpose |
|-------|-----------|---------|
| Frontend framework | React 18 + Vite | Fast HMR, component-based UI |
| Animations | Framer Motion | Chat transitions, card reveals |
| Charts | Recharts | FIRE milestone charts, score visualization |
| Styling | Tailwind CSS 3 | Utility-first, dark mode |
| HTTP client | Axios | API calls |
| Routing | React Router v6 | Protected routes, feature navigation |
| Notifications | react-hot-toast | In-app feedback toasts |
| Backend framework | FastAPI | Async Python, auto-Swagger, WebSocket |
| LLM | Groq (LLaMA 3) | Ultra-fast inference, structured JSON |
| Auth | python-jose + bcrypt | JWT tokens, secure hashing |
| PDF parsing | pdfplumber | Form 16 + CAMS statement extraction |
| Numerical math | scipy (Brent's method) | XIRR for irregular cashflows |
| ORM | SQLAlchemy | DB models and queries |
| Migrations | Alembic | Schema version management |
| Database (prod) | PostgreSQL 15 | Persistent relational storage |
| Database (dev) | SQLite | Zero-config local fallback |

---

## Getting Started

### Prerequisites

- Python 3.11+
- Node.js 18+
- PostgreSQL 15+ (optional — SQLite works locally without any setup)
- Free Groq API key from [console.groq.com](https://console.groq.com)

---

### Step 1 — Clone

```bash
git clone https://github.com/jaineejain/ArthMitra.git
cd ArthMitra
```

---

### Step 2 — Backend

```bash
cd arthmitra/backend

# Create and activate virtual environment
python -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate

# Install all dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
```

Edit `.env`:
```env
GROQ_API_KEY=your_groq_key_here
DATABASE_URL=postgresql://user:password@localhost:5432/arthmitra
# Remove DATABASE_URL entirely to fall back to SQLite automatically
```

```bash
# Set up PostgreSQL (skip if using SQLite)
createdb arthmitra
psql arthmitra < schema.sql
psql arthmitra < schema_extensions.sql

# Start backend
uvicorn main:app --reload --port 8000
```

✅ Backend: `http://localhost:8000`
✅ Swagger docs: `http://localhost:8000/docs`

---

### Step 3 — Frontend

```bash
cd arthmitra/frontend

npm install

# Environment is pre-configured in .env.development
# VITE_API_URL=http://localhost:8000

npm run dev
```

✅ Frontend: `http://localhost:5173`

---

### Step 4 — Seed demo data

```bash
cd arthmitra/backend
python seed_demo.py
```

Creates sample users and financial profiles so every screen has real data to show during a demo.

---

### Step 5 — Verify

| URL | Expected |
|-----|---------|
| `http://localhost:5173` | Login / Signup |
| `http://localhost:5173/dashboard` | MHS ring, feature grid, karma widget |
| `http://localhost:5173/mentor` | AI Mentor chat |
| `http://localhost:8000/docs` | Interactive Swagger explorer |
| `http://localhost:8000/api/health` | `{"status":"ok","services":[...]}` |
| `http://localhost:8000/api/v2/mentor/health` | `{"status":"ok","version":"2.1"}` |

---

## Screenshots

> Screenshots will be added post-deployment. Here's what each screen contains:

| Screen | What's there |
|--------|-------------|
| **Dashboard** | MHS circular ring chart, 6 dimension bars with color bands, Karma score floating widget (bottom-right), 6 feature cards linking to each chat |
| **Mentor Chat** | Sidebar with session history, structured response cards (answer / key numbers / action steps / risk notes), language selector, flow selector (Tax / FIRE / Invest / Couple / Debt), notification bell |
| **FIRE Planner** | Recharts milestone chart (current vs required trajectory), corpus target, SIP gap, achievability indicator |
| **Tax Wizard** | Old vs new regime comparison table, HRA breakdown, missed deductions with individual ₹ saving estimates, Form 16 upload button |
| **Onboarding** | Chat interface, step-by-step profile builder, typing indicator |
| **MF X-Ray** | Portfolio type distribution, XIRR result, CAMS PDF upload, overlap warnings |

---

## Demo Video

> 🎬 Link will be added after recording.

The demo covers: signup → onboarding chat → dashboard → FIRE planner chat → tax optimizer with Form 16 upload → AI Mentor with Hinglish input → SIP simulation → watchdog alerts.

---

## Running Tests

```bash
# Backend test suite
cd arthmitra/backend
python -m pytest tests/test_finance_api.py -v

# Standalone test file at repo root
cd ArthMitra
python test_finance_api.py
```

---

## Project Structure

```
ArthMitra/
├── arthmitra/
│   ├── backend/
│   │   ├── agents/
│   │   │   ├── orchestrator.py          # Routes requests to mentor engine with full context
│   │   │   ├── domain_detector.py       # Finance vs general intent (30+ regex patterns)
│   │   │   └── language_detect.py       # Hindi/Hinglish/Gujarati/Marathi from Unicode + vocab
│   │   ├── core/
│   │   │   ├── calculator.py            # High-level wrapper around finance_engine
│   │   │   ├── security.py              # JWT creation/decode, bcrypt hashing
│   │   │   ├── deps.py                  # FastAPI dependency injection (current user)
│   │   │   └── validator.py             # Input sanitization for financial profiles
│   │   ├── data/
│   │   │   └── knowledge_base.json      # Local RAG snippets (token-overlap retrieval)
│   │   ├── database/
│   │   │   ├── models.py                # SQLAlchemy: User, Chat, Message, FinancialProfile
│   │   │   └── session.py               # DB session factory (PostgreSQL + SQLite fallback)
│   │   ├── routers/
│   │   │   ├── auth.py                  # Signup, login, forgot/reset password
│   │   │   ├── chat.py                  # Module-scoped feature chats with DB persistence
│   │   │   ├── finance.py               # Direct calculation API endpoints
│   │   │   ├── mentor.py                # v2 mentor: REST + WebSocket + SIP sim + watchdog
│   │   │   ├── upload.py                # Form 16 + CAMS PDF upload and parsing
│   │   │   ├── users.py                 # User profile CRUD
│   │   │   ├── goals.py                 # Goals endpoint (stub, wired)
│   │   │   ├── sapna.py                 # Sapna score endpoint
│   │   │   ├── bharat_score.py          # Bharat score endpoint
│   │   │   └── feed.py                  # Financial news feed (stub)
│   │   ├── services/
│   │   │   ├── finance_engine.py        # MHS, FIRE, Tax, Loan, XIRR, Couple, Karma (scipy)
│   │   │   ├── mentor_engine.py         # Full LLM pipeline: RAG + domain + lang + structured JSON
│   │   │   ├── mentor_prompts.py        # CA layer, intelligence layer, language rules per locale
│   │   │   ├── arth_protocol_prompt.py  # 7-level conversation depth protocol + guard rails
│   │   │   ├── master_advisor_prompt.py # Master system prompt for Arth persona
│   │   │   ├── claude_service.py        # Groq API wrapper (groq_raw_completion)
│   │   │   ├── rag_service.py           # Token-overlap retrieval from knowledge_base.json
│   │   │   ├── pdf_parser.py            # Form 16 + CAMS extraction (pdfplumber + XIRR)
│   │   │   ├── tax_engine.py            # Tax formatting helpers for stable ResultCard shape
│   │   │   ├── mhs_scorer.py            # MHS calculation wrapper
│   │   │   └── sapna_calculator.py      # Sapna score (in progress)
│   │   ├── main.py                      # FastAPI app, CORS, router registration, DB startup
│   │   ├── config.py                    # Settings loaded from .env
│   │   ├── db_bootstrap.py              # Applies schema on startup (safe on existing DBs)
│   │   ├── schema.sql                   # Core DB schema
│   │   ├── schema_extensions.sql        # Extended tables
│   │   └── seed_demo.py                 # Populates demo users and financial profiles
│   └── frontend/
│       └── src/
│           ├── pages/
│           │   ├── Login.jsx / Signup.jsx
│           │   ├── Onboarding.jsx           # Conversational profile builder chat
│           │   ├── Dashboard.jsx            # MHS + dimensions + karma + feature grid
│           │   ├── FeatureChat.jsx          # FIRE / Tax / Life Event / MF / Couple / MHS
│           │   └── MentorPro.jsx            # Premium AI mentor with session sidebar
│           ├── components/
│           │   ├── ScoreRing.jsx            # Circular animated MHS score
│           │   ├── DimensionBar.jsx         # Horizontal dimension score bars
│           │   ├── KarmaScore.jsx           # Floating karma widget (0–1000 + percentile)
│           │   ├── ChatBubble.jsx           # Individual chat message
│           │   ├── TypingIndicator.jsx      # Animated dots while AI responds
│           │   ├── AppLayout.jsx            # Shared layout wrapper
│           │   ├── ProtectedRoute.jsx       # JWT auth gate
│           │   ├── mentor/
│           │   │   ├── ChatSidebar.jsx      # Session history list with localStorage persistence
│           │   │   ├── StructuredMessage.jsx # Renders JSON response schema as visual cards
│           │   │   └── NotificationBell.jsx # Watchdog alerts bell icon
│           │   └── ResultCards/
│           │       ├── FireCard.jsx         # FIRE result visualization
│           │       ├── TaxCard.jsx          # Tax regime comparison card
│           │       ├── MHSCard.jsx          # Money health score result
│           │       ├── CoupleCard.jsx       # Couple optimization result
│           │       ├── MFXrayCard.jsx       # Portfolio X-Ray result
│           │       └── LifeEventCard.jsx    # Life event impact card
│           ├── context/
│           │   └── AuthContext.jsx          # JWT state, login/logout, bootstrap check
│           └── services/
│               └── api.js                   # All API calls via Axios with auth headers
├── arthmitra.db                             # SQLite database (dev fallback)
└── test_finance_api.py                      # API test suite
```

---

## What Makes This Different

A few things worth pointing out that go beyond the typical hackathon build:

**The math is real.** XIRR uses `scipy.optimize.brentq` — not an approximation. FIRE uses 6.5% inflation and 3.5% SWR, which are actually India-appropriate conservative numbers. HRA exemption uses the actual three-way minimum formula from the Income Tax Act. The FY2024-25 new and old regime slabs are both fully coded with their cess.

**Language detection is not a dropdown.** It detects Devanagari script via Unicode character ranges `[\u0900-\u097F]`, Gujarati via `[\u0A80-\u0AFF]`, and Hinglish via a vocabulary list of 30+ common words. The LLM is then instructed to respond in that detected language — not just labelled differently in the UI.

**The Arth Protocol has real guard rails.** The system prompt for feature chats enforces: don't recommend equity before confirming emergency fund exists when DTI > 50%. Don't finalize tax advice without comparing both regimes. Never use flat-rate interest for loan calculations. End major advice blocks with a satisfaction check. These aren't cosmetic — they're embedded in the system prompt that runs on every message.

**Couple optimization is actual optimization.** The HRA is assigned to whichever partner has the higher marginal rate. The 80C split is weighted inversely by income with headroom-based redistribution when caps clip. This produces a genuinely lower combined tax number, not a generic "split it equally" suggestion.

**The fallback response is also well-written.** When the LLM call fails or input is too vague, the `_fallback_response` function returns a properly structured Hinglish response with sensible India-first defaults — emergency fund first, term insurance if you have dependents, then SIP. The product never shows a blank screen or an error message.

---

## Roadmap

**Near term**
- [ ] Redis session store — replace the in-process `_USER_MEMORY` dict for production scale
- [ ] Goals module — endpoint and router are wired, DB model and calculation logic pending
- [ ] Bharat Score — endpoint exists, scoring algorithm in progress
- [ ] Email delivery for password reset tokens (currently in-memory, demo-ready)

**Next milestone**
- [ ] Live NAV data integration via AMFI API
- [ ] Scheduled watchdog alerts with cron jobs (infra is designed, trigger is stub)
- [ ] Step-up SIP calculator (annual increment on SIP)
- [ ] Capital gains tracker — STCG/LTCG with holding period awareness

**Longer horizon**
- [ ] Upgrade RAG from JSON + token overlap to vector DB (Qdrant or ChromaDB)
- [ ] WhatsApp integration
- [ ] Voice input/output with Indic TTS
- [ ] Mobile app (React Native)
- [ ] B2B API for neo-banks and fintech apps

---

## Impact

India has roughly 500 million working-age people. Fewer than 15 million have ever spoken to a financial advisor.

The barriers are: cost (₹2,000–10,000 per session), language (most advisors operate only in English), and intimidation (people don't know what questions to ask).

ArthMitra removes all three. It is free, it speaks Hinglish, and it is designed to be the patient, non-judgmental financial conversation that most Indians have never had access to.

The goal is not to replace human advisors. It is to make sure that when someone finally walks into an advisor's office, they already understand what a SIP is, what their FOIR looks like, why term insurance matters, and what their FIRE number is. That first conversation should not cost ₹5,000 just to establish the basics.

---

## Contributing

PRs are welcome. Areas where help would make the biggest difference:

- **RAG upgrade** — swap `knowledge_base.json` + token overlap for a proper vector DB
- **Goals module** — `routers/goals.py` is wired, just needs DB model + calculation logic
- **Feed module** — `routers/feed.py` stub exists, financial news summarization via Groq
- **Tests** — finance engine edge cases, regime comparison corner cases, XIRR with edge cashflows

```bash
# Fork → branch → PR
git checkout -b feature/your-feature-name
git commit -m "clear description of what and why"
git push origin feature/your-feature-name
```

---

## License

MIT — free to use, fork, and build on. See [LICENSE](LICENSE).

---

## Disclaimer

ArthMitra provides educational financial information, not personalized investment advice. All calculations use illustrative assumptions and should not be treated as guaranteed outcomes. For decisions involving significant sums, consult a SEBI-registered Investment Advisor (RIA) or a practicing Chartered Accountant.

---

<div align="center">
Built for India. Built to last.
</div>
