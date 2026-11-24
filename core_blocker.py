import json
import ssl
import urllib.request
from urllib.parse import quote_plus
from PyQt6.QtWebEngineCore import QWebEngineUrlRequestInterceptor

AD_AND_TRACKER_DOMAINS = {
    "doubleclick.net", "googlesyndication.com", "googleadservices.com",
    "google-analytics.com", "googletagmanager.com", "://google.com",
    "connect.facebook.net", "://facebook.com", "ads-twitter.com",
    "://tiktok.com", "amazon-adsystem.com", "criteo.com",
    "taboola.com", "outbrain.com", "pubmatic.com", "rubiconproject.com",
    "openx.net", "adnxs.com", "scorecardresearch.com", "quantserve.com",
    "hotjar.com", "mixpanel.com", "segment.io", "sentry.io",
    "://duckduckgo.com", "://duckduckgo.com", "://bing.com"
}


def resolve_doh(hostname: str) -> str:
    """Resolves a domain over encrypted Cloudflare DNS-over-HTTPS (1.1.1.1) to bypass DNS blocks."""
    try:
        url = f"https://1.1.1{quote_plus(hostname)}&type=A"
        req = urllib.request.Request(url, headers={"Accept": "application/dns-json"})
        ctx = ssl._create_unverified_context()
        with urllib.request.urlopen(req, timeout=4, context=ctx) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        for ans in data.get("Answer", []):
            if ans.get("type") == 1 and ans.get("data"):
                return ans["data"]
    except Exception:
        pass
    return hostname


class CoreRequestBlocker(QWebEngineUrlRequestInterceptor):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.enabled = True
        self.stealth_https = True
        self.blocked_count = 0

    def interceptRequest(self, info):
        url = info.requestUrl()
        scheme = url.scheme().lower()
        host = url.host().lower()
        path = url.path().lower()

        # 1. Strip identifying headers so third-party software cannot fingerprint CORE
        if self.stealth_https:
            info.setHttpHeader(b"X-Requested-With", b"")
            info.setHttpHeader(b"Sec-GPC", b"1")
            if scheme == "http" and host not in ("localhost", "127.0.0.1") and not host.startswith("192.168."):
                secure_url = url
                secure_url.setScheme("https")
                info.redirect(secure_url)
                return

        if not self.enabled:
            return

        # 2. Block matching ad/tracker domains
        for domain in AD_AND_TRACKER_DOMAINS:
            if host == domain or host.endswith("." + domain):
                info.block(True)
                self.blocked_count += 1
                return

        # 3. Block DuckDuckGo ad clicks (/y.js) and ad-serving paths
        if ("duckduckgo.com" in host and path.startswith("/y.js")) or "/pagead/" in path:
            info.block(True)
            self.blocked_count += 1
            return
