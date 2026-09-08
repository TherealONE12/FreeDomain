from flask import render_template, request, Flask, make_response
import pyotp
import secrets
import string
import sqlite3
import hashlib
import qrcode
import time
import os
from namecheap import Namecheap


nc = Namecheap()

domains = nc.domains.check("freedomain.meme")

for domain in domains:
    if domain.available:
        print(f"Domain {domain.domain} is available!")

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
    subdomain   TEXT DEFAULT -1,
    updated_at     TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS session(
    id      INTEGER PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
    session_key    TEXT NOT NULL,
    updated_at     TIMESTAMP
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
    
    return 1




def MakeNewUser(ipadress: str) -> str:
    # Generate User auth code
    alphabet = string.ascii_letters + string.digits
    password = ''.join(secrets.choice(alphabet) for i in range(64))

    # Hash user auth code
    hash_pw = hashlib.sha256(password.encode()).hexdigest()

    #write into db
    try:
        with get_conn() as conn:
            conn.execute("INSERT INTO users (hash_secret, ip_address) VALUES (?, ?)", (hash_pw, ipadress))
            conn.commit()
        return password
    except sqlite3.Error as e:
        if "UNIQUE constraint failed" in str(e):
            return -1
        else:
            return -2


def VerifyUser(password: str, ip_addr: str) -> bool:
    hash_pw = hashlib.sha256(password.encode()).hexdigest() # removed (password) from encode() funktion, please work
    with get_conn() as conn:
        row = conn.execute("SELECT * FROM users WHERE hash_secret = ?", (hash_pw,)).fetchone()
        conn.commit()
        if row == None:
            return -1
        elif row['ip_address'] != ip_addr:
            return -1
        elif row['is_restricted'] == 1:
            return -1
        else:
            return row['id']





def verify(id: int, session: str):
    age = -1
    restricted = -1
    with get_conn() as conn:
        coll = conn.execute("SELECT * FROM session WHERE id = ?", (id,)).fetchone()
        age = coll['updated_at']

        restricted = conn.execute("SELECT is_restricted FROM users WHERE id = ?", (id,)).fetchone()

    if id == -1 or age == -1 or time.time() - age >= 60*30 or restricted  == 1:
        return -1
    else:
        return 1



def make_domain(id: int, subdomainname: str, ip: int):
    ok = verify(id)

    if ok == 1:
        with get_conn() as conn:
            subdomain_state = conn.execute("SELECT subdomain FROM subdomains WHERE id = ?", (id,)).fetchone()
            
            subdomain_other = conn.execute("SELECT subdomain FROM subdomains WHERE id != ?", (id,)).fetchall()
            append = 0
            curcnt = 0
            for row in subdomain_other:
                for row in subdomain_other:
                    if row['subdomain'] == subdomainname or row['subdomain'] == f"{curcnt}.{subdomainname}":
                        append +=1
                curcnt += 1

            if append == 0:
                if subdomain_state is None or subdomain_state['subdomain'] == -1:
                    nc.dns.add("freedomain.meme",
                    nc.dns.builder()
                    .a(subdomainname, ip, 1799))
                    return 1
                else:
                    return -1
            else:
                newdomain = f"{append}.{subdomainname}"
                if subdomain_state is None or subdomain_state['subdomain'] == -1:
                    nc.dns.add("freedomain.meme",
                    nc.dns.builder()
                    .a(newdomain, ip, 1799))
                    return 2
                else:
                    return -1
            




@app.route('/')
def ping():
    return render_template('homepage.html')


@app.route('/login.html')
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        password = request.form['auth_code']
        ip_addr = request.remote_addr
        if VerifyUser(password=password, ip_addr=ip_addr) != -1:
            resp = make_response(render_template('otp_input.html'))
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

        pw = MakeNewUser(ip_addr)

        if pw == -1:
            return f"An user is already registerd from {ip_addr}. Please contact Support"
        elif pw == -2:
            return "An Error occured. Try again or contact support."
        else:
            if VerifyUser(password=pw, ip_addr=ip_addr) != -1: # Still a bug idk pleaseee why is it not hashing my stuff AHHHH
                resp = make_response(f"""
<!DOCTYPE html>
<html>
    <body>
        <h3>Request Accepted. Your new Login Data is {pw}</h3>
        <form method="get" action="/verify_otp.html">
            <input type="submit" value="continue">
        </form>
    </body>
</html>
""")
                resp.set_cookie(
                    'pw', pw,
                    httponly=True,
                    secure=True,
                    samesite='Lax',
                    max_age=60*30     # 30 minutes
                )
                return resp 
    return render_template('register.html')


@app.route('/otp_input.html')
@app.route('/otp_input', methods=['GET', 'POST'])
def otp_input():
    if request.method == 'POST':
        otp = request.form['otp']
        ip_addr = request.remote_addr
        password = request.cookies.get('pw')
        if VerifyUser(password=password, ip_addr=ip_addr) != -1:
            key = -1

            with get_conn() as conn:
                key = conn.execute("SELECT * FROM user_2fa WHERE id = ?", (VerifyUser(password=password, ip_addr=ip_addr),)).fetchone()

            totp_verify = pyotp.TOTP(key["totp_secret"])
            
            if totp_verify.verify(otp=otp):
                session_alphabet = string.printable
                session_id = ''.join(secrets.choice(session_alphabet) for i in range(128))

                userid = VerifyUser(password, ip_addr)
                with get_conn() as conn:
                    conn.execute("INSERT INTO session (id, session_key, updated_at) VALUES (?, ?, ?) ON CONFLICT(id) DO UPDATE SET session_key = excluded.session_key, updated_at = excluded.updated_at",(userid, session_id, time.time()))

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
    ip_addr = request.remote_addr
    password = request.cookies.get('pw')
    if VerifyUser(password=password, ip_addr=ip_addr) != -1:
        setup_otp(VerifyUser(password=password, ip_addr=ip_addr))
        userid = VerifyUser(password=password, ip_addr=ip_addr)
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

@app.route('/make_domain')
@app.route('/make_domain.html', methods=['GET', 'POST'])
def homepage():
    session = request.cookies.get('session')
    if verify(VerifyUser(request.cookies.get('pw'), request.remote_addr), request.remote_addr) == 1:
        if request.method == 'POST':
            domainname = request.form('domainname')
            ip_link = request.form('ip')
            if make_domain(VerifyUser(request.cookies.get('pw'), request.remote_addr), domainname, ip_link) == -1:
                return render_template('failure.html')
            else:
                return render_template('sucsess.html')
            return render_template('failure.html')
        return render_template('make_domain.html')
    return render_template('failure.html')


@app.route('/homepage')
@app.route('/homepage.html', methods=['GET', 'POST'])
def homepage():
    return render_template("home_loggedin.html")

if __name__ == '__main__':
    init_db()
    app.run()
