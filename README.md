# Kluisjesbeheer

Webapplicatie voor het beheer van schoolkluisjes — uitleen, inname, defectmelding, reservesleutels, ruilen, rapportages. Geschreven als alternatief voor de betaalde kluismodule van Magister.

**Status:** productie-stabiel. Multi-school / multi-vestiging support; geschikt voor scholen van enkele honderden tot enkele duizenden kluisjes.

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
- **Data**: Magister Medius SOAP/XML-webservice (read-only, `Algemeen.Login` + `ADFuncties.GetActiveStudents`)

## Installatie

Op een verse **Debian 12/13** server (VM of LXC), als root:

```bash
apt-get update && apt-get install -y git
git clone https://github.com/Rietbird/kluisjesbeheer.git /root/kluisjesbeheer
cd /root/kluisjesbeheer
bash install.sh
```

Daarna open je `https://<server-ip>/` in de browser — je krijgt een
setup-scherm waarin je de Entra-gegevens invult (TenantId, ClientId,
ClientSecret, RedirectUri). Na opslaan kun je direct inloggen — de
eerste user wordt automatisch beheerder.

**Updaten:** `cd /root/kluisjesbeheer && git pull && bash install.sh`.

Volledig stappenplan met Entra-checklist, TLS, Magister-koppeling en
troubleshooting: **[install/README.md](install/README.md)**.

<details>
<summary>Alternatief — Proxmox helper-script (in 5-7 min een complete LXC)</summary>

Op de **Proxmox host** als root:

```bash
bash -c "$(curl -fsSL https://raw.githubusercontent.com/Rietbird/kluisjesbeheer/master/proxmox/install-ct.sh)"
```

Maakt automatisch een Debian 12 LXC aan, installeert kluisjesbeheer
erin en geeft je IP + URL. Zie [docs/proxmox.md](docs/proxmox.md).

</details>

<details>
<summary>Alternatief — Docker compose</summary>

```bash
git clone https://github.com/Rietbird/kluisjesbeheer.git
cd kluisjesbeheer
docker compose up -d --build
```

Zie [docs/docker.md](docs/docker.md).

</details>

## Documentatie

| Doel | Document |
|---|---|
| Installeren op verse VM (volledig stappenplan) | [install/README.md](install/README.md) |
| Systeemeisen vooraf | [docs/systeemeisen.md](docs/systeemeisen.md) |
| Configuratie na install | [docs/configuratie.md](docs/configuratie.md) |
| Onderhoud en troubleshooting | [docs/onderhoud.md](docs/onderhoud.md) |
| Architectuur | [docs/architectuur.md](docs/architectuur.md) |
| Conciërge-handleiding (functioneel) | [docs/handleiding/HANDLEIDING.md](docs/handleiding/HANDLEIDING.md) |
| Lokaal ontwikkelen (backend + frontend + tests) | [CLAUDE.md](CLAUDE.md) |

## Licentie

[MIT](LICENSE) — vrij te gebruiken, aan te passen en (her)verdelen, voor scholen, leveranciers en iedereen die er iets aan heeft.

## Bijdragen

Issues en pull requests zijn welkom. Voor security-meldingen liever direct contact via een persoonlijk bericht in plaats van een publiek issue.
