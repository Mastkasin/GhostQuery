import os
# Force disable macOS C-framework proxy detection to prevent thread segfaults
os.environ['no_proxy'] = '*'
os.environ['NO_PROXY'] = '*'

import json
import random
import re
import ssl
import threading
import http.client
from http.server import BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs, quote, unquote

USER_AGENTS = [
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36"
]

def get_ssl_context():
    """Bypasses macOS Python SSL Certificate verification issues."""
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    return ctx

def parse_ddg_html(html_content):
    """Parses html.duckduckgo.com results."""
    results = []
    # Match result links and snippets
    blocks = re.findall(r'<a\s+class="[^"]*result__a[^"]*"\s+href="([^"]+)">(.*?)</a>', html_content, re.DOTALL | re.IGNORECASE)
    snippets = re.findall(r'<(?:a|div)\s+class="[^"]*result__snippet[^"]*"[^>]*>(.*?)</(?:a|div)>', html_content, re.DOTALL | re.IGNORECASE)

    for idx, block in enumerate(blocks):
        try:
            url, raw_title = block[0].strip(), block[1].strip()
            title = re.sub(r'<[^>]+>', '', raw_title).strip()
            snippet = re.sub(r'<[^>]+>', '', snippets[idx]).strip() if idx < len(snippets) else ""

            # Unescape HTML entities
            title = title.replace('&amp;', '&').replace('&quot;', '"').replace('&#39;', "'")
            snippet = snippet.replace('&amp;', '&').replace('&quot;', '"').replace('&#39;', "'").replace('\n', ' ')

            # Resolve DDG target redirects (uddg=)
            if 'uddg=' in url:
                parsed = parse_qs(urlparse(url).query)
                if 'uddg' in parsed:
                    url = unquote(parsed['uddg'][0])

            if url and title and not url.startswith('//duckduckgo.com') and not url.startswith('https://duckduckgo.com'):
                results.append({"title": title, "url": url, "snippet": snippet or f"Search result for {title}."})
        except Exception:
            continue
    return results

def fetch_duckduckgo_api(query):
    """Tier 1: Official DuckDuckGo Instant Answer API (JSON, 0% 202 Rate Limits)"""
    try:
        print(f"🦆 [DDG API Tier 1] Querying DuckDuckGo JSON API for: '{query}'")
        conn = http.client.HTTPSConnection("api.duckduckgo.com", port=443, timeout=5, context=get_ssl_context())
        path = f"/?q={quote(query)}&format=json&no_html=1&skip_disambig=1"
        headers = {'User-Agent': random.choice(USER_AGENTS)}
        conn.request("GET", path, headers=headers)
        res = conn.getresponse()
        
        if res.status == 200:
            data = json.loads(res.read().decode('utf-8'))
            conn.close()
            results = []
            
            # Primary abstract if present
            if data.get("AbstractText") and data.get("AbstractURL"):
                title = data.get("Heading") or query.title()
                results.append({
                    "title": title,
                    "url": data.get("AbstractURL"),
                    "snippet": data.get("AbstractText")
                })
            
            # Related topics
            topics = data.get("RelatedTopics", [])
            for topic in topics:
                if isinstance(topic, dict) and topic.get("FirstURL") and topic.get("Text"):
                    raw_text = topic.get("Text", "")
                    parts = raw_text.split(" - ", 1)
                    title = parts[0] if len(parts) > 1 else raw_text[:40] + "..."
                    snippet = parts[1] if len(parts) > 1 else raw_text
                    
                    results.append({
                        "title": title.strip(),
                        "url": topic["FirstURL"],
                        "snippet": snippet.strip()
                    })
            if results:
                print(f"✅ [DDG API Tier 1] Found {len(results)} DuckDuckGo results.")
                return results
        conn.close()
    except Exception as e:
        print(f"⚠️ [DDG API Tier 1 Error]: {e}")
    return []

def get_ddg_vqd_token(query):
    """Fetches the session vqd token from DuckDuckGo to bypass HTTP 202 anti-bot blocks."""
    try:
        conn = http.client.HTTPSConnection("duckduckgo.com", port=443, timeout=4, context=get_ssl_context())
        headers = {
            'User-Agent': random.choice(USER_AGENTS),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5'
        }
        conn.request("GET", f"/?q={quote(query)}", headers=headers)
        res = conn.getresponse()
        if res.status == 200:
            html = res.read().decode('utf-8', errors='ignore')
            conn.close()
            match = re.search(r'vqd=["\']?([\d-]+)["\']?', html)
            if not match:
                match = re.search(r'vqd=([\d-]+)', html)
            if match:
                return match.group(1)
        conn.close()
    except Exception:
        pass
    return None

