# Voorinschrijving leerlingen volgend schooljaar - Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Leerlingen van het komende schooljaar vooraf in de app zetten (klasloos, met een vlag) zodat conciërges ze nu al aan vrije kluisjes kunnen koppelen; op 1-8 nemen ze automatisch hun echte klas over en valt de vlag weg.

**Architecture:** Een aparte import (los van de gewone Magister-sync) haalt de volgend-jaars leerlingen op uit een custom Magister Decibel DD-lijst via `Data.GetData`, en schrijft ze klasloos in `leerlingen` met `nieuw_voor_schooljaar` gezet - zonder vertrokken-markering. De dagelijkse sync beschermt die leerlingen tot 1-8 en wist de vlag zodra ze actief binnenkomen. De klas op een gekoppeld kluisje volgt via een `COALESCE(snapshot, live)` op de leesquery (zelfde patroon als de klas-fix van 16-17 juni), niet via een snapshot-mutatie.

**Tech Stack:** Flask + SQLite (backend), pytest (tests), React/Vite (frontend), Magister SWP-webservice (`library=Data&function=GetData`).

## Global Constraints

- **Bron = Decibel DD-lijst via `library=Data&function=GetData&Layout=<naam>`** - NIET `library=ADFuncties` (dat is alleen voor de vaste `GetActiveStudents`). Zie `docs/decibel/sql-get-kluisjes-voorinschrijving.sql` + `c:/Projects/isk-analyse/docs/decibel/aanroep-patroon.md`.
- **Klasloos importeren** - `klas=''`. De nieuwe klas (bijv. "1A") botst met de huidige "1A"; klas komt op 1-8 via de gewone sync.
- **De import doet GEEN vertrokken-markering** (eigen functie, niet `sync_leerlingen_to_db`).
- **Lijstnaam configureerbaar** via `instellingen.voorinschrijving_lijst`; default `sql-get-kluisjes-voorinschrijving`.
- **Service-account per school**: Erasmus vermoedelijk `webuser`, Hengelo `Kluisjesmodule` (in de DB-instelling `magister_user`, niet in deze code).
- **React + SQLite-bool**: render `nieuw_voor_schooljaar` conditioneel met een expliciete check (geen kale `0`/`''` in JSX) - zie memory `feedback_react_sqlite_bool`.
- **XML-parsing** volgt het bestaande `magister_client.py` (stdlib `xml.etree.ElementTree`). `defusedxml` (zoals in isk-analyse) is een eenvoudige hardening-swap tegen XXE/billion-laughs als gewenst; de SWP-server is intern en vertrouwd, dus het risico is laag. Bij invoeren: in `magister_client.py` `import defusedxml.ElementTree as ET` en `defusedxml` aan `requirements.txt` toevoegen.
- **Commits zonder `Co-Authored-By`-trailer.**

## Pre-flight (maandag, vóór Task 5/6 live getest worden)

De webservice-keten is op SQL-niveau bewezen maar nog niet end-to-end via `GetData`. De unit-tests in Task 5/6 gebruiken **mocks**, dus bouwen kan al. Vóór live gebruik één keer handmatig verifiëren op CT101 (Erasmus, 10.20.0.15, direct SSH):

```bash
# spike4.py staat klaar in de sessie-scratchpad; kopieer naar de backend en draai:
scp -P 22 spike4.py root@10.20.0.15:/opt/kluisjesbeheer/backend/spike4.py
ssh -p 22 root@10.20.0.15 "cd /opt/kluisjesbeheer/backend && /opt/kluisjesbeheer/.venv/bin/python spike4.py 'sql-get-kluisjes-voorinschrijving' ''; rm -f spike4.py"
# Verwacht: Result=True, ~436 rijen, kolommen Leerlingnummer/Voornaam/Tussenvoegsel/Achternaam/Email/Locatie/Klas
```
Noteer de **wrapper-tag** + de exacte kolomnamen uit de respons; controleer dat ze matchen met `_map_record` (Task 6).

---

### Task 1: DB-kolom `nieuw_voor_schooljaar` op leerlingen

**Files:**
- Modify: `backend/schema.sql` (leerlingen-tabel)
- Modify: `backend/db.py` (init_db migratie-blok)
- Test: `backend/tests/test_voorinschrijving.py` (nieuw)

**Interfaces:**
- Produces: kolom `leerlingen.nieuw_voor_schooljaar TEXT DEFAULT NULL` (NULL = gewone leerling; anders het doel-schooljaar, bijv. `"2026-2027"`).

- [ ] **Step 1: Schrijf de falende test**

