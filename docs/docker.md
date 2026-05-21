# Kluisjesbeheer — Docker-uitrol

Alternatief voor de [install.sh-route](../install/README.md). Doet
hetzelfde — Python + gunicorn + cron + nginx + self-signed TLS — maar
verpakt in twee containers via `docker compose`. Geschikt voor servers
waar Docker al draait (eigen VM, VPS, NAS, Raspberry Pi).

**Vergelijking:**

| | `install.sh` | Docker |
|---|---|---|
| OS-vereisten | Debian 12/13 | elk OS met Docker |
| Install-tijd | ~5 min | ~3 min (na image-pull) |
| Updates | `git pull && bash install.sh` | `docker compose pull && up -d` |
| Isolatie van host | gedeeld (apt-deps, systemd) | volledig (container) |
| TLS | self-signed (vervangbaar) | self-signed (vervangbaar) |
| Cron-sync | host-cron | in-container cron via supervisord |

---

## Vereisten

- Een server met **Docker Engine** + **Docker Compose plugin**
  - Debian/Ubuntu: `apt-get install docker.io docker-compose-plugin`
  - Of de officiële Docker-install: https://docs.docker.com/engine/install/
- Poort 80 + 443 vrij op de host
- Entra ID app-registratie (zie [install/README.md stap 0](../install/README.md))

---

## Stap 1 — Compose-stack ophalen

```bash
# Maak een werkmap voor de stack
mkdir -p /opt/kluisjesbeheer && cd /opt/kluisjesbeheer

# Pak de docker-compose.yml + bind-mount-bestanden uit de repo
curl -fsSL https://raw.githubusercontent.com/Rietbird/kluisjesbeheer/master/docker-compose.yml -o docker-compose.yml
mkdir -p docker
curl -fsSL https://raw.githubusercontent.com/Rietbird/kluisjesbeheer/master/docker/nginx.conf -o docker/nginx.conf
curl -fsSL https://raw.githubusercontent.com/Rietbird/kluisjesbeheer/master/docker/nginx-entrypoint.sh -o docker/nginx-entrypoint.sh
chmod +x docker/nginx-entrypoint.sh
```

> 💡 Privé repo? Vervang de URL's door je eigen mirror, of `git clone`
> de hele repo en draai `docker compose` vanuit daar — de
> `docker-compose.yml` werkt ook vanuit een gecloonde repo.

---

## Stap 2 — Image bouwen óf pullen

**Optie A — Pullen** (snelste, vereist publieke image of GHCR-login):

```bash
docker compose pull
```

**Optie B — Lokaal bouwen** (vanuit een gecloonde repo):

```bash
# In docker-compose.yml: comment `image:` regels uit en uncomment `build: .`
git clone https://github.com/Rietbird/kluisjesbeheer.git
cd kluisjesbeheer
docker compose build
```

---

## Stap 3 — Starten

```bash
docker compose up -d
```

Dit doet vier dingen:
1. **`init-config`-container** draait eenmalig: maakt `config.json` met
   random `SecretKey` in het data-volume (als die nog niet bestaat).
2. **`init-cert`-container** draait eenmalig: genereert self-signed cert
   (10 jaar) in nginx-ssl-volume (als die nog niet bestaat).
3. **`app`-container** start: gunicorn op 5000 + cron via supervisord.
   Eerste run geeft HTTP 500 op `/auth/login` — verwacht, want
   Entra-credentials staan nog op `VUL_IN_*`.
4. **`nginx`-container** start: HTTP→HTTPS redirect + proxy 443 naar app.

> ⚠️ **Default: alleen op 127.0.0.1 bereikbaar.** Voor toegang vanaf het
> schoolnetwerk: open `docker-compose.yml` en verwijder de `127.0.0.1:`
> prefix uit de `ports:`-sectie van de nginx-service. Daarna:
> `docker compose up -d nginx`. Of plaats een eigen reverse proxy
> (Cloudflare Tunnel, Traefik) ervoor en laat het op localhost.

