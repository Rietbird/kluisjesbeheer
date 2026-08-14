from flask import Blueprint, jsonify, g, request, Response
from auth import login_required, user_vestiging_ids
from klas import KLAS_SQL
from config import config
import io
from datetime import date

dashboard_bp = Blueprint('dashboard', __name__, url_prefix='/api')


def _scope_report_vestiging(vestiging_id):
    """Conciërge mag alleen rapporten van eigen vestiging(en); beheerder = alles.
    Return (vestiging_id, error_or_None). Conciërge zonder filter → auto-scope
    naar de enige vestiging, of 403 bij meerdere (kies er één)."""
    allowed = user_vestiging_ids()
    if allowed is None:
        return vestiging_id, None
    if not allowed:
        return None, (jsonify({'error': 'Geen vestiging-toegang'}), 403)
    if vestiging_id:
        if int(vestiging_id) not in allowed:
            return None, (jsonify({'error': 'Geen toegang tot deze vestiging'}), 403)
        return vestiging_id, None
    if len(allowed) == 1:
        return str(next(iter(allowed))), None
    return None, (jsonify({'error': 'Kies een vestiging'}), 403)


@dashboard_bp.route('/dashboard/stats', methods=['GET'])
@login_required
def stats():
    allowed = user_vestiging_ids()
    where, wparams = '', []
    if allowed is not None:
        if not allowed:
            return jsonify([])
        where = 'WHERE v.id IN (%s)' % ','.join('?' * len(allowed))
        wparams = list(allowed)
    rows = g.db.execute(f'''
        SELECT v.id, v.naam,
            COUNT(k.id) as totaal,
            SUM(CASE WHEN k.status='uitgeleend' THEN 1 ELSE 0 END) as uitgeleend,
            SUM(CASE WHEN k.status='vrij' AND k.geen_sleutel=0 THEN 1 ELSE 0 END) as vrij,
            SUM(CASE WHEN k.is_defect=1 THEN 1 ELSE 0 END) as defect
        FROM vestigingen v
        LEFT JOIN kluisjes k ON k.vestiging_id = v.id AND k.verwijderd = 0
        {where}
        GROUP BY v.id
        ORDER BY v.naam
    ''', wparams).fetchall()

    result = []
    for r in rows:
        vid = r['id']

        # Count lockers where key was not returned
        sleutel_count = g.db.execute('''
            SELECT COUNT(DISTINCT k.id) as cnt
            FROM kluisjes k
            JOIN toewijzingen t ON k.id = t.kluisje_id
            WHERE k.vestiging_id = ? AND k.verwijderd = 0
              AND k.status = 'vrij' AND t.actief = 0
              AND t.sleutel_ingeleverd = 0
              AND t.id = (SELECT MAX(t2.id) FROM toewijzingen t2 WHERE t2.kluisje_id = k.id)
        ''', (vid,)).fetchone()['cnt']

        # Borg stats for active assignments
        borg_row = g.db.execute('''
            SELECT
                COALESCE(SUM(t.borgbedrag), 0) as borg_totaal,
                COALESCE(SUM(CASE WHEN t.borg_betaald = 1 THEN t.borgbedrag ELSE 0 END), 0) as borg_ontvangen,
                SUM(CASE WHEN t.borg_betaald = 0 AND t.borgbedrag > 0 THEN 1 ELSE 0 END) as borg_niet_betaald
            FROM toewijzingen t
            JOIN kluisjes k ON t.kluisje_id = k.id
            WHERE k.vestiging_id = ? AND k.verwijderd = 0 AND t.actief = 1
        ''', (vid,)).fetchone()

        # Borg not yet returned (inactive assignments)
        borg_retour = g.db.execute('''
            SELECT
                SUM(CASE WHEN t.borg_betaald = 1 AND t.borg_teruggestort = 0 THEN 1 ELSE 0 END) as borg_niet_terug
            FROM toewijzingen t
            JOIN kluisjes k ON t.kluisje_id = k.id
            WHERE k.vestiging_id = ? AND k.verwijderd = 0 AND t.actief = 0
        ''', (vid,)).fetchone()

        result.append({
            'vestiging_id': vid,
            'vestiging_naam': r['naam'],
            'totaal': r['totaal'] or 0,
            'uitgeleend': r['uitgeleend'] or 0,
            'vrij': r['vrij'] or 0,
            'defect': r['defect'] or 0,
            'sleutel_niet_ingeleverd': sleutel_count,
            'borg_totaal': float(borg_row['borg_totaal'] or 0),
            'borg_ontvangen': float(borg_row['borg_ontvangen'] or 0),
            'borg_niet_betaald': borg_row['borg_niet_betaald'] or 0,
            'borg_niet_terug': borg_retour['borg_niet_terug'] or 0,
        })
    return jsonify(result)


