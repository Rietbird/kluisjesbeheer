# Kluisjesbeheer

School locker management web app. Replaces the Magister locker module.

## Architecture

- **Backend:** Flask REST API (`backend/`) — Python 3.11+, SQLite
- **Frontend:** React SPA (`frontend/`) — Vite, TailwindCSS
- **Auth:** Entra ID SSO via MSAL (authorization code flow)
- **Data:** Magister API (read-only) for student data

## Development

### Backend
```bash
cd backend
python -m venv venv
venv\Scripts\activate   # Windows
pip install -r requirements.txt
python app.py           # Runs on port 5000
```

### Frontend
```bash
cd frontend
npm install
npm run dev             # Runs on port 5173, proxies /api + /auth to :5000
```

### Tests
```bash
cd backend
pytest -v
```

## Config

Copy `backend/config.example.json` to `backend/config.json` and fill in secrets.

## Spec & Plan

- Design spec: `docs/superpowers/specs/2026-03-24-kluisjesbeheer-design.md`
- Implementation plan: `docs/superpowers/plans/2026-03-24-kluisjesbeheer.md`
