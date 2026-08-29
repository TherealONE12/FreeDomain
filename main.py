from flask import render_template, request, Flask
import pyotp
import secrets
import string
import sqlite3
import hashlib
import qrcode
import time
import os



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
    totp_secret    TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS subdomains(
    id     INTEGER PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
    subdomain   TEXT UNIQUE,
    updated_at     TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS session(
    id      INTEGER PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
    session_key    TEXT NOT NULL
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

def setup_otp(userid: int):
    key = pyotp.random_base32()
    totp_auth = pyotp.totp.TOTP(key).provisioning_uri(name=str(userid), issuer_name="FreeDomain.meme")


    os.makedirs(f"static/qr/{userid}", exist_ok=True)
    qrcode.make(totp_auth).save(f"static/qr/{userid}/qr_auth.png")
    
    with get_conn() as conn:
        conn.execute("INSERT INTO user_2fa (id, totp_secret) VALUES (?, ?) ON CONFLICT(id) DO UPDATE SET totp_secret = excluded.totp_secret",(userid, key))
        conn.commit()
    
    return f"""
<!DOCTYPE html>
<html>
    <body>
        <h3>Setup your OTP now - You will need it to login again:</h3>
        <br><br>
        <img src="/static/qr/{userid}/qr_auth.png" alt="Your otp password">
        <br><br>
        <a href="login.html"> Continue to Verify OTP</a>
    </body>
</html>
    
"""




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
        row = conn.execute("SELECT * FROM users WHERE hash_secret = ?)", (hash_pw,)).fetchone()
        conn.commit()
        if row is None:
            return -1
        elif row['ip_address'] is not ip_addr:
            return -1
        elif row['is_restricted'] == '1':
            return -1
        else:
            return row['id']


def VerifyOtpByUserId():
    return -1


@app.route('/')
def ping():
    return 'Pong!'







@app.route('/login.html')
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        password = request.form['auth_code']
        ip_addr = request.remote_addr
        if VerifyUser(password=password, ip_addr=ip_addr) is not '-1':
            resp = make_response(render_template('otp_input'))
            resp.set_cookie(
                'pw', password,
                httponly=True,
                secure=True,
                samesite='Lax',
                max_age=60*30     # 30 minutes
            )
            return resp
        else:
            return render_template('failure.html')
    return render_template('login.html')


@app.route('/register.html')
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        ip_addr = request.remote_addr
        return f"Request Accepted. Your new Login Data is {MakeNewUser(ip_addr)}"
    return render_template('register.html')


@app.route('/otp_input.html')
@app.route('/otp_input', methods=['GET', 'POST'])
def otp_input():
    if request.method == 'POST':
        otp = request.form['otp']
        ip_addr = request.remote_addr
        password = request.cookies.get['pw']
        if VerifyUser(password=password, ip_addr=ip_addr) is not '-1':
            key = "-1"

            with get_conn() as conn:
                key = conn.execute("SELECT * FROM user_2fa WHERE id = ?)", (VerifyUser(password=password, ip_addr=ip_addr),)).fetchone()

            totp_verify = pyotp.TOTP(key)
            
            if totp_verify.verify(otp=otp):
                session_alphabet = string.printable
                session_id = ''.join(secrets.choice(session_alphabet) for i in range(128))

                with get_conn() as conn:
                    conn.execute("INSERT INTO session (id, session_key, updated_at) VALUES (?, ?, ?) ON CONFLICT(id) DO UPDATE SET session_key = excluded.session_key updated_at = excluded.updated_at",(userid, session_id, time.now()))

                resp = make_response(render_template('homepage.html'))
                resp.set_cookie(
                    'session', session_id,
                    httponly=True,
                    secure=True,
                    samesite='Lax',
                    max_age=60*30     # 30 minutes
                )
                return resp
            else:
               return render_template('failure.html') 
        else:
            return render_template('failure.html')
    return render_template('otp_input.html')

@app.route('/verify_otp.html')
@app.route('/verify_otp', methods=['GET', 'POST'])
def otp_verify_afther_creation():
    if request.method == 'POST':
        otp = request.form['otp']
        ip_addr = request.remote_addr
        password = request.cookies.get['pw']
        if VerifyUser(password=password, ip_addr=ip_addr) is not '-1':
            key = "-1"

            with get_conn() as conn:
                key = conn.execute("SELECT * FROM user_2fa WHERE id = ?)", (VerifyUser(password=password, ip_addr=ip_addr),)).fetchone()

            totp_verify = pyotp.TOTP(key)
            
            if totp_verify.verify(otp=otp):
                return render_template('sucsess.html')
        else:
            return render_template('failure.html')
    return render_template('verify_otp.html')


if __name__ == '__main__':
    init_db()
    app.run()
