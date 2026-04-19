import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), 'trustloop.db')

SCHEMA = """
CREATE TABLE IF NOT EXISTS applications (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    ref           TEXT UNIQUE NOT NULL,
    full_name     TEXT NOT NULL,
    national_id   TEXT NOT NULL,
    phone         TEXT NOT NULL,
    dob           TEXT,
    county        TEXT,
    employment    TEXT,
    employer      TEXT,
    monthly_income REAL DEFAULT 0,
    loan_amount   REAL NOT NULL,
    loan_purpose  TEXT,
    tenure        TEXT,
    status        TEXT DEFAULT 'Pending',
    score         INTEGER,
    score_data    TEXT,          -- JSON blob from SpinMobile
    pdf_path      TEXT,          -- path to uploaded M-Pesa PDF
    created_at    TEXT DEFAULT (datetime('now','localtime')),
    updated_at    TEXT DEFAULT (datetime('now','localtime'))
);

CREATE INDEX IF NOT EXISTS idx_status ON applications(status);
CREATE INDEX IF NOT EXISTS idx_phone  ON applications(phone);
CREATE INDEX IF NOT EXISTS idx_ref    ON applications(ref);
"""

def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_conn()
    conn.executescript(SCHEMA)
    conn.commit()
    conn.close()
    print(f"[DB] Initialised at {DB_PATH}")

def insert_application(data: dict) -> int:
    conn = get_conn()
    cur = conn.execute("""
        INSERT INTO applications
          (ref, full_name, national_id, phone, dob, county, employment, employer,
           monthly_income, loan_amount, loan_purpose, tenure, pdf_path)
        VALUES
          (:ref, :full_name, :national_id, :phone, :dob, :county, :employment, :employer,
           :monthly_income, :loan_amount, :loan_purpose, :tenure, :pdf_path)
    """, data)
    conn.commit()
    row_id = cur.lastrowid
    conn.close()
    return row_id

def update_score(ref: str, score: int, score_data: str, status: str = 'Reviewing'):
    conn = get_conn()
    conn.execute("""
        UPDATE applications
        SET score = ?, score_data = ?, status = ?,
            updated_at = datetime('now','localtime')
        WHERE ref = ?
    """, (score, score_data, status, ref))
    conn.commit()
    conn.close()

def update_status(ref: str, status: str):
    conn = get_conn()
    conn.execute("""
        UPDATE applications
        SET status = ?, updated_at = datetime('now','localtime')
        WHERE ref = ?
    """, (status, ref))
    conn.commit()
    conn.close()

def get_application(ref: str) -> dict | None:
    conn = get_conn()
    row = conn.execute("SELECT * FROM applications WHERE ref = ?", (ref,)).fetchone()
    conn.close()
    return dict(row) if row else None

def list_applications(status: str = None, limit: int = 200) -> list[dict]:
    conn = get_conn()
    if status:
        rows = conn.execute(
            "SELECT * FROM applications WHERE status = ? ORDER BY created_at DESC LIMIT ?",
            (status, limit)
        ).fetchall()
    else:
        rows = conn.execute(
            "SELECT * FROM applications ORDER BY created_at DESC LIMIT ?",
            (limit,)
        ).fetchall()
    conn.close()
    return [dict(r) for r in rows]

if __name__ == '__main__':
    init_db()
