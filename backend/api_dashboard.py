from flask import Blueprint, jsonify, g, request, Response
from auth import login_required
import io
from datetime import date

dashboard_bp = Blueprint('dashboard', __name__, url_prefix='/api')

@dashboard_bp.route('/dashboard/stats', methods=['GET'])
@login_required
def stats():
    rows = g.db.execute('''
        SELECT v.id, v.naam,
            COUNT(k.id) as totaal,
            SUM(CASE WHEN k.status='uitgeleend' THEN 1 ELSE 0 END) as uitgeleend,
            SUM(CASE WHEN k.status='vrij' THEN 1 ELSE 0 END) as vrij,
            SUM(CASE WHEN k.status='defect' THEN 1 ELSE 0 END) as defect
        FROM vestigingen v
        LEFT JOIN kluisjes k ON k.vestiging_id = v.id AND k.verwijderd = 0
        GROUP BY v.id
        ORDER BY v.naam
    ''').fetchall()

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


@dashboard_bp.route('/dashboard/rapport', methods=['GET'])
@login_required
def rapport():
    """Export a PDF report. Query params: type (sleutels|borg|toewijzingen), vestiging_id (optional)."""
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4, landscape
    from reportlab.lib.units import mm
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

    report_type = request.args.get('type', 'toewijzingen')
    vestiging_id = request.args.get('vestiging_id')
    today = date.today().strftime('%d-%m-%Y')

    titles = {
        'sleutels': 'Openstaande sleutels',
        'borg': 'Openstaande borg',
        'toewijzingen': 'Actieve toewijzingen',
    }

    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=landscape(A4), leftMargin=15*mm, rightMargin=15*mm, topMargin=15*mm, bottomMargin=15*mm)

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle('Title', parent=styles['Title'], fontSize=16, textColor=colors.HexColor('#1e3a5f'))
    subtitle_style = ParagraphStyle('Sub', parent=styles['Normal'], fontSize=9, textColor=colors.gray)
    erasmus_orange = colors.HexColor('#FF8200')

    elements = []
    elements.append(Paragraph(f"Kluisjesbeheer — {titles.get(report_type, 'Rapport')}", title_style))
    elements.append(Paragraph(f"School — {today}", subtitle_style))
    elements.append(Spacer(1, 8*mm))

    header_style = TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), erasmus_orange),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 8),
        ('FONTSIZE', (0, 1), (-1, -1), 7.5),
        ('ALIGN', (0, 0), (-1, 0), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#FFF7ED')]),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#E2E8F0')),
        ('TOPPADDING', (0, 0), (-1, -1), 3),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
        ('LEFTPADDING', (0, 0), (-1, -1), 5),
        ('RIGHTPADDING', (0, 0), (-1, -1), 5),
    ])

    if report_type == 'sleutels':
        headers = ['Vestiging', 'Kluisnr', 'Sleutelnr', 'Laatste huurder', 'Stamnr', 'Klas', 'Periode tot', 'Einddatum']
        query = '''
            SELECT v.naam as vestiging, k.kluisnummer, k.sleutelnummer,
                   t.leerling_naam, t.leerling_stamnr, t.leerling_klas, t.periode_tot, t.einddatum
            FROM kluisjes k
            JOIN vestigingen v ON k.vestiging_id = v.id
            JOIN toewijzingen t ON k.id = t.kluisje_id
            WHERE k.verwijderd = 0 AND k.status = 'vrij'
              AND t.actief = 0 AND t.sleutel_ingeleverd = 0
              AND t.id = (SELECT MAX(t2.id) FROM toewijzingen t2 WHERE t2.kluisje_id = k.id)
        '''
        params = []
        if vestiging_id:
            query += ' AND k.vestiging_id = ?'
            params.append(int(vestiging_id))
        query += ' ORDER BY v.naam, k.kluisnummer'
        data = [headers]
        for r in g.db.execute(query, params).fetchall():
            data.append([r['vestiging'], r['kluisnummer'], r['sleutelnummer'] or '',
                         r['leerling_naam'], r['leerling_stamnr'], r['leerling_klas'] or '',
                         r['periode_tot'] or '', r['einddatum'] or ''])

    elif report_type == 'borg':
        headers = ['Vestiging', 'Kluisnr', 'Leerling', 'Stamnr', 'Klas', 'Borg', 'Betaald', 'Teruggestort', 'Actief']
        query = '''
            SELECT v.naam as vestiging, k.kluisnummer,
                   t.leerling_naam, t.leerling_stamnr, t.leerling_klas,
                   t.borgbedrag, t.borg_betaald, t.borg_teruggestort, t.actief
            FROM toewijzingen t
            JOIN kluisjes k ON t.kluisje_id = k.id
            JOIN vestigingen v ON k.vestiging_id = v.id
            WHERE k.verwijderd = 0 AND t.borgbedrag > 0
              AND ((t.actief = 1 AND t.borg_betaald = 0) OR (t.actief = 0 AND t.borg_betaald = 1 AND t.borg_teruggestort = 0))
        '''
        params = []
        if vestiging_id:
            query += ' AND k.vestiging_id = ?'
            params.append(int(vestiging_id))
        query += ' ORDER BY v.naam, k.kluisnummer'
        data = [headers]
        for r in g.db.execute(query, params).fetchall():
            data.append([r['vestiging'], r['kluisnummer'], r['leerling_naam'],
                         r['leerling_stamnr'], r['leerling_klas'] or '',
                         f"\u20ac{r['borgbedrag']:.2f}",
                         'Ja' if r['borg_betaald'] else 'Nee',
                         'Ja' if r['borg_teruggestort'] else 'Nee',
                         'Ja' if r['actief'] else 'Nee'])

    else:  # toewijzingen
        headers = ['Vestiging', 'Cluster', 'Kluisnr', 'Sleutelnr', 'Leerling', 'Stamnr', 'Klas', 'Van', 'Tot', 'Borg', 'Betaald']
        query = '''
            SELECT v.naam as vestiging, c.naam as cluster, k.kluisnummer, k.sleutelnummer,
                   t.leerling_naam, t.leerling_stamnr, t.leerling_klas,
                   t.periode_van, t.periode_tot, t.borgbedrag, t.borg_betaald
            FROM toewijzingen t
            JOIN kluisjes k ON t.kluisje_id = k.id
            JOIN vestigingen v ON k.vestiging_id = v.id
            JOIN clusters c ON k.cluster_id = c.id
            WHERE k.verwijderd = 0 AND t.actief = 1
        '''
        params = []
        if vestiging_id:
            query += ' AND k.vestiging_id = ?'
            params.append(int(vestiging_id))
        query += ' ORDER BY v.naam, c.naam, k.kluisnummer'
        data = [headers]
        for r in g.db.execute(query, params).fetchall():
            data.append([r['vestiging'], r['cluster'], r['kluisnummer'],
                         r['sleutelnummer'] or '', r['leerling_naam'],
                         r['leerling_stamnr'], r['leerling_klas'] or '',
                         r['periode_van'] or '', r['periode_tot'] or '',
                         f"\u20ac{r['borgbedrag']:.2f}" if r['borgbedrag'] else '',
                         'Ja' if r['borg_betaald'] else 'Nee'])

    if len(data) == 1:
        elements.append(Paragraph("Geen gegevens gevonden voor dit rapport.", styles['Normal']))
    else:
        elements.append(Paragraph(f"{len(data)-1} rijen", subtitle_style))
        elements.append(Spacer(1, 3*mm))
        table = Table(data, repeatRows=1)
        table.setStyle(header_style)
        elements.append(table)

    doc.build(elements)
    buf.seek(0)

    filename = f'kluisjes-rapport-{report_type}-{date.today().isoformat()}.pdf'
    return Response(
        buf.getvalue(),
        mimetype='application/pdf',
        headers={'Content-Disposition': f'attachment; filename={filename}'}
    )
