import json
import re
from typing import List, Dict

import requests
from bs4 import BeautifulSoup


def fetch_portfolio_list(root_url: str) -> List[Dict[str, str]]:
    """Fetch a Yahoo Finance portfolio page and extract portfolio links and names.

    Returns a list of dicts: {'name': <display name>, 'url': <absolute url>}.

    This is a best-effort HTML parse and may not work for all Yahoo pages if
    the site layout changes or if content is dynamically loaded by JavaScript.
    """
    try:
        # Use more realistic browser-like headers to reduce automatic blocking
        headers = {
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
            "Referer": "https://finance.yahoo.com/",
        }
        resp = requests.get(root_url, headers=headers, timeout=10)
        # If blocked or rate-limited, return empty early
        if resp.status_code == 429:
            return []
        resp.raise_for_status()
    except Exception:
        return []

    html = resp.text

    # First try to extract portfolio metadata from embedded JSON
    data = _extract_json_from_html(html)
    found = {}
    if data:
        # Look for objects that look like portfolios (have a name and an id/url)
        def _scan_for_portfolios(obj):
            if isinstance(obj, dict):
                # common keys: 'portfolios', 'portfolio', 'views'
                for k, v in obj.items():
                    if isinstance(k, str) and 'portfolio' in k.lower():
                        # v might be a list of portfolio dicts
                        if isinstance(v, list):
                            for item in v:
                                if isinstance(item, dict):
                                    name = item.get('name') or item.get('title') or item.get('portfolioName')
                                    url = item.get('url') or item.get('link') or item.get('path')
                                    if name and url:
                                        from urllib.parse import urljoin

                                        full = urljoin(root_url, str(url))
                                        found[full] = name
                        elif isinstance(v, dict):
                            name = v.get('name') or v.get('title')
                            url = v.get('url') or v.get('link')
                            if name and url:
                                from urllib.parse import urljoin

                                full = urljoin(root_url, str(url))
                                found[full] = name
                # recurse
                for v in obj.values():
                    _scan_for_portfolios(v)
            elif isinstance(obj, list):
                for item in obj:
                    _scan_for_portfolios(item)

        _scan_for_portfolios(data)

    # Fallback to HTML anchors search if JSON didn't yield results
    if not found:
        soup = BeautifulSoup(html, "lxml")
        anchors = soup.find_all("a", href=True)
        for a in anchors:
            href = a["href"]
            # look for portfolio links (pattern contains '/portfolio/' or '/portfolio/p_')
            if "/portfolio/" in href or "/portfolio/p_" in href:
                # get text if available
                name = a.get_text(strip=True)
                if not name:
                    # fallback to last path segment
                    name = href.rstrip("/").split("/")[-1]
                # build absolute URL
                from urllib.parse import urljoin

                full = urljoin(root_url, href)
                found[full] = name

    results = [{"name": v, "url": k} for k, v in found.items()]
    return results


def _extract_json_from_html(html: str):
    """Try to locate embedded JSON in Yahoo pages under root.App.main or similar."""
    # Common pattern: root.App.main = { ... };
    m = re.search(r"root\.App\.main\s*=\s*(\{.*\})\s*;", html, re.DOTALL)
    if not m:
        # alternative: look for 'window.__INITIAL_STATE__ = {...}'
        m = re.search(r"window\.__INITIAL_STATE__\s*=\s*(\{.*\})\s*;", html, re.DOTALL)
    if not m:
        return None
    try:
        return json.loads(m.group(1))
    except Exception:
        return None


def _walk_for_symbols(obj):
    """Recursively walk a JSON-like object and collect strings that look like tickers."""
    symbols = set()

    def _is_ticker(s: str) -> bool:
        # simple heuristic: uppercase letters, numbers, dots or dashes, short
        return bool(re.fullmatch(r"[A-Z0-9\.\-]{1,6}", s))

    def _recurse(o):
        if isinstance(o, dict):
            for k, v in o.items():
                if isinstance(k, str) and _is_ticker(k):
                    symbols.add(k)
                _recurse(v)
        elif isinstance(o, list):
            for item in o:
                _recurse(item)
        elif isinstance(o, str):
            if _is_ticker(o):
                symbols.add(o)

    _recurse(obj)
    return sorted(symbols)


