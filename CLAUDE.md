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

## Bekende valkuilen

**Soft deletes:**
- Kluisjes gebruiken `verwijderd` flag — queries MOETEN `AND verwijderd = 0` bevatten
- Unique index op kluisnummer geldt alleen voor `WHERE verwijderd = 0` — undeleten vereist eerst nummering aanpassen
- Verwijderen is cascading fake-delete: kluisjes worden gemarkeerd, toewijzingen-historie blijft bestaan

**Toewijzing state machine:**
- Nieuwe toewijzing pas mogelijk als vorige toewijzing's sleutel is ingeleverd EN borg is teruggestort
- Één actieve toewijzing per kluisje (unique index `WHERE actief = 1`)
- Bulk operaties zijn niet atomisch — partial state bij crash

**Magister API:**
- SSL verificatie staat uit (`verify=False`) — oude SWPI/SOMtoday systemen hebben cert-issues
- Session tokens gecacht voor 60 seconden, geen retry bij verlopen token
- `sync_magister.py` hardcoded `vestiging_id=1` — werkt alleen voor eerste vestiging

**Database:**
- Migraties zijn try-catch `ALTER TABLE` in `init_db()` — geen versie-tracking of rollback
- Timestamps gebruiken SQLite `datetime('now')` (UTC) zonder timezone-conversie
- `ON CONFLICT` upsert in `api_instellingen.py` specificeert value tweemaal (werkt maar redundant)

**Auth (Entra ID):**
- Group membership check heeft 10s timeout, geen retry — netwerkstoring = 403
- Profielfoto endpoint retourneert 204 bij failure — browser cachet "geen foto" indefiniet
- Session lifetime: 8 uur

**Frontend:**
- Vite proxy stuurt `/api` + `/auth` naar Flask :5000 — zonder Flask krijg je cryptische CORS errors
- Filters in `useKluisjes` zijn niet gedebounced — snel typen veroorzaakt meerdere API calls
- Error response format inconsistent (soms JSON, soms plain text)

**PDF/Rapporten:**
- DejaVuSans font hardcoded naar `/usr/share/fonts/truetype/dejavu/` — fallback Helvetica op Windows (Unicode-issues)
- `_get_rapport_data()` retourneert 4 of 5 items (fragiel unpacking)

**XLSX Import:**
- All-or-nothing: duplicate kluisnummer rollt hele import terug
- Duplicate detectie via `'UNIQUE' in str(e)` — fragiel

**Deploy:**
- `schoolvakanties.json` moet jaarlijks handmatig bijgewerkt worden (geen API)
- Gunicorn multi-worker: elke worker heeft eigen Magister token cache (dubbele calls)

## Spec & Plan

- Design spec: `docs/superpowers/specs/2026-03-24-kluisjesbeheer-design.md`
- Implementation plan: `docs/superpowers/plans/2026-03-24-kluisjesbeheer.md`