Maak `backend/tests/test_voorinschrijving.py`:
```python
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))


def test_nieuw_voor_schooljaar_column_exists(db):
    cols = [r[1] for r in db.execute("PRAGMA table_info(leerlingen)").fetchall()]
    assert 'nieuw_voor_schooljaar' in cols
```

- [ ] **Step 2: Run de test - verwacht FAIL**

Run: `cd backend && pytest tests/test_voorinschrijving.py::test_nieuw_voor_schooljaar_column_exists -v`
Expected: FAIL (kolom bestaat nog niet).

- [ ] **Step 3: Voeg de kolom toe aan het schema**

In `backend/schema.sql`, in de `leerlingen`-tabel, voeg toe direct na de regel `vertrokken_op DATE DEFAULT NULL,`:
```sql
    nieuw_voor_schooljaar TEXT DEFAULT NULL,
```

- [ ] **Step 4: Voeg de idempotente migratie toe**

In `backend/db.py`, in `init_db`, naast de andere `ALTER TABLE`-migraties (bijv. na het `vertrokken_op`-blok rond regel 127-132):
```python
    # Migration: nieuw_voor_schooljaar - voorinschrijving leerlingen volgend schooljaar
    try:
        conn.execute("ALTER TABLE leerlingen ADD COLUMN nieuw_voor_schooljaar TEXT DEFAULT NULL")
        conn.commit()
    except Exception:
        pass  # kolom bestaat al
```

- [ ] **Step 5: Run de test - verwacht PASS**

Run: `cd backend && pytest tests/test_voorinschrijving.py::test_nieuw_voor_schooljaar_column_exists -v`
Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add backend/schema.sql backend/db.py backend/tests/test_voorinschrijving.py
git commit -m "feat(voorinschrijving): add nieuw_voor_schooljaar column to leerlingen"
```

---

### Task 2: Import-core `import_voorinschrijvingen()`

**Files:**
- Modify: `backend/leerling_sync.py`
- Test: `backend/tests/test_voorinschrijving.py`

**Interfaces:**
- Consumes: kolom uit Task 1.
- Produces: `import_voorinschrijvingen(db, leerlingen, schooljaar) -> {'imported': int}`. `leerlingen` is een lijst dicts met minimaal `stamnr`, `naam`; optioneel `roepnaam`, `tussenvoegsel`, `achternaam`, `email`, `locatie`. Schrijft klasloos + `nieuw_voor_schooljaar=schooljaar`, markeert niemand vertrokken, en laat de bestaande `klas` van een al-bestaande leerling ongemoeid.

- [ ] **Step 1: Schrijf de falende tests**

Voeg toe aan `backend/tests/test_voorinschrijving.py`:
```python
from leerling_sync import import_voorinschrijvingen, sync_leerlingen_to_db


def _vi(stamnr, naam='Brugklasser', **kw):
    return dict(stamnr=stamnr, naam=naam, locatie='Hoofd', **kw)


def _ll(stamnr, naam='Naam', klas='1A'):
    return dict(stamnr=stamnr, naam=naam, roepnaam='', tussenvoegsel='',
               achternaam=naam, email='', klas=klas, leerjaar='1', studie='', locatie='Hoofd')


def test_import_sets_flag_klasloos_no_vertrokken(db):
    res = import_voorinschrijvingen(db, [_vi('9001')], '2026-2027')
    row = db.execute("SELECT klas, nieuw_voor_schooljaar, vertrokken_op, locatie "
                     "FROM leerlingen WHERE stamnr='9001'").fetchone()
    assert row['klas'] == ''
    assert row['nieuw_voor_schooljaar'] == '2026-2027'
    assert row['vertrokken_op'] is None
    assert row['locatie'] == 'Hoofd'
    assert res['imported'] == 1


def test_import_does_not_mark_existing_vertrokken(db):
    sync_leerlingen_to_db(db, [_ll('1'), _ll('2')])
    import_voorinschrijvingen(db, [_vi('9001')], '2026-2027')
    n = db.execute("SELECT COUNT(*) AS n FROM leerlingen WHERE vertrokken_op IS NOT NULL").fetchone()['n']
    assert n == 0


def test_import_preserves_klas_of_existing_student(db):
    sync_leerlingen_to_db(db, [_ll('1', klas='3A')])
    import_voorinschrijvingen(db, [dict(stamnr='1', naam='X', locatie='Hoofd')], '2026-2027')
    assert db.execute("SELECT klas FROM leerlingen WHERE stamnr='1'").fetchone()['klas'] == '3A'