def fetch_portfolio_tickers(portfolio_url: str) -> List[str]:
    """Fetch a Yahoo portfolio page and attempt to extract the holding tickers.

    Strategy:
    1. Try to parse embedded JSON under common global variables and extract symbols.
    2. Fallback to scraping visible tables/links and regex-matching ticker-like tokens.
    Returns a list of tickers (may be empty if extraction fails).
    """
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
            "Referer": "https://finance.yahoo.com/",
        }
        resp = requests.get(portfolio_url, headers=headers, timeout=10)
        if resp.status_code == 429:
            return []
        resp.raise_for_status()
    except Exception:
        return []

    html = resp.text

    # 1) Try embedded JSON
    data = _extract_json_from_html(html)
    if data:
        # Look for holdings/positions-like structures first
        candidates = set()

        def _scan_for_holdings(obj):
            if isinstance(obj, dict):
                # direct 'positions' or 'holdings'
                for k, v in obj.items():
                    key_lower = k.lower() if isinstance(k, str) else ''
                    if key_lower in ('positions', 'holdings', 'quotes', 'portfolio') and isinstance(v, list):
                        for entry in v:
                            if isinstance(entry, dict):
                                # common keys with ticker/symbol
                                for candidate_key in ('symbol', 'symbolName', 'ticker', 'id'):
                                    val = entry.get(candidate_key)
                                    if isinstance(val, str) and re.fullmatch(r"[A-Z0-9\.\-]{1,8}", val):
                                        candidates.add(val)
                                # some entries have nested 'quote' dict
                                q = entry.get('quote') or entry.get('symbol')
                                if isinstance(q, dict):
                                    s = q.get('symbol') or q.get('shortName')
                                    if isinstance(s, str) and re.fullmatch(r"[A-Z0-9\.\-]{1,8}", s):
                                        candidates.add(s)
                # recurse
                for v in obj.values():
                    _scan_for_holdings(v)
            elif isinstance(obj, list):
                for item in obj:
                    _scan_for_holdings(item)

        _scan_for_holdings(data)
        if candidates:
            return sorted(candidates)

        # fallback: generic symbol search in JSON
        symbols = _walk_for_symbols(data)
        if symbols:
            return symbols

    # 2) Fallback to HTML scraping
    soup = BeautifulSoup(html, "lxml")
    # Prefer anchors to quote pages: '/quote/SYMBOL' is a reliable indicator
    candidates = set()
    for a in soup.find_all("a", href=True):
        m = re.search(r"/quote/([A-Z0-9\.\-]{1,8})", a["href"])
        if m:
            candidates.add(m.group(1))

    # If none found via quote links, try table-based extraction but look for nearby anchors
    if not candidates:
        for table in soup.find_all("table"):
            for row in table.find_all("tr"):
                # look for anchor in the row linking to quote
                a = row.find("a", href=re.compile(r"/quote/"))
                if a and 'href' in a.attrs:
                    m = re.search(r"/quote/([A-Z0-9\.\-]{1,8})", a['href'])
                    if m:
                        candidates.add(m.group(1))
                else:
                    # fallback: check first cell text for ticker-like token
                    cells = row.find_all(["td", "th"])
                    if cells:
                        txt = cells[0].get_text(strip=True)
                        if re.fullmatch(r"[A-Z0-9\.\-]{1,8}", txt):
                            candidates.add(txt)

    # Final fallback: search page text but reduce false positives by requiring a short token (<=5)
    if not candidates:
        tokens = re.findall(r"\b[A-Z0-9\.\-]{1,6}\b", soup.get_text())
        for tok in tokens:
            if re.search(r"[A-Z]", tok) and not tok.isdigit() and len(tok) <= 5:
                candidates.add(tok)

    return sorted(candidates)
