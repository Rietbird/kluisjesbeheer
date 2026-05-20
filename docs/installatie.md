# Installatie

## Vooraf

Zorg dat je de volgende gegevens bij de hand hebt (zie [Systeemeisen](systeemeisen.md)):

- Entra ID: TenantId, ClientId, ClientSecret (+ *"Assignment required: Yes"* op de Enterprise App, met gebruikers/groepen toegewezen)
- Een HTTPS-domein (bijv. `kluisjes.jouwschool.nl`)
- Servertoegang (SSH als root)

De Magister API-koppeling is optioneel en kan later via de app worden ingesteld.

## Stap 1: Bestanden op de server zetten

```bash
scp -r kluisjesbeheer/ root@[server-ip]:/opt/
```

## Stap 2: Deploy script draaien

```bash
cd /opt/kluisjesbeheer
bash deploy.sh
```

Dit doet het volgende:
- Installeert Python- en Node.js-dependencies
- Bouwt de frontend (React/Vite)
- Maakt een systemd service aan (`kluisjesbeheer.service`)
- Maakt een `kluisjes` gebruiker en groep aan
- Start de app

## Stap 3: config.json invullen

```bash
cp /opt/kluisjesbeheer/backend/config.example.json /opt/kluisjesbeheer/backend/config.json
nano /opt/kluisjesbeheer/backend/config.json
```

**Minimale configuratie — alleen deze velden zijn vereist:**

```json
{
  "TenantId": "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx",
  "ClientId": "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx",
  "ClientSecret": "je-client-secret",
  "RedirectUri": "https://kluisjes.jouwschool.nl/auth/callback",
  "SecretKey": "willekeurige-lange-string",
  "AllowedOrigins": ["https://kluisjes.jouwschool.nl"]
}
```

Genereer een veilige SecretKey:

```bash
python3 -c "import secrets; print(secrets.token_hex(32))"
```

Alle overige instellingen (schoolnaam, logo, kleur, Magister API) worden via de app geconfigureerd.

## Stap 4: NGINX configureren

Maak `/etc/nginx/sites-enabled/kluisjesbeheer`:

```nginx
server {
    listen 80;
    server_name kluisjes.jouwschool.nl;
    return 301 https://$host$request_uri;
}

server {
    listen 443 ssl;
    server_name kluisjes.jouwschool.nl;

    ssl_certificate /etc/nginx/ssl/cert.crt;
    ssl_certificate_key /etc/nginx/ssl/cert.key;

    client_max_body_size 16M;

    location /img/ {
        root /opt/kluisjesbeheer/frontend/dist;
        expires 1h;
        add_header Cache-Control "public";
    }

    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

Test en herlaad:

```bash
nginx -t && systemctl reload nginx
```

> **Alternatief:** gebruik een [Cloudflare tunnel](https://developers.cloudflare.com/cloudflare-one/connections/connect-apps/) naar `http://127.0.0.1:5000` in plaats van een eigen SSL-certificaat.

## Stap 5: Service starten

```bash
systemctl restart kluisjesbeheer
systemctl status kluisjesbeheer
```

De app is nu bereikbaar op `https://kluisjes.jouwschool.nl`.

## Stap 6: Backups configureren

De app maakt automatisch dagelijkse backups van de database (opgeslagen in `backend/backups/`). Dit werkt direct na de eerste start zonder extra configuratie.

Voor extra bescherming wordt aanbevolen om op de **Proxmox host** het backup-script `/usr/local/bin/backup-kluisjes.sh` in te richten:
- Dagelijks om 02:00 de database ophalen via `pct exec` + `pct pull`
- Wekelijks op zondag een volledige `vzdump` snapshot maken

Zie [Onderhoud > Backup](onderhoud.md#backup) voor details over de drie backuplagen en restore-procedures.

## Volgende stap

Ga naar [Configuratie](configuratie.md) voor de eerste inrichting via de app.
