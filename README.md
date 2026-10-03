I recently started an Homeserver. However, all Free domain services needed either an Invite, where inactive or just weren't working. So, I made 

# FreeDomain.meme 

A free Subdomain hosting service.

## Features

- **1 Free subdomain** - What do you expect from an *Free Subdomain Service*?
- **And thats it.** - Nothing more, nothing less.

## Tech Stack

- **Backend**: Flask with Python. Why: Why Not? Simple and Easy! + cool and many Libaries 
- **Database**: SQLite 


## Installation

### Prerequisites

- Python 3.14+ (or 3.10+)
- Namecheap account with API access (Or the Playground - See example.env)
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

Update these in `main.py` for your Discord server:

- Line 109: Log channel ID
- Line 169: New domain notifications
- Line 191: Ban notifications

Update line 502, 518, 532, 551, 569, 585 with your Discord user ID for admin access.


6. Start everything & Init DB:
```bash
python main.py
```

## Usage

### Running the Application

```bash
python main.py
```

The app runs on `http://localhost:5000` by default.

### Discord Bot Commands

Admin commands:

- `$test <arg>` - Test bot responsiveness
- `$ban <userid> <reason>` - Ban user and remove their domain
- `$unbanKeepDomain <userid> <reason>` - Unban user, keep their domain
- `$whipe <userid> <reason>` - Remove user's domain without banning
- `$deleteUserCompetly <userid> <reason>` - Permanently delete user
- `$listAllUsr` - List all registered users
- `$getInfo <userid>` - Get detailed user information

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

### Rate Limits

Configured in line 50-55. Default: 200/day, 50/hour globally.

## Known Limitations

- One subdomain per IP address
- Subdomain names cannot contain "www"
- Only A DNS records supported

## Contributing

This is a personal project. Feel free to fork and modify for your own use.

## License

Web scraper adapted from [r0xd4n3t/spider-to-wordlist](https://github.com/r0xd4n3t/spider-to-wordlist) (Apache 2.0)
See `Apache 2.0 License From scraper.py original projekt.txt` for original license.

## Support

For issues or questions, visit the `/support` page or contact me through Discord.

## Why Does It Look So Bad?

Well, does it need to look good? It works, and that's the main thing it needs to do!

---

Made with ~~bugs~~ love ❤️  (and a bit of Bugs)