def _get_rapport_data(report_type, vestiging_id, db):
    """Haal data op voor een rapport. Geeft (title, klassen_of_data, borg_actief, toon_sleutelnr) terug."""
    titles = {
        'sleutels': 'Openstaande sleutels',
        'borg': 'Openstaande borg',
        'toewijzingen': 'Actieve toewijzingen',
        'inname': 'Innameoverzicht sleutels/borg',
        'defect': 'Defecte kluisjes',
        'zonder_kluisje': 'Leerlingen zonder kluisje',
        'vertrokken': 'Vertrokken leerlingen (per schooljaar)',
    }
    title = titles.get(report_type, 'Rapport')

    borg_actief = True
    vestiging_naam = ''
    if vestiging_id:
        v_row = db.execute('SELECT borg_actief, naam FROM vestigingen WHERE id = ?', (int(vestiging_id),)).fetchone()
        borg_actief = bool(v_row and v_row['borg_actief'])
        vestiging_naam = v_row['naam'] if v_row else ''

    if report_type == 'defect':
        query = '''
            SELECT v.naam as vestiging, c.naam as cluster, k.kluisnummer, k.sleutelnummer,
                   k.locatie, k.opmerkingen
            FROM kluisjes k
            JOIN vestigingen v ON k.vestiging_id = v.id
            JOIN clusters c ON k.cluster_id = c.id
            WHERE k.verwijderd = 0 AND k.is_defect = 1
        '''
        params = []
        if vestiging_id:
            query += ' AND k.vestiging_id = ?'
            params.append(int(vestiging_id))
        query += ' ORDER BY v.naam, k.kluisnummer'
        rows = db.execute(query, params).fetchall()
        return title, rows, borg_actief, vestiging_naam

    elif report_type == 'sleutels':
        query = f'''
            SELECT v.naam as vestiging, k.kluisnummer, k.sleutelnummer,
                   t.leerling_naam, t.leerling_stamnr,
                   {KLAS_SQL} as leerling_klas,
                   t.periode_tot, t.einddatum,
                   l.vertrokken_op
            FROM kluisjes k
            JOIN vestigingen v ON k.vestiging_id = v.id
            JOIN toewijzingen t ON k.id = t.kluisje_id
            LEFT JOIN leerlingen l ON t.leerling_stamnr = l.stamnr
            WHERE k.verwijderd = 0 AND k.status = 'vrij'
              AND t.actief = 0 AND t.sleutel_ingeleverd = 0
              AND t.id = (SELECT MAX(t2.id) FROM toewijzingen t2 WHERE t2.kluisje_id = k.id)
        '''
        params = []
        if vestiging_id:
            query += ' AND k.vestiging_id = ?'
            params.append(int(vestiging_id))
        query += ' ORDER BY v.naam, k.kluisnummer'
        rows = db.execute(query, params).fetchall()
        return title, rows, borg_actief, vestiging_naam

    elif report_type == 'borg':
        query = f'''
            SELECT v.naam as vestiging, k.kluisnummer,
                   t.leerling_naam, t.leerling_stamnr,
                   {KLAS_SQL} as leerling_klas,
                   t.borgbedrag, t.borg_betaald, t.borg_teruggestort, t.actief,
                   l.vertrokken_op
            FROM toewijzingen t
            JOIN kluisjes k ON t.kluisje_id = k.id
            JOIN vestigingen v ON k.vestiging_id = v.id
            LEFT JOIN leerlingen l ON t.leerling_stamnr = l.stamnr
            WHERE k.verwijderd = 0 AND t.borgbedrag > 0
              AND ((t.actief = 1 AND t.borg_betaald = 0) OR (t.actief = 0 AND t.borg_betaald = 1 AND t.borg_teruggestort = 0))
        '''
        params = []
        if vestiging_id:
            query += ' AND k.vestiging_id = ?'
            params.append(int(vestiging_id))
        query += ' ORDER BY v.naam, k.kluisnummer'
        rows = db.execute(query, params).fetchall()
        return title, rows, borg_actief, vestiging_naam

    elif report_type == 'vertrokken':
        # Historie van iedereen die van school is en een kluisje had, inclusief
        # de al afgehandelde gevallen: de vraag is niet alleen wie nog een
        # sleutel heeft, maar ook wat er met de rest gebeurd is.
        #
        # Rijen zonder bijbehorende leerling staan er bewust in: die zijn
        # nergens als vertrokken te markeren en zouden anders nooit opduiken.
        #
        # De klas is hier expres de MOMENTOPNAME van de toewijzing, niet de
        # actuele: een vertrekker heeft geen actuele klas meer, en je zoekt hem
        # op onder de klas waarin hij zat toen hij het kluisje had.
        query = '''
            SELECT v.naam as vestiging, k.kluisnummer, k.sleutelnummer,
                   t.leerling_naam, t.leerling_stamnr,
                   COALESCE(NULLIF(TRIM(t.leerling_klas), ''), l.klas, '') as leerling_klas,
                   t.periode_tot, t.einddatum, t.actief, l.vertrokken_op,
                   CASE WHEN t.actief = 0 AND t.sleutel_ingeleverd = 1
                        THEN 1 ELSE 0 END as sleutel_terug,
                   CASE WHEN l.stamnr IS NULL THEN 1 ELSE 0 END as onbekend
            FROM toewijzingen t
            JOIN kluisjes k ON t.kluisje_id = k.id
            JOIN vestigingen v ON k.vestiging_id = v.id
            LEFT JOIN leerlingen l ON t.leerling_stamnr = l.stamnr
            WHERE k.verwijderd = 0
              AND (l.vertrokken_op IS NOT NULL OR (l.stamnr IS NULL AND t.actief = 1))
        '''
        params = []
        if vestiging_id:
            query += ' AND k.vestiging_id = ?'
            params.append(int(vestiging_id))
        query += ' ORDER BY leerling_klas, t.leerling_naam'
        rows = db.execute(query, params).fetchall()
        return title, rows, borg_actief, vestiging_naam

    elif report_type == 'zonder_kluisje':
        # Students in leerlingen table without an active toewijzing (exclude vertrokken)
        query = '''
            SELECT l.naam, l.stamnr, l.klas, l.leerjaar, l.studie, l.locatie
            FROM leerlingen l
            WHERE l.vertrokken_op IS NULL AND NOT EXISTS (
                SELECT 1 FROM toewijzingen t
                WHERE t.leerling_stamnr = l.stamnr AND t.actief = 1
            )
        '''
        params = []
        if vestiging_id:
            # Filter by locaties linked to this vestiging
            query += ''' AND l.locatie IN (
                SELECT locatie FROM vestigingen_locaties WHERE vestiging_id = ?
            )'''
            params.append(int(vestiging_id))
        query += ' ORDER BY l.klas, l.naam'
        rows = db.execute(query, params).fetchall()
        return title, rows, borg_actief, vestiging_naam

    else:  # toewijzingen + inname
        query = f'''
            SELECT t.leerling_naam,
                   {KLAS_SQL} as leerling_klas,
                   t.leerling_stamnr,
                   k.kluisnummer, k.sleutelnummer,
                   t.periode_van, t.periode_tot, t.borgbedrag, t.borg_betaald,
                   l.vertrokken_op
            FROM toewijzingen t
            JOIN kluisjes k ON t.kluisje_id = k.id
            LEFT JOIN leerlingen l ON t.leerling_stamnr = l.stamnr
            WHERE k.verwijderd = 0 AND t.actief = 1
        '''
        params = []
        if vestiging_id:
            query += ' AND k.vestiging_id = ?'
            params.append(int(vestiging_id))
        query += ' ORDER BY leerling_klas, t.leerling_naam'
        rows = db.execute(query, params).fetchall()
        # Determine if sleutelnummer is always equal to kluisnummer (hide if so)
        return title, rows, borg_actief, vestiging_naam, True


