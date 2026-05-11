#!/usr/bin/env python3
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "agents"))

from memory import MemoryDB
import tempfile

db_path = Path(tempfile.mktemp(suffix=".db"))
db = MemoryDB(db_path)

db.store_experience("Bug A", "Solution A", success=True)
db.store_experience("Bug B", "Failed attempt", success=False)

results = db.search_experience("Bug", success_only=False)
print(f"Search results: {len(results)}")

cursor = db.conn.cursor()
cursor.execute("SELECT COUNT(*) as count FROM experience_fts")
print(f"FTS5 rows: {cursor.fetchone()['count']}")

db.close()
