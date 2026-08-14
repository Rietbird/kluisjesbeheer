"""Schooljaar-grenzen op een plek.

Gebruikt door de API (voorstel bij een nieuwe toewijzing) en door de dagelijkse
sync (doorlopende huren meetrekken naar het nieuwe schooljaar), dus dit staat
los van Flask: de cron draait buiten een request-context.
"""
import re
from datetime import date, timedelta

# 1 augustus tot en met 31 juli. Dat is de grens waar de rest van het systeem al
# op draait: Magister kantelt op 1 augustus de klassen, de leerlingsync markeert
# dan de vertrekkers en de voorinschrijving-bescherming loopt tot dan. De grens
# valt bovendien altijd in de zomervakantie, dus een huurperiode verspringt
# nooit terwijl er leerlingen op school zijn.
STANDAARD_VAN = '08-01'
STANDAARD_TOT = '07-31'


def huidig_schooljaar(vandaag=None):
    d = vandaag or date.today()
    if d.month >= 8:
        return f'{d.year}-{d.year + 1}'
    return f'{d.year - 1}-{d.year}'


def maanddag(waarde, standaard):
    """Accepteer een MM-DD-instelling, val bij onzin terug op de standaard.

    Een kapotte instelling mag nooit als datum in het toewijsformulier landen.
    """
    waarde = (waarde or '').strip()
    if not re.fullmatch(r'\d{2}-\d{2}', waarde):
        return standaard
    maand, dag = int(waarde[:2]), int(waarde[3:])
    if not (1 <= maand <= 12 and 1 <= dag <= 31):
        return standaard
    return waarde


def periode_voor(db, vandaag=None):
    """Geeft (schooljaar, periode_van, periode_tot) voor het huidige schooljaar."""
    rows = db.execute(
        "SELECT key, value FROM instellingen WHERE key IN ('standaard_periode_van', 'standaard_periode_tot')"
    ).fetchall()
    cfg = {r['key']: r['value'] for r in rows}

    sj = huidig_schooljaar(vandaag)
    start_jaar, eind_jaar = sj.split('-')
    van = maanddag(cfg.get('standaard_periode_van'), STANDAARD_VAN)
    tot = maanddag(cfg.get('standaard_periode_tot'), STANDAARD_TOT)
    return sj, f'{start_jaar}-{van}', f'{eind_jaar}-{tot}'


def schooljaar_van_vertrek(vertrokken_op):
    """Het schooljaar waarin een leerling van school ging.

    De dagelijkse sync markeert vertrekkers op de dag dat ze uit de actieve
    Magister-lijst vallen, en dat is bij de jaarwisseling 1 augustus. Zo iemand
    heeft het vorige jaar gewoon afgemaakt, dus die hoort bij het jaar dat net
    eindigde en niet bij het jaar dat diezelfde dag begint. Daarom telt de dag
    vóór de vertrekdatum.

    Geeft None als er geen vertrekdatum is (huurders zonder stamnummer hebben
    er nooit een).
    """
    if not vertrokken_op:
        return None
    tekst = str(vertrokken_op).split(' ')[0].split('T')[0]
    try:
        d = date.fromisoformat(tekst)
    except ValueError:
        return None
    return huidig_schooljaar(d - timedelta(days=1))
