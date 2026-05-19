# Kluisjesbeheer

School locker management web app. Replaces the Magister locker module.

## Architecture

- **Backend:** Flask REST API (`backend/`) — Python 3.11+, SQLite
- **Frontend:** React SPA (`frontend/`) — Vite, TailwindCSS
- **Auth:** Entra ID SSO via MSAL (authorization code flow)
- **Data:** Magister API (read-only) for student data
- **Backup:** `backend/backup.py` (scheduler + sqlite3.backup), `backend/api_backup.py` (REST endpoints)

## Deploy

> **CRITICAL: NEVER include `*.db` or `config.json` in deploy tarballs!**
> On 2026-04-15, a deploy without `--exclude='*.db'` overwrote the production database on CT101. 5 days of data was lost.

- tar MUST always use `--exclude='*.db'` and `--exclude='config.json'`
- Pre-deploy: trigger a manual backup via POST /api/backups/create (beheerder only)
- Three backup layers are in place (see Backup section below)

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

## Backup System

Three layers of backup protection:

1. **In-app backup** (`backend/backup.py` + `backend/api_backup.py`):
   - Background thread creates daily SQLite backups using `sqlite3.backup()` API (safe during writes)
   - Retention: 7 daily + 4 weekly, rolling
   - Stored in `backend/backups/`
   - API endpoints (beheerder only): GET /api/backups, POST /api/backups/create, GET /api/backups/<naam>/download
   - Registered in app.py as `backup_bp` blueprint, scheduler starts at app startup

2. **Proxmox host cronjob** (`/usr/local/bin/backup-kluisjes.sh`):
   - Runs daily at 02:00 via cron
   - Pulls database from CT101 and CT102 via `pct exec` + `pct pull`
   - Stored in `/var/lib/vz/dump/kluisjes-db/`, 7 daily per container
   - Sunday: full `vzdump` snapshot of both containers (4 weeks retained)

3. **Deploy protection**: tar MUST always use `--exclude='*.db'` and `--exclude='config.json'`

## Bekende valkuilen

**Deploy / Database:**
- **NEVER deploy without `--exclude='*.db'` and `--exclude='config.json'`** — production DB was overwritten on 2026-04-15
- Always trigger a manual backup (POST /api/backups/create) before deploying

**Soft deletes:**
- Kluisjes gebruiken `verwijderd` flag — queries MOETEN `AND verwijderd = 0` bevatten
- Unique index op kluisnummer geldt alleen voor `WHERE verwijderd = 0` — undeleten vereist eerst nummering aanpassen
- Verwijderen is cascading fake-delete: kluisjes worden gemarkeerd, toewijzingen-historie blijft bestaan

**Toewijzing state machine:**
- Nieuwe toewijzing pas mogelijk als vorige toewijzing's sleutel is ingeleverd EN borg is teruggestort
- Één actieve toewijzing per kluisje (unique index `WHERE actief = 1`)
- Bulk operaties zijn niet atomisch — partial state bij crash

**Magister API:**
- SSL-verificatie configureerbaar via `MAGISTER_SSL_VERIFY` (True / CA-bundle pad / False) — oude SWP-systemen hebben soms cert-issues
- Session tokens gecacht voor 60 seconden, geen retry bij verlopen token
- Dagelijkse leerling-sync = `cron_sync.py` (cron 06:00 op CT101); roept alleen `get_leerlingen()` aan. De kluisjes-import is een eenmalige Excel-export uit Magister (geen API)

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
- Normalisatie van kluisnummers optioneel via `normaliseer=1` form-veld; preview retourneert `normalisatie`-advies (krom/breedte/collision). Default aan bij kromme data, geblokkeerd bij collisions. Import doet een voor-scan (workbook 2x lezen via file.seek(0))

**Cluster verplaatsen:**
- `POST /api/clusters/<id>/verplaats-reeks` (prefix+van+tot, op getal) en `/verplaats-selectie` (kluisje_ids) — alleen binnen dezelfde vestiging (409 anders)

**Deploy:**
- `schoolvakanties.json` moet jaarlijks handmatig bijgewerkt worden (geen API)
- Gunicorn multi-worker: elke worker heeft eigen Magister token cache (dubbele calls)

## Spec & Plan

- Design spec: `docs/superpowers/specs/2026-03-24-kluisjesbeheer-design.md`
- Implementation plan: `docs/superpowers/plans/2026-03-24-kluisjesbeheer.md`
