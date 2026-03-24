CREATE TABLE IF NOT EXISTS vestigingen (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    naam TEXT NOT NULL,
    adres TEXT DEFAULT '',
    created_at DATETIME DEFAULT (datetime('now')),
    updated_at DATETIME DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS clusters (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    vestiging_id INTEGER NOT NULL REFERENCES vestigingen(id),
    naam TEXT NOT NULL,
    standaard_borg REAL DEFAULT 0.0,
    created_at DATETIME DEFAULT (datetime('now')),
    updated_at DATETIME DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS kluisjes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    cluster_id INTEGER NOT NULL REFERENCES clusters(id),
    vestiging_id INTEGER NOT NULL REFERENCES vestigingen(id),
    kluisnummer TEXT NOT NULL,
    sleutelnummer TEXT DEFAULT '',
    locatie TEXT DEFAULT '',
    status TEXT NOT NULL DEFAULT 'vrij' CHECK(status IN ('vrij', 'uitgeleend', 'defect')),
    opmerkingen TEXT DEFAULT '',
    verwijderd INTEGER NOT NULL DEFAULT 0,
    created_at DATETIME DEFAULT (datetime('now')),
    updated_at DATETIME DEFAULT (datetime('now'))
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_kluisnummer_per_vestiging
    ON kluisjes(vestiging_id, kluisnummer) WHERE verwijderd = 0;

CREATE TABLE IF NOT EXISTS toewijzingen (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    kluisje_id INTEGER NOT NULL REFERENCES kluisjes(id),
    leerling_stamnr TEXT NOT NULL,
    leerling_naam TEXT NOT NULL,
    leerling_klas TEXT DEFAULT '',
    periode_van DATE NOT NULL,
    periode_tot DATE NOT NULL,
    borgbedrag REAL DEFAULT 0.0,
    borg_betaald INTEGER NOT NULL DEFAULT 0,
    borg_teruggestort INTEGER NOT NULL DEFAULT 0,
    sleutel_ingeleverd INTEGER DEFAULT NULL,
    einddatum DATE DEFAULT NULL,
    opmerking TEXT DEFAULT '',
    actief INTEGER NOT NULL DEFAULT 1,
    aangemaakt_door TEXT DEFAULT '',
    created_at DATETIME DEFAULT (datetime('now')),
    updated_at DATETIME DEFAULT (datetime('now'))
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_active_toewijzing_per_kluisje
    ON toewijzingen(kluisje_id) WHERE actief = 1;

CREATE TABLE IF NOT EXISTS instellingen (
    key TEXT PRIMARY KEY,
    value TEXT DEFAULT ''
);
