import os
import socket
import ssl
import subprocess
import shutil
import time
import urllib.request
from PyQt6.QtNetwork import QNetworkProxy

_tor_proc = None


def _port_open(host: str, port: int, timeout: float = 0.8) -> bool:
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except Exception:
        return False


def _ensure_tor_running() -> bool:
    global _tor_proc
    if _port_open("127.0.0.1", 9050):
        return True
    if _port_open("127.0.0.1", 9150):
        return True
    tor_bin = shutil.which("tor")
    if not tor_bin:
        return False
    tor_data = os.path.join(os.path.expanduser("~"), ".core-browser", "tor_data")
    os.makedirs(tor_data, exist_ok=True)
    _tor_proc = subprocess.Popen(
        [tor_bin, "--SocksPort", "9050", "--DataDirectory", tor_data],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
    )
    for _ in range(16):
        if _port_open("127.0.0.1", 9050, 0.5):
            return True
        time.sleep(0.5)
    return False


def _fetch_working_relay():
    """Fetches live verified HTTP/SOCKS5 relays and returns the first fast reachable (type, host, port)."""
    ctx = ssl._create_unverified_context()
    sources = [
        ("http", "https://proxyscrape.com"),
        ("socks5", "https://proxyscrape.com")
    ]
    for ptype, url in sources:
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=5, context=ctx) as resp:
                lines = resp.read().decode("utf-8", errors="ignore").splitlines()
            for line in lines[:25]:
                if ":" not in line:
                    continue
                h, p_str = line.strip().split(":", 1)
                p = int(p_str)
                if _port_open(h, p, 0.7):
                    return ptype, h, p
        except Exception:
            continue
    return None


def apply_network_proxy(settings: dict) -> str:
    mode = settings.get("proxy_mode", "direct")
    host = settings.get("proxy_host", "").strip()
    port = int(settings.get("proxy_port", 0) or 0)
    user = settings.get("proxy_user", "").strip()
    pwd = settings.get("proxy_pass", "").strip()

    if mode == "auto":
        relay = _fetch_working_relay()
        if relay:
            rtype, rh, rp = relay
            qt_type = QNetworkProxy.ProxyType.Socks5Proxy if rtype == "socks5" else QNetworkProxy.ProxyType.HttpProxy
            QNetworkProxy.setApplicationProxy(QNetworkProxy(qt_type, rh, rp))
            return f"VPN Relay ({rh}:{rp})"
        QNetworkProxy.setApplicationProxy(QNetworkProxy(QNetworkProxy.ProxyType.NoProxy))
        return "Direct + DoH (No Relay)"

    if mode == "tor":
        if _ensure_tor_running():
            p_num = 9050 if _port_open("127.0.0.1", 9050) else 9150
            QNetworkProxy.setApplicationProxy(QNetworkProxy(QNetworkProxy.ProxyType.Socks5Proxy, "127.0.0.1", p_num))
            return f"Tor Onion (127.0.0.1:{p_num})"
        QNetworkProxy.setApplicationProxy(QNetworkProxy(QNetworkProxy.ProxyType.NoProxy))
        return "Direct + DoH"

    if mode in ("socks5", "http") and host and port > 0:
        if _port_open(host, port, 1.5):
            ptype = QNetworkProxy.ProxyType.Socks5Proxy if mode == "socks5" else QNetworkProxy.ProxyType.HttpProxy
            QNetworkProxy.setApplicationProxy(QNetworkProxy(ptype, host, port, user, pwd))
            return f"{mode.upper()} ({host}:{port})"
        QNetworkProxy.setApplicationProxy(QNetworkProxy(QNetworkProxy.ProxyType.NoProxy))
        return "Direct + DoH (Proxy Offline)"

    QNetworkProxy.setApplicationProxy(QNetworkProxy(QNetworkProxy.ProxyType.NoProxy))
    return "Direct + DoH"
