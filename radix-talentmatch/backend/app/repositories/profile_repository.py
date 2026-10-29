import json, os, sqlite3
from datetime import datetime, timezone
from pathlib import Path

ROOT=Path(__file__).resolve().parents[3]
def db_path(): return os.getenv("RADIX_DB_PATH", str(ROOT/"backend"/"profiles.db"))
def connect():
    path=db_path(); Path(path).parent.mkdir(parents=True,exist_ok=True)
    conn=sqlite3.connect(path); conn.row_factory=sqlite3.Row
    conn.execute("CREATE TABLE IF NOT EXISTS profiles (id TEXT PRIMARY KEY, data TEXT NOT NULL)")
    conn.execute("CREATE TABLE IF NOT EXISTS assessments (id INTEGER PRIMARY KEY AUTOINCREMENT, data TEXT NOT NULL)")
    return conn

def all_profiles():
    with connect() as c: return [json.loads(r[0]) for r in c.execute("SELECT data FROM profiles ORDER BY id")]
def get_profile(pid):
    with connect() as c:
        row=c.execute("SELECT data FROM profiles WHERE id=?",(pid,)).fetchone()
        return json.loads(row[0]) if row else None
def save_profile(data):
    with connect() as c: c.execute("INSERT INTO profiles(id,data) VALUES(?,?) ON CONFLICT(id) DO UPDATE SET data=excluded.data",(data["id"],json.dumps(data)))
def add_assessment(kind, candidate_id, candidate_name, target, score):
    item={"type":kind,"candidate_id":candidate_id,"candidate_name":candidate_name,"target":target,"score":int(score),"timestamp":datetime.now(timezone.utc).isoformat()}
    with connect() as c: c.execute("INSERT INTO assessments(data) VALUES(?)",(json.dumps(item),))
    return item
def recent_assessments(limit=50):
    with connect() as c:
        rows=c.execute("SELECT data FROM assessments ORDER BY id DESC LIMIT ?",(max(1,min(int(limit),200)),)).fetchall()
        return [json.loads(r[0]) for r in rows]
