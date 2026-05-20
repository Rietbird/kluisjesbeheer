# Kluisjesbeheer — uitrol op een nieuwe server

Voor jezelf (Vincent). Tarball klaarzetten en uitrollen op een verse
Debian 12/13 VM (VMware / LXC / VPS).

---

## 1. Tarball (her)bouwen

```bash
bash install/build-bundle.sh
```

Output: `install/dist/kluisjesbeheer-install.tgz` (~155 KB).

Het script controleert automatisch dat er geen `.db`, `config.json`,
`venv/`, `node_modules/`, `backups/` of `.git/` in de tarball belanden,
en dat de kern-bestanden (`install.sh`, `app.py`, `cron_sync.py`,
`magister_client.py`, `requirements.txt`, `package.json`,
`vite.config.js`) wel aanwezig zijn.

De tarball staat in `.gitignore` — wordt nooit gecommit.

---

## 2. Naar de Demo-server kopiëren

> Pad: jij scp't direct vanaf je werkstation naar de Demo-VM
> (jullie zitten in hetzelfde netwerk / je hebt SSH-toegang).

Vervang `<server-ip>` door het interne IP van de Demo-VM, en
`<gebruiker>` door een gebruiker met sudo-rechten (vaak `root` of
`debian` of `Demo` — vraag het bij hen na).

```bash
scp install/dist/kluisjesbeheer-install.tgz <gebruiker>@<server-ip>:/tmp/
```

Werkt poort 22 niet (firewall / WifiMan-VPN blokkeert poort 22)?
Probeer een alternatieve SSH-poort:

```bash
scp -P 2222 install/dist/kluisjesbeheer-install.tgz <gebruiker>@<server-ip>:/tmp/
```

---

## 3. Op de Demo-server uitrollen (console / SSH)

Log in op de server en draai:

```bash
ssh <gebruiker>@<server-ip>
sudo -i                                     # root worden
cd /root                                    # of een andere werkmap
tar xzf /tmp/kluisjesbeheer-install.tgz
cd kluisjesbeheer-install
bash install.sh                             # idempotent — opnieuw draaien is veilig
```

Het script doet alles automatisch (apt, user, code, venv, npm build,
config.json met willekeurige SecretKey, systemd-service, cron-job,
log-perms). Aan het eind toont het:

- het **uitgaande publieke IP** van de server → voor de SWP-whitelist
- de **handmatige vervolgstappen** (config.json invullen, restart,
  eerste login, Magister-credentials via UI)

---

## 4. Na de installatie (handmatig, op de server)

```bash
sudo nano /opt/kluisjesbeheer/backend/config.json
```

Vul de `VUL_IN_*`-velden in:
- `TenantId`, `ClientId`, `ClientSecret`, `DashboardGroupId` (Entra)
- `RedirectUri` (productie-URL incl. `/auth/callback`)
- `AllowedOrigins` (frontend-URL, bv. `["https://kluisjes.intern.school.nl"]`)
- `SchoolNaam`, `SchoolSubtitel`, `SchoolLogo`, `SchoolKleur`

> ⚠️ `SecretKey` is al automatisch ingevuld — **niet wijzigen** na
> gebruik (versleutelt het Magister-wachtwoord in de DB).

Daarna:

```bash
sudo systemctl restart kluisjesbeheer
```

Open de app in de browser → log in → je wordt automatisch beheerder →
*Beheer → Import* → Magister-koppeling invullen.

Voor de details zie `docs/installatie-vmware.md` (geef je ook aan
Demo IT).

---

## 5. Updaten van een bestaande installatie

Zelfde recept:

```bash
# Lokaal:
bash install/build-bundle.sh
scp install/dist/kluisjesbeheer-install.tgz <gebruiker>@<server-ip>:/tmp/

# Op de server:
cd /root && rm -rf kluisjesbeheer-install
tar xzf /tmp/kluisjesbeheer-install.tgz
cd kluisjesbeheer-install
bash install.sh
```

`install.sh` is idempotent: `config.json` en de database worden
**nooit** overschreven. Code wordt vervangen, frontend opnieuw gebouwd,
service herstart.

---

## 6. Troubleshooting tijdens uitrol

| Symptoom | Oplossing |
|---|---|
| `scp`: "Connection refused" | Check SSH-poort (22 vs 2222) en of `ssh`-daemon draait op de VM |
| `bash install.sh`: "Bundle gevonden in /root" + crash | Verkeerde werkmap — moet `cd kluisjesbeheer-install` zijn vóór je `bash install.sh` doet |
| Build faalt bij `npm ci` | Internet-toegang naar `registry.npmjs.org`? Probeer `curl -I https://registry.npmjs.org` op de server |
| Service start niet | `journalctl -u kluisjesbeheer -n 50` — meestal ontbreekt iets in `config.json` |
| Cron-sync krijgt geen verbinding (poort 8800) | IP-whitelist nog niet actief bij SWP — geef het server-IP uit het eindrapport door aan Demo's Magister-beheerder |

---

## Voor Demo IT

Geef hen:
1. `install/dist/kluisjesbeheer-install.tgz` (de tarball)
2. `docs/installatie-vmware.md` (hun stappenplan, uitgebreider dan dit
   bestand — dit is een verkorte versie voor jou)
