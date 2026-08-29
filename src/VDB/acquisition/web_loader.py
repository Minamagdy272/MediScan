"""
web_loader.py - Robust web document scraper with browser headers & fallback parsing.
"""

import requests
from bs4 import BeautifulSoup
from typing import Optional, Dict

DEFAULT_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
}


def fetch_url_html(url: str, timeout: int = 30) -> str:
    """Fetch HTML raw content using custom headers."""
    resp = requests.get(url, headers=DEFAULT_HEADERS, timeout=timeout)
    resp.raise_for_status()
    return resp.text


def extract_clean_text_from_html(html_content: str) -> str:
    """Parse HTML and extract clean readable text stripped of scripts and styles."""
    soup = BeautifulSoup(html_content, "html.parser")
    for elem in soup(["script", "style", "nav", "footer", "header", "noscript", "aside"]):
        elem.extract()
    return soup.get_text(separator="\n", strip=True)


def load_web_page(url: str, timeout: int = 30) -> str:
    """Convenience function: fetch and extract clean text from a web URL."""
    html = fetch_url_html(url, timeout=timeout)
    return extract_clean_text_from_html(html)
