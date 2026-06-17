# Klas-filter + per-klas PDF-export — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Kluisjes per klas kunnen filteren in het overzicht en per klas (of alle klassen) een PDF-overzicht uitdraaien met "mét kluisje" en "zonder kluisje".

**Architecture:** Backend Flask blueprints (`api_kluisjes.py`, `api_dashboard.py`); frontend React (`Toolbar.jsx`, `useKluisjes.jsx`, `Uitleenoverzicht.jsx`). De klas komt overal via `COALESCE(NULLIF(TRIM(t.leerling_klas),''), l.klas)` — de toewijzing-snapshot, met de live `leerlingen.klas` als die leeg is.

**Tech Stack:** Flask + SQLite, ReportLab (PDF), React + Vite + Tailwind. Tests: pytest (backend). Frontend: handmatig + `npm run build`.

---

## File Structure

- `backend/api_kluisjes.py` — `klas`-param op `search_kluisjes` + nieuw endpoint `GET /api/vestigingen/<vid>/klassen`.
- `backend/api_dashboard.py` — COALESCE-klas op bestaande rapporten + nieuw rapport-type `klas` (data-helper + PDF + HTML-preview).
- `backend/tests/test_kluisjes.py` — tests voor klas-filter + klassen-endpoint.
- `backend/tests/test_dashboard.py` — tests voor COALESCE-klas + klas-rapport.
- `frontend/src/hooks/useKluisjes.jsx` — `klas` in filter-state + meesturen.
- `frontend/src/pages/Uitleenoverzicht.jsx` — klas resetten bij vestiging-wissel.
- `frontend/src/components/Toolbar.jsx` — klas-dropdown + Rapport-blok "Per klas".

**Gedeelde SQL-expressie** (overal identiek gebruiken): `COALESCE(NULLIF(TRIM(t.leerling_klas), ''), l.klas)`.

---

## Task 1: Backend — `klas`-filter op `GET /api/kluisjes`

**Files:**
- Modify: `backend/api_kluisjes.py` (functie `search_kluisjes`, ~regel 64-150)
- Test: `backend/tests/test_kluisjes.py`

- [ ] **Step 1: Schrijf de falende tests**

Voeg toe aan `backend/tests/test_kluisjes.py`:

```python
def test_search_filter_op_klas_snapshot(client):
    """Filter op klas die op de toewijzing zelf staat (snapshot)."""
    client.post('/api/clusters/1/kluisjes', json={'kluisnummer': 'P001', 'sleutelnummer': 'S-001'})
    client.post('/api/clusters/1/kluisjes', json={'kluisnummer': 'P002', 'sleutelnummer': 'S-002'})
    client.post('/api/kluisjes/1/toewijzen', json={
        'leerling_stamnr': '100', 'leerling_naam': 'Anna', 'leerling_klas': '2A',
        'periode_van': '2026-01-01', 'periode_tot': '2026-07-31', 'borgbedrag': 0
    })
    client.post('/api/kluisjes/2/toewijzen', json={
        'leerling_stamnr': '200', 'leerling_naam': 'Bram', 'leerling_klas': '3B',
        'periode_van': '2026-01-01', 'periode_tot': '2026-07-31', 'borgbedrag': 0
    })
    rv = client.get('/api/kluisjes?vestiging_id=1&klas=2A')
    data = rv.get_json()
    assert rv.status_code == 200
    assert [d['kluisnummer'] for d in data] == ['P001']


def test_search_filter_op_klas_live_fallback(client, db):
    """Lege snapshot-klas -> klas komt uit de live leerlingen-tabel."""
    client.post('/api/clusters/1/kluisjes', json={'kluisnummer': 'P001', 'sleutelnummer': 'S-001'})
    # toewijzing zonder klas
    client.post('/api/kluisjes/1/toewijzen', json={
        'leerling_stamnr': '300', 'leerling_naam': 'Cara', 'leerling_klas': '',
        'periode_van': '2026-01-01', 'periode_tot': '2026-07-31', 'borgbedrag': 0
    })
    # leerling met klas in de live tabel (zelfde stamnr)
    db.execute("INSERT INTO leerlingen (stamnr, naam, klas) VALUES ('300', 'Cara', 'M2HV1')")
    db.commit()
    rv = client.get('/api/kluisjes?vestiging_id=1&klas=M2HV1')
    data = rv.get_json()
    assert [d['kluisnummer'] for d in data] == ['P001']
```

