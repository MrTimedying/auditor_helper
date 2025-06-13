# This file makes the core/db directory a Python package 

from pathlib import Path
import sqlite3

# Absolute path to the SQLite database shipped with the application
DB_PATH = Path(__file__).resolve().parent / 'tasks.db'
DB_FILE = str(DB_PATH)

# --- Compatibility layer ----------------------------------------------------
# Historically the codebase opened the database via `sqlite3.connect('tasks.db')`.
# After the project re-organisation the real database now lives in the
# `src/core/db/` folder, so that relative path no longer works when the working
# directory is elsewhere (e.g. `src/`).
#
# We transparently patch `sqlite3.connect` so that *any* call that passes the
# bare filename `'tasks.db'` is silently redirected to the correct absolute
# file path.  This avoids the need to touch dozens of legacy call-sites and
# guarantees that every part of the application is talking to the same
# database file.

_original_connect = sqlite3.connect


def _patched_connect(database, *args, **kwargs):
    if database == 'tasks.db':
        database = DB_FILE
    return _original_connect(database, *args, **kwargs)

# Apply the monkey-patch once at import time
sqlite3.connect = _patched_connect

# Re-export the `connect` symbol so that `from core.db import sqlite3` gives the
# patched version if someone does that (unlikely but safe).
__all__ = ['DB_PATH', 'DB_FILE', 'sqlite3'] 