# FreeDomain.meme 🌐

A free subdomain hosting service that provides easy-to-remember domains for your services, with built-in protections.

## Features

- **Free Subdomain Registration** - Get your own `*.freedomain.meme` subdomain
- **Automatic Bad Word Detection** - AI-powered filtering prevents inappropriate domain names
- **Content Moderation** - Automated web scraping checks for harmful content
- **Two-Factor Authentication** - Secure OTP-based 2FA for all accounts required
- **Discord Integration** - Real-time logging and admin commands via Discord bot
- **One Domain Per User** - Fair usage policy with one subdomain per IP address

## Tech Stack

- **Backend**: Flask (Python) Why: Why Not? Simple and Easy! + cool and many Libaries 
- **Database**: SQLite 
- **DNS Provider**: Namecheap API
- **Authentication**: pyotp (TOTP), SHA-256 password hashing
- **Content Analysis**: profanity-check, NLTK
- **Web Scraping**: BeautifulSoup4, urllib3
- **Bot**: Discord.py

## Installation

### Prerequisites

- Python 3.14+ (or 3.10+)
- Namecheap account with API access
- Discord bot token

### Setup

1. Clone the repository:
```bash
git clone <repository-url>
cd FreeDomain
```

2. Create a virtual environment and install dependencies:
```bash
python -m venv .venv
source .venv/bin/activate
pip install flask python-dotenv pyotp qrcode discord.py flask-limiter
pip install profanity-check beautifulsoup4 urllib3 fake-useragent nltk
pip install namecheap-sdk
```

3. Download NLTK stopwords:
```python
python -c "import nltk; nltk.download('stopwords')"
```

4. Create a `.env` file based on `example.env`:
```bash
cp example.env .env
```

5. Configure your `.env` file:
```env
DC_BOT_TKN=your_discord_bot_token_here
NAMECHEAP_API_KEY=your_namecheap_api_key
NAMECHEAP_API_USER=your_namecheap_username
NAMECHEAP_CLIENT_IP=your_whitelisted_ip
```

6. Initialize the database:
```bash
python main.py
```

The application will automatically create `app.db` with the required schema.

## Usage

### Running the Application

```bash
python main.py
```

The Flask app runs on `http://localhost:5000` by default.

### User Workflow

1. **Register** at `/register` - Receive a secure 64-character password
2. **Setup 2FA** at `/verify_otp` - Scan QR code with authenticator app
3. **Login** at `/login` - Enter password and OTP code
4. **Create Subdomain** - Choose subdomain name and target IP/domain
5. **Manage Domain** - Update or delete your subdomain anytime

### Discord Bot Commands

Admin commands (requires hardcoded admin Discord ID - In code editable):

- `$test <arg>` - Test bot responsiveness
- `$ban <userid> <reason>` - Ban user and remove their domain
- `$unbanKeepDomain <userid> <reason>` - Unban user, keep their domain
- `$whipe <userid> <reason>` - Remove user's domain without banning
- `$deleteUserCompetly <userid> <reason>` - Permanently delete user
- `$listAllUsr` - List all registered users
- `$getInfo <userid>` - Get detailed user information

## Architecture

### Database Schema

- **users** - User accounts with password hashes and IP addresses
- **user_2fa** - TOTP secrets for two-factor authentication
- **subdomains** - Subdomain mappings to target IPs
- **session** - Active user sessions with 30-minute timeout etc

### Security Features

1. **Password Generation** - Server-generated 64-character passwords
2. **Session Management** - HttpOnly, Secure, SameSite cookies
3. **Rate Limiting** - 25 requests per hour on sensitive endpoints
4. **TOTP 2FA** - Time-based one-time passwords
5. **Content Filtering** - Automated profanity and harmful content detection

### Content Moderation

The system runs automated checks every 6 hours:

1. Scrapes up to 100 pages per subdomain
2. Extracts and analyzes text content
3. Runs profanity detection on extracted words
4. Automatically bans domains when the chance of a bad word is greater than 50%
5. Sends Discord notifications for manual review

## Project Structure

```
FreeDomain/
├── main.py              # Flask app, Discord bot, main logic
├── scraper.py           # Web crawler for content analysis
├── web_target.py        # URL normalization and DNS helpers
├── templates/           # HTML templates
├── static/              # Static assets and QR codes
├── app.db               # SQLite database
├── .env                 # Environment variables (not in git - obviously)
└── README.md            # This file
```

## API Endpoints

- `GET /` - Homepage
- `GET /register` - Registration page
- `POST /register` - Create new account
- `GET /login` - Login page
- `POST /login` - Authenticate user
- `GET /verify_otp` - 2FA setup page
- `POST /otp_input` - 2FA verification
- `POST /make_domain` - Create subdomain
- `POST /removedomain` - Delete subdomain
- `POST /deleteme` - Delete account
- `GET /homepage` - User dashboard
- `GET /support` - Support page

## Configuration

### Discord Channel IDs

Update these in `main.py` for your Discord server:

- Line 109: Log channel ID
- Line 169: New domain notifications
- Line 191: Ban notifications

### Admin Discord ID

Update line 502, 518, 532, 551, 569, 585 with your Discord user ID for admin access.

### Rate Limits

Configured in line 50-55. Default: 200/day, 50/hour globally.

## Known Limitations

- One subdomain per IP address
- 30-minute session timeout
- Subdomain names cannot contain "freedomain.meme" or "www"
- Only A and AAAA DNS records supported

## Contributing

This is a personal project. Feel free to fork and modify for your own use.

## License

Web scraper adapted from [r0xd4n3t/spider-to-wordlist](https://github.com/r0xd4n3t/spider-to-wordlist) (Apache 2.0)
See `Apache 2.0 License From scraper.py original projekt.txt` for original license.

## Support

For issues or questions, visit the `/support` page or contact the admin through Discord.

## Why Does It Look So Bad?

Well, does it need to look good? It works, and that's the main thing it needs to do!

---

Made with ~~bugs~~ love ❤️  (and a bit of Bugs)