- [ ] **Step 2: Run de tests — verwacht FAIL**

Run: `cd backend && python -m pytest tests/test_kluisjes.py::test_search_filter_op_klas_snapshot tests/test_kluisjes.py::test_search_filter_op_klas_live_fallback -v`
Expected: FAIL — zonder filter komen beide kluisjes terug (assert faalt).

- [ ] **Step 3: Voeg de `klas`-param toe aan `search_kluisjes`**

In `backend/api_kluisjes.py`, in `search_kluisjes`, bij het uitlezen van de query-params (naast `status = request.args.get('status')`):

```python
    klas = request.args.get('klas')
```

En vlak vóór `query += ' ORDER BY k.kluisnummer'` (na het `if q:`-blok):

```python
    if klas:
        query += " AND COALESCE(NULLIF(TRIM(t.leerling_klas), ''), l.klas) = ?"
        params.append(klas)
```

- [ ] **Step 4: Run de tests — verwacht PASS**

Run: `cd backend && python -m pytest tests/test_kluisjes.py::test_search_filter_op_klas_snapshot tests/test_kluisjes.py::test_search_filter_op_klas_live_fallback -v`
Expected: PASS (2 passed).

- [ ] **Step 5: Commit**

```bash
git add backend/api_kluisjes.py backend/tests/test_kluisjes.py
git commit -m "feat(kluisjes): filter overview by klas (snapshot + live fallback)"
```

---

## Task 2: Backend — endpoint klassenlijst per vestiging

Levert de gesorteerde, unieke klassen die in een vestiging een **huidige huurder** hebben (voor de dropdown).

**Files:**
- Modify: `backend/api_kluisjes.py` (nieuw endpoint)
- Test: `backend/tests/test_kluisjes.py`

- [ ] **Step 1: Schrijf de falende test**

```python
def test_klassen_per_vestiging(client):
    client.post('/api/clusters/1/kluisjes', json={'kluisnummer': 'P001'})
    client.post('/api/clusters/1/kluisjes', json={'kluisnummer': 'P002'})
    client.post('/api/clusters/1/kluisjes', json={'kluisnummer': 'P003'})
    client.post('/api/kluisjes/1/toewijzen', json={
        'leerling_stamnr': '1', 'leerling_naam': 'A', 'leerling_klas': '3B',
        'periode_van': '2026-01-01', 'periode_tot': '2026-07-31', 'borgbedrag': 0})
    client.post('/api/kluisjes/2/toewijzen', json={
        'leerling_stamnr': '2', 'leerling_naam': 'B', 'leerling_klas': '2A',
        'periode_van': '2026-01-01', 'periode_tot': '2026-07-31', 'borgbedrag': 0})
    # P003 blijft vrij -> levert geen klas
    rv = client.get('/api/vestigingen/1/klassen')
    assert rv.status_code == 200
    assert rv.get_json() == ['2A', '3B']  # uniek + gesorteerd, geen lege
```

- [ ] **Step 2: Run — verwacht FAIL (404)**

Run: `cd backend && python -m pytest tests/test_kluisjes.py::test_klassen_per_vestiging -v`
Expected: FAIL — endpoint bestaat nog niet (404).

- [ ] **Step 3: Voeg het endpoint toe**

In `backend/api_kluisjes.py`, na `search_kluisjes` (of bij de andere routes):

