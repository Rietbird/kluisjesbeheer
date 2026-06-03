# Kluisjesbeheer — uitrol-stappenplan

Stap-voor-stap copy-paste vanaf een **kale Debian 12/13 installatie**
tot een draaiende app.

> 📋 **Werkwijze:** vervang in de commando's `<server-ip>` door het
> interne IP van je doelserver. Markering:
> 🖥️ = jouw werkstation · 🐧 = doelserver (via console).

---

> 🔒 **Security First:** Dit stappenplan gaat uit van SSH-sleutel authenticatie. 
> Gebruik geen wachtwoorden voor SSH, zelfs niet op interne netwerken.

---

## Stap 0 — Entra ID voorbereiden (vóór de uitrol)

Dit hoeft niet op de server, maar wil je vóór stap 1 geregeld hebben.
Toegang tot de app loopt 100% via Microsoft Entra ID (single sign-on).
De wachttijd zit in de Entra-acties, niet in de code — dus regel dit
vooraf, dan is de uitrol zelf vlot.

> 🔑 **Toegangsbeleid:** wij gebruiken Entra's **"Assignment required"**.
> Microsoft regelt vóór onze app überhaupt iets ziet wie wel/niet
> binnen mag. Geen aparte groep-check in onze code; je wijst gewoon
> users en/of groepen toe aan de Enterprise Application. De eerste
> persoon die inlogt wordt automatisch lokale beheerder; rollen +
> vestigingen beheer je daarna in *Beheer → Gebruikers* in de app
> zelf.

### Checklist (vraag dit aan de tenant-beheerder)

| # | Wat | Waar in Entra | Resultaat |
|---|---|---|---|
| 1 | App-registratie aanmaken | Entra → App registrations → New registration | `ClientId` (GUID) + `TenantId` (GUID) |
| 2 | Redirect URI toevoegen | App registration → Authentication → Web platform → Add URI | URL eindigend op `/auth/callback`, bv. `https://<server-ip>/auth/callback` of `https://kluisjes.intern.<school>.nl/auth/callback` |
| 3 | Client-secret aanmaken | App registration → Certificates & secrets → New client secret | `ClientSecret` (string — **direct kopiëren**, na 1× tonen onleesbaar) |
| 4 | API permissions | App registration → API permissions | `Microsoft Graph → Delegated → User.Read` + **"Grant admin consent"** |
| 5 | Assignment required = Yes | Enterprise applications → [jouw app] → Properties | "Assignment required" op **Yes** |
| 6 | Users toewijzen | Enterprise applications → [jouw app] → Users and groups → Add user/group | Voeg jezelf + de Demo-beheerders toe (later kun je daar groepen aan koppelen) |

> 💡 **Stap 6 mag ook met een Security-groep** — handiger als je veel
> users hebt en het beheer bij iemand anders ligt. Maak dan een groep
> aan, voeg de groep toe in *Users and groups*, en beheer members in
> de groep i.p.v. in de app-registratie.

### Variabelen voor `config.json` (stap 4 van de installatie)

Vul tijdens de Entra-setup deze tabel in, dan kun je 'm morgen letterlijk
overnemen:

```
TenantId      = ________________________________
ClientId      = ________________________________
ClientSecret  = ________________________________
RedirectUri   = https://________________/auth/callback
```

`DashboardGroupId` is **verouderd** en hoef je niet meer in te vullen
(toegangscontrole zit nu in Entra Assignment, niet in onze code).

### Aandachtspunt — HTTPS vereiste

Entra accepteert geen HTTP-RedirectUri (behalve `http://localhost`).
Self-signed cert is wel OK — `install.sh` genereert er zelf één bij
installatie. Browser geeft 1× "Niet beveiligd"-waarschuwing
("Geavanceerd → Doorgaan"), daarna werkt SSO normaal. Voor productie
met een echt cert: zie stap 7.

---

## Stap 1 — Kale Debian voorbereiden (op de doelserver)

> Uitgangspunt: een verse Debian 12/13 VM (VMware / LXC / VPS), waarop
> alleen root-toegang via de console beschikbaar is (geen SSH nog).

### 1.1 Op de VMware-console: inloggen en netwerk verifiëren

Log in als `root` op de console van de VM. Eerste check:

```bash
ip -4 addr show | grep inet
ping -c 2 8.8.8.8
cat /etc/debian_version
```

Je moet zien: een statisch intern IP, werkende internetverbinding, en
versie `12.x` of `13.x`. Werkt internet niet, los dat eerst op met
de netwerkbeheerder — verder zonder internet kan niet (apt + npm-install).

### 1.2 Apt updaten + basistools installeren

```bash
apt-get update && apt-get upgrade -y
apt-get install -y openssh-server sudo curl nano less ca-certificates
```