```

- [ ] **Step 2: Run de tests - verwacht FAIL**

Run: `cd backend && pytest tests/test_voorinschrijving.py -k import -v`
Expected: FAIL (`ImportError: cannot import name 'import_voorinschrijvingen'`).

- [ ] **Step 3: Implementeer `import_voorinschrijvingen`**

Voeg onderaan `backend/leerling_sync.py` toe:
```python
def import_voorinschrijvingen(db, leerlingen, schooljaar):
    """Upsert pre-registration students for an upcoming school year.

    Writes klasloos (klas='') with nieuw_voor_schooljaar=schooljaar set. Does NOT
    mark anyone vertrokken (unlike sync_leerlingen_to_db) and leaves the existing
    klas of an already-known student untouched (a doorstromer keeps its current
    class). Returns {'imported': <count>}.
    """
    imported = 0
    for l in leerlingen:
        db.execute('''
            INSERT INTO leerlingen
                (stamnr, naam, roepnaam, tussenvoegsel, achternaam, email,
                 klas, leerjaar, studie, locatie, nieuw_voor_schooljaar, vertrokken_op, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, '', '', '', ?, ?, NULL, datetime('now'))
            ON CONFLICT(stamnr) DO UPDATE SET
                naam=excluded.naam, roepnaam=excluded.roepnaam, tussenvoegsel=excluded.tussenvoegsel,
                achternaam=excluded.achternaam, email=excluded.email, locatie=excluded.locatie,
                nieuw_voor_schooljaar=excluded.nieuw_voor_schooljaar,
                vertrokken_op=NULL, updated_at=datetime('now')
        ''', (
            l['stamnr'], l['naam'], l.get('roepnaam', ''), l.get('tussenvoegsel', ''),
            l.get('achternaam', ''), l.get('email', ''), l.get('locatie', ''), schooljaar,
        ))
        imported += 1
    db.commit()
    return {'imported': imported}
```

- [ ] **Step 4: Run de tests - verwacht PASS**

Run: `cd backend && pytest tests/test_voorinschrijving.py -k import -v`
Expected: PASS (3 tests).

- [ ] **Step 5: Commit**

```bash
git add backend/leerling_sync.py backend/tests/test_voorinschrijving.py
git commit -m "feat(voorinschrijving): add import_voorinschrijvingen (klasloos, no vertrokken-marking)"
```

---

### Task 3: Sync - bescherming vóór 1-8 + vlag wissen bij activatie

**Files:**
- Modify: `backend/leerling_sync.py` (`sync_leerlingen_to_db`)
- Test: `backend/tests/test_voorinschrijving.py`

**Interfaces:**
- Consumes: `import_voorinschrijvingen` (Task 2), de kolom (Task 1).
- Produces: `sync_leerlingen_to_db` slaat de vertrokken-markering over voor een voorinschrijving zolang `date('now') < <startjaar>-08-01`, en wist `nieuw_voor_schooljaar` zodra een leerling actief via de sync binnenkomt.

- [ ] **Step 1: Schrijf de falende tests**

Voeg toe aan `backend/tests/test_voorinschrijving.py`:
```python
def test_voorinschrijving_protected_before_rollover(db):
    # doel-schooljaar ver in de toekomst -> altijd "vóór 1-8"
    import_voorinschrijvingen(db, [_vi('9001')], '2099-2100')
    # gewone sync zonder 9001 mag 'm NIET vertrokken-markeren
    sync_leerlingen_to_db(db, [_ll('1'), _ll('2')])
    assert db.execute("SELECT vertrokken_op FROM leerlingen WHERE stamnr='9001'").fetchone()['vertrokken_op'] is None


def test_flag_cleared_and_klas_set_when_active(db):
    import_voorinschrijvingen(db, [_vi('9001')], '2026-2027')
    # leerling komt nu actief binnen met echte klas
    sync_leerlingen_to_db(db, [_ll('9001', klas='1A'), _ll('1')])
    row = db.execute("SELECT klas, nieuw_voor_schooljaar FROM leerlingen WHERE stamnr='9001'").fetchone()
    assert row['nieuw_voor_schooljaar'] is None
    assert row['klas'] == '1A'


def test_noshow_marked_vertrokken_after_rollover(db):
    # doel-schooljaar in het verleden -> bescherming is vervallen
    import_voorinschrijvingen(db, [_vi('9001')], '2000-2001')
    sync_leerlingen_to_db(db, [_ll('1'), _ll('2')])
    assert db.execute("SELECT vertrokken_op FROM leerlingen WHERE stamnr='9001'").fetchone()['vertrokken_op'] is not None
