import csv, io, sqlite3
import config
COLS = ["college_code", "college_name", "district", "college_type", "branch", "community", "cutoff", "year"]

def conn(path=None):
    c = sqlite3.connect(path or config.DB_PATH)
    c.row_factory = sqlite3.Row
    return c

def import_csv(text, path=None, replace=True):
    """Load CSV text into SQLite. Blank cutoff = data unavailable. Returns (rows_loaded, errors)."""
    rows, errors = [], []
    reader = csv.DictReader(io.StringIO(text))
    missing = [c for c in COLS if c not in (reader.fieldnames or [])]
    if missing:
        return 0, [f"Missing columns: {', '.join(missing)}"]
    for i, r in enumerate(reader, start=2):
        try:
            cut = (r["cutoff"] or "").strip()
            cut = float(cut) if cut else None
            if cut is not None and not 0 <= cut <= 200:
                raise ValueError("cutoff must be 0-200")
            yr = int(r["year"]) if (r["year"] or "").strip() else None
            if not r["college_code"].strip() or not r["college_name"].strip() or not r["branch"].strip():
                raise ValueError("code, name and branch are required")
            rows.append((r["college_code"].strip(), r["college_name"].strip(), r["district"].strip(),
                         r["college_type"].strip(), r["branch"].strip(), r["community"].strip().upper(), cut, yr))
        except Exception as e:
            errors.append(f"Row {i}: {e}")
    c = conn(path)
    c.execute("""CREATE TABLE IF NOT EXISTS colleges(college_code TEXT, college_name TEXT, district TEXT,
                 college_type TEXT, branch TEXT, community TEXT, cutoff REAL, year INTEGER)""")
    if replace:
        c.execute("DELETE FROM colleges")
    c.executemany("INSERT INTO colleges VALUES(?,?,?,?,?,?,?,?)", rows)
    c.commit(); c.close()
    return len(rows), errors

def ensure_db(path=None):
    c = conn(path)
    try:
        n = c.execute("SELECT COUNT(*) FROM colleges").fetchone()[0]
    except sqlite3.OperationalError:
        n = 0
    c.close()
    if n == 0:
        with open(config.CSV_PATH, encoding="utf-8") as f:
            import_csv(f.read(), path)

def options(c):
    q = lambda col: [r[0] for r in c.execute(f"SELECT DISTINCT {col} FROM colleges WHERE {col}<>'' ORDER BY {col}")]
    return {"branches": q("branch"), "districts": q("district"), "types": q("college_type")}
