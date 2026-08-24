from flask import render_template, request, Flask
import secrets
import string
import sqlite3
import hashlib

app = Flask(__name__)

DB_PATH = "app.db"


DB_SHEMA = """
PRAGMA foreign_keys = ON;
CREATE TABLE IF NOT EXISTS users(
    id      INTEGER PRIMARY KEY AUTOINCREMENT,
    hash_secret    TEXT NOT NULL,
    created_at   TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_restricted   INTEGER NOT NULL DEFAULT 0,
    ip_address TEXT NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS user_2fa(
    id      INTEGER PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
    totp_secret    TEXT NOT NULL,
    enabled       INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS subdomains(
    id     INTEGER PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
    subdomain   TEXT UNIQUE,
    updated_at     TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
"""

def get_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON")   # muss bei jeder Connection neu gesetzt werden
    conn.row_factory = sqlite3.Row             # dict-artiger Zugriff auf Zeilen
    return conn


def init_db():
    with get_conn() as conn:
        conn.execute("PRAGMA foreign_keys = ON")
        conn.executescript(DB_SHEMA)


def MakeNewUser(ipadress: str) -> str:
    # Generate User auth code
    alphabet = string.ascii_letters + string.digits
    password = ''.join(secrets.choice(alphabet) for i in range(64))

    # Hash user auth code
    hash_pw = hashlib.sha256(password.encode()).hexdigest()

    #write into db
    with get_conn() as conn:
        conn.execute("INSERT INTO users (hash_secret, ip_address) VALUES (?, ?)", (hash_pw, ipadress))
        conn.commit()
    return password

def VerifyUser(password: str, ip_addr: str) -> bool:
    hash_pw = hashlib.sha256(password.encode()).hexdigest()
    with get_conn() as conn:
        row = conn.execute("SELECT * FROM users WHERE hash_secrets = ?)", (hash_pw,)).fetchone
        conn.commit()
        if row is none:
            return -1
        else if row['ip_address']





@app.route('/')
def ping():
    return 'Pong!'







@app.route('/login.html')
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        name = request.form['auth_code']
        return f"Hello {name}, POST request received"
    return render_template('login.html')


@app.route('/register.html')
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        ip_addr = request.remote_addr
        return f"Request Accepted. Your new Login Data is {MakeNewUser(ip_addr)}"
    return render_template('register.html')




if __name__ == '__main__':
    init_db()
    app.run()
