from flask import render_template, request, Flask, make_response
from profanity_check import predict, predict_prob
from namecheap.models import DNSRecord
from namecheap import Namecheap
from dotenv import load_dotenv
from discord.ext import commands
import discord
import pyotp
import secrets
import string
import sqlite3
import hashlib
import qrcode
import time
import os
import threading
import asyncio


# Setup stuff
load_dotenv()
nc = Namecheap()
domains = nc.domains.check("freedomain.meme")
for domain in domains:
    if domain.available:
        print(f"Domain {domain.domain} is available!")
#DC setup
intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix='$', intents=intents)

app = Flask(__name__)


DB_PATH = "app.db"

#Database shema. 
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

# All discord helper funktions are below

def run_bot():
    asyncio.run(bot.start(TOKEN))

def send_log(txt: str, critical_lvl: int): # 1 = warn, 2 = Error 3 = Failure 4 = Logmsg
    channel = bot.get_channel(1548006957091393597)

    if channel is None:
        print("Channel Not Found :( (send_log)")
        return -1
    
    if critical_lvl == 1:
        embed1 = discord.Embed(
            title="log",
            description=txt,
            color=905708
        )

        embed1.set_author(
            name="Log - Freedomain.meme",
            url="https://freedomain.meme",
            icon_url="https://external-content.duckduckgo.com/iu/?u=https%3A%2F%2Ftse4.mm.bing.net%2Fth%2Fid%2FOIP.-BIpLQvTGIJ6MrS1p0xgCAHaHa%3Fr%3D0%26pid%3DApi&f=1&ipt=da212e0dab2702e7b59fc2dd40cddd50b551d6834c5197912d45bceeb6000fe2&ipo=images"
        )
    elif critical_lvl == 2:
        embed1 = discord.Embed(
            title="log - Error",
            description=txt,
            color=905708
        )

        embed1.set_author(
            name="Log - Freedomain.meme",
            url="https://freedomain.meme",
            icon_url="https://external-content.duckduckgo.com/iu/?u=https%3A%2F%2Ftse3.mm.bing.net%2Fth%2Fid%2FOIP.XUXv_6u9GIhNkZUZk51tlwHaHa%3Fr%3D0%26pid%3DApi&f=1&ipt=21f28b6e803415a08e4a4afa7817ef9bb944e9de2c98683f5507f878efd9fb8b&ipo=images"
        )
    elif critical_lvl == 3:
        embed1 = discord.Embed(
            title="log - Critical",
            description=txt,
            color=15469837
        )

        embed1.set_author(
            name="Log - Freedomain.meme",
            url="https://freedomain.meme",
            icon_url="https://external-content.duckduckgo.com/iu/?u=https%3A%2F%2Ftse2.mm.bing.net%2Fth%2Fid%2FOIP.K5C429akAhTgYKe10T4DnQAAAA%3Fr%3D0%26pid%3DApi&f=1&ipt=b9940359e56dba4aeb73a35b36ca97a3144d9c1f4aedf2d9d526f5b7c3d1b092&ipo=images"
        )
    else:
        embed1 = discord.Embed(
            title="log",
            description=txt,
            color=905708
        )

        embed1.set_author(
            name="Logmessage - Freedomain.meme",
            url="https://freedomain.meme",
            icon_url="https://external-content.duckduckgo.com/iu/?u=https%3A%2F%2Ftse1.mm.bing.net%2Fth%2Fid%2FOIP.TYX8oNxxjrh8uUhEBtGLsgHaHa%3Fr%3D0%26pid%3DApi&f=1&ipt=dc9d362de04c09f30ce1d8c6e30ef5dadb61f3cd74e892f37fa09cd0d0a0e1d3&ipo=images"
        )

    coro =  channel.send(embed=embed1)
    asyncio.run_coroutine_threadsafe(coro, bot.loop)