def fetch_duckduckgo_vqd_html(query):
    """Tier 2: DDG HTML Search with vqd Token Authentication"""
    try:
        print(f"🕵️ [DDG vqd Tier 2] Attempting vqd handshake for: '{query}'")
        vqd = get_ddg_vqd_token(query)
        
        conn = http.client.HTTPSConnection("html.duckduckgo.com", port=443, timeout=5, context=get_ssl_context())
        headers = {
            'User-Agent': random.choice(USER_AGENTS),
            'Content-Type': 'application/x-www-form-urlencoded',
            'Referer': 'https://html.duckduckgo.com/',
            'Origin': 'https://html.duckduckgo.com',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5'
        }
        
        body = f"q={quote(query)}&b=&kl=us-en"
        if vqd:
            body += f"&vqd={vqd}"
            
        conn.request("POST", "/html/", body=body, headers=headers)
        res = conn.getresponse()
        
        if res.status == 200:
            html = res.read().decode('utf-8', errors='ignore')
            conn.close()
            parsed = parse_ddg_html(html)
            if parsed:
                print(f"✅ [DDG vqd Tier 2] Found {len(parsed)} HTML results!")
                return parsed
        else:
            print(f"⚠️ [DDG vqd Tier 2] Blocked with HTTP Status {res.status}")
        conn.close()
    except Exception as e:
        print(f"⚠️ [DDG vqd Tier 2 Error]: {e}")
    return []

def fetch_wikipedia_fallback(query):
    """Tier 3: Wikipedia OpenSearch API (Failover)"""
    print(f"🔄 [Failover Tier 3] Querying Wikipedia API...")
    try:
        conn = http.client.HTTPSConnection("en.wikipedia.org", port=443, timeout=5, context=get_ssl_context())
        path = f"/w/api.php?action=opensearch&search={quote(query)}&limit=5&format=json"
        conn.request("GET", path, headers={'User-Agent': 'GhostQuery/1.0'})
        res = conn.getresponse()
        if res.status == 200:
            data = json.loads(res.read().decode('utf-8'))
            results = []
            if len(data) == 4:
                titles, snippets, urls = data[1], data[2], data[3]
                for i in range(len(titles)):
                    results.append({
                        "title": titles[i],
                        "url": urls[i],
                        "snippet": snippets[i] if snippets[i] else f"Wikipedia article for {titles[i]}."
                    })
            return results
    except Exception as e:
        print(f"⚠️ [Wiki Fallback Error]: {e}")
    return []

def fire_background_noise():
    """Fires a background noise query safely in a detached thread."""
    try:
        noise = random.choice(["weather", "recipes", "time", "history"])
        print(f"👻 [GhostQuery] Firing noise query: '{noise}'")
        fetch_duckduckgo_api(noise)
    except Exception:
        pass

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        try:
            parsed_path = urlparse(self.path)
            query_params = parse_qs(parsed_path.query)
            search_query = query_params.get('q', [''])[0]

            if not search_query:
                self._send_json({"error": "Missing query parameter 'q'."}, status=400)
                return

            # 1. Fire noise query in detached thread
            threading.Thread(target=fire_background_noise, daemon=True).start()

            # 2. Sequential DuckDuckGo pipeline: API Tier 1 -> vqd HTML Tier 2 -> Wikipedia Tier 3
            results = fetch_duckduckgo_api(search_query)
            if not results:
                results = fetch_duckduckgo_vqd_html(search_query)
            if not results:
                results = fetch_wikipedia_fallback(search_query)

            self._send_json({"results": results})

        except Exception as e:
            print(f"❌ [Server Exception]: {e}")
            self._send_json({"error": str(e)}, status=500)

    def _send_json(self, payload, status=200):
        body = json.dumps(payload).encode('utf-8')
        self.send_response(status)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Content-Length', str(len(body)))
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Cache-Control', 'no-store, no-cache, must-revalidate')
        self.end_headers()
        self.wfile.write(body)

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