```python
@kluisjes_bp.route('/vestigingen/<int:vid>/klassen', methods=['GET'])
@login_required
def klassen_in_vestiging(vid):
    """Unieke klassen met een actieve huurder in deze vestiging (voor de filter-dropdown)."""
    err = assert_vestiging_access(vid)
    if err: return err
    rows = g.db.execute(
        '''SELECT DISTINCT COALESCE(NULLIF(TRIM(t.leerling_klas), ''), l.klas) AS klas
           FROM toewijzingen t
           JOIN kluisjes k ON t.kluisje_id = k.id
           LEFT JOIN leerlingen l ON t.leerling_stamnr = l.stamnr
           WHERE k.verwijderd = 0 AND t.actief = 1 AND k.vestiging_id = ?
             AND COALESCE(NULLIF(TRIM(t.leerling_klas), ''), l.klas) IS NOT NULL
             AND TRIM(COALESCE(NULLIF(TRIM(t.leerling_klas), ''), l.klas)) <> ''
           ORDER BY klas''',
        (vid,)
    ).fetchall()
    return jsonify([r['klas'] for r in rows])
```

- [ ] **Step 4: Run — verwacht PASS**

Run: `cd backend && python -m pytest tests/test_kluisjes.py::test_klassen_per_vestiging -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add backend/api_kluisjes.py backend/tests/test_kluisjes.py
git commit -m "feat(kluisjes): add klassen-per-vestiging endpoint for filter dropdown"
```

---

## Task 3: Backend — COALESCE-klas op de bestaande rapporten

De rapport-queries (`toewijzingen`/`inname`, `sleutels`, `borg`) tonen/sorteren nu de lege snapshot-klas. Overzetten op de COALESCE-klas.

**Files:**
- Modify: `backend/api_dashboard.py` (`_get_rapport_data`, ~regel 138-219)
- Test: `backend/tests/test_dashboard.py`

- [ ] **Step 1: Schrijf de falende test**

Voeg toe aan `backend/tests/test_dashboard.py`:

```python
def test_rapport_toewijzingen_gebruikt_live_klas(client, db):
    """Rapport toont de live klas als de toewijzing-snapshot leeg is."""
    client.post('/api/kluisjes/1/toewijzen', json={
        'leerling_stamnr': '500', 'leerling_naam': 'Dirk', 'leerling_klas': '',
        'periode_van': '2026-01-01', 'periode_tot': '2026-07-31', 'borgbedrag': 0})
    db.execute("INSERT INTO leerlingen (stamnr, naam, klas) VALUES ('500', 'Dirk', '4VWO')")
    db.commit()
    rv = client.get('/api/dashboard/rapport/preview?type=toewijzingen&vestiging_id=1')
    assert rv.status_code == 200
    assert 'Klas: 4VWO' in rv.get_data(as_text=True)
```

- [ ] **Step 2: Run — verwacht FAIL**

Run: `cd backend && python -m pytest tests/test_dashboard.py::test_rapport_toewijzingen_gebruikt_live_klas -v`
Expected: FAIL — preview bevat `Klas: -` (snapshot leeg) i.p.v. `Klas: 4VWO`.

- [ ] **Step 3: Zet de queries op de COALESCE-klas**

In `backend/api_dashboard.py`, in `_get_rapport_data`:

(a) `sleutels` (de SELECT bij `report_type == 'sleutels'`): vervang `t.leerling_klas,` door:
```python
                   COALESCE(NULLIF(TRIM(t.leerling_klas), ''), l.klas) as leerling_klas,
```

(b) `borg` (de SELECT bij `report_type == 'borg'`): vervang `t.leerling_klas,` door dezelfde regel:
```python
                   COALESCE(NULLIF(TRIM(t.leerling_klas), ''), l.klas) as leerling_klas,
```

(c) `toewijzingen`/`inname` (de `else`-tak): vervang `t.leerling_naam, t.leerling_klas, t.leerling_stamnr,` door:
```python
            SELECT t.leerling_naam,
                   COALESCE(NULLIF(TRIM(t.leerling_klas), ''), l.klas) as leerling_klas,
                   t.leerling_stamnr,
```
en wijzig de `ORDER BY t.leerling_klas, t.leerling_naam` naar:
```python
        query += ' ORDER BY leerling_klas, t.leerling_naam'
```

- [ ] **Step 4: Run — verwacht PASS + geen regressies**