### 1.3 SWP-whitelist alvast aanvragen

> ⏱️ SWP heeft soms 1-2 werkdagen nodig om een IP te whitelisten. Door
> dit hier al te doen, loopt de aanvraag parallel aan de rest van de
> installatie — in stap 7 hoef je alleen nog te verifiëren.

```bash
curl -s https://ifconfig.me ; echo
```

Noteer dit IP en mail het direct naar de Magister-/SWP-beheerder van
de school met het verzoek: *"Whitelisten voor toegang tot
`<jouwschool>.swp.nl` op poort 8800."*

### 1.4 SSH-daemon controleren + root-login toestaan

```bash
systemctl enable --now ssh
systemctl status ssh --no-pager | head -3
ss -tlnp | grep :22 || echo "ssh luistert NIET op poort 22"
```

Standaard staat Debian 12/13 op `PermitRootLogin prohibit-password`
(root mag in, maar **alleen met SSH-key**). Voor wachtwoord-auth als
root moet dit op `yes`:

```bash
sed -i 's/^#*PermitRootLogin.*/PermitRootLogin yes/' /etc/ssh/sshd_config
systemctl restart ssh
grep -E '^PermitRootLogin' /etc/ssh/sshd_config       # controle: yes
```

> 💡 Als poort 22 geblokkeerd is en je 2222 wilt: bewerk
> `/etc/ssh/sshd_config`, regel `#Port 22` → `Port 2222`, dan
> `systemctl restart ssh`. Gebruik daarna `ssh -p 2222 ...` en
> `scp -P 2222 ...` in de stappen hieronder.

### 1.5 SSH-verbinding testen vanaf je werkstation

🖥️ **Werkstation**:

```bash
ssh root@<server-ip> "echo 'SSH werkt'; cat /etc/debian_version"
```

Eerste keer: SSH vraagt om host-key bevestiging (`yes`) + het root-
wachtwoord. Verwacht: `SSH werkt` + versie-nummer. Werkt het? Door naar
stap 2. Werkt het niet? Niet verder gaan — eerst dit oplossen.

> 🔒 **Productie-tip:** voor een server die ook van buiten het beheernet
> bereikbaar is, schakel root + wachtwoord-auth ná de installatie uit en
> gebruik een admin-account met SSH-key. Dit stappenplan kiest voor de
> snelle weg (root + wachtwoord) omdat het in de meeste school-uitrollen
> om een server op een intern beheernet gaat.

---

## Stap 2 — Code op de server krijgen

Twee paden — kies wat past:

### Pad A — Git clone (aanbevolen, makkelijkste updates)

🐧 **Server** — log in en clone direct (repo is publiek, geen auth nodig):

```bash
ssh root@<server-ip>
apt-get update && apt-get install -y git
git clone https://github.com/Rietbird/kluisjesbeheer.git /root/kluisjesbeheer
cd /root/kluisjesbeheer
bash install.sh
```

**Update later** is dan triviaal:

```bash
cd /root/kluisjesbeheer && git pull && bash install.sh
```

### Pad B — Tarball (offline / lucht-gat / geen GitHub-toegang)

Voor servers zonder GitHub-toegang. Genereer een bundel op een werkstation
mét toegang en kopieer 'm over.

🖥️ **Werkstation** — vanuit de kluisjesbeheer repo-root:

```bash
cd /c/Projects/kluisjesbeheer            # of jouw pad naar de repo
bash install/build-bundle.sh
scp install/dist/kluisjesbeheer-install.tgz root@<server-ip>:/tmp/
```

🐧 **Server** — log in, uitpakken, installeren:

```bash
ssh root@<server-ip>
cd /root
tar xzf /tmp/kluisjesbeheer-install.tgz
cd kluisjesbeheer-install
bash install.sh
```

> Het script bouwt zelf de frontend (`npm ci` + `npm run build`) op de
> server — er hoeft niets vooraf gebouwd te worden. Alleen Python en
> Node moeten via apt geïnstalleerd kunnen worden (regelt install.sh).

---

## Stap 3 — Wat install.sh doet

Het script draait nu ~3-5 minuten. Aan het eind toont het:
- Pad naar `config.json`
- Het **uitgaande publieke IP** van de server (noteer dit — voor de
  SWP-whitelist)
- De vervolgstappen die hieronder staan

> 💡 Het script is **idempotent** — als er iets misgaat kun je 'm
> gewoon opnieuw draaien. `config.json` en de database worden nooit
> overschreven.

---

## Stap 4 — Entra-gegevens invullen via de browser

🌐 **Open in de browser**: `https://<server-ip>/`

De browser geeft één keer een "Niet beveiligd"-waarschuwing (zelf-ondertekend
certificaat) — klik **Geavanceerd → Doorgaan naar deze website**.