def _get_klas_rapport_data(vestiging_id, klassen, db):
    """Per-klas overzicht: {klasnaam: [rij, ...]}, één rij per leerling.

    Iedereen uit de klas staat er precies één keer in, met een leeg kluisveld
    als hij er geen heeft. Zo is de uitdraai regel voor regel naast de papieren
    klassenlijst te leggen, want die bevat de hele klas.

    `klassen` is een lijst met gekozen klassen; leeg betekent alle klassen die
    in deze vestiging een actieve huurder hebben (zelfde set als de
    filter-dropdown). Een expliciet gekozen klas komt altijd terug, ook als
    niemand daar een kluisje heeft: dat lege geval is juist wat je zoekt.
    """
    klassen = [k for k in (klassen or []) if k]
    params = [int(vestiging_id)]
    klas_filter = ''
    if klassen:
        placeholders = ','.join('?' * len(klassen))
        klas_filter = f' AND {KLAS_SQL} IN ({placeholders})'
        params.extend(klassen)
    met_rows = db.execute(f'''
        SELECT {KLAS_SQL} AS klas, t.leerling_naam AS naam, t.leerling_stamnr AS stamnr,
               k.kluisnummer, k.sleutelnummer, t.periode_van, t.periode_tot,
               l.vertrokken_op
        FROM toewijzingen t
        JOIN kluisjes k ON t.kluisje_id = k.id
        LEFT JOIN leerlingen l ON t.leerling_stamnr = l.stamnr
        WHERE k.verwijderd = 0 AND t.actief = 1 AND k.vestiging_id = ?{klas_filter}
        ORDER BY klas, t.leerling_naam
    ''', params).fetchall()

    if klassen:
        # Gekozen volgorde aanhouden, dubbelingen eruit.
        volgorde = list(dict.fromkeys(klassen))
    else:
        volgorde = []
        for r in met_rows:
            kn = r['klas'] or '-'
            if kn not in volgorde:
                volgorde.append(kn)

    result = {}
    for kn in volgorde:
        # Vertrekkers zijn van school en horen dus niet bij de nieuwe klas. Dit
        # overzicht is een momentopname van nu; hun historie, inclusief of de
        # sleutel terug is, staat in het rapport 'vertrokken'.
        rijen = [dict(r) for r in met_rows
                 if (r['klas'] or '-') == kn and not r['vertrokken_op']]
        if kn != '-':
            # Klasgenoten zonder kluisje erbij, met lege kluisvelden.
            zonder = db.execute('''
                SELECT l.naam, l.stamnr
                FROM leerlingen l
                WHERE l.klas = ? AND l.vertrokken_op IS NULL
                  AND NOT EXISTS (
                    SELECT 1 FROM toewijzingen t WHERE t.leerling_stamnr = l.stamnr AND t.actief = 1)
                ORDER BY l.naam
            ''', (kn,)).fetchall()
            for r in zonder:
                rijen.append({
                    'klas': kn, 'naam': r['naam'], 'stamnr': r['stamnr'],
                    'kluisnummer': '', 'sleutelnummer': '',
                    'periode_van': '', 'periode_tot': '', 'vertrokken_op': None,
                })
        rijen.sort(key=lambda r: (r['naam'] or '').lower())
        result[kn] = rijen
    return result


def _klas_titel(klassen):
    """Titel voor het per-klas rapport.

    Bij 'alles selecteren' stond elke klasnaam in de titelbalk, wat een
    onleesbare regel gaf. Vanaf vier klassen dus alleen het aantal.
    """
    if not klassen:
        return 'Kluisjes per klas'
    if len(klassen) <= 3:
        return 'Kluisjes per klas - ' + ', '.join(klassen)
    return f'Kluisjes per klas ({len(klassen)} klassen)'


ONBEKEND_IN_MAGISTER = 'Onbekend in Magister'


def _groepeer_vertrokken(rows):
    """Groepeer vertrekkers per schooljaar van vertrek, daarbinnen per klas.

    Nieuwste schooljaar bovenaan. Huurders zonder stamnummer hebben geen
    vertrekdatum en dus geen schooljaar; die vormen de laatste groep.
    """
    from schooljaar import schooljaar_van_vertrek
    groepen = {}
    for r in rows:
        sj = schooljaar_van_vertrek(r['vertrokken_op']) or ONBEKEND_IN_MAGISTER
        klas = r['leerling_klas'] or 'Klas onbekend'
        groepen.setdefault(sj, {}).setdefault(klas, []).append(r)
    volgorde = sorted((s for s in groepen if s != ONBEKEND_IN_MAGISTER), reverse=True)
    if ONBEKEND_IN_MAGISTER in groepen:
        volgorde.append(ONBEKEND_IN_MAGISTER)
    return {s: groepen[s] for s in volgorde}


def _sleutel_status(row):
    """Twee waarden: de sleutel is terug, of hij is dat niet.

    Een huur die nog loopt is nooit afgesloten, dus die sleutel is ook niet
    ingeleverd. Dat telt hier hetzelfde als een afgesloten huur waarbij hij
    niet terugkwam.
    """
    return 'ingeleverd' if row['sleutel_terug'] else 'NIET ingeleverd'


def _register_font():
    """Registreer DejaVuSans voor Unicode-ondersteuning (accenten etc.)."""
    try:
        from reportlab.pdfbase import pdfmetrics
        from reportlab.pdfbase.ttfonts import TTFont
        import os
        font_path = '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'
        bold_path = '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'
        if os.path.exists(font_path):
            pdfmetrics.registerFont(TTFont('DejaVu', font_path))
            if os.path.exists(bold_path):
                pdfmetrics.registerFont(TTFont('DejaVu-Bold', bold_path))
            return 'DejaVu', 'DejaVu-Bold'
    except Exception:
        pass
    return 'Helvetica', 'Helvetica-Bold'