Run: `cd backend && python -m pytest tests/test_dashboard.py -v`
Expected: nieuwe test PASS, bestaande dashboard-tests blijven groen.

- [ ] **Step 5: Commit**

```bash
git add backend/api_dashboard.py backend/tests/test_dashboard.py
git commit -m "fix(rapport): use live klas (COALESCE) in existing reports"
```

---

## Task 4: Backend — nieuw rapport-type `klas` (data + PDF + preview)

**Files:**
- Modify: `backend/api_dashboard.py` (data-helper + `rapport` + `rapport_preview`)
- Test: `backend/tests/test_dashboard.py`

- [ ] **Step 1: Schrijf de falende tests**

```python
def test_klas_rapport_preview_met_en_zonder(client, db):
    # Eén leerling MET kluisje in klas 2A
    client.post('/api/kluisjes/1/toewijzen', json={
        'leerling_stamnr': '10', 'leerling_naam': 'Eva Met', 'leerling_klas': '2A',
        'periode_van': '2026-01-01', 'periode_tot': '2026-07-31', 'borgbedrag': 0})
    # Eén leerling ZONDER kluisje in klas 2A (alleen in leerlingen-tabel)
    db.execute("INSERT INTO leerlingen (stamnr, naam, klas) VALUES ('11', 'Finn Zonder', '2A')")
    db.commit()
    rv = client.get('/api/dashboard/rapport/preview?type=klas&vestiging_id=1')
    body = rv.get_data(as_text=True)
    assert rv.status_code == 200
    assert 'Eva Met' in body
    assert 'Finn Zonder' in body
    assert 'Klas: 2A' in body


def test_klas_rapport_filtert_op_klas(client, db):
    client.post('/api/kluisjes/1/toewijzen', json={
        'leerling_stamnr': '10', 'leerling_naam': 'Eva 2A', 'leerling_klas': '2A',
        'periode_van': '2026-01-01', 'periode_tot': '2026-07-31', 'borgbedrag': 0})
    client.post('/api/kluisjes/2/toewijzen', json={
        'leerling_stamnr': '20', 'leerling_naam': 'Gijs 3B', 'leerling_klas': '3B',
        'periode_van': '2026-01-01', 'periode_tot': '2026-07-31', 'borgbedrag': 0})
    rv = client.get('/api/dashboard/rapport/preview?type=klas&vestiging_id=1&klas=2A')
    body = rv.get_data(as_text=True)
    assert 'Eva 2A' in body
    assert 'Gijs 3B' not in body


def test_klas_rapport_pdf_download(client):
    client.post('/api/kluisjes/1/toewijzen', json={
        'leerling_stamnr': '10', 'leerling_naam': 'Eva', 'leerling_klas': '2A',
        'periode_van': '2026-01-01', 'periode_tot': '2026-07-31', 'borgbedrag': 0})
    rv = client.get('/api/dashboard/rapport?type=klas&vestiging_id=1')
    assert rv.status_code == 200
    assert rv.mimetype == 'application/pdf'
    assert rv.get_data().startswith(b'%PDF')
```

Let op: de fixture in `test_dashboard.py` maakt 3 kluisjes (P001-P003) aan; `kluisje/1` en `kluisje/2` bestaan dus.

- [ ] **Step 2: Run — verwacht FAIL**

Run: `cd backend && python -m pytest tests/test_dashboard.py::test_klas_rapport_preview_met_en_zonder tests/test_dashboard.py::test_klas_rapport_filtert_op_klas tests/test_dashboard.py::test_klas_rapport_pdf_download -v`
Expected: FAIL — type `klas` valt nu in de `toewijzingen`-tak (geen "Zonder kluisje", geen filter), en PDF-download geeft de toewijzingen-PDF.

- [ ] **Step 3: Voeg de data-helper toe**

In `backend/api_dashboard.py`, vlak boven `def _register_font():`:

