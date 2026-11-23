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


class CoreRequestBlocker(QWebEngineUrlRequestInterceptor):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.enabled = True
        self.blocked_count = 0

    def interceptRequest(self, info):
        if not self.enabled:
            return
        url = info.requestUrl()
        host = url.host().lower()
        path = url.path().lower()

        # Block matching ad/tracker domains and subdomains
        for domain in AD_AND_TRACKER_DOMAINS:
            if host == domain or host.endswith("." + domain):
                info.block(True)
                self.blocked_count += 1
                return

        # Block DuckDuckGo ad clicks (/y.js) and ad-serving paths
        if ("duckduckgo.com" in host and path.startswith("/y.js")) or "/pagead/" in path:
            info.block(True)
            self.blocked_count += 1
            return