Je komt automatisch op een setup-scherm:

![Setup-wizard](../docs/handleiding/screenshots/setup-wizard.png)

Vul in:

| Veld | Waarde |
|---|---|
| Tenant ID | Entra Tenant-GUID |
| Client ID | Entra App Registration GUID |
| Client Secret | Entra Client Secret |
| Redirect URI | `https://<server-ip>/auth/callback` (moet exact matchen met wat in Entra staat) |

Klik **Opslaan en inloggen** — de app schrijft de waarden naar
`backend/config.json`, laadt de configuratie opnieuw en stuurt je door
naar de Microsoft-login.

> ⚠️ Andere velden (`SchoolNaam`, `SchoolLogo`, `SchoolKleur`,
> `AllowedOrigins`, etc.) stel je later in via **Beheer → Instellingen**
> binnen de app. `SecretKey` is al automatisch gegenereerd — **NIET
> wijzigen** na gebruik (versleutelt het Magister-wachtwoord in de DB).

Verwacht: je wordt doorgestuurd naar Microsoft, logt in en komt op het
kluisjesbeheer-dashboard. De eerste gebruiker wordt automatisch
beheerder.

---

## Stap 5 — TLS / reverse proxy

`install.sh` zet zelf NGINX op (poort 80 → 443, met een self-signed
cert in `/etc/nginx/ssl/`). De app is meteen bereikbaar op
`https://<server-ip>/` — bij de eerste open vraagt de browser om de
cert-waarschuwing te accepteren ("Geavanceerd → Doorgaan").

Self-signed is genoeg om met Entra te werken (Entra eist HTTPS, niet
een geldig CA-cert). Voor productie kun je het cert later vervangen:

- **Eigen cert van school-CA:** overschrijf `/etc/nginx/ssl/self.crt`
  en `/etc/nginx/ssl/self.key` met de echte bestanden (zelfde namen),
  daarna `nginx -t && systemctl reload nginx`.
- **Externe URL met Let's Encrypt:** plaats een reverse-proxy
  (Cloudflare Tunnel, F5, externe NGINX) vóór deze server en laat die
  het cert regelen. De ingebouwde NGINX hoeft dan niet uit — kan ook
  als binnenste laag dienen.

De `RedirectUri` in `config.json` (stap 4) moet **exact** matchen met
wat in de Entra app-registration staat. Bij self-signed bv.
`https://<server-ip>/auth/callback`, bij eigen cert / externe URL de
publieke variant.

---

## Stap 6 — Eerste login + Magister-koppeling (browser)

Open `https://kluisjes.intern.<school>.nl` (of de URL die in
`RedirectUri` staat) in een browser. Log in met een beheerderaccount.

> 🔑 De **eerste gebruiker die inlogt wordt automatisch beheerder**.
> Volgende collega's loggen ook gewoon zelf in via Entra (mits ze op
> de Enterprise App zijn *Assigned*) en verschijnen automatisch in
> *Beheer → Gebruikers* — daar koppel je hun rol + vestiging(en).

Ga naar **Beheer → Import → Magister-koppeling**:
- URL: `https://<jouwschool>.swp.nl:8800/doc`
- Account: het service-account (door de Magister-beheerder aangevraagd)
- Wachtwoord: het service-account-wachtwoord

Klik *Opslaan*. Het wachtwoord wordt versleuteld (Fernet / AES-128-CBC
+ HMAC) in de database opgeslagen.

> 💡 Wil je later de Entra-koppeling wijzigen (bv. RedirectUri
> aanpassen na het toevoegen van een eigen domein, of ClientSecret
> roteren)? Dat kan volledig via **Beheer → Entra**. Het secret blijft
> gemaskeerd — leeg laten = ongewijzigd. Geen herstart nodig.

---

## Stap 7 — IP-whitelist verifiëren (aangevraagd in 1.4)

🐧 **Server** — controleer dat het uitgaande IP nog hetzelfde is als
wat je in stap 1.4 hebt doorgegeven:

```bash
curl -s https://ifconfig.me ; echo
```

Wijkt het af van wat je gemaild hebt? Stuur de SWP-beheerder een
correctie. Bij verhuizing naar een ander netwerk moet de whitelist-
aanvraag herhaald worden.

> Niet aangevraagd in 1.4 (vergeten / overgeslagen)? Doe het nu —
> verwerking duurt 1-2 werkdagen.

---

## Stap 8 — Test de leerling-sync

🐧 **Server** (als root of via sudo):

```bash
sudo -u kluisjes /opt/kluisjesbeheer/.venv/bin/python /opt/kluisjesbeheer/backend/cron_sync.py
```