```python
def _get_klas_rapport_data(vestiging_id, klas, db):
    """Per-klas overzicht. Geeft een dict {klasnaam: {'met': [...], 'zonder': [...]}}.
    Klassen-set = de klassen die in deze vestiging een actieve huurder hebben
    (zelfde set als de filter-dropdown). 'zonder' = leerlingen in die klas zonder
    actieve toewijzing (leunt op de leerlingen-tabel / Magister-sync)."""
    KLAS = "COALESCE(NULLIF(TRIM(t.leerling_klas), ''), l.klas)"
    params = [int(vestiging_id)]
    klas_filter = ''
    if klas:
        klas_filter = f' AND {KLAS} = ?'
        params.append(klas)
    met_rows = db.execute(f'''
        SELECT {KLAS} AS klas, t.leerling_naam, t.leerling_stamnr,
               k.kluisnummer, k.sleutelnummer, t.periode_van, t.periode_tot,
               l.vertrokken_op
        FROM toewijzingen t
        JOIN kluisjes k ON t.kluisje_id = k.id
        LEFT JOIN leerlingen l ON t.leerling_stamnr = l.stamnr
        WHERE k.verwijderd = 0 AND t.actief = 1 AND k.vestiging_id = ?{klas_filter}
        ORDER BY klas, t.leerling_naam
    ''', params).fetchall()

    klassen = []
    for r in met_rows:
        kn = r['klas'] or '-'
        if kn not in klassen:
            klassen.append(kn)

    result = {}
    for kn in klassen:
        result[kn] = {
            'met': [r for r in met_rows if (r['klas'] or '-') == kn],
            'zonder': [],
        }
        if kn == '-':
            continue
        result[kn]['zonder'] = db.execute('''
            SELECT l.naam, l.stamnr, l.klas
            FROM leerlingen l
            WHERE l.klas = ? AND l.vertrokken_op IS NULL
              AND NOT EXISTS (
                SELECT 1 FROM toewijzingen t WHERE t.leerling_stamnr = l.stamnr AND t.actief = 1)
            ORDER BY l.naam
        ''', (kn,)).fetchall()
    return result
```

- [ ] **Step 4: Voeg de HTML-preview toe voor type `klas`**

In `rapport_preview`, direct na de regels die `report_type`/`vestiging_id`/`today` bepalen en vóór `result = _get_rapport_data(...)`, een vroege afhandeling:

```python
    if report_type == 'klas':
        import html as htmllib
        klas = request.args.get('klas')
        data = _get_klas_rapport_data(vestiging_id, klas, g.db)
        def e(v):
            return htmllib.escape(str(v) if v else '')
        kleur = config.get('SchoolKleur', '#FF8200')
        title = f"Kluisjes per klas{(' — ' + klas) if klas else ''}"
        secties = ''
        for kn, groep in data.items():
            secties += f'<h3>Klas: {e(kn)} <span>({len(groep["met"])} mét kluisje, {len(groep["zonder"])} zonder)</span></h3>'
            secties += '<h4>Mét kluisje</h4><table><thead><tr><th>Naam</th><th class="nr">Kluisnr</th><th class="nr">Sleutelnr</th><th>Van</th><th>Tot</th></tr></thead><tbody>'
            for i, r in enumerate(groep['met']):
                rc = 'alt' if i % 2 else ''
                vt = ' <span style="color:#dc2626;font-size:10px;font-weight:bold">[Vertrokken]</span>' if r['vertrokken_op'] else ''
                secties += f'<tr class="{rc}"><td class="naam">{e(r["leerling_naam"])}{vt}</td><td class="nr">{e(r["kluisnummer"])}</td><td class="nr">{e(r["sleutelnummer"])}</td><td>{e(r["periode_van"])}</td><td>{e(r["periode_tot"])}</td></tr>'
            secties += '</tbody></table>'
            if groep['zonder']:
                secties += '<h4>Zonder kluisje</h4><table><thead><tr><th>Naam</th><th>Stamnr</th></tr></thead><tbody>'
                for i, r in enumerate(groep['zonder']):
                    rc = 'alt' if i % 2 else ''
                    secties += f'<tr class="{rc}"><td class="naam">{e(r["naam"])}</td><td>{e(r["stamnr"])}</td></tr>'
                secties += '</tbody></table>'
        if not data:
            secties = '<p>Geen klassen met huurders gevonden.</p>'
        pdf_url = f'/api/dashboard/rapport?type=klas' + (f'&vestiging_id={vestiging_id}' if vestiging_id else '') + (f'&klas={htmllib.escape(klas)}' if klas else '')
        today = date.today().strftime('%d-%m-%Y')
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
  @media print {{ .toolbar {{ display: none; }} body {{ background: white; }} .content {{ margin: 0; max-width: 100%; }} table {{ page-break-inside: avoid; }} }}
</style></head><body>
<div class="toolbar"><h1>Kluisjesbeheer &mdash; {e(title)}</h1><a href="{pdf_url}">Download PDF</a></div>
<div class="content"><p style="color:#64748b;font-size:12px">{e(config.get('SchoolNaam', ''))} &mdash; {today}</p>{secties}</div>
</body></html>'''
        return Response(html_out, mimetype='text/html; charset=utf-8')
```

