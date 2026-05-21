"""Automatic daily SQLite backup with rolling retention.

Runs as a background thread inside the Flask app. Creates timestamped
copies using SQLite's built-in backup API (safe, even during writes).

Retention: 7 daily + 4 weekly backups.
"""
import os
import shutil
import sqlite3
import threading
import time
import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

from db import default_backups_dir
BACKUP_DIR = default_backups_dir()
DAILY_KEEP = 7
WEEKLY_KEEP = 4
INTERVAL_HOURS = 6  # check every 6 hours, backup once per day


def _ensure_dir():
    os.makedirs(BACKUP_DIR, exist_ok=True)


def create_backup(db_path, label=None):
    """Create a backup of the database. Returns the backup file path."""
    _ensure_dir()
    ts = datetime.now().strftime('%Y%m%d_%H%M%S')
    suffix = f'_{label}' if label else ''
    backup_name = f'kluisjesbeheer_{ts}{suffix}.db'
    backup_path = os.path.join(BACKUP_DIR, backup_name)

    # Use SQLite online backup API — safe during concurrent reads/writes
    src = sqlite3.connect(db_path)
    dst = sqlite3.connect(backup_path)
    try:
        src.backup(dst)
        logger.info(f'Backup created: {backup_name}')
    finally:
        dst.close()
        src.close()

    return backup_path


def cleanup_backups():
    """Remove old backups, keeping 7 daily + 4 weekly."""
    _ensure_dir()
    files = sorted([
        f for f in os.listdir(BACKUP_DIR)
        if f.startswith('kluisjesbeheer_') and f.endswith('.db')
        and '_predeploy' not in f  # never auto-delete pre-deploy backups
    ])

    if len(files) <= DAILY_KEEP:
        return

    now = datetime.now()
    keep = set()

    # Keep the most recent DAILY_KEEP backups
    for f in files[-DAILY_KEEP:]:
        keep.add(f)

    # Keep one per week for the last WEEKLY_KEEP weeks
    for weeks_ago in range(WEEKLY_KEEP):
        target_date = (now - timedelta(weeks=weeks_ago + 1)).date()
        best = None
        for f in files:
            try:
                ts_str = f.replace('kluisjesbeheer_', '').replace('.db', '').split('_')[0]
                fdate = datetime.strptime(ts_str, '%Y%m%d').date()
                if fdate <= target_date and (best is None or fdate > best[1]):
                    best = (f, fdate)
            except (ValueError, IndexError):
                continue
        if best:
            keep.add(best[0])

    for f in files:
        if f not in keep:
            path = os.path.join(BACKUP_DIR, f)
            try:
                os.remove(path)
                logger.info(f'Old backup removed: {f}')
            except OSError:
                pass


def _last_backup_today():
    """Check if a backup was already made today."""
    _ensure_dir()
    today = datetime.now().strftime('%Y%m%d')
    return any(
        f.startswith(f'kluisjesbeheer_{today}') and f.endswith('.db')
        for f in os.listdir(BACKUP_DIR)
    )


def _backup_loop(db_path):
    """Background thread: create daily backup + cleanup."""
    while True:
        try:
            if not _last_backup_today():
                create_backup(db_path)
                cleanup_backups()
                logger.info('Daily backup completed')
            else:
                logger.debug('Backup already exists for today, skipping')
        except Exception as e:
            logger.error(f'Backup failed: {e}')

        time.sleep(INTERVAL_HOURS * 3600)


def start_backup_scheduler(db_path):
    """Start the background backup thread. Call once at app startup."""
    t = threading.Thread(target=_backup_loop, args=(db_path,), daemon=True)
    t.start()
    logger.info(f'Backup scheduler started (every {INTERVAL_HOURS}h, keeping {DAILY_KEEP}d + {WEEKLY_KEEP}w)')
