# Run ArthMitra locally

## Environment

Put secrets in **`arthmitra/backend/.env`** (next to `config.py`). The app loads that file **automatically**, even if you start uvicorn from the repo root — you do **not** need a `.env` in the project root unless you want to override.

## 1) Backend (terminal 1)

From the **repo root** (`ArthMitra/`, where the `arthmitra` folder lives):

```bash
pip install -r arthmitra/backend/requirements.txt
python -m uvicorn arthmitra.backend.main:app --reload --host 127.0.0.1 --port 8000
```

Check: open <http://127.0.0.1:8000/health> — should return `{"status":"ok",...}`.

## 2) Frontend (terminal 2)

```bash
cd arthmitra/frontend
npm install
npm run dev
```

Open <http://127.0.0.1:5173> (or the URL Vite prints).

The dev server **proxies** `/auth` and `/api` to `http://127.0.0.1:8000`, so signup/login work without CORS/localhost issues.

## If signup still fails

- Confirm Postgres is running and `DATABASE_URL` in `arthmitra/backend/.env` is correct.
- Do **not** set `VITE_API_URL=http://localhost:8000` in frontend `.env` unless the backend is running; on Windows, prefer `127.0.0.1` over `localhost` if you must set it.