- [ ] **Step 5: Voeg de PDF-export toe voor type `klas`**

In `rapport`, direct na het bepalen van `report_type`/`vestiging_id`/scope-check en `font_normal, font_bold = _register_font()`, een vroege afhandeling vóór `result = _get_rapport_data(...)`:

```python
    if report_type == 'klas':
        from reportlab.lib import colors
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.units import mm
        from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        klas = request.args.get('klas')
        data = _get_klas_rapport_data(vestiging_id, klas, g.db)
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

        title = f"Kluisjes per klas{(' - ' + klas) if klas else ''}"
        elements = [Paragraph(f"Kluisjesbeheer - {title}", title_style),
                    Paragraph(f"{config.get('SchoolNaam', '')} - {date.today().strftime('%d-%m-%Y')}", sub_style),
                    Spacer(1, 6*mm)]
        if not data:
            elements.append(Paragraph("Geen klassen met huurders gevonden.", styles['Normal']))
        nr_w = 28*mm
        date_w = 26*mm
        for kn, groep in data.items():
            elements.append(Paragraph(
                f"Klas: {kn}  ({len(groep['met'])} mét kluisje, {len(groep['zonder'])} zonder)", klas_style))
            elements.append(Paragraph("Mét kluisje", sub_style))
            mdata = [['Naam', 'Kluisnr', 'Sleutelnr', 'Van', 'Tot']]
            for r in groep['met']:
                naam = r['leerling_naam'] + (' [V]' if r['vertrokken_op'] else '')
                mdata.append([naam, r['kluisnummer'], r['sleutelnummer'] or '',
                              r['periode_van'] or '', r['periode_tot'] or ''])
            elements.append(ktable(mdata, [page_w - 2*nr_w - 2*date_w, nr_w, nr_w, date_w, date_w]))
            if groep['zonder']:
                elements.append(Paragraph("Zonder kluisje", sub_style))
                zdata = [['Naam', 'Stamnr']]
                for r in groep['zonder']:
                    zdata.append([r['naam'], r['stamnr']])
                elements.append(ktable(zdata, [page_w - nr_w, nr_w]))
            elements.append(Spacer(1, 5*mm))
        doc.build(elements)
        buf.seek(0)
        suffix = f'-{klas}' if klas else '-alle'
        filename = f'kluisjes-klas{suffix}-{date.today().isoformat()}.pdf'
        return Response(buf.getvalue(), mimetype='application/pdf',
                        headers={'Content-Disposition': f'attachment; filename={filename}'})
```

- [ ] **Step 6: Run de tests — verwacht PASS + geen regressies**

Run: `cd backend && python -m pytest tests/test_dashboard.py -v`
Expected: de 3 nieuwe klas-tests PASS, bestaande tests groen.

- [ ] **Step 7: Commit**

```bash
git add backend/api_dashboard.py backend/tests/test_dashboard.py
git commit -m "feat(rapport): per-class report (met/zonder kluisje) PDF + preview"
```

---

## Task 5: Frontend — `klas` in de filter-state

**Files:**
- Modify: `frontend/src/hooks/useKluisjes.jsx`