```

- [ ] **Step 2: Run de tests - verwacht FAIL**

Run: `cd backend && pytest tests/test_voorinschrijving.py -k "protected or cleared or noshow" -v`
Expected: FAIL (`test_voorinschrijving_protected_before_rollover` markeert nu wél, `test_flag_cleared...` houdt de vlag).

- [ ] **Step 3: Wis de vlag bij activatie (upsert)**

In `backend/leerling_sync.py`, in `sync_leerlingen_to_db`, in de `ON CONFLICT(stamnr) DO UPDATE SET ...` van de upsert (regel ~35-39), voeg toe (bijv. direct na `vertrokken_op=NULL,`):
```python
                nieuw_voor_schooljaar=NULL,
```
Zodat het SET-blok o.a. `vertrokken_op=NULL, nieuw_voor_schooljaar=NULL, updated_at=datetime('now')` bevat. (Een leerling die in `GetActiveStudents` zit, is actief → vlag hoort weg.)

- [ ] **Step 4: Bescherm voorinschrijvingen in de vertrokken-markering**

In dezelfde functie, in de vertrokken-`UPDATE` (regel ~55-58), breid de `WHERE` uit:
```python
    cur = db.execute(f'''
        UPDATE leerlingen SET vertrokken_op = date('now'), updated_at = datetime('now')
        WHERE stamnr NOT IN ({placeholders}) AND vertrokken_op IS NULL
          AND NOT (
                nieuw_voor_schooljaar IS NOT NULL
                AND date('now') < (substr(nieuw_voor_schooljaar, 1, 4) || '-08-01')
          )
    ''', list(synced_stamnrs))
```

- [ ] **Step 5: Run de tests - verwacht PASS**

Run: `cd backend && pytest tests/test_voorinschrijving.py -v && pytest tests/test_leerling_sync.py -v`
Expected: alle PASS (de bestaande sync-tests blijven groen - gewone leerlingen hebben `nieuw_voor_schooljaar IS NULL`, dus de `NOT(...)` is altijd waar voor hen).

- [ ] **Step 6: Commit**

```bash
git add backend/leerling_sync.py backend/tests/test_voorinschrijving.py
git commit -m "feat(voorinschrijving): protect flagged students before 1-8 and clear flag on activation"
```

---

### Task 4: Effectieve klas + vlag in `actieve_toewijzingen`

**Files:**
- Modify: `backend/api_toewijzingen.py` (`actieve_toewijzingen`, query rond regel 287-294)
- Test: `backend/tests/test_voorinschrijving.py`

**Interfaces:**
- Consumes: kolom (Task 1).
- Produces: `GET /api/toewijzingen/actief` geeft per rij extra velden `leerling_klas_effectief` (= `COALESCE(NULLIF(TRIM(t.leerling_klas),''), l.klas)`) en `leerling_nieuw_voor_schooljaar` (= `l.nieuw_voor_schooljaar`). De bestaande `leerling_klas` (snapshot) blijft ongewijzigd beschikbaar.

- [ ] **Step 1: Schrijf de falende test**

Voeg toe aan `backend/tests/test_voorinschrijving.py`:
```python
def _seed_kluisje_met_toewijzing(db, stamnr, snapshot_klas=''):
    db.execute("INSERT INTO vestigingen (id, naam) VALUES (1, 'Hoofd')")
    db.execute("INSERT INTO clusters (id, vestiging_id, naam) VALUES (1, 1, 'C1')")
    db.execute("INSERT INTO kluisjes (id, cluster_id, vestiging_id, kluisnummer, status) "
               "VALUES (1, 1, 1, 'A001', 'uitgeleend')")
    db.execute("INSERT INTO toewijzingen (kluisje_id, leerling_stamnr, leerling_naam, leerling_klas, "
               "periode_van, periode_tot, actief) VALUES (1, ?, 'Brug', ?, '2026-08-01', '2027-07-31', 1)",
               (stamnr, snapshot_klas))
    db.commit()


def test_actieve_toewijzingen_effective_klas_and_flag(client, db, db_path):
    # voorinschrijving (klasloos) + lege snapshot, daarna krijgt de leerling z'n live klas
    import_voorinschrijvingen(db, [_vi('9001')], '2026-2027')
    _seed_kluisje_met_toewijzing(db, '9001', snapshot_klas='')
    db.execute("UPDATE leerlingen SET klas='1A' WHERE stamnr='9001'")  # alsof 1-8 voorbij is
    db.commit()
    rows = client.get('/api/toewijzingen/actief').get_json()
    row = next(r for r in rows if r['leerling_stamnr'] == '9001')
    assert row['leerling_klas'] == ''                       # snapshot ongewijzigd
    assert row['leerling_klas_effectief'] == '1A'           # valt terug op live klas
    assert row['leerling_nieuw_voor_schooljaar'] == '2026-2027'