def send_newDomain(domainname: str):
    channel = bot.get_channel(1548007928588406907)

    if channel is None:
        print("Channel Not Found :( (send_newDomain)")
        return -1
    
    embed1 = discord.Embed(
        title= "New Domain",
        description= f"New Domain entry: {domainname}",
        color=2092045
    )

    embed1.set_author(
        name="New Domain - Freedomain.meme",
        url="https://freedomain.meme",
        icon_url="https://external-content.duckduckgo.com/iu/?u=https%3A%2F%2Ftse2.mm.bing.net%2Fth%2Fid%2FOIP.WvH_o_PB0swLCPLGphzCSgHaHa%3Fr%3D0%26pid%3DApi&f=1&ipt=70c9270d60dcfcd9b792f69d5a93ec8495c81312b434aec8ccd0f80b39c10a27&ipo=images"
    )

    coro =  channel.send(embed=embed1)
    asyncio.run_coroutine_threadsafe(coro, bot.loop)

def send_ban(userid: int, domainname: str, ip:str):
    channel = bot.get_channel(1548007980740382741)

    if channel is None:
        print("Channel Not Found :( (send_ban)")
        return -1
    
    embed1 = discord.Embed(
      title= "Banned",
      description= f"Banned UserId {userid} with old domainname {domainname} and redirect-ip of {ip}",
      color= 15469837,
    )

    embed1.set_author(
        name="Banned - Freedomain.meme",
        url="https://freedomain.meme",
        icon_url="https://external-content.duckduckgo.com/iu/?u=https%3A%2F%2Ftse3.mm.bing.net%2Fth%2Fid%2FOIP.dGMEN6Ae7i-pQXdf7TJsvAHaHa%3Fr%3D0%26pid%3DApi&f=1&ipt=171875b5f25fc5ee1f5017e1f4e9407bf293a7b80a888feb22e111d107617ab7&ipo=images"
    )

    coro =  channel.send(embed=embed1)
    asyncio.run_coroutine_threadsafe(coro, bot.loop)






# All website helper funktions are below. 

def get_conn() -> sqlite3.Connection: # gets an databank connection going 
    conn = sqlite3.connect(DB_PATH)   
    conn.execute("PRAGMA foreign_keys = ON")   # Testing queries for errors, I belive
    conn.row_factory = sqlite3.Row      # Allows for row-specific acsesss  
    send_log("Starts an DB Connection!", 4)     
    return conn


def init_db(): #Initialises the db
    with get_conn() as conn:
        conn.execute("PRAGMA foreign_keys = ON")
        conn.executescript(DB_SHEMA)
        send_log("Initialised the DB!", 4)
        

def setup_otp(userid: int):
    key = pyotp.random_base32() #Generate an OTP secret key
    totp_auth = pyotp.totp.TOTP(key).provisioning_uri(name=str(userid), issuer_name="FreeDomain.meme") # generates the pair for the user to import as link

    try: 
        os.makedirs(f"static/qr/{userid}", exist_ok=True) # Makes the directory for the qr code for the user
    except OSError as error: # If an error happens
        send_log(f"{userid} Tried to make an path - Didnt work!", 2)
        return -1 # Directory cant be created. Send help
    qrcode.make(totp_auth).save(f"static/qr/{userid}/qr_auth.png") # generates an qr code for the user to easily scan with an mobile
    
    with get_conn() as conn:
        conn.execute("INSERT INTO user_2fa (id, totp_secret) VALUES (?, ?) ON CONFLICT(id) DO UPDATE SET totp_secret = excluded.totp_secret",(userid, key))
        conn.commit()  # LINE ABOVE: Writes the secret key into the db for that specific userid CURRENT LINE: Commits it to the db
    send_log(f"{userid} Registerd OTP!", 4)
    return 1 # Return 1 on Sucsess. And prays that there are no errors causethey are currently not handled. Whoops




def MakeNewUser(ipadress: str) -> str:
    # Generate User auth code
    alphabet = string.ascii_letters + string.digits # The accepted alphabet for the password. All letters and digits
    password = ''.join(secrets.choice(alphabet) for i in range(64)) # 64 letetrs/digits is fair enought for that there are no special chars

    # Hash user auth code
    hash_pw = hashlib.sha256(password.encode()).hexdigest()

    #write into db
    try:
        with get_conn() as conn:
            conn.execute("INSERT INTO users (hash_secret, ip_address) VALUES (?, ?)", (hash_pw, ipadress)) # writes into db
            conn.commit()

            userid = conn.execute("SELECT id FROM users WHERE hash_secret = ?", (hash_pw,)).fetchone()
            send_log(f"{userid['id']} Registerd from {ipadress} at {time.time()}!", 4)
        return password
    except sqlite3.Error as e: # if an error happens at the writing
        if "UNIQUE constraint failed" in str(e): # and it has that string in the error message
            send_log(f"An user tried to register from {ipadress} but there was already an user at that IP adress!", 1)
            return -1 # The user has already registerd from that ip
        else:
            send_log(f"An user tried to register from {ipadress} and something failed!", 2)
            return -2 # Else something different happend


