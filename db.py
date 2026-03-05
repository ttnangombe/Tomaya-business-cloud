
import os, sqlite3, hashlib, hmac, base64
from datetime import datetime

def now():
    return datetime.now().isoformat(timespec="seconds")

def db_path():
    return os.getenv("TOMAYA_DB_PATH", "tomaya_business.db")

def connect():
    path = db_path()
    if os.path.dirname(path):
        os.makedirs(os.path.dirname(path), exist_ok=True)
    con = sqlite3.connect(path, check_same_thread=False)
    con.row_factory = sqlite3.Row
    return con

def hash_password(password: str, salt: bytes | None = None, iterations: int = 180_000) -> str:
    if salt is None:
        salt = os.urandom(16)
    dk = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, iterations)
    return "pbkdf2_sha256$%s$%d$%s" % (
        base64.b64encode(salt).decode("utf-8"),
        iterations,
        base64.b64encode(dk).decode("utf-8"),
    )

def verify_password(password: str, stored: str) -> bool:
    try:
        algo, b64salt, iters, b64hash = stored.split("$", 3)
        if algo != "pbkdf2_sha256":
            return False
        salt = base64.b64decode(b64salt.encode("utf-8"))
        iterations = int(iters)
        expected = base64.b64decode(b64hash.encode("utf-8"))
        dk = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, iterations)
        return hmac.compare_digest(dk, expected)
    except Exception:
        return False

def init_db(con):
    cur = con.cursor()
    cur.execute("CREATE TABLE IF NOT EXISTS settings (key TEXT PRIMARY KEY, value TEXT NOT NULL)")
    cur.execute("""CREATE TABLE IF NOT EXISTS users(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        role TEXT NOT NULL,
        is_active INTEGER NOT NULL DEFAULT 1,
        created_at TEXT NOT NULL
    )""")
    cur.execute("""CREATE TABLE IF NOT EXISTS companies(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        reg_no TEXT, tin TEXT, vat_no TEXT,
        address TEXT, contact_name TEXT, contact_email TEXT, contact_phone TEXT,
        created_at TEXT NOT NULL
    )""")
    cur.execute("""CREATE TABLE IF NOT EXISTS receipts(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        company_id INTEGER NOT NULL,
        receipt_date TEXT NOT NULL,
        payer TEXT NOT NULL,
        description TEXT,
        amount REAL NOT NULL,
        vat_included TEXT NOT NULL,
        category TEXT,
        reference TEXT,
        created_at TEXT NOT NULL
    )""")
    cur.execute("""CREATE TABLE IF NOT EXISTS transactions(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        company_id INTEGER NOT NULL,
        tx_date TEXT NOT NULL,
        description TEXT NOT NULL,
        amount REAL NOT NULL,
        direction TEXT NOT NULL,
        vat_included TEXT NOT NULL,
        category TEXT,
        reference TEXT,
        source TEXT,
        imported_at TEXT NOT NULL
    )""")
    cur.execute("""CREATE TABLE IF NOT EXISTS audit_log(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        ts TEXT NOT NULL,
        username TEXT,
        action TEXT NOT NULL,
        details TEXT
    )""")
    for k,v in {"vat_rate":"0.15","currency":"N$","practice_name":"Tomaya Business Cloud"}.items():
        cur.execute("INSERT OR IGNORE INTO settings(key,value) VALUES(?,?)",(k,v))
    cur.execute("SELECT COUNT(*) AS n FROM users")
    if cur.fetchone()["n"] == 0:
        cur.execute("INSERT INTO users(username,password_hash,role,is_active,created_at) VALUES(?,?,?,?,?)",
                    ("admin", hash_password("tomaya123"), "ADMIN", 1, now()))
    con.commit()

def get_setting(con, key, default=None):
    cur = con.cursor()
    cur.execute("SELECT value FROM settings WHERE key=?", (key,))
    r = cur.fetchone()
    return r["value"] if r else default

def set_setting(con, key, value):
    cur = con.cursor()
    cur.execute("INSERT OR REPLACE INTO settings(key,value) VALUES(?,?)", (key, str(value)))
    con.commit()

def log(con, username, action, details=None):
    cur = con.cursor()
    cur.execute("INSERT INTO audit_log(ts, username, action, details) VALUES(?,?,?,?)",
                (now(), username, action, details))
    con.commit()