```

- [ ] **Step 2: Run de test - verwacht FAIL**

Run: `cd backend && pytest tests/test_voorinschrijving.py::test_actieve_toewijzingen_effective_klas_and_flag -v`
Expected: FAIL (`KeyError: 'leerling_klas_effectief'`).

- [ ] **Step 3: Breid de query uit**

In `backend/api_toewijzingen.py`, in `actieve_toewijzingen`, in de `SELECT` (regel ~288-294), voeg twee kolommen toe aan de selectie (na `l.vertrokken_op AS leerling_vertrokken_op`):
```python
               l.vertrokken_op AS leerling_vertrokken_op,
               l.nieuw_voor_schooljaar AS leerling_nieuw_voor_schooljaar,
               COALESCE(NULLIF(TRIM(t.leerling_klas), ''), l.klas) AS leerling_klas_effectief
```

- [ ] **Step 4: Run de test - verwacht PASS**

Run: `cd backend && pytest tests/test_voorinschrijving.py::test_actieve_toewijzingen_effective_klas_and_flag -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add backend/api_toewijzingen.py backend/tests/test_voorinschrijving.py
git commit -m "feat(voorinschrijving): expose effective klas + flag on active toewijzingen"
```

---

### Task 5: Webservice - `get_data()` op de Magister-client

**Files:**
- Modify: `backend/magister_client.py`
- Test: `backend/tests/test_voorinschrijving.py`

**Interfaces:**
- Produces: `MagisterClient.get_data(self, layout, parameters='') -> list[dict]`. Roept `library=Data&function=GetData` aan, parse de generieke `<Table><Wrapper><Item>…` naar een lijst dicts (kolom-tag → tekst). Gooit `ConnectionError` (met `safe_error`-veilige boodschap) bij fouten.

- [ ] **Step 1: Schrijf de falende test**

Voeg toe aan `backend/tests/test_voorinschrijving.py`:
```python
def test_get_data_parses_records(monkeypatch):
    import magister_client as mc
    client = mc.MagisterClient(url='http://x', user='u', password='p')
    monkeypatch.setattr(client, '_login', lambda: 'TOKEN')
    xml = (
        '<Response><Result>True</Result><Table><Voorinschrijvingen>'
        '<Voorinschrijving><Leerlingnummer>9001</Leerlingnummer><Voornaam>Bo</Voornaam>'
        '<Tussenvoegsel></Tussenvoegsel><Achternaam>Jansen</Achternaam>'
        '<Locatie>HET ERASMUS vestiging PrO</Locatie></Voorinschrijving>'
        '<Voorinschrijving><Leerlingnummer>9002</Leerlingnummer><Voornaam>Sam</Voornaam>'
        '<Tussenvoegsel>de</Tussenvoegsel><Achternaam>Vos</Achternaam>'
        '<Locatie>HET ERASMUS vestiging PrO</Locatie></Voorinschrijving>'
        '</Voorinschrijvingen></Table></Response>'
    )

    class FakeResp:
        text = xml

    monkeypatch.setattr(mc.requests, 'get', lambda *a, **k: FakeResp())
    records = client.get_data('sql-get-kluisjes-voorinschrijving')
    assert len(records) == 2
    assert records[0]['Leerlingnummer'] == '9001'
    assert records[0]['Voornaam'] == 'Bo'
    assert records[1]['Tussenvoegsel'] == 'de'
```

- [ ] **Step 2: Run de test - verwacht FAIL**

Run: `cd backend && pytest tests/test_voorinschrijving.py::test_get_data_parses_records -v`
Expected: FAIL (`AttributeError: 'MagisterClient' object has no attribute 'get_data'`).

- [ ] **Step 3: Implementeer `get_data`**

In `backend/magister_client.py`, in de `MagisterClient`-klasse (bijv. na `get_klassen`), voeg toe:
```python
    def get_data(self, layout, parameters=''):
        """Run a Magister Decibel DD-lijst via Data.GetData and return a list of
        dicts (one per record, column-tag -> text).

        DD-lijsten gaan via library=Data (NIET ADFuncties). Parameters vullen
        #naam#-placeholders in de querydefinitie, vorm 'naam=waarde;naam2=waarde2'.
        Zie docs/decibel/aanroep-patroon.md.
        """
        token = self._login()
        params = {
            'library': 'Data',
            'function': 'GetData',
            'SessionToken': token,
            'Layout': layout,
            'Parameters': parameters,
            'Type': 'XML',
        }
        try:
            resp = requests.get(self.url, params=params, timeout=60, verify=MAGISTER_SSL_VERIFY)
            root = ET.fromstring(resp.text)
        except (requests.Timeout, requests.ConnectionError):
            raise ConnectionError('Geen verbinding met de Magister-webservice tijdens GetData (poort 8800).')
        except requests.RequestException:
            raise ConnectionError('Magister-webservice gaf een onverwacht antwoord (HTTP-fout).')
        except ET.ParseError:
            raise ConnectionError('Magister-webservice gaf een ongeldig antwoord (geen geldige XML).')
        except Exception:
            raise ConnectionError('Onverwachte fout bij het benaderen van de Magister-webservice.')

        if root.findtext('Result') == 'False':
            msg = root.findtext('Fout_omschrijving') or root.findtext('ResultMessage') or 'onbekende fout'
            raise ConnectionError(f'Magister GetData mislukt voor lijst "{layout}": {msg}')
        exc = root.findtext('Exception')
        if exc:
            raise ConnectionError(f'Medius fout: {exc}: {root.findtext("ExceptionMsg")}')

        table = root.find('Table')
        if table is None:
            return []
        wrappers = list(table)
        if not wrappers:
            return []
        return [{child.tag: (child.text or '') for child in item} for item in list(wrappers[0])]