Check (vanaf de host zelf):

```bash
docker compose ps                          # alle services up?
docker compose logs -f app                 # gunicorn-output
curl -k https://127.0.0.1/api/health       # verwacht: {"status":"ok"}
```

---

## Stap 4 — Config invullen

`config.json` zit in het named volume `kluisjesbeheer_app-data`. Bewerken
vanaf de host:

```bash
# Vind de host-locatie van het volume
docker volume inspect kluisjesbeheer_app-data --format '{{ .Mountpoint }}'
# -> /var/lib/docker/volumes/kluisjesbeheer_app-data/_data

# Bewerk
sudo nano /var/lib/docker/volumes/kluisjesbeheer_app-data/_data/config.json
```

Vul `TenantId`, `ClientId`, `ClientSecret`, `RedirectUri`,
`AllowedOrigins`. **Niet wijzigen:** `SecretKey` (versleutelt Magister-
wachtwoord in DB).

Herstart de app-container zodat de nieuwe config geladen wordt:

```bash
docker compose restart app
```

---

## Stap 5 — Eerste login + Magister

Open `https://<server-ip>/` in de browser. Eerste login = automatisch
beheerder. Daarna *Beheer → Import* → Magister-koppeling invullen.

Voor de SWP-whitelist-aanvraag heb je het uitgaande server-IP nodig:

```bash
curl -s https://ifconfig.me
```

---

## Onderhoud

| Commando | Wat |
|---|---|
| `docker compose ps` | service-status |
| `docker compose logs -f app` | app-logs (gunicorn + cron) |
| `docker compose logs -f nginx` | nginx-logs |
| `docker compose pull && docker compose up -d` | update naar nieuwste image |
| `docker compose restart app` | app herstarten (na config-wijziging) |
| `docker compose down` | stop alles (volumes blijven) |
| `docker compose down -v` | ⚠️ stop alles **+ data weg** (alleen voor reset) |

**Backups** worden door de in-app scheduler in het volume gezet
(`/var/lib/docker/volumes/kluisjesbeheer_app-data/_data/backups/`).
Voeg eventueel een host-cron toe die deze map dagelijks naar je
backup-doelwit kopieert.

---

## TLS vervangen (productie)

Default is self-signed. Echte cert plaatsen:

```bash
# Stop nginx, vervang cert + key in het volume, herstart
docker compose stop nginx
docker run --rm -v kluisjesbeheer_nginx-ssl:/ssl alpine sh -c '
    rm /ssl/self.crt /ssl/self.key
'
# Plaats jouw cert + key in het volume:
docker run --rm -v kluisjesbeheer_nginx-ssl:/ssl -v $PWD:/in alpine sh -c '
    cp /in/jouw-cert.crt /ssl/self.crt
    cp /in/jouw-key.key  /ssl/self.key
    chmod 644 /ssl/self.crt && chmod 600 /ssl/self.key
'
docker compose up -d nginx
```

---

## Troubleshooting

| Symptoom | Oplossing |
|---|---|
| `docker compose up` faalt met `image not found` | Image is privé op GHCR — log in (`docker login ghcr.io`) of bouw lokaal (zie stap 2 optie B) |
| App-container restart-loopt | `docker compose logs app` — meestal ontbreekt een veld in `config.json` of klopt `RedirectUri` niet |
| Browser: `redirect_uri_mismatch` | `RedirectUri` in `config.json` moet exact matchen met wat in de Entra app-registration staat |
| Browser: "Niet beveiligd" (self-signed) | Klik *Geavanceerd → Doorgaan*. Voor productie: vervang cert (zie hierboven) |
| Cron-sync werkt niet | `docker compose exec app crontab -l` (geeft cron-job); `docker compose exec app /usr/local/bin/python /opt/kluisjesbeheer/backend/cron_sync.py` voor handmatige test |
| 502 Bad Gateway na login | Onverwacht — proxy-buffers staan al op 16k in `docker/nginx.conf`. Check `docker compose logs app` voor stacktrace |
