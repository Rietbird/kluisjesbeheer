# Kluisjesbeheer

Webapplicatie voor het beheer van schoolkluisjes — uitleen, inname, defectmelding, reservesleutels, ruilen, rapportages. Geschreven als alternatief voor de betaalde kluismodule van Magister.

**Status:** productie-stabiel. Twee scholen draaien er live op (samen ~5000 kluisjes, ~1700 actieve toewijzingen). Multi-school support sinds april 2026.

---

## Functionaliteit

- **Overzicht** met kluis-grid per vestiging, real-time status (vrij / uitgeleend / defect)
- **Uitleen-flow**: zoek leerling (uit Magister) → selecteer kluisje → toewijzing met sleutel + borg
- **Bulk-wizards** voor collectief uitlenen / innemen (begin/einde schooljaar)
- **Defect-melding** los van huurstatus — een defect kluisje kan tegelijk uitgeleend zijn, gegevens van de huurder blijven bewaard
- **Reservesleutels** registreren per toewijzing
- **Ruilen** van twee kluisjes binnen één vestiging (atomair, met audit-trail)
- **Cluster-beheer**: groepen kluisjes (bv. per gang of verdieping), met bulk-verplaatsing
- **Import** vanuit Excel-export uit Magister (eenmalig per school) — met automatische kluisnummer-normalisatie
- **Dagelijkse leerling-sync** via Magister Medius SOAP-API (cron 06:00)
- **Backup**: 3 lagen (in-app rollend, host-cronjob, deploy-bescherming)
- **In-app handleiding** voor conciërges, plus uitgebreide IT-documentatie in [docs/](docs/)

## Stack

- **Backend**: Flask 3 + SQLite (WAL) + Gunicorn op Python 3.11+
- **Frontend**: React 18 + Vite + Tailwind 3 (dark mode, dynamische branding)
- **Auth**: Entra ID SSO (MSAL) — *"Assignment required: Yes"* op de Enterprise Application
- **Reverse proxy**: NGINX (HTTPS 443 met self-signed cert, of eigen cert)
- **Data**: Magister Medius SOAP/XML-webservice (read-only, alleen `User.Read` en `GetActiveStudents`)

## Installatie

Volledige stappenplan vanaf een verse Debian 12 of 13 VM staat in **[install/README.md](install/README.md)** — copy-paste-vriendelijke instructies, idempotent installatiescript, automatische generatie van self-signed cert + NGINX-config + cron-job + Fernet-encryptiekey.

Korte versie:

Op de doelserver, als root:

```bash
# 1. Git + SSH-key (eenmalig)
apt-get update && apt-get install -y git
ssh-keygen -t ed25519 -N "" -f /root/.ssh/id_ed25519 -C "kluisjes-deploy-$(hostname)"
cat /root/.ssh/id_ed25519.pub
# ↑ kopieer deze regel → plak in GitHub:
#   https://github.com/Rietbird/kluisjesbeheer/settings/keys (read-only)

# 2. Clone + installeer
ssh-keyscan -t ed25519 github.com >> /root/.ssh/known_hosts
git clone git@github.com:Rietbird/kluisjesbeheer.git /root/kluisjesbeheer
cd /root/kluisjesbeheer
bash install.sh
```

Daarna `config.json` invullen (Entra-credentials), service herstarten, inloggen en de eerste user wordt automatisch beheerder. **Updaten later** is `git pull && bash install.sh` — `config.json` en de database blijven intact.

> 💡 Geen GitHub-toegang beschikbaar? Zie [install/README.md](install/README.md) voor de tarball-route als alternatief.

## Ontwikkelen

```bash
# Backend
cd backend
python -m venv venv
venv/Scripts/activate     # Windows; Linux/macOS: . venv/bin/activate
pip install -r requirements.txt
python app.py             # draait op http://localhost:5000

# Frontend
cd frontend
npm install
npm run dev               # draait op http://localhost:5173 (proxy /api naar :5000)
```

Tests draaien: `cd backend && pytest -v`.

## Documentatie

| Doel | Document |
|---|---|
| Installeren op verse VM | [install/README.md](install/README.md) |
| Configuratie na install | [docs/configuratie.md](docs/configuratie.md) |
| Systeemeisen | [docs/systeemeisen.md](docs/systeemeisen.md) |
| Onderhoud en troubleshooting | [docs/onderhoud.md](docs/onderhoud.md) |
| Architectuur | [docs/architectuur.md](docs/architectuur.md) |
| Conciërge-handleiding (functioneel) | [docs/handleiding/HANDLEIDING.md](docs/handleiding/HANDLEIDING.md) |

## Licentie

[MIT](LICENSE) — vrij te gebruiken, aan te passen en (her)verdelen, voor scholen, leveranciers en iedereen die er iets aan heeft.

## Bijdragen

Issues en pull requests zijn welkom. Voor security-meldingen liever direct contact via een persoonlijk bericht in plaats van een publiek issue.
