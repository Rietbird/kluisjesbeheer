# Beveiligingsbeleid

Bedankt dat je de moeite neemt om beveiligingsproblemen in Kluisjesbeheer
verantwoord te melden. We nemen meldingen serieus en behandelen ze met zorg.

## Een kwetsbaarheid melden

Meld kwetsbaarheden **privé** via GitHub, niet via een openbaar issue of een
pull request:

> **[Report a vulnerability](https://github.com/Rietbird/kluisjesbeheer/security/advisories/new)**
> (knop onder het tabblad **Security** → *Advisories*)

Zo blijft de melding besloten totdat er een fix beschikbaar is. Maak dus
**geen** publiek GitHub-issue aan voor beveiligingsproblemen.

Vermeld in je melding zoveel mogelijk van het volgende:

- een beschrijving van het probleem en de mogelijke impact;
- stappen om het te reproduceren (of een proof-of-concept);
- de getroffen versie / commit en je omgeving (OS, browser, deploy-methode);
- eventuele suggesties voor een oplossing.

## Wat je van ons mag verwachten

- **Ontvangstbevestiging** binnen ~5 werkdagen.
- Een inschatting en, waar nodig, vervolgvragen kort daarna.
- Een fix op `master` zodra de impact is bevestigd, plus een vermelding van
  jouw bijdrage in de release-notes als je dat op prijs stelt.
- We vragen je de melding besloten te houden tot er een fix beschikbaar is.

## Ondersteunde versies

Kluisjesbeheer is een rolling-release-applicatie zonder versie-tags. Alleen de
**laatste `master`** wordt ondersteund en krijgt beveiligingsfixes. Updaten doe
je op je eigen server met:

```bash
cd /root/kluisjesbeheer && git pull && bash install.sh
```

| Versie         | Ondersteund |
|----------------|-------------|
| `master` (HEAD)| ✅          |
| oudere commits | ❌          |

## Scope en eigen verantwoordelijkheid

Kluisjesbeheer is **zelf-gehost**: elke school draait een eigen instance met
eigen configuratie (Entra ID, Magister-koppeling, TLS-certificaat, NGINX). Een
groot deel van de beveiliging hangt daarom af van een correcte installatie en
een actuele server.

Houd in elk geval het volgende up-to-date en goed geconfigureerd:

- de applicatie zelf (`git pull && bash install.sh`);
- het onderliggende OS en NGINX;
- TLS (gebruik een geldig certificaat, geen self-signed in productie);
- de Entra ID Enterprise Application met *"Assignment required: Yes"*.

Meldingen over de **code in deze repository** zijn welkom via het kanaal
hierboven. Configuratie- of infrastructuurproblemen van een specifieke
installatie horen bij de beheerder van die school.