@dashboard_bp.route('/dashboard/rapport/preview', methods=['GET'])
@login_required
def rapport_preview():
    """HTML preview van een rapport."""
    import html as htmllib
    report_type = request.args.get('type', 'inname')
    vestiging_id = request.args.get('vestiging_id')
    vestiging_id, err = _scope_report_vestiging(vestiging_id)
    if err: return err
    today = date.today().strftime('%d-%m-%Y')

    if report_type == 'klas':
        from urllib.parse import quote
        klassen = [k for k in request.args.getlist('klas') if k]
        data = _get_klas_rapport_data(vestiging_id, klassen, g.db)
        def e(v):
            return htmllib.escape(str(v) if v else '')
        kleur = config.get('SchoolKleur', '#FF8200')
        title = _klas_titel(klassen)
        secties = ''
        def klas_tabel(rows):
            h = '<table><thead><tr><th>Naam</th><th>Stamnr</th><th class="nr">Kluisnr</th><th class="nr">Sleutelnr</th></tr></thead><tbody>'
            for i, r in enumerate(rows):
                rc = 'alt' if i % 2 else ''
                h += (f'<tr class="{rc}"><td class="naam">{e(r["naam"])}</td><td>{e(r["stamnr"])}</td>'
                      f'<td class="nr">{e(r["kluisnummer"])}</td><td class="nr">{e(r["sleutelnummer"])}</td></tr>')
            return h + '</tbody></table>'

        for kn, rijen in data.items():
            zonder = sum(1 for r in rijen if not r['kluisnummer'])
            meervoud = 'en' if len(rijen) != 1 else ''
            secties += '<section class="klas">'
            secties += f'<h3>Klas: {e(kn)} <span>({len(rijen)} leerling{meervoud}, {zonder} zonder kluisje)</span></h3>'
            secties += klas_tabel(rijen)
            secties += '</section>'
        if not data:
            secties = '<p>Geen klassen met huurders gevonden.</p>'
        pdf_url = ('/api/dashboard/rapport?type=klas'
                   + (f'&vestiging_id={vestiging_id}' if vestiging_id else '')
                   + ''.join(f'&klas={htmllib.escape(quote(k))}' for k in klassen))
        html_out = f'''<!DOCTYPE html><html lang="nl"><head><meta charset="utf-8"><title>{e(title)}</title>
<style>
  body {{ font-family: Arial, sans-serif; font-size: 13px; margin: 0; background: #f8fafc; color: #1e293b; }}
  .toolbar {{ background: #1e3a5f; color: white; padding: 12px 24px; display: flex; align-items: center; gap: 16px; position: sticky; top: 0; }}
  .toolbar h1 {{ margin: 0; font-size: 16px; flex: 1; }}
  .toolbar a {{ background: {kleur}; color: white; padding: 7px 18px; border-radius: 6px; text-decoration: none; font-weight: bold; }}
  .content {{ max-width: 900px; margin: 24px auto; padding: 0 16px; }}
  h3 {{ color: #1e3a5f; font-size: 14px; margin: 24px 0 4px; }}
  h3 span {{ color: #64748b; font-weight: normal; }}
  h4 {{ color: #334155; font-size: 12px; margin: 10px 0 4px; }}
  table {{ width: 100%; border-collapse: collapse; margin-bottom: 8px; }}
  th {{ background: {kleur}; color: white; text-align: left; padding: 7px 10px; font-size: 12px; }}
  td {{ padding: 6px 10px; border-bottom: 1px solid #e2e8f0; font-size: 12px; }}
  tr.alt td {{ background: #fff7ed; }}
  @media print {{ .toolbar {{ display: none; }} body {{ background: white; }} .content {{ margin: 0; max-width: 100%; }} table {{ page-break-inside: avoid; }}
    /* Elke klas op een eigen bladzijde, ook bij printen vanuit deze preview. */
    .klas {{ page-break-before: always; }} .klas:first-of-type {{ page-break-before: auto; }} }}
</style></head><body>
<div class="toolbar"><h1>Kluisjesbeheer - {e(title)}</h1><a href="{pdf_url}">Download PDF</a></div>
<div class="content"><p style="color:#64748b;font-size:12px">{e(config.get('SchoolNaam', ''))} - {today}</p>{secties}</div>
</body></html>'''
        return Response(html_out, mimetype='text/html; charset=utf-8')

    result = _get_rapport_data(report_type, vestiging_id, g.db)
    title, rows, borg_actief, vestiging_naam = result[0], result[1], result[2], result[3]
    toon_sleutelnr = result[4] if len(result) > 4 else True

    def e(v):
        return htmllib.escape(str(v) if v else '')

    if report_type == 'defect':
        tabel_html = '<table><thead><tr><th>Vestiging</th><th>Cluster</th><th class="nr">Kluisnr</th><th class="nr">Sleutelnr</th><th>Locatie</th><th>Opmerkingen</th></tr></thead><tbody>'
        for i, r in enumerate(rows):
            row_class = 'alt' if i % 2 else ''
            tabel_html += f'<tr class="{row_class}"><td>{e(r["vestiging"])}</td><td>{e(r["cluster"])}</td><td class="nr">{e(r["kluisnummer"])}</td><td class="nr">{e(r["sleutelnummer"])}</td><td>{e(r["locatie"])}</td><td>{e(r["opmerkingen"])}</td></tr>'
        tabel_html += '</tbody></table>'

    elif report_type == 'inname':
        # Groepeer per klas
        klassen = {}
        for r in rows:
            klas = r['leerling_klas'] or '-'
            klassen.setdefault(klas, []).append(r)

        sleutelnr_th = '<th class="nr">Sleutelnr</th>' if toon_sleutelnr else ''
        borg_th = '<th class="check">Borg</th>' if borg_actief else ''

        tabel_html = ''
        for klas, leerlingen in klassen.items():
            tabel_html += f'<h3>Klas: {e(klas)} <span>({len(leerlingen)} leerlingen)</span></h3>'
            tabel_html += f'<table><thead><tr><th>Naam</th><th class="nr">Kluisnr</th>{sleutelnr_th}<th class="check">Sleutel</th>{borg_th}</tr></thead><tbody>'
            for i, r in enumerate(leerlingen):
                sleutelnr_td = f'<td class="nr">{e(r["sleutelnummer"])}</td>' if toon_sleutelnr else ''
                borg_td = '<td class="check"></td>' if borg_actief else ''
                row_class = 'alt' if i % 2 else ''
                vertrokken_tag = ' <span style="color:#dc2626;font-size:10px;font-weight:bold">[Vertrokken]</span>' if r['vertrokken_op'] else ''
                tabel_html += f'<tr class="{row_class}"><td class="naam">{e(r["leerling_naam"])}{vertrokken_tag}</td><td class="nr">{e(r["kluisnummer"])}</td>{sleutelnr_td}<td class="check"></td>{borg_td}</tr>'
            tabel_html += '</tbody></table>'

    elif report_type in ('toewijzingen',):
        klassen = {}
        for r in rows:
            klas = r['leerling_klas'] or '-'
            klassen.setdefault(klas, []).append(r)

        extra_th = '<th>Borg</th><th>Borg betaald</th>' if borg_actief else ''
        sleutelnr_th = '<th>Sleutelnr</th>' if toon_sleutelnr else ''

        tabel_html = ''
        for klas, leerlingen in klassen.items():
            tabel_html += f'<h3>Klas: {e(klas)}</h3>'
            tabel_html += f'<table><thead><tr><th>Naam</th><th>Stamnr</th><th>Kluisnr</th>{sleutelnr_th}<th>Klas</th><th>Van</th><th>Tot</th>{extra_th}</tr></thead><tbody>'
            for i, r in enumerate(leerlingen):
                sleutelnr_td = f'<td>{e(r["sleutelnummer"])}</td>' if toon_sleutelnr else ''
                borg_bedrag_str = ('EUR ' + f'{r["borgbedrag"]:.2f}') if r['borgbedrag'] else ''
                borg_betaald_str = 'Ja' if r['borg_betaald'] else 'Nee'
                borg_tds = f'<td>{borg_bedrag_str}</td><td>{borg_betaald_str}</td>' if borg_actief else ''
                row_class = 'alt' if i % 2 else ''
                vertrokken_tag = ' <span style="color:#dc2626;font-size:10px;font-weight:bold">[Vertrokken]</span>' if r['vertrokken_op'] else ''
                tabel_html += f'<tr class="{row_class}"><td class="naam">{e(r["leerling_naam"])}{vertrokken_tag}</td><td>{e(r["leerling_stamnr"])}</td><td>{e(r["kluisnummer"])}</td>{sleutelnr_td}<td>{e(klas)}</td><td>{e(r["periode_van"])}</td><td>{e(r["periode_tot"])}</td>{borg_tds}</tr>'
            tabel_html += '</tbody></table>'
    elif report_type == 'vertrokken':
        tabel_html = ''
        for sj, klassen in _groepeer_vertrokken(rows).items():
            aantal = sum(len(v) for v in klassen.values())
            open_sleutels = sum(1 for v in klassen.values() for r in v if not r['sleutel_terug'])
            kop = e(sj) if sj == ONBEKEND_IN_MAGISTER else f'Schooljaar {e(sj)}'
            tabel_html += (f'<h2>{kop} <span>({aantal} leerlingen, '
                           f'{open_sleutels} sleutel niet ingeleverd)</span></h2>')
            for klas, leerlingen in klassen.items():
                tabel_html += f'<h3>Klas: {e(klas)} <span>({len(leerlingen)})</span></h3>'
                tabel_html += '<table><thead><tr><th>Naam</th><th>Stamnr</th><th class="nr">Kluisnr</th><th class="nr">Sleutelnr</th><th>Vertrokken</th><th>Sleutel</th></tr></thead><tbody>'
                for i, r in enumerate(leerlingen):
                    row_class = 'alt' if i % 2 else ''
                    vertrek = 'niet in Magister' if r['onbekend'] else e(r['vertrokken_op'])
                    status = _sleutel_status(r)
                    kleur = '' if r['sleutel_terug'] else ' style="color:#dc2626;font-weight:bold"'
                    tabel_html += (f'<tr class="{row_class}"><td class="naam">{e(r["leerling_naam"])}</td>'
                                   f'<td>{e(r["leerling_stamnr"])}</td><td class="nr">{e(r["kluisnummer"])}</td>'
                                   f'<td class="nr">{e(r["sleutelnummer"])}</td><td>{vertrek}</td>'
                                   f'<td{kleur}>{status}</td></tr>')
                tabel_html += '</tbody></table>'

    elif report_type == 'sleutels':
        tabel_html = '<table><thead><tr><th>Vestiging</th><th class="nr">Kluisnr</th><th class="nr">Sleutelnr</th><th>Laatste huurder</th><th>Stamnr</th><th>Klas</th><th>Periode tot</th><th>Status</th></tr></thead><tbody>'
        for i, r in enumerate(rows):
            row_class = 'alt' if i % 2 else ''
            vertrokken = '<span style="color:#dc2626;font-weight:bold">Vertrokken</span>' if r['vertrokken_op'] else ''
            tabel_html += f'<tr class="{row_class}"><td>{e(r["vestiging"])}</td><td class="nr">{e(r["kluisnummer"])}</td><td class="nr">{e(r["sleutelnummer"])}</td><td class="naam">{e(r["leerling_naam"])}</td><td>{e(r["leerling_stamnr"])}</td><td>{e(r["leerling_klas"])}</td><td>{e(r["periode_tot"])}</td><td>{vertrokken}</td></tr>'
        tabel_html += '</tbody></table>'

    elif report_type == 'borg':
        tabel_html = '<table><thead><tr><th>Vestiging</th><th class="nr">Kluisnr</th><th>Leerling</th><th>Stamnr</th><th>Klas</th><th>Borg</th><th>Betaald</th><th>Teruggestort</th><th>Actief</th><th>Status</th></tr></thead><tbody>'
        for i, r in enumerate(rows):
            row_class = 'alt' if i % 2 else ''
            borg_str = f'EUR {r["borgbedrag"]:.2f}' if r['borgbedrag'] else ''
            vertrokken = '<span style="color:#dc2626;font-weight:bold">Vertrokken</span>' if r['vertrokken_op'] else ''
            tabel_html += f'<tr class="{row_class}"><td>{e(r["vestiging"])}</td><td class="nr">{e(r["kluisnummer"])}</td><td class="naam">{e(r["leerling_naam"])}</td><td>{e(r["leerling_stamnr"])}</td><td>{e(r["leerling_klas"])}</td><td>{borg_str}</td><td>{"Ja" if r["borg_betaald"] else "Nee"}</td><td>{"Ja" if r["borg_teruggestort"] else "Nee"}</td><td>{"Ja" if r["actief"] else "Nee"}</td><td>{vertrokken}</td></tr>'
        tabel_html += '</tbody></table>'

    elif report_type == 'zonder_kluisje':
        klassen = {}
        for r in rows:
            klas = r['klas'] or '-'
            klassen.setdefault(klas, []).append(r)

        tabel_html = ''
        for klas, leerlingen in klassen.items():
            tabel_html += f'<h3>Klas: {e(klas)} <span>({len(leerlingen)} leerlingen)</span></h3>'
            tabel_html += '<table><thead><tr><th>Naam</th><th>Stamnr</th><th>Klas</th><th>Leerjaar</th><th>Studie</th></tr></thead><tbody>'
            for i, r in enumerate(leerlingen):
                row_class = 'alt' if i % 2 else ''
                tabel_html += f'<tr class="{row_class}"><td class="naam">{e(r["naam"])}</td><td>{e(r["stamnr"])}</td><td>{e(r["klas"])}</td><td>{e(r["leerjaar"])}</td><td>{e(r["studie"])}</td></tr>'
            tabel_html += '</tbody></table>'

    else:
        tabel_html = '<p>Preview niet beschikbaar voor dit rapporttype.</p>'

    pdf_url = f'/api/dashboard/rapport?type={report_type}' + (f'&vestiging_id={vestiging_id}' if vestiging_id else '')
    kleur = config.get('SchoolKleur', '#FF8200')

    html_out = f'''<!DOCTYPE html>
<html lang="nl">
<head>
<meta charset="utf-8">
<title>{e(title)}</title>
<style>
  body {{ font-family: Arial, sans-serif; font-size: 13px; margin: 0; background: #f8fafc; color: #1e293b; }}
  .toolbar {{ background: #1e3a5f; color: white; padding: 12px 24px; display: flex; align-items: center; gap: 16px; position: sticky; top: 0; z-index: 10; }}
  .toolbar h1 {{ margin: 0; font-size: 16px; flex: 1; }}
  .toolbar a {{ background: {kleur}; color: white; padding: 7px 18px; border-radius: 6px; text-decoration: none; font-size: 13px; font-weight: bold; }}
  .content {{ max-width: 900px; margin: 24px auto; padding: 0 16px; }}
  .meta {{ color: #64748b; font-size: 12px; margin-bottom: 20px; }}
  h3 {{ color: #1e3a5f; font-size: 14px; margin: 24px 0 6px; }}
  h3 span {{ color: #64748b; font-weight: normal; }}
  table {{ width: 100%; border-collapse: collapse; margin-bottom: 8px; }}
  th {{ background: {kleur}; color: white; text-align: left; padding: 7px 10px; font-size: 12px; }}
  td {{ padding: 6px 10px; border-bottom: 1px solid #e2e8f0; font-size: 12px; }}
  tr.alt td {{ background: #fff7ed; }}
  th.check, td.check {{ width: 70px; min-width: 70px; max-width: 70px; border-left: 2px solid #cbd5e1; text-align: center; }}
  th.nr, td.nr {{ width: 80px; min-width: 80px; max-width: 100px; }}
  td.naam {{ min-width: 160px; }}
  @media print {{
    .toolbar {{ display: none; }}
    body {{ background: white; }}
    .content {{ margin: 0; max-width: 100%; }}
    h3 {{ page-break-before: auto; }}
    table {{ page-break-inside: avoid; }}
  }}
</style>
</head>
<body>
<div class="toolbar">
  <h1>Kluisjesbeheer - {e(title)}</h1>
  <a href="{pdf_url}">Download PDF</a>
</div>
<div class="content">
  <p class="meta">{e(config.get('SchoolNaam', ''))} - {today} - {len(rows)} rijen</p>
  {tabel_html}
</div>
</body>
</html>'''

    return Response(html_out, mimetype='text/html; charset=utf-8')