def VerifyUser(password: str, ip_addr: str) -> bool: # Also used to get the userid, lol. Uses only the password
    if password == None: # afther 30  mins the cookie runs out and gets deleted, so the user needs to login again, but without this the line afther the if staement just throws an error into the users face.
        return -2

    hash_pw = hashlib.sha256(password.encode()).hexdigest() # hashing the supposed right password that we got
    with get_conn() as conn:
        row = conn.execute("SELECT * FROM users WHERE hash_secret = ?", (hash_pw,)).fetchone() # checking if that password exists
        conn.commit()
        if row == None: #if not, then deny acsess
            return -1
        elif row['ip_address'] != ip_addr: # if the ip adress is wrong, also deny acsess (sorry to all non-static ip users)
            return -1
        elif row['is_restricted'] == 1:# If the account is restricted, also deny acsess (What did u do??)
            return -1
        else:
            return row['id'] # ELse, give back the userid 





def verify(id: int, session: str): # Usexd to verify the sessiontoken. Idk why I thought i needed a second verification progress, but hey, now we are here
    age = -1
    restricted = -1
    with get_conn() as conn:
        mimimi = conn.execute("SELECT * FROM session WHERE id = ?", (id,)).fetchone() # fetched the age

        age = mimimi['updated_at'] # why mimimi? Because If YoU PuLL aN InTeGeR FrOm SQlIte YoU sTiLl gEt aN sQLitE RoW NoT aN iNt VaR

        restricted = conn.execute("SELECT is_restricted FROM users WHERE id = ?", (id,)).fetchone()  # fetched, if the user got restricted

    if id == -1 or age == -1 or time.time() - age >= 60*30 or restricted  == 1 or mimimi['session_key'] != session: #Big fat verification logik
        return -1
    else:
        return 1

def make_domain(id: int, subdomainname: str, ip: int, session: str): # makes a domain
    if "freedomain.meme" in subdomainname: # checks if the main domain is in the subdomain. if so, then DENY the request.
        return -2

    if verify(id, session) == 1: # Not wanting to ban anyone if someone cracked a users pw
        result = predict_prob(subdomainname.splitlines()) # tries to predict if the subdomainname is a bad word
        if result[0] > 0.5: # If yes (i hope 0.5 is big enought for not so many false-positives)
            with get_conn() as conn:
                conn.execute("INSERT INTO users (id, is_restricted) VALUES (?, ?) ON CONFLICT(id) DO UPDATE SET is_restricted = excluded.is_restricted",(id, 1))
                conn.commit() # LINE ABOVE: Set his restricted status to 1, and basacly banning him away from the plattform, though if false-positive then allowing him back on afther human review
                send_ban(id, subdomainname, ip)
                return -1 

    ok = verify(id, session) # verifying the session again if the restricted value updated

    if ok == 1:
        subdomain_state = -1
        with get_conn() as conn:
            subdomain_state = conn.execute("SELECT subdomain FROM subdomains WHERE id = ?", (id,)).fetchone() # current subdomain
        
        if subdomain_state is not None or subdomain_state['subdomain'] != -1: # dont waste power computing stuff, if the user doesnt have the rights to create a new subdomain
            return -1

        dns_existing = nc.dns.get("freedomain.meme")
        subdomain_other = [DNSRecord for DNSRecord in dns_existing if DNSRecord.type == 'A']

        append = 0 
        curcnt = 0
        for record in subdomain_other:# going through all rows
            for record_fr in subdomain_other:# checing for duplicates way to many times
                if (record_fr.name == subdomainname and curcnt == 0) or record_fr.name == f"{curcnt}.{subdomainname}":
                    append +=1
            curcnt += 1

        if append == 0: # if no appending is required
            if subdomain_state is None or subdomain_state['subdomain'] == -1: # if no subdomain got set
                record = DNSRecord(name=subdomainname, type="A", value=ip, ttl=1799) # make the record
                nc.dns.add("freedomain.meme",record) # and write it to the namecheap servers

                with get_conn() as conn: # write the new cool domain into the db
                    conn.execute("INSERT INTO subdomains (id, subdomain) VALUES (?, ?) ON CONFLICT(id) DO UPDATE SET subdomain = excluded.subdomain", (id,subdomainname)).fetchone() # current subdomain
                send_log(f"User {id} made an Domain named {subdomainname}.freedomain.meme at {time.time()} with link to {ip}!", 1)
                return 0 # all good
            else:
                return -1 # u already have a subdomain or smth like that
        else:
            newdomain = f"{append}.{subdomainname}" # appending the prefix
            if subdomain_state is None or subdomain_state['subdomain'] == -1:
                record = DNSRecord(name=newdomain, type="A", value=ip, ttl=1799) # make the record and ship it to the servers. same as above
                nc.dns.add("freedomain.meme",record)

                with get_conn() as conn: # write the new cool domain into the db
                    conn.execute("INSERT INTO subdomains (id, subdomain) VALUES (?, ?) ON CONFLICT(id) DO UPDATE SET subdomain = excluded.subdomain", (id,subdomainname)).fetchone() # current subdomain
                send_log(f"User {id} made an Domain named {newdomain}.freedomain.meme at {time.time()} with link to {ip}!", 1)
                return append # different return to let the user know
            else:
                return -1
            
