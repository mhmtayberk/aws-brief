import logging
import feedparser
import requests
import random
import time
from typing import List, Dict, Any
from urllib.parse import urlparse
from bs4 import BeautifulSoup
from src.utils.config import settings
from datetime import datetime
from time import mktime

logger = logging.getLogger(__name__)

class FeedScraper:
    """
    Secure RSS/Atom Feed Scraper with SSRF protection and retry logic.
    """
    USER_AGENTS = [
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:109.0) Gecko/20100101 Firefox/119.0",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    ]
    TIMEOUT = 30
    ALLOWED_DOMAINS = ["aws.amazon.com", "amazon.com"]
    MAX_RETRIES = 3

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": random.choice(self.USER_AGENTS)})

    def _validate_url(self, url: str) -> bool:
        """Validate URL against whitelist to prevent SSRF attacks."""
        try:
            parsed = urlparse(url)
            domain = parsed.netloc.lower()
            return any(domain == allowed or domain.endswith(f".{allowed}") 
                      for allowed in self.ALLOWED_DOMAINS)
        except Exception:
            return False

    def fetch(self, url: str) -> str:
        """
        Fetch feed content with URL validation and retry logic.
        """
        if not self._validate_url(url):
            raise ValueError(f"URL not in whitelist: {url}")
        
        last_exception = None
        for attempt in range(self.MAX_RETRIES):
            try:
                ua = random.choice(self.USER_AGENTS)
                self.session.headers.update({"User-Agent": ua})
                
                sleep_time = random.uniform(1.5, 4.0)
                logger.debug(f"Sleeping {sleep_time:.2f}s before fetching {url}...")
                time.sleep(sleep_time)

                logger.info(f"Fetching feed: {url}")
                response = self.session.get(url, timeout=self.TIMEOUT)
                response.raise_for_status()
                return response.text
                
            except requests.RequestException as e:
                last_exception = e
                if attempt < self.MAX_RETRIES - 1:
                    wait_time = 2 ** attempt
                    logger.warning(f"Fetch failed (attempt {attempt + 1}/{self.MAX_RETRIES}), retrying in {wait_time}s: {e}")
                    time.sleep(wait_time)
                else:
                    logger.error(f"Failed to fetch {url} after {self.MAX_RETRIES} attempts: {e}")
        
        raise last_exception

    def parse(self, content: str) -> List[Dict[str, Any]]:
        """
        Parse raw feed content and return a list of simplified items.
        """
        feed = feedparser.parse(content)
        
        if feed.bozo:
            # Most of the time these are benign (e.g. encoding issues, mismatched tags in legacy feeds)
            # Log as debug to keep output clean, unless there are no entries (which implies failure)
            if not feed.entries:
                 logger.warning(f"Feed parsing failed (empty entries). Error: {feed.bozo_exception}")
            else:
                 logger.debug(f"Feed parsing warning (benign): {feed.bozo_exception}")

        items = []
        for entry in feed.entries:
            item = self._process_entry(entry)
            if item:
                items.append(item)
        
        logger.info(f"Parsed {len(items)} items from feed.")
        return items

    def _process_entry(self, entry: Any) -> Dict[str, Any]:
        """
        Process and sanitize a single feed entry.
        """
        try:
            # Extract basic fields
            title = self._sanitize_html(entry.get("title", "No Title"))
            link = entry.get("link", "")
            guid = entry.get("id", link)
            
            # Extract content: prefer 'content', then 'summary', then 'description'
            content_raw = ""
            if "content" in entry:
                content_raw = entry["content"][0].value
            elif "summary" in entry:
                content_raw = entry["summary"]
            else:
                content_raw = entry.get("description", "")

            content_clean = self._sanitize_html(content_raw)

            # Date handling
            published_struct = entry.get("published_parsed", entry.get("updated_parsed"))
            if published_struct:
                published_at = datetime.fromtimestamp(mktime(published_struct))
            else:
                published_at = datetime.utcnow()

            return {
                "source_id": guid,
                "title": title,
                "url": link,
                "content": content_clean,
                "published_at": published_at
            }
        except Exception as e:
            logger.error(f"Error processing entry: {e}")
            return None

    def _sanitize_html(self, html_text: str) -> str:
        """
        Remove dangerous tags and attributes from HTML.
        Uses BeautifulSoup.
        """
        if not html_text:
             return ""
        
        soup = BeautifulSoup(html_text, "html.parser")
        
        # Remove script and style elements
        for script in soup(["script", "style", "iframe", "object", "embed"]):
            script.decompose()

        # Get text only (simple version) or minimal safe HTML.
        # For now, let's keep it safe by returning text, 
        # or simplified HTML if needed. The constraint mentioned 'Secure Parsing'.
        # Returning get_text() is safest, but might lose formatting.
        # Let's return text for now as it's easier for LLM to summarize.
        
        return soup.get_text(separator=' ', strip=True)