@dashboard_bp.route('/dashboard/rapport', methods=['GET'])
@login_required
def rapport():
    """Export a PDF report. Query params: type (sleutels|borg|toewijzingen|inname), vestiging_id (optional)."""
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4, landscape
    from reportlab.lib.units import mm
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

    report_type = request.args.get('type', 'toewijzingen')
    vestiging_id = request.args.get('vestiging_id')
    vestiging_id, err = _scope_report_vestiging(vestiging_id)
    if err: return err
    today = date.today().strftime('%d-%m-%Y')

    font_normal, font_bold = _register_font()

    if report_type == 'klas':
        klassen = [k for k in request.args.getlist('klas') if k]
        data = _get_klas_rapport_data(vestiging_id, klassen, g.db)
        buf = io.BytesIO()
        doc = SimpleDocTemplate(buf, pagesize=A4, leftMargin=15*mm, rightMargin=15*mm,
                                topMargin=15*mm, bottomMargin=15*mm)
        page_w = A4[0] - 30*mm
        styles = getSampleStyleSheet()
        school_color = colors.HexColor(config.get('SchoolKleur', '#FF8200'))
        title_style = ParagraphStyle('KTitle', parent=styles['Title'], fontSize=16,
                                     fontName=font_bold, textColor=colors.HexColor('#1e3a5f'))
        klas_style = ParagraphStyle('KKlas', parent=styles['Normal'], fontSize=11,
                                    fontName=font_bold, textColor=colors.HexColor('#1e3a5f'),
                                    spaceBefore=8, spaceAfter=2)
        sub_style = ParagraphStyle('KSub', parent=styles['Normal'], fontSize=9,
                                   fontName=font_bold, textColor=colors.gray, spaceBefore=4)

        def ktable(data_rows, col_widths):
            t = Table(data_rows, colWidths=col_widths, repeatRows=1)
            t.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), school_color),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('FONTNAME', (0, 0), (-1, -1), font_normal),
                ('FONTNAME', (0, 0), (-1, 0), font_bold),
                ('FONTSIZE', (0, 0), (-1, -1), 9),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#FFF7ED')]),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#E2E8F0')),
                ('TOPPADDING', (0, 0), (-1, -1), 4),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
                ('LEFTPADDING', (0, 0), (-1, -1), 5),
                ('RIGHTPADDING', (0, 0), (-1, -1), 5),
            ]))
            return t

        title = _klas_titel(klassen)
        elements = [Paragraph(f"Kluisjesbeheer - {title}", title_style),
                    Paragraph(f"{config.get('SchoolNaam', '')} - {today}", sub_style),
                    Spacer(1, 6*mm)]
        if not data:
            elements.append(Paragraph("Geen klassen met huurders gevonden.", styles['Normal']))
        nr_w = 28*mm
        date_w = 26*mm
        kolommen = [page_w - 3*nr_w, nr_w, nr_w, nr_w]

        def klas_tabel(rows):
            mdata = [['Naam', 'Stamnr', 'Kluisnr', 'Sleutelnr']]
            for r in rows:
                mdata.append([r['naam'] or '', r['stamnr'] or '',
                              r['kluisnummer'] or '', r['sleutelnummer'] or ''])
            return ktable(mdata, kolommen)

        for index, (kn, rijen) in enumerate(data.items()):
            # Elke klas op een eigen bladzijde: de uitdraai gaat per klas naast
            # de papieren klassenlijst om met de hand na te lopen.
            if index:
                elements.append(PageBreak())
            zonder = sum(1 for r in rijen if not r['kluisnummer'])
            meervoud = 'en' if len(rijen) != 1 else ''
            elements.append(Paragraph(
                f"Klas: {kn}  ({len(rijen)} leerling{meervoud}, {zonder} zonder kluisje)",
                klas_style))
            elements.append(klas_tabel(rijen))
            elements.append(Spacer(1, 5*mm))
        doc.build(elements)
        buf.seek(0)
        if len(klassen) == 1:
            suffix = f'-{klassen[0]}'
        elif klassen:
            suffix = f'-{len(klassen)}klassen'
        else:
            suffix = '-alle'
        filename = f'kluisjes-klas{suffix}-{date.today().isoformat()}.pdf'
        return Response(buf.getvalue(), mimetype='application/pdf',
                        headers={'Content-Disposition': f'attachment; filename={filename}'})

    result = _get_rapport_data(report_type, vestiging_id, g.db)
    title, rows, borg_actief, vestiging_naam = result[0], result[1], result[2], result[3]
    toon_sleutelnr = result[4] if len(result) > 4 else True

    buf = io.BytesIO()
    portrait_types = ('inname', 'zonder_kluisje', 'vertrokken')
    page_size = A4 if report_type in portrait_types else landscape(A4)
    doc = SimpleDocTemplate(buf, pagesize=page_size,
                            leftMargin=15*mm, rightMargin=15*mm,
                            topMargin=15*mm, bottomMargin=15*mm)
    page_w = page_size[0] - 30*mm  # usable width

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle('RTitle', parent=styles['Title'], fontSize=16,
                                 fontName=font_bold, textColor=colors.HexColor('#1e3a5f'))
    subtitle_style = ParagraphStyle('RSub', parent=styles['Normal'], fontSize=9,
                                    fontName=font_normal, textColor=colors.gray)
    klas_style = ParagraphStyle('RKlas', parent=styles['Normal'], fontSize=9,
                                fontName=font_bold, textColor=colors.HexColor('#1e3a5f'),
                                spaceBefore=4, spaceAfter=2)
    school_color = colors.HexColor(config.get('SchoolKleur', '#FF8200'))

    is_portrait = report_type in portrait_types

    def make_table(data, col_widths=None, checkbox_cols=None):
        t = Table(data, colWidths=col_widths, repeatRows=1)
        fs_header = 9 if is_portrait else 7.5
        fs_body = 9 if is_portrait else 7
        pad = 5 if is_portrait else 3
        style_cmds = [
            ('BACKGROUND', (0, 0), (-1, 0), school_color),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, -1), font_normal),
            ('FONTNAME', (0, 0), (-1, 0), font_bold),
            ('FONTSIZE', (0, 0), (-1, 0), fs_header),
            ('FONTSIZE', (0, 1), (-1, -1), fs_body),
            ('ALIGN', (0, 0), (-1, 0), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#FFF7ED')]),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#E2E8F0')),
            ('TOPPADDING', (0, 0), (-1, -1), pad),
            ('BOTTOMPADDING', (0, 0), (-1, -1), pad),
            ('LEFTPADDING', (0, 0), (-1, -1), 4),
            ('RIGHTPADDING', (0, 0), (-1, -1), 4),
        ]
        if checkbox_cols:
            for col in checkbox_cols:
                style_cmds += [
                    ('LINEWIDTH', (col, 0), (col, -1), 1.5),
                    ('ALIGN', (col, 1), (col, -1), 'CENTER'),
                ]
        t.setStyle(TableStyle(style_cmds))
        return t

    elements = []
    elements.append(Paragraph(f"Kluisjesbeheer - {title}", title_style))
    elements.append(Paragraph(f"{config.get('SchoolNaam', '')} - {today}", subtitle_style))
    elements.append(Spacer(1, 8*mm))

    if report_type == 'defect':
        headers = ['Vestiging', 'Cluster', 'Kluisnr', 'Sleutelnr', 'Locatie', 'Opmerkingen']
        nr_w = 22*mm
        col_widths = [page_w*0.18, page_w*0.14, nr_w, nr_w, page_w*0.18, page_w - page_w*0.5 - 2*nr_w]
        data = [headers]
        for r in rows:
            data.append([r['vestiging'], r['cluster'], r['kluisnummer'],
                         r['sleutelnummer'] or '', r['locatie'] or '', r['opmerkingen'] or ''])
        if len(data) == 1:
            elements.append(Paragraph("Geen defecte kluisjes gevonden.", styles['Normal']))
        else:
            elements.append(Paragraph(f"{len(data)-1} kluisjes", subtitle_style))
            elements.append(Spacer(1, 3*mm))
            elements.append(make_table(data, col_widths=col_widths))

    elif report_type == 'sleutels':
        headers = ['Vestiging', 'Kluisnr', 'Sleutelnr', 'Laatste huurder', 'Stamnr', 'Klas', 'Per. tot', 'Einddatum', 'Status']
        nr_w = 20*mm
        date_w = 24*mm
        status_w = 22*mm
        fixed = 2*nr_w + nr_w + nr_w + 2*date_w + status_w
        rest = page_w - fixed
        col_widths = [rest*0.35, nr_w, nr_w, rest*0.65, nr_w, nr_w, date_w, date_w, status_w]
        data = [headers]
        vertrokken_style = ParagraphStyle('Vertrokken', parent=styles['Normal'],
                                          fontSize=7, fontName=font_bold,
                                          textColor=colors.HexColor('#DC2626'))
        for r in rows:
            status_cell = Paragraph('Vertrokken', vertrokken_style) if r['vertrokken_op'] else ''
            data.append([r['vestiging'], r['kluisnummer'], r['sleutelnummer'] or '',
                         r['leerling_naam'], r['leerling_stamnr'], r['leerling_klas'] or '',
                         r['periode_tot'] or '', r['einddatum'] or '', status_cell])
        if len(data) == 1:
            elements.append(Paragraph("Geen gegevens gevonden voor dit rapport.", styles['Normal']))
        else:
            elements.append(Paragraph(f"{len(data)-1} rijen", subtitle_style))
            elements.append(Spacer(1, 3*mm))
            elements.append(make_table(data, col_widths=col_widths))

    elif report_type == 'borg':
        headers = ['Vestiging', 'Kluisnr', 'Leerling', 'Stamnr', 'Klas', 'Borg', 'Betaald', 'Terug', 'Actief', 'Status']
        small_w = 16*mm
        nr_w = 20*mm
        borg_w = 22*mm
        status_w = 22*mm
        fixed = nr_w + nr_w + nr_w + borg_w + 3*small_w + status_w
        rest = page_w - fixed
        col_widths = [rest*0.4, nr_w, rest*0.6, nr_w, nr_w, borg_w, small_w, small_w, small_w, status_w]
        vertrokken_style = ParagraphStyle('VertrokkenBorg', parent=styles['Normal'],
                                          fontSize=7, fontName=font_bold,
                                          textColor=colors.HexColor('#DC2626'))
        data = [headers]
        for r in rows:
            status_cell = Paragraph('Vertrokken', vertrokken_style) if r['vertrokken_op'] else ''
            data.append([r['vestiging'], r['kluisnummer'], r['leerling_naam'],
                         r['leerling_stamnr'], r['leerling_klas'] or '',
                         f"EUR {r['borgbedrag']:.2f}",
                         'Ja' if r['borg_betaald'] else 'Nee',
                         'Ja' if r['borg_teruggestort'] else 'Nee',
                         'Ja' if r['actief'] else 'Nee', status_cell])
        if len(data) == 1:
            elements.append(Paragraph("Geen gegevens gevonden voor dit rapport.", styles['Normal']))
        else:
            elements.append(Paragraph(f"{len(data)-1} rijen", subtitle_style))
            elements.append(Spacer(1, 3*mm))
            elements.append(make_table(data, col_widths=col_widths))

    elif report_type == 'zonder_kluisje':
        if not rows:
            elements.append(Paragraph("Alle leerlingen hebben een kluisje.", styles['Normal']))
        else:
            klassen = {}
            for r in rows:
                klas = r['klas'] or '-'
                klassen.setdefault(klas, []).append(r)

            elements.append(Paragraph(f"{len(rows)} leerlingen", subtitle_style))
            elements.append(Spacer(1, 3*mm))

            for klas, leerlingen in klassen.items():
                elements.append(Paragraph(
                    f"Klas: {klas}  ({len(leerlingen)} leerlingen)", klas_style))
                elements.append(Spacer(1, 1*mm))
                data = [['Naam', 'Stamnr', 'Klas', 'Leerjaar', 'Studie']]
                small_w = 20*mm
                col_widths = [page_w - 4*small_w, small_w, small_w, small_w, small_w]
                for r in leerlingen:
                    data.append([r['naam'], r['stamnr'], r['klas'] or '', r['leerjaar'] or '', r['studie'] or ''])
                elements.append(make_table(data, col_widths=col_widths))
                elements.append(Spacer(1, 5*mm))

    elif report_type == 'vertrokken':
        if not rows:
            elements.append(Paragraph("Geen vertrokken leerlingen met een kluisje.", styles['Normal']))
        else:
            status_w = 28*mm
            nr_w = 22*mm
            datum_w = 26*mm
            stamnr_w = 20*mm
            naam_w = page_w - 2*nr_w - stamnr_w - datum_w - status_w
            col_widths = [naam_w, stamnr_w, nr_w, nr_w, datum_w, status_w]

            open_totaal = sum(1 for r in rows if not r['sleutel_terug'])
            elements.append(Paragraph(
                f"{len(rows)} leerlingen, {open_totaal} sleutel niet ingeleverd", subtitle_style))
            elements.append(Spacer(1, 3*mm))

            for index, (sj, klassen) in enumerate(_groepeer_vertrokken(rows).items()):
                # Elk schooljaar op een eigen bladzijde: dit is per jaar een
                # afgerond overzicht dat je los archiveert.
                if index:
                    elements.append(PageBreak())
                aantal = sum(len(v) for v in klassen.values())
                open_sleutels = sum(1 for v in klassen.values() for r in v if not r['sleutel_terug'])
                kop = sj if sj == ONBEKEND_IN_MAGISTER else f'Schooljaar {sj}'
                elements.append(Paragraph(
                    f"{kop}  ({aantal} leerlingen, {open_sleutels} sleutel niet ingeleverd)",
                    klas_style))
                for klas, leerlingen in klassen.items():
                    elements.append(Paragraph(f"Klas: {klas}  ({len(leerlingen)})", subtitle_style))
                    elements.append(Spacer(1, 1*mm))
                    data = [['Naam', 'Stamnr', 'Kluisnr', 'Sleutelnr', 'Vertrokken', 'Sleutel']]
                    for r in leerlingen:
                        vertrek = 'niet in Magister' if r['onbekend'] else (r['vertrokken_op'] or '')
                        data.append([r['leerling_naam'], r['leerling_stamnr'] or '',
                                     r['kluisnummer'], r['sleutelnummer'] or '', vertrek,
                                     _sleutel_status(r)])
                    elements.append(make_table(data, col_widths=col_widths))
                    elements.append(Spacer(1, 5*mm))

    elif report_type == 'inname':
        if not rows:
            elements.append(Paragraph("Geen gegevens gevonden voor dit rapport.", styles['Normal']))
        else:
            # Kolom labels kort houden zodat ze passen
            sleutel_label = 'Sleutel'
            borg_label = 'Borg'
            # Breedtes afhankelijk van aantal checkboxkolommen
            n_check = 1 + (1 if borg_actief else 0)
            n_nr = 1 + (1 if toon_sleutelnr else 0)  # kluisnr + evt sleutelnr
            check_w = 22*mm  # vaste breedte voor afvinkkolom
            nr_w = 20*mm     # vaste breedte voor nummers
            naam_w = page_w - n_nr * nr_w - n_check * check_w

            col_defs = [('Naam', naam_w), ('Kluisnr', nr_w)]
            if toon_sleutelnr:
                col_defs.append(('Sleutelnr', nr_w))
            col_defs.append((sleutel_label, check_w))
            if borg_actief:
                col_defs.append((borg_label, check_w))
            col_headers = [c[0] for c in col_defs]
            col_widths = [c[1] for c in col_defs]
            checkbox_cols = [i for i, c in enumerate(col_headers) if c in (sleutel_label, borg_label)]

            # Group by klas
            klassen = {}
            for r in rows:
                klas = r['leerling_klas'] or '-'
                klassen.setdefault(klas, []).append(r)

            total = len(rows)
            elements.append(Paragraph(f"{total} leerlingen", subtitle_style))
            elements.append(Spacer(1, 3*mm))

            for klas, leerlingen in klassen.items():
                elements.append(Paragraph(
                    f"Klas: {klas}  ({len(leerlingen)} leerlingen)", klas_style))
                elements.append(Spacer(1, 1*mm))
                data = [col_headers]
                for r in leerlingen:
                    naam = r['leerling_naam']
                    if r['vertrokken_op']:
                        naam += ' [V]'
                    row_data = [naam, r['kluisnummer']]
                    if toon_sleutelnr:
                        row_data.append(r['sleutelnummer'] or '')
                    row_data.append('')  # Sleutel ingeleverd checkbox
                    if borg_actief:
                        row_data.append('')  # Borg betaald checkbox
                    data.append(row_data)
                elements.append(make_table(data, col_widths=col_widths, checkbox_cols=checkbox_cols))
                elements.append(Spacer(1, 5*mm))

    else:  # toewijzingen
        if not rows:
            elements.append(Paragraph("Geen gegevens gevonden voor dit rapport.", styles['Normal']))
        else:
            nr_w = 20*mm
            date_w = 22*mm
            klas_w = 18*mm
            borg_w = 22*mm
            betaald_w = 18*mm

            col_defs = [('Naam', None), ('Stamnr', nr_w), ('Kluisnr', nr_w)]
            if toon_sleutelnr:
                col_defs.append(('Sleutelnr', nr_w))
            col_defs += [('Klas', klas_w), ('Van', date_w), ('Tot', date_w)]
            if borg_actief:
                col_defs += [('Borg', borg_w), ('Betaald', betaald_w)]

            fixed_w = sum(w for _, w in col_defs if w is not None)
            naam_w = page_w - fixed_w
            col_widths = [naam_w if w is None else w for _, w in col_defs]
            col_headers = [h for h, _ in col_defs]

            elements.append(Paragraph(f"{len(rows)} rijen", subtitle_style))
            elements.append(Spacer(1, 3*mm))

            klassen = {}
            for r in rows:
                klas = r['leerling_klas'] or '-'
                klassen.setdefault(klas, []).append(r)

            for klas, leerlingen in klassen.items():
                elements.append(Paragraph(f"Klas: {klas}", klas_style))
                data = [col_headers]
                for r in leerlingen:
                    naam = r['leerling_naam']
                    if r['vertrokken_op']:
                        naam += ' [V]'
                    row_data = [naam, r['leerling_stamnr'], r['kluisnummer']]
                    if toon_sleutelnr:
                        row_data.append(r['sleutelnummer'] or '')
                    row_data += [klas, r['periode_van'] or '', r['periode_tot'] or '']
                    if borg_actief:
                        row_data += [
                            f"EUR {r['borgbedrag']:.2f}" if r['borgbedrag'] else '',
                            'Ja' if r['borg_betaald'] else 'Nee'
                        ]
                    data.append(row_data)
                elements.append(make_table(data, col_widths=col_widths))
                elements.append(Spacer(1, 4*mm))

    doc.build(elements)
    buf.seek(0)

    filename = f'kluisjes-rapport-{report_type}-{date.today().isoformat()}.pdf'
    return Response(
        buf.getvalue(),
        mimetype='application/pdf',
        headers={'Content-Disposition': f'attachment; filename={filename}'}
    )