```

- [ ] **Step 4: Run de test - verwacht PASS**

Run: `cd backend && pytest tests/test_voorinschrijving.py::test_get_data_parses_records -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add backend/magister_client.py backend/tests/test_voorinschrijving.py
git commit -m "feat(voorinschrijving): add MagisterClient.get_data for Decibel DD-lijsten"
```

---

### Task 6: Import-route + blueprint

**Files:**
- Create: `backend/api_voorinschrijving.py`
- Modify: `backend/app.py` (blueprint registreren)
- Test: `backend/tests/test_voorinschrijving.py`

**Interfaces:**
- Consumes: `magister.get_data` (Task 5), `import_voorinschrijvingen` (Task 2).
- Produces: `POST /api/leerlingen/import-voorinschrijving` (`@beheerder_required`). Body: `{"schooljaar": "2026-2027"}`. Haalt de DD-lijst op (lijstnaam uit `instellingen.voorinschrijving_lijst`, default `sql-get-kluisjes-voorinschrijving`; `Parameters=peildatum=<startjaar>-08-01`), mapt de kolommen en importeert. Geeft `{"geimporteerd": int, "schooljaar": str, "bron": "webservice"}`.

- [ ] **Step 1: Schrijf de falende test**

Voeg toe aan `backend/tests/test_voorinschrijving.py`:
```python
def test_import_voorinschrijving_route(client, monkeypatch):
    import magister_client
    captured = {}

    def fake_get_data(layout, parameters=''):
        captured['layout'] = layout
        captured['parameters'] = parameters
        return [
            {'Leerlingnummer': '9001', 'Voornaam': 'Bo', 'Tussenvoegsel': '',
             'Achternaam': 'Jansen', 'Email': '9001@school.nl', 'Locatie': 'Hoofd'},
            {'Leerlingnummer': '9002', 'Voornaam': 'Sam', 'Tussenvoegsel': 'de',
             'Achternaam': 'Vos', 'Email': '9002@school.nl', 'Locatie': 'Hoofd'},
        ]

    monkeypatch.setattr(magister_client.magister, 'get_data', fake_get_data)
    monkeypatch.setattr(magister_client.magister, 'flush_cache', lambda: None)

    resp = client.post('/api/leerlingen/import-voorinschrijving', json={'schooljaar': '2026-2027'})
    assert resp.status_code == 200
    body = resp.get_json()
    assert body['geimporteerd'] == 2
    assert captured['layout'] == 'sql-get-kluisjes-voorinschrijving'
    assert captured['parameters'] == 'peildatum=2026-08-01'

    # end-to-end: vindbaar in de zoek, met vlag, klasloos
    found = client.get('/api/magister/leerlingen?q=Jansen').get_json()
    bo = next(l for l in found if l['stamnr'] == '9001')
    assert bo['nieuw_voor_schooljaar'] == '2026-2027'
    assert bo['naam'] == 'Bo Jansen'
    assert bo['klas'] == ''


def test_import_voorinschrijving_requires_schooljaar(client):
    resp = client.post('/api/leerlingen/import-voorinschrijving', json={})
    assert resp.status_code == 400
```

- [ ] **Step 2: Run de tests - verwacht FAIL**

Run: `cd backend && pytest tests/test_voorinschrijving.py -k route -v`
Expected: FAIL (404 - route bestaat nog niet).

- [ ] **Step 3: Maak de blueprint**

Maak `backend/api_voorinschrijving.py`:
```python
from flask import Blueprint, request, jsonify, g
from auth import beheerder_required
from magister_client import magister, safe_error as _safe_error
from leerling_sync import import_voorinschrijvingen

