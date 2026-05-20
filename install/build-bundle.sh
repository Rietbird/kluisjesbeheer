#!/bin/bash
# Bouw een installatie-tarball van kluisjesbeheer voor uitrol op een nieuwe
# Debian 12/13 server (VMware / LXC / VPS). Output: install/dist/kluisjesbeheer-install.tgz
#
# Gebruik:
#   bash install/build-bundle.sh                  # vanuit repo-root
#   bash build-bundle.sh                          # vanuit install/
#
# De tarball bevat install.sh + backend/ + frontend/ (bronbestanden, geen build —
# install.sh draait `npm run build` op de doelserver).
#
# Bewust UITGESLOTEN: *.db, config.json, venv/, node_modules/, backups/, .git/,
# docs/, __pycache__/, .pytest_cache/, TheVault/, install/dist/

set -euo pipefail

# ============================================================
# Werkmap bepalen — script kan vanuit elke locatie aangeroepen worden
# ============================================================
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
DIST_DIR="$SCRIPT_DIR/dist"
BUNDLE_NAME="kluisjesbeheer-install"
TARBALL="$DIST_DIR/${BUNDLE_NAME}.tgz"

cd "$REPO_ROOT"

# ============================================================
# Sanity checks
# ============================================================
if [[ ! -f install.sh ]]; then
    echo "FOUT: install.sh niet gevonden in $REPO_ROOT" >&2
    echo "Draai dit script vanuit de kluisjesbeheer repo-root of install/." >&2
    exit 1
fi
if [[ ! -d backend || ! -d frontend ]]; then
    echo "FOUT: backend/ of frontend/ ontbreekt in $REPO_ROOT" >&2
    exit 1
fi

mkdir -p "$DIST_DIR"

# ============================================================
# Bundel bouwen
# ============================================================
echo "==> Bundel bouwen..."
echo "    bron:   $REPO_ROOT"
echo "    output: $TARBALL"

# tar --transform zorgt dat de tarball uitpakt naar kluisjesbeheer-install/
# i.p.v. losse install.sh + backend/ + frontend/ in cwd.
rm -f "$TARBALL"
tar czf "$TARBALL" \
    --exclude='*.db' \
    --exclude='*.db-journal' \
    --exclude='backend/config.json' \
    --exclude='backend/venv' \
    --exclude='backend/.venv' \
    --exclude='backend/.pytest_cache' \
    --exclude='backend/backups' \
    --exclude='backend/__pycache__' \
    --exclude='backend/*/__pycache__' \
    --exclude='frontend/node_modules' \
    --exclude='frontend/dist' \
    --exclude='.git' \
    --exclude='docs' \
    --exclude='TheVault' \
    --exclude='install/dist' \
    --transform="s,^,${BUNDLE_NAME}/," \
    install.sh backend frontend

# ============================================================
# Verificatie
# ============================================================
echo ""
echo "==> Verifieren..."

SIZE_BYTES=$(stat -c %s "$TARBALL" 2>/dev/null || stat -f %z "$TARBALL")
SIZE_KB=$(( SIZE_BYTES / 1024 ))
FILE_COUNT=$(tar tzf "$TARBALL" | wc -l)
echo "    grootte:  ${SIZE_KB} KB"
echo "    bestanden: $FILE_COUNT"

# Check op secrets/state die er niet in zouden mogen
echo "    secret-scan:"
LEAKS=$(tar tzf "$TARBALL" | grep -E '(\.db$|config\.json|venv/|node_modules|backups/|\.git/|\.pytest_cache)' || true)
if [[ -n "$LEAKS" ]]; then
    echo "    !! GEVONDEN — handmatig nakijken:"
    echo "$LEAKS" | sed 's/^/        /'
    exit 1
else
    echo "    OK (geen db, config.json, venv, node_modules, backups, .git)"
fi

# Check op aanwezigheid kritieke bestanden
echo "    kern-bestanden:"
TARBALL_LIST=$(tar tzf "$TARBALL")
for f in "${BUNDLE_NAME}/install.sh" \
         "${BUNDLE_NAME}/backend/app.py" \
         "${BUNDLE_NAME}/backend/cron_sync.py" \
         "${BUNDLE_NAME}/backend/magister_client.py" \
         "${BUNDLE_NAME}/backend/requirements.txt" \
         "${BUNDLE_NAME}/frontend/package.json" \
         "${BUNDLE_NAME}/frontend/vite.config.js"; do
    if echo "$TARBALL_LIST" | grep -qFx "$f"; then
        echo "        OK  $f"
    else
        echo "        !!  ONTBREEKT: $f"
        exit 1
    fi
done

echo ""
echo "==> Klaar."
echo "    $TARBALL"
echo ""
echo "Volgende stap: zie install/README.md voor kopieer-instructies."