**Werkt het?** Verwachte output:
```
=== CRON MAGISTER LEERLINGEN SYNC ===
Magister-config uit database: https://<jouwschool>.swp.nl:8800/doc
1234 leerlingen opgehaald, 56 klassen
Database bijgewerkt. Done!
```

De cron staat al ingepland voor 06:00 dagelijks
(`/etc/cron.d/kluisjesbeheer-sync`).

**Werkt het niet?** Symptomen + oplossing:

| Melding | Oorzaak |
|---|---|
| `Geen verbinding met de Magister-webservice (poort 8800)` | IP-whitelist nog niet actief — vraag bij SWP na (stap 7) |
| `Medius login mislukt` | Verkeerd account/wachtwoord in *Beheer → Import* |
| `kan magister_pass niet ontsleutelen` | `SecretKey` in `config.json` is gewijzigd na het opslaan van het wachtwoord — vul het wachtwoord opnieuw in via de UI |

Test de netwerkverbinding los van credentials:
```bash
openssl s_client -connect <jouwschool>.swp.nl:8800 </dev/null 2>&1 | head -5
```
Krijg je geen TLS-handshake = poort dicht = whitelist niet actief.

---

## Stap 9 — Kluisjes importeren (eenmalig)

Excel-export uit Magister (kluisjesmodule) → uploaden via *Beheer →
Import* in kluisjesbeheer. Vestigingen en clusters worden automatisch
aangemaakt.

Bij kromme nummering (MO-1 / MO-100 / MO-1000): vink "kluisnummers
normaliseren" aan → wordt automatisch MO-0001 / MO-0100 / MO-1000.

---

## Onderhoud — daily commands

🐧 **Server**:

| Wat | Commando |
|---|---|
| Service-status | `systemctl status kluisjesbeheer` |
| App-logs (live) | `journalctl -u kluisjesbeheer -f` |
| Cron-logs | `tail -f /var/log/kluisjes-sync.log` |
| Herstarten | `systemctl restart kluisjesbeheer` |
| Backups | `ls -lt /opt/kluisjesbeheer/backend/backups/ \| head` |
| Handmatige backup | via app: *Beheer → Backup* |

---

## Updaten van een bestaande installatie

### Pad A — git clone werd gebruikt (aanbevolen)

🐧 **Server**:
```bash
cd /root/kluisjesbeheer
git pull
bash install.sh
```

### Pad B — tarball werd gebruikt

🖥️ **Werkstation**:
```bash
cd /c/Projects/kluisjesbeheer
git pull
bash install/build-bundle.sh
scp install/dist/kluisjesbeheer-install.tgz root@<server-ip>:/tmp/
```

🐧 **Server**:
```bash
cd /root && rm -rf kluisjesbeheer-install
tar xzf /tmp/kluisjesbeheer-install.tgz
cd kluisjesbeheer-install
bash install.sh
```

In beide gevallen: `config.json` en de database blijven onaangeroerd;
code wordt vervangen, frontend wordt opnieuw gebouwd op de server,
service herstart automatisch.

---

## Troubleshooting tijdens uitrol

| Symptoom | Oplossing |
|---|---|
| `scp`: "Connection refused" | Check SSH-poort (22 of 2222 — gebruik `-P 2222` resp. `-p 2222`) en `systemctl status ssh` op de server |
| `scp`: "Permission denied" | Wachtwoord-auth uit / wrong user / `PermitRootLogin` niet op `yes` (stap 1.4) |
| `bash install.sh`: crasht direct | Vergeten `cd kluisjesbeheer-install`? Pwd moet eindigen op `/kluisjesbeheer-install` |
| `npm ci` faalt | Geen internet naar `registry.npmjs.org` — proxy/firewall check |
| Service start niet (`failed`) | `journalctl -u kluisjesbeheer -n 50` — meestal ontbreekt een veld in `config.json` of klopt `RedirectUri` niet |
| Browser: `redirect_uri_mismatch` | `RedirectUri` in `config.json` moet **letterlijk** matchen met de URL in de Entra app-registration |
| Browser: blanco pagina, geen errors | Frontend build leeg — `cd /opt/kluisjesbeheer/frontend && npm run build` met foutmelding tonen |

Voor diepere problemen: `journalctl -u kluisjesbeheer -n 200 --no-pager`
+ `tail -50 /var/log/kluisjes-sync.log`.

---

## Voor school-IT (overhandig na uitrol)

Geef hen:
1. Link naar deze repo: <https://github.com/Rietbird/kluisjesbeheer>
   — voor toekomstige updates (`git pull && bash install.sh` op de
   server). Of, bij offline-omgeving, een verse
   `install/dist/kluisjesbeheer-install.tgz`.
2. De `RedirectUri` die je in `config.json` hebt gezet (moeten ze in
   de Entra app-registration controleren).
3. Het uitgaande server-IP — voor whitelisting bij SWP.