voorinschrijving_bp = Blueprint('voorinschrijving', __name__, url_prefix='/api')

DEFAULT_LIST = 'sql-get-kluisjes-voorinschrijving'


def _peildatum_voor(schooljaar):
    """'2026-2027' -> '2026-08-01' (1 augustus = schooljaarwissel)."""
    start = schooljaar.split('-')[0]
    return f'{start}-08-01'


def _map_record(rec):
    """DD-lijst-record -> leerling-dict; stelt de volledige naam samen."""
    roepnaam = (rec.get('Voornaam') or '').strip()
    tussenvoegsel = (rec.get('Tussenvoegsel') or '').strip()
    achternaam = (rec.get('Achternaam') or '').strip()
    naam = ' '.join(p for p in [roepnaam, tussenvoegsel, achternaam] if p)
    return {
        'stamnr': (rec.get('Leerlingnummer') or '').strip(),
        'naam': naam,
        'roepnaam': roepnaam,
        'tussenvoegsel': tussenvoegsel,
        'achternaam': achternaam,
        'email': (rec.get('Email') or '').strip(),
        'locatie': (rec.get('Locatie') or '').strip(),
    }


@voorinschrijving_bp.route('/leerlingen/import-voorinschrijving', methods=['POST'])
@beheerder_required
def import_voorinschrijving():
    data = request.get_json() or {}
    schooljaar = (data.get('schooljaar') or '').strip()
    if not schooljaar or '-' not in schooljaar:
        return jsonify({'error': 'schooljaar is verplicht (vorm "2026-2027")'}), 400

    row = g.db.execute("SELECT value FROM instellingen WHERE key='voorinschrijving_lijst'").fetchone()
    layout = row['value'] if row and row['value'] else DEFAULT_LIST
    parameters = f'peildatum={_peildatum_voor(schooljaar)}'

    try:
        magister.flush_cache()
        records = magister.get_data(layout, parameters)
    except ConnectionError as e:
        return jsonify({'error': _safe_error(e)}), 502

    leerlingen = [_map_record(r) for r in records if (r.get('Leerlingnummer') or '').strip()]
    summary = import_voorinschrijvingen(g.db, leerlingen, schooljaar)
    return jsonify({'geimporteerd': summary['imported'], 'schooljaar': schooljaar, 'bron': 'webservice'})
```

- [ ] **Step 4: Registreer de blueprint**

In `backend/app.py`, bij de andere blueprint-registraties (rond regel 119, naast `from api_magister import magister_bp`):
```python
    from api_voorinschrijving import voorinschrijving_bp
    app.register_blueprint(voorinschrijving_bp)