- [ ] **Step 1: Voeg `klas` toe aan de filters + querystring**

In `useKluisjes.jsx`, de initiële state:
```javascript
  const [filters, setFilters] = useState({
    vestiging_id: null, cluster_id: null, status: '', q: '', klas: '', view: 'grid',
  })
```

In `loadKluisjes`, na `if (filters.q) params.set('q', filters.q)`:
```javascript
    if (filters.klas) params.set('klas', filters.klas)
```

En voeg `filters.klas` toe aan de dependency-array van `loadKluisjes`:
```javascript
  }, [filters.vestiging_id, filters.status, filters.q, filters.klas])
```

- [ ] **Step 2: Verifieer de build**

Run: `cd frontend && npm run build`
Expected: build slaagt zonder errors.

- [ ] **Step 3: Commit**

```bash
git add frontend/src/hooks/useKluisjes.jsx
git commit -m "feat(frontend): add klas to overview filter state"
```

---

## Task 6: Frontend — klas-dropdown in de toolbar + reset bij vestiging-wissel

**Files:**
- Modify: `frontend/src/components/Toolbar.jsx`
- Modify: `frontend/src/pages/Uitleenoverzicht.jsx`

- [ ] **Step 1: Reset `klas` bij vestiging-wissel in Uitleenoverzicht**

In `Uitleenoverzicht.jsx`, in `selectVestiging`, voeg `klas: ''` toe aan beide `setFilters`-takken, en in de concierge-auto-select-effect. Concreet:
- `setFilters(f => ({ ...f, vestiging_id: null, cluster_id: null, klas: '' }))`
- `setFilters(f => ({ ...f, vestiging_id: String(id), cluster_id: null, klas: '' }))`
- in de auto-select useEffect: `setFilters(f => ({ ...f, vestiging_id: String(vestigingen[0].id), cluster_id: null, klas: '' }))`

- [ ] **Step 2: Voeg de klas-dropdown toe in Toolbar**

In `Toolbar.jsx`, bovenaan de imports `useState` is er al; voeg `useEffect` toe:
```javascript
import { useState, useEffect } from 'react'
```

In de `Toolbar`-component, na `const [filtersOpen, setFiltersOpen] = useState(false)`:
```javascript
  const [klassen, setKlassen] = useState([])
  useEffect(() => {
    if (!vestigingId) { setKlassen([]); return }
    api.get(`/api/vestigingen/${vestigingId}/klassen`).then(setKlassen).catch(() => setKlassen([]))
  }, [vestigingId])
```
Voeg de api-import toe bovenaan het bestand:
```javascript
import { api } from '../api'
```

Render de dropdown direct na de cluster-`<select>` (vóór de Search-div):
```javascript
        {/* Klas */}
        <select className={selectClass} value={filters.klas || ''}
          onChange={e => setFilters(f => ({ ...f, klas: e.target.value }))}>
          <option value="">Alle klassen</option>
          {klassen.map(k => <option key={k} value={k}>{k}</option>)}
        </select>
```

- [ ] **Step 3: Verifieer de build**

Run: `cd frontend && npm run build`
Expected: build slaagt.

- [ ] **Step 4: Commit**

```bash
git add frontend/src/components/Toolbar.jsx frontend/src/pages/Uitleenoverzicht.jsx
git commit -m "feat(frontend): klas filter dropdown in toolbar"
```

---

## Task 7: Frontend — Rapport-blok "Per klas"

**Files:**
- Modify: `frontend/src/components/Toolbar.jsx`

- [ ] **Step 1: Geef de huidige klas door aan RapportDropdown**

In `Toolbar.jsx`, in de render van `Toolbar`, wijzig `<RapportDropdown vestigingId={vestigingId} />` naar:
```javascript
        <RapportDropdown vestigingId={vestigingId} klas={filters.klas} />
```

- [ ] **Step 2: Verwerk `klas` in RapportDropdown**