# All discord routes are below

@bot.event
async def on_ready():
    print(f"Logged in Admin-Bot as {bot.user}")
    
@bot.command()
async def test(ctx, arg):
    await ctx.send(f"You said $test {arg}!")











# All Website routes are below

@app.route('/')  # if root gets requested from the browser
def ping():
    return render_template('homepage.html') # render that template


@app.route('/login.html')
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST': # if post (aka the form got filled)
        password = request.form['auth_code'] # extract the password
        ip_addr = request.remote_addr # extract the ip adress
        if VerifyUser(password=password, ip_addr=ip_addr) >= 0: # if the user got verified
            resp = make_response(render_template('otp_input.html')) # goto next step
            resp.set_cookie( #set all of the cookies
                'pw', password, # a cookie named pw with value, well, your password
                httponly=True, # only send on http/https connectionn
                secure=True, # and only if its https!
                samesite='Lax', # only sending the cookie (aka your password) if its probably a safe request
                max_age=60*30     # 30 minutes max age
            )
            return resp # returning to the client
        else:
            return render_template('failure.html') # nope
    return render_template('login.html') # if the form didnt got filled, then send the user the form


@app.route('/register.html')
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST': # if the form got send
        ip_addr = request.remote_addr # extract ip adress

        pw = MakeNewUser(ip_addr) # get an password

        if pw == -1: # error handeling
            return f"An user is already registerd from {ip_addr}. Please contact Support"
        elif pw == -2:
            return "An Error occured. Try again or contact support."
        else:
            if VerifyUser(password=pw, ip_addr=ip_addr) >= 0: # check if everything worked
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
""") # sending the user his password
                resp.set_cookie( # setting his cookies
                    'pw', pw,
                    httponly=True,
                    secure=True,
                    samesite='Lax',
                    max_age=60*30     # 30 minutes
                )
                return resp # and returning them
    return render_template('register.html') # if he hadnt clicked on the button (aka not a POST request, a GET request) then send him the site to click the button at


@app.route('/otp_input.html')
@app.route('/otp_input', methods=['GET', 'POST'])
def otp_input():
    if request.method == 'POST': # if the methode is post, aka the form got filled
        otp = request.form['otp'] # extract the otp
        ip_addr = request.remote_addr # extract the ip adrress
        password = request.cookies.get('pw') # get the password
        if VerifyUser(password=password, ip_addr=ip_addr) >= 0: # if the password/ip match, then ...
            key = -1

            with get_conn() as conn:
                key = conn.execute("SELECT * FROM user_2fa WHERE id = ?", (VerifyUser(password=password, ip_addr=ip_addr),)).fetchone() #get the otp passkey secret key

            if key == -1:
                return -1 # check if the key got changed to the coll

            totp_verify = pyotp.TOTP(key["totp_secret"]) # get the needed thing 
            
            if totp_verify.verify(otp=otp): # if the otp was correct
                session_alphabet = string.printable # get all printable chars (WHat could possibly go wrong, lol)
                session_id = ''.join(secrets.choice(session_alphabet) for i in range(128))  #  make a new session id with 128 chars

                userid = VerifyUser(password, ip_addr) # get the user id
                with get_conn() as conn:
                    conn.execute("INSERT INTO session (id, session_key, updated_at) VALUES (?, ?, ?) ON CONFLICT(id) DO UPDATE SET session_key = excluded.session_key, updated_at = excluded.updated_at",(userid, session_id, time.time()))
                    #LINE ABOVE: insert into the session the userid and session key, if the userid already exists (wich it does) it updates the session field instead of crashing
                resp = make_response(render_template('home_loggedin.html'))
                resp.set_cookie(
                    'session', session_id, # set the sessionid cookie
                    httponly=True, # only http/https
                    secure=True, #only https
                    samesite='Lax', # and only probably-ok requests
                    max_age=60*30     # 30 minutes
                )
                return resp
            else:
               return render_template('failure.html')  # TOPTP not ok
        else:
            return render_template('failure.html') #Password/Ip not matching
    return render_template('otp_input.html') # sending the form

@app.route('/verify_otp.html')
@app.route('/verify_otp', methods=['GET', 'POST'])
def otp_verify_afther_creation():
    ip_addr = request.remote_addr # get, once again the ip
    password = request.cookies.get('pw') # and gets the pw
    if VerifyUser(password=password, ip_addr=ip_addr) >= 0: # if they match
        ret = setup_otp(VerifyUser(password=password, ip_addr=ip_addr)) # setup the otp for the user
        userid = VerifyUser(password=password, ip_addr=ip_addr) # gets the userid

        if ret == -1: # If an error happens
            return f"An Error Happend and your Directory cant be made. This is NOT supposed to happen. Please contact me and say your id is {userid}"

        return f"""