```

- [ ] **Step 5: Run de tests - verwacht PASS**

Run: `cd backend && pytest tests/test_voorinschrijving.py -v`
Expected: alle PASS.

- [ ] **Step 6: Commit**

```bash
git add backend/api_voorinschrijving.py backend/app.py backend/tests/test_voorinschrijving.py
git commit -m "feat(voorinschrijving): add import-voorinschrijving route via Decibel DD-lijst"
```

---

### Task 7: Frontend - import-knop (Onderhoud) + badge `'26-'27`

**Files:**
- Modify: `frontend/src/pages/Beheer.jsx` (Onderhoud - import-knop)
- Modify: `frontend/src/components/AssignForm.jsx` (badge in leerling-zoekresultaten)
- Modify: `frontend/src/components/LockerModal.jsx` (badge + effectieve klas op het kluisje)

**Interfaces:**
- Consumes: `POST /api/leerlingen/import-voorinschrijving` (Task 6); `nieuw_voor_schooljaar` op leerling-zoekresultaten (`GET /api/magister/leerlingen`, al via `SELECT *`); `leerling_nieuw_voor_schooljaar` + `leerling_klas_effectief` op `GET /api/toewijzingen/actief` (Task 4).

> **Frontend wordt klik-getest (geen pytest), volgens het projectpatroon.** Lees eerst de bestaande "Synchroniseer leerlingen"-knop in `Beheer.jsx` en gebruik die qua opzet (fetch + busy-state + resultaat-toast) als sjabloon.

- [ ] **Step 1: Helper voor het chip-label**

Voeg een klein hulpje toe (bovenin `AssignForm.jsx` en `LockerModal.jsx`, of in een gedeeld util-bestand als dat al bestaat):
```jsx
// "2026-2027" -> "'26-'27"
function schooljaarChip(sj) {
  const m = /^(\d{2})(\d{2})-(\d{2})(\d{2})$/.exec(sj || '');
  return m ? `'${m[2]}-'${m[4]}` : sj;
}
```

- [ ] **Step 2: Import-knop in Onderhoud (`Beheer.jsx`)**

Naast de bestaande "Synchroniseer leerlingen"-knop: een knop "Voorinschrijving volgend schooljaar importeren" met een schooljaar-veld (default = komend schooljaar). Op klik:
```jsx
const res = await fetch('/api/leerlingen/import-voorinschrijving', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ schooljaar }),
});
const data = await res.json();
// toon: res.ok ? `${data.geimporteerd} leerlingen geïmporteerd voor ${data.schooljaar}` : data.error
```
Volg exact de busy/disabled/toast-afhandeling van de bestaande sync-knop ernaast.

- [ ] **Step 3: Badge in de leerling-zoekresultaten (`AssignForm.jsx`)**

Waar een gevonden leerling wordt gerenderd (naam + klas), voeg conditioneel het chipje toe (expliciete check i.v.m. SQLite-bool):
```jsx
{leerling.nieuw_voor_schooljaar ? (
  <span className="ml-2 rounded bg-amber-100 px-1.5 py-0.5 text-xs font-medium text-amber-800"
        title="Voorinschrijving volgend schooljaar">
    {schooljaarChip(leerling.nieuw_voor_schooljaar)}
  </span>
) : null}
```

- [ ] **Step 4: Badge + effectieve klas op het kluisje (`LockerModal.jsx`)**

Gebruik voor de getoonde klas `toewijzing.leerling_klas_effectief ?? toewijzing.leerling_klas`, en toon het chipje als `toewijzing.leerling_nieuw_voor_schooljaar` gezet is (zelfde JSX als Step 3, met `toewijzing.leerling_nieuw_voor_schooljaar`).

- [ ] **Step 5: Build + klik-test**

```bash
cd frontend && npm run build
```
Klik-test (dev-login): Beheer → Onderhoud → import-knop draait en toont het aantal; in de toewijs-flow tonen voorinschrijvingen het chipje `'26-'27`; na het zetten van een live klas toont het kluisje die klas.

- [ ] **Step 6: Commit**

```bash
git add frontend/src/pages/Beheer.jsx frontend/src/components/AssignForm.jsx frontend/src/components/LockerModal.jsx
git commit -m "feat(voorinschrijving): import button in Onderhoud + 26-27 badge"
```

---

### Task 8 (optioneel, later): Excel-fallback als bron

**Files:**
- Modify: `backend/api_voorinschrijving.py` (extra route of `multipart`-tak)
- Test: `backend/tests/test_voorinschrijving.py`

Alleen bouwen als de webservice-bron onverhoopt niet bruikbaar blijkt. Voeg een tak toe die een geüpload `.xlsx` (kolommen `Stamnummer`, `Naam`, `Locatie`) parse't met `openpyxl` (hergebruik `_safe_load_xlsx` uit `api_kluisjes.py`), naar dezelfde `_map_record`-vorm mapt en via `import_voorinschrijvingen` wegschrijft. Test met een in-memory `openpyxl`-workbook. **YAGNI: niet bouwen tenzij nodig.**

---

## Self-Review

**Spec-dekking:**
- Datamodel (Deel 1) → Task 1. ✓
- Ophalen + importeren (Deel 2) → Task 5 (get_data) + Task 6 (route + map + import) + Task 2 (import-core). ✓
- Sync-aanpassing (Deel 3a bescherming + 3b vlag/klas) → Task 3 (bescherming + vlag-clear) + Task 4 (effectieve klas i.p.v. snapshot-mutatie, conform de spec-NB). ✓
- No-show (Deel 4) → Task 3 (`test_noshow_marked_vertrokken_after_rollover`). ✓
- UI (Deel 5: knop + chip) → Task 7. ✓
- Excel-achtervang → Task 8 (optioneel). ✓

**Afwijking van de spec (bewust):** Deel 3b "snapshot-refresh op de actieve toewijzing" is vervangen door de eenvoudiger **COALESCE(snapshot, live)** in `actieve_toewijzingen` (Task 4) - conform de NB in de spec, en consistent met de klas-fix van 16-17 juni (`GET /api/kluisjes`). Geen data-mutatie nodig.

**Placeholder-scan:** geen TBD/TODO in de tasks; alle stappen bevatten echte code/commando's.

**Type-consistentie:** `import_voorinschrijvingen(db, leerlingen, schooljaar)` (Task 2) wordt zo aangeroepen in Task 6; `get_data(layout, parameters='')` (Task 5) idem; nieuwe API-velden `leerling_klas_effectief` / `leerling_nieuw_voor_schooljaar` (Task 4) worden in Task 7 gebruikt; `nieuw_voor_schooljaar` consistent overal.