Wijzig de signatuur en de download/preview-functies van `RapportDropdown`:
```javascript
function RapportDropdown({ vestigingId, klas }) {
  const [open, setOpen] = useState(false)
  const { borgActiefVoor } = useInstellingen()

  function download(type, extra = {}) {
    const params = new URLSearchParams({ type })
    if (vestigingId) params.set('vestiging_id', vestigingId)
    Object.entries(extra).forEach(([k, v]) => v && params.set(k, v))
    window.open(`/api/dashboard/rapport?${params}`, '_blank')
    setOpen(false)
  }

  function preview(type, extra = {}) {
    const params = new URLSearchParams({ type })
    if (vestigingId) params.set('vestiging_id', vestigingId)
    Object.entries(extra).forEach(([k, v]) => v && params.set(k, v))
    window.open(`/api/dashboard/rapport/preview?${params}`, '_blank')
    setOpen(false)
  }
```

- [ ] **Step 3: Voeg het "Per klas"-blok toe in het dropdown-menu**

In het menu van `RapportDropdown`, na het "Openstaand"-blok (na de borg-`RapportRij`), vóór de afsluitende `</div>`:
```javascript
            <div className="border-t border-slate-100 dark:border-slate-700 my-1" />
            <div className="px-4 py-1.5 text-xs font-semibold text-slate-400 uppercase tracking-wide">Per klas</div>
            {klas ? (
              <div className="flex items-center justify-between pr-2">
                <button onClick={() => download('klas', { klas })}
                  className="flex-1 text-left px-4 py-2 text-sm hover:bg-slate-50 dark:hover:bg-slate-700">
                  Huidige klas ({klas})
                </button>
                <button onClick={() => preview('klas', { klas })} className="text-slate-400 hover:text-primary px-2 py-1" title="Preview"><EyeIcon /></button>
              </div>
            ) : (
              <div className="px-4 py-1.5 text-xs text-slate-400">Kies eerst een klas in de filterbalk voor één klas</div>
            )}
            <div className="flex items-center justify-between pr-2">
              <button onClick={() => download('klas')}
                className="flex-1 text-left px-4 py-2 text-sm hover:bg-slate-50 dark:hover:bg-slate-700">
                Alle klassen
              </button>
              <button onClick={() => preview('klas')} className="text-slate-400 hover:text-primary px-2 py-1" title="Preview"><EyeIcon /></button>
            </div>
```

- [ ] **Step 4: Verifieer de build**

Run: `cd frontend && npm run build`
Expected: build slaagt.

- [ ] **Step 5: Commit**

```bash
git add frontend/src/components/Toolbar.jsx
git commit -m "feat(frontend): per-class report block in rapport dropdown"
```

---

## Task 8: Volledige verificatie

- [ ] **Step 1: Volledige backend-suite**

Run: `cd backend && python -m pytest -q`
Expected: alle nieuwe tests groen; alleen de bekende, niet-gerelateerde `test_csv_import` blijft rood (CSV vs XLSX, bestond al).

- [ ] **Step 2: Frontend-build**

Run: `cd frontend && npm run build`
Expected: slaagt.

- [ ] **Step 3: Handmatige check (lokaal of na deploy naar CT102)**
  - Kies een vestiging → klas-dropdown vult zich met de aanwezige klassen.
  - Filter op een klas → overzicht toont alleen die klas.
  - Rapport → "Per klas" → "Huidige klas (X)" preview/PDF toont mét + zonder kluisje.
  - Rapport → "Per klas" → "Alle klassen" toont per klas een sectie.
  - Bestaande rapporten (toewijzingen/inname) tonen nu een gevulde klas-kolom.

- [ ] **Step 4: Deploy** (apart van dit plan, na akkoord Vincent): push naar `master`, dan update-knop / `kluisjes-update` op CT102, daarna CT101.

---

## Notities
- Geen Excel (bewust buiten scope, mogelijk later).
- "Zonder kluisje" en de volledigheid van de klassenlijst leunen op de `leerlingen`-tabel (Magister-sync). Geen sync → die lijsten blijven leeg; geen fout.
- Géén `Co-Authored-By`-trailer in commits (gebruikersvoorkeur).
