# Kluisjesbeheer — Documentatie

Kluisjesbeheer is een webapplicatie voor het beheren van schoolkluisjes. Gebouwd als vervanging van de Magister kluismodule, met ondersteuning voor meerdere vestigingen, rolverdeling en automatische leerlingensynchronisatie.

## Inhoud

| Pagina | Beschrijving |
|--------|-------------|
| [Systeemeisen](systeemeisen.md) | Server, Entra ID en Magister API vereisten |
| [Installatie](installatie.md) | Server inrichten, config invullen, NGINX configureren |
| [Configuratie](configuratie.md) | Eerste gebruik via de app: instellingen, import, gebruikers |
| [Architectuur](architectuur.md) | Technisch overzicht, stack, database, encryptie |
| [Onderhoud](onderhoud.md) | Logs, updates, cronjobs, troubleshooting |

## Quickstart

```
1. Server inrichten (Debian 12, Python 3.11+, NGINX)
2. bash deploy.sh
3. config.json invullen (Entra ID + SecretKey)
4. NGINX configureren + service starten
5. Inloggen -> eerste gebruiker wordt automatisch beheerder
6. Instellingen -> Import -> Vestigingen -> Gebruikers
```

Zie [Installatie](installatie.md) voor de volledige stappen.