<!DOCTYPE html>
<html>
    <body>
        <h3>Setup your OTP now - You will need it to login again:</h3>
        <br><br>
        <img src="/static/qr/{userid}/qr_auth.png" alt="Your otp password">
        <br><br>
        <a href="otp_input.html"> Continue to Verify OTP</a>
    </body>
</html>
    
""" # returns the qr code to scan with the phine. then routes to /otp_input

@app.route('/make_domain', methods=['POST'])
@app.route('/make_domain.html', methods=['POST'])
def homepage():
    session = request.cookies.get('session') # gets the session cookie

    if VerifyUser(request.cookies.get('pw'), request.remote_addr) == -2:
        return render_template("login.html")

    if verify(VerifyUser(request.cookies.get('pw'), request.remote_addr), request.cookies.get("session")) == 1: # verivies the session cookie
        if request.method == 'POST': # if it is post (aka user wants to make a domain)
            domainname = request.form['domainname'] # extract the subdomain name
            ip_link = request.form['ip'] # extract the ip adress for the subdomain

            retourncode = make_domain(VerifyUser(request.cookies.get('pw'), request.remote_addr), domainname, ip_link, session) # makes the domain
            if retourncode == -1: # if something happend
                return render_template('failure.html')
            elif retourncode == -2: # if the user added .freedomain.meme in the subdomain
                return "Sorry. Please DO NOT include .freedomain.meme in your A record!!!"
            elif retourncode == 0:
                return render_template('sucsess.html') # everything worked
            else:
                return f"Your Ip was already Taken. Rerouted you to {retourncode}.{domainname}.freedomain.meme"
    return render_template('failure.html') # the session verify didnt worked 



@app.route('/homepage')
@app.route('/homepage.html', methods=['GET', 'POST'])
def homepagev2():
    session = request.cookies.get('session')
    pw = request.cookies.get('pw')
    ip_addr = request.remote_addr

    if VerifyUser(request.cookies.get('pw'), request.remote_addr) == -2:
        return render_template("login.html")

    if verify(VerifyUser(pw, ip_addr), session) == 1:
        return render_template("home_loggedin.html")
    else:
        return render_template("login.html")

if __name__ == '__main__':
    init_db()
    TOKEN = os.getenv('DC_BOT_TKN')

    bot_thread = threading.Thread(target=run_bot, daemon=True)
    bot_thread.start()

    app.run()
