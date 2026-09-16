# Adapted from r0xd4n3t/spider-to-wordlist (Apache 2.0)
# https://github.com/r0xd4n3t/spider-to-wordlist
# Original License File from 14.09.2026 At 10:00 is under "Apache 2.0 License From scraper.py original projekt.txt"
# Go Check Him out!!!!!

import re
import time
from urllib.parse import urlparse, urljoin

import urllib3
from bs4 import BeautifulSoup
from urllib3.exceptions import InsecureRequestWarning
from fake_useragent import UserAgent
import logging
import nltk
from nltk.corpus import stopwords
from collections import Counter
from web_target import normalize_url

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Disable insecure request warnings
urllib3.disable_warnings(category=InsecureRequestWarning)


try:
    stopwords.words('english')
except LookupError:
    nltk.download('stopwords')


class WebCrawler:
    def __init__(self, starting_urls, cleanup_interval=60, cleanup_delay=5, max_retries=2, host_header=None):
        self.visited_urls = set()
        self.wordlist = Counter()      
        self.urls_to_crawl = set()
        self.cleanup_interval = cleanup_interval
        self.cleanup_delay = cleanup_delay
        self.max_retries = max_retries 
        self.last_cleanup_time = time.time()
        self.allowed_domains = []
        self.host_header = host_header  
        self.reachable = False        
        self.http = urllib3.PoolManager(cert_reqs='CERT_NONE') 

        self.starting_urls = [normalize_url(url) for url in starting_urls]
        self.max_pages = 100
        self.last_response_url = None

        for url in starting_urls:
            self.allowed_domains.append(urlparse(url).netloc)
            self.urls_to_crawl.add(url)

    def build_wordlist(self, words):
        stop_en = set(stopwords.words('english'))
        for word in words:
            cleaned = word.strip().lower()
            if cleaned.isalpha() and cleaned not in stop_en:
                self.wordlist[cleaned] += 1

    def set_random_user_agent(self):
        """Generate a random user agent."""
        user_agent = UserAgent()
        return user_agent.random

    def fetch_url(self, url):
        headers = {'User-Agent': self.set_random_user_agent()}
        if self.host_header:
            headers['Host'] = self.host_header

        candidates = [url]
        if url.startswith("https://"):
            candidates.append("http://" + url[len("https://"):])

        timeout = urllib3.Timeout(connect=3.0, read=5.0)

        for candidate in candidates:
            for attempt in range(self.max_retries):
                try:
                    current = candidate
                    for redirect_count in range(6):
                        response = self.http.request(
                            'GET', current, headers=headers, timeout=timeout, retries=False, redirect=False
                        )
                        if response.status not in (301, 302, 303, 307, 308):
                            break
                        location = response.headers.get('Location')
                        if not location or redirect_count == 5:
                            break
                        current = normalize_url(urljoin(current, location))
                except urllib3.exceptions.SSLError as e:
                    logging.warning(f"SSL error (SNI/Cloudflare-typisch): {candidate} - {e}")
                    break  
                except urllib3.exceptions.MaxRetryError as e:
                    logging.warning(f"Connection failed: {candidate} - {e}")
                    break
                except urllib3.exceptions.TimeoutError as e:
                    logging.warning(f"Timeout: {candidate} - {e}")
                    time.sleep(0.5) 
                except Exception as e:
                    logging.warning(f"Error fetching {candidate}: {e}")
                    time.sleep(0.5)
        return None

    def is_valid_domain(self, url):
        """Check if the URL is within the allowed domain and subdomains."""
        parsed_url = urlparse(url)
        return any(
            parsed_url.netloc == domain or parsed_url.netloc.endswith('.' + domain)
            for domain in self.allowed_domains
        )

    def is_valid_url(self, url):
        """Check if the URL is valid and not a JavaScript or mailto link."""
        parsed_url = urlparse(url)
        return parsed_url.scheme in ['http', 'https'] and bool(parsed_url.netloc)

    def crawl_domain(self, base_url):
        """Crawl all pages within the specified domain."""
        self.urls_to_crawl.add(base_url)

        while self.urls_to_crawl and len(self.visited_urls) < self.max_pages:
            url = self.urls_to_crawl.pop()
            if url in self.visited_urls:
                continue
            self.visited_urls.add(url)

            response = self.fetch_url(url)
            if not response:
                continue

            url = self.last_response_url or url
            html = response.data
            try:
                soup = BeautifulSoup(html, 'html.parser')
            except Exception as e:
                logging.warning(f"Parser error: {url} - {e}")
                continue

            for element in soup(['skript', 'style', 'noskript']):
                element.decompose()
            text = soup.get_text()
            words = re.findall(r"[a-zA-Z]+", text)
            words = [word.encode('ascii', 'ignore').decode('utf-8') for word in words]
            self.build_wordlist(words)

            for link in soup.find_all('a', href=True):
                href = link['href']
                next_url = urljoin(url, href).split('#', 1)[0]
                if (
                    self.is_valid_domain(next_url)
                    and self.is_valid_url(next_url)
                    and next_url not in self.visited_urls
                ):
                    self.urls_to_crawl.add(next_url)

            logging.info(f"Crawled page: {url} [{len(words)} word(s) found]")

    def crawl(self) -> bool:
        
        try:
            for base_url in self.starting_urls:
                logging.info(f"Starting crawl for URL: {base_url}")
                self.crawl_domain(base_url)
        except KeyboardInterrupt:
            logging.info("Crawling process interrupted. Cleaning up and exiting gracefully.")
        return self.reachable


def start_thingy(url: str, amount: int):

    try:
        crawler = WebCrawler([normalize_url(starting_urls)])
    except ValueError as e:
        logging.warning("Invalid scrape target: %s", e)
        return None
    
    reachable = crawler.crawl()
    if not reachable or not crawler.wordlist:
        return None

    counts = Counter(crawler.wordlist)
    top_words = [word for word, count in counts.most_common(amount)]
    return top_words