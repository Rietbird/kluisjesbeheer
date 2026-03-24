import sqlite3
import pytest

def test_tables_created(db):
    """All required tables exist after init."""
    cursor = db.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
    tables = [row[0] for row in cursor.fetchall()]
    assert 'vestigingen' in tables
    assert 'clusters' in tables
    assert 'kluisjes' in tables
    assert 'toewijzingen' in tables
    assert 'instellingen' in tables

def test_kluisnummer_unique_per_vestiging(db):
    """Cannot create duplicate kluisnummer in same vestiging."""
    db.execute("INSERT INTO vestigingen (naam) VALUES ('Hoofdgebouw')")
    db.execute("INSERT INTO clusters (vestiging_id, naam, standaard_borg) VALUES (1, 'Gang A', 15.00)")
    db.execute("INSERT INTO kluisjes (cluster_id, vestiging_id, kluisnummer, sleutelnummer, status) VALUES (1, 1, 'P001', 'S-001', 'vrij')")
    db.commit()
    with pytest.raises(sqlite3.IntegrityError):
        db.execute("INSERT INTO kluisjes (cluster_id, vestiging_id, kluisnummer, sleutelnummer, status) VALUES (1, 1, 'P001', 'S-002', 'vrij')")

def test_kluisnummer_allowed_different_vestiging(db):
    """Same kluisnummer allowed in different vestigingen."""
    db.execute("INSERT INTO vestigingen (naam) VALUES ('Hoofdgebouw')")
    db.execute("INSERT INTO vestigingen (naam) VALUES ('Dependance')")
    db.execute("INSERT INTO clusters (vestiging_id, naam, standaard_borg) VALUES (1, 'Gang A', 15.00)")
    db.execute("INSERT INTO clusters (vestiging_id, naam, standaard_borg) VALUES (2, 'Gang B', 15.00)")
    db.execute("INSERT INTO kluisjes (cluster_id, vestiging_id, kluisnummer, sleutelnummer, status) VALUES (1, 1, 'P001', 'S-001', 'vrij')")
    db.execute("INSERT INTO kluisjes (cluster_id, vestiging_id, kluisnummer, sleutelnummer, status) VALUES (2, 2, 'P001', 'S-101', 'vrij')")
    db.commit()

def test_unique_active_toewijzing_per_kluisje(db):
    """Cannot have two active toewijzingen for the same kluisje."""
    db.execute("INSERT INTO vestigingen (naam) VALUES ('Hoofdgebouw')")
    db.execute("INSERT INTO clusters (vestiging_id, naam, standaard_borg) VALUES (1, 'Gang A', 15.00)")
    db.execute("INSERT INTO kluisjes (cluster_id, vestiging_id, kluisnummer, sleutelnummer, status) VALUES (1, 1, 'P001', 'S-001', 'uitgeleend')")
    db.execute("INSERT INTO toewijzingen (kluisje_id, leerling_stamnr, leerling_naam, leerling_klas, periode_van, periode_tot, borgbedrag, actief) VALUES (1, '22001', 'Test', '2A', '2026-01-01', '2026-07-31', 15.00, 1)")
    db.commit()
    with pytest.raises(sqlite3.IntegrityError):
        db.execute("INSERT INTO toewijzingen (kluisje_id, leerling_stamnr, leerling_naam, leerling_klas, periode_van, periode_tot, borgbedrag, actief) VALUES (1, '22002', 'Test2', '3B', '2026-01-01', '2026-07-31', 15.00, 1)")

def test_soft_deleted_kluisnummer_reusable(db):
    """Soft-deleted kluisje allows same kluisnummer to be reused."""
    db.execute("INSERT INTO vestigingen (naam) VALUES ('Hoofdgebouw')")
    db.execute("INSERT INTO clusters (vestiging_id, naam, standaard_borg) VALUES (1, 'Gang A', 15.00)")
    db.execute("INSERT INTO kluisjes (cluster_id, vestiging_id, kluisnummer, sleutelnummer, status, verwijderd) VALUES (1, 1, 'P001', 'S-001', 'vrij', 1)")
    db.execute("INSERT INTO kluisjes (cluster_id, vestiging_id, kluisnummer, sleutelnummer, status) VALUES (1, 1, 'P001', 'S-002', 'vrij')")
    db.commit()

def test_timestamps_auto_set(db):
    """created_at and updated_at should be set automatically."""
    db.execute("INSERT INTO vestigingen (naam) VALUES ('Test')")
    db.commit()
    row = db.execute("SELECT created_at, updated_at FROM vestigingen WHERE id=1").fetchone()
    assert row[0] is not None
    assert row[1] is not None
