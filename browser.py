import sys
import os


def _init_ota_path():
    ota_dir = os.path.join(os.path.expanduser("~"), ".core-browser", "ota")
    os.makedirs(ota_dir, exist_ok=True)
    if ota_dir not in sys.path:
        sys.path.insert(0, ota_dir)
    return ota_dir


OTA_DIR = _init_ota_path()

import json
import base64
import urllib.request
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse, quote_plus, unquote

from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

from PyQt6.QtCore import QUrl, Qt, QSize, QTimer
from PyQt6.QtGui import QColor, QIcon, QPixmap, QPainter, QFont
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QTabWidget, QLineEdit,
    QPushButton, QDockWidget, QWidget, QVBoxLayout, QHBoxLayout,
    QTextEdit, QLabel, QInputDialog, QMessageBox, QListWidget
)
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtWebEngineCore import QWebEngineProfile, QWebEnginePage, QWebEngineScript

from core_blocker import CoreRequestBlocker, AD_AND_TRACKER_DOMAINS
from core_ui import (
    THEMES, BROWSER_PROFILES, build_qt_stylesheet,
    render_home_html, render_settings_html
)
from core_desktop import render_desktop_html


def get_resource_path(filename: str) -> str:
    if hasattr(sys, "_MEIPASS"):
        return os.path.join(sys._MEIPASS, filename)
    return os.path.join(get_app_dir(), filename)


def get_app_dir() -> str:
    if getattr(sys, 'frozen', False):
        exe_dir = os.path.dirname(sys.executable)
        if os.access(exe_dir, os.W_OK):
            return exe_dir
        user_dir = os.path.join(os.path.expanduser("~"), ".core-browser")
        os.makedirs(user_dir, exist_ok=True)
        return user_dir
    return os.path.dirname(os.path.abspath(__file__))


class CryptoVault:
    def __init__(self, vault_file="core_vault.enc"):
        base_dir = get_app_dir()
        self.vault_path = os.path.join(base_dir, vault_file)
        self.salt_path = os.path.join(base_dir, "core_vault.salt")
        self.fernet = None

    def _get_salt(self) -> bytes:
        if os.path.exists(self.salt_path):
            with open(self.salt_path, "rb") as f:
                return f.read()
        salt = os.urandom(16)
        with open(self.salt_path, "wb") as f:
            f.write(salt)
        return salt

    def unlock(self, password: str) -> bool:
        salt = self._get_salt()
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=480000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(password.encode()))
        self.fernet = Fernet(key)
        try:
            self.load_data()
            return True
        except Exception:
            self.fernet = None
            return False

    def load_data(self) -> dict:
        if not self.fernet:
            raise ValueError("Vault is locked.")
        if not os.path.exists(self.vault_path):
            return {"bookmarks": [], "notes": ""}
        with open(self.vault_path, "rb") as f:
            encrypted = f.read()
        decrypted = self.fernet.decrypt(encrypted)
        return json.loads(decrypted.decode("utf-8"))

    def save_data(self, data: dict):
        if not self.fernet:
            raise ValueError("Vault is locked.")
        raw = json.dumps(data).encode("utf-8")
        encrypted = self.fernet.encrypt(raw)
        with open(self.vault_path, "wb") as f:
            f.write(encrypted)


TRACKING_PARAMS = {
    "utm_source", "utm_medium", "utm_campaign", "utm_term", "utm_content",
    "fbclid", "gclid", "msclkid", "mc_eid", "ref", "ref_src"
}


def clean_url(raw_url: str) -> str:
    if not raw_url.startswith(("http://", "https://")):
        raw_url = "https://" + raw_url
    parsed = urlparse(raw_url)
    query_params = parse_qs(parsed.query)
    cleaned_params = {
        k: v for k, v in query_params.items() if k.lower() not in TRACKING_PARAMS
    }
    new_query = urlencode(cleaned_params, doseq=True)
    return urlunparse((
        parsed.scheme, parsed.netloc, parsed.path,
        parsed.params, new_query, parsed.fragment
    ))


CORE_AD_AND_DDG_SCRUB_JS = """
(function() {
    const scrub = () => {
        if (!window.location.href.includes('duckduckgo.com')) return;
        const head = document.head || document.documentElement;
        if (head && !document.getElementById('core-ddg-css')) {
            const s = document.createElement('style');
            s.id = 'core-ddg-css';
            s.textContent = `
                html, body, .site-wrapper, .header-wrap, #header_wrapper { background-color: #14171c !important; }
                a[href*="duck.ai"], [data-testid="duckai-button"], [aria-label*="Duck.ai" i],
                button[aria-label*="feedback" i], [data-testid="feedback-prompt"],
                [data-testid="ad"], .result--ad, .results--ads, li[data-layout="ad"],
                .js-badge-link, .badge-link, .header--aside, .nav-menu--theme, .footer {
                    display: none !important;
                }
            `;
            head.appendChild(s);
        }
        document.querySelectorAll('header a[href="/"], header a[href^="/?"], [data-testid="header-logo"]').forEach(link => {
            if (!link.dataset.coreSwapped) {
                link.dataset.coreSwapped = '1';
                link.innerHTML = '<span style="color:#f0f6fc;font-weight:800;font-size:18px;letter-spacing:4px;font-family:sans-serif;padding:0 8px;">CORE</span>';
            }
        });
        document.querySelectorAll('article, li').forEach(card => {
            if (card.querySelector('a[href*="://duckduckgo.com"], span[data-testid="ad-badge"]')) {
                card.style.setProperty('display', 'none', 'important');
            }
        });
        document.querySelectorAll('a, button, span').forEach(el => {
            if (el.children.length > 0) return;
            const txt = (el.textContent || '').trim();
            if (txt === 'Ask Duck.ai' || txt === 'Share Feedback') {
                const item = el.closest('li, button, a') || el;
                item.style.setProperty('display', 'none', 'important');
            }
        });
        if (document.title.includes('DuckDuckGo')) {
            document.title = document.title.replace(/at DuckDuckGo/gi, '- CORE').replace(/DuckDuckGo/gi, 'CORE');
        }
    };
    const start = () => {
        if (!document.documentElement) { requestAnimationFrame(start); return; }
        scrub();
        new MutationObserver(scrub).observe(document.documentElement, { childList: true, subtree: true });
    };
    start();
})();
"""


class CoreBrowser(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("CORE")
        self.resize(1280, 820)
        icon_file = get_resource_path("core_icon.png")
        if os.path.exists(icon_file):
            self.setWindowIcon(QIcon(icon_file))

        self.settings_path = os.path.join(get_app_dir(), "core_settings.json")
        self.settings = self._load_settings()
        self.ota_path = os.path.join(get_app_dir(), "core_ota.json")
        self.ota_info = self._load_ota()

        self.ram_profile = QWebEngineProfile()
        self.ram_profile.setHttpCacheType(QWebEngineProfile.HttpCacheType.MemoryHttpCache)
        self.ram_profile.setPersistentCookiesPolicy(
            QWebEngineProfile.PersistentCookiesPolicy.AllowPersistentCookies
        )

        self.blocker = CoreRequestBlocker()
        self.blocker.enabled = self.settings.get("blocker_enabled", True)
        self.ram_profile.setUrlRequestInterceptor(self.blocker)

        script = QWebEngineScript()
        script.setName("CoreInstantSkin")
        script.setSourceCode(CORE_AD_AND_DDG_SCRUB_JS)
        script.setInjectionPoint(QWebEngineScript.InjectionPoint.DocumentCreation)
        script.setWorldId(QWebEngineScript.ScriptWorldId.MainWorld)
        script.setRunsOnSubFrames(True)
        self.ram_profile.scripts().insert(script)

        self.vault = CryptoVault()

        central = QWidget()
        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        self.setCentralWidget(central)

        self.tabs = QTabWidget()
        self.tabs.setDocumentMode(True)
        self.tabs.setTabsClosable(True)
        self.tabs.setMovable(True)
        self.tabs.setIconSize(QSize(15, 15))
        self.tabs.tabCloseRequested.connect(self.close_tab)
        self.tabs.currentChanged.connect(self.update_url_bar)

        new_tab_btn = QPushButton("+")
        new_tab_btn.setObjectName("NewTabBtn")
        new_tab_btn.setToolTip("New Tab")
        new_tab_btn.clicked.connect(self.open_core_home)
        self.tabs.setCornerWidget(new_tab_btn, Qt.Corner.TopRightCorner)

        nav_bar = QWidget()
        nav_bar.setObjectName("NavBar")
        nav_layout = QHBoxLayout(nav_bar)
        nav_layout.setContentsMargins(8, 5, 10, 5)
        nav_layout.setSpacing(4)

        for label, tip, slot in [
            ("←", "Back", lambda: self.current_browser().back()),
            ("→", "Forward", lambda: self.current_browser().forward()),
            ("↻", "Reload", lambda: self.current_browser().reload()),
            ("⌂", "Home", lambda: self.load_core_home(self.current_browser())),
        ]:
            btn = QPushButton(label)
            btn.setProperty("class", "NavBtn")
            btn.setToolTip(tip)
            btn.clicked.connect(slot)
            nav_layout.addWidget(btn)

        self.url_bar = QLineEdit()
        self.url_bar.setObjectName("UrlBar")
        self.url_bar.setPlaceholderText("Search or enter web address")
        self.url_bar.returnPressed.connect(self.navigate_to_url)
        nav_layout.addWidget(self.url_bar, 1)

        self.shield_badge = QLabel()
        self.shield_badge.setObjectName("ShieldBadge")
        nav_layout.addWidget(self.shield_badge)

        desktop_btn = QPushButton("🖥")
        desktop_btn.setProperty("class", "NavBtn")
        desktop_btn.setToolTip("CORE OS Desktop (core://desktop)")
        desktop_btn.clicked.connect(lambda: self.load_core_desktop(self.current_browser()))
        nav_layout.addWidget(desktop_btn)

        settings_btn = QPushButton("⚙")
        settings_btn.setProperty("class", "NavBtn")
        settings_btn.setToolTip("CORE Settings (core://settings)")
        settings_btn.clicked.connect(lambda: self.load_core_settings(self.current_browser()))
        nav_layout.addWidget(settings_btn)

        save_btn = QPushButton("☆")
        save_btn.setProperty("class", "NavBtn")
        save_btn.setToolTip("Bookmark to Encrypted Vault")
        save_btn.clicked.connect(self.save_current_bookmark)
        nav_layout.addWidget(save_btn)

        tools_btn = QPushButton("☰")
        tools_btn.setProperty("class", "NavBtn")
        tools_btn.setToolTip("CORE Vault & Developer Tools")
        tools_btn.clicked.connect(self.toggle_tools_dock)
        nav_layout.addWidget(tools_btn)

        main_layout.addWidget(self.tabs.tabBar())
        main_layout.addWidget(nav_bar)
        main_layout.addWidget(self.tabs, 1)

        self._init_tools_dock()
        self._apply_settings_state()
        self.open_core_home()

    def _load_settings(self) -> dict:
        default = {
            "theme": "Midnight Slate",
            "engine": "Chromium",
            "blocker_enabled": True,
            "widgets": {"clock": True, "shield": True, "notes": True, "shortcuts": True}
        }
        if os.path.exists(self.settings_path):
            try:
                with open(self.settings_path, "r") as f:
                    default.update(json.load(f))
            except Exception:
                pass
        return default

    def _save_settings(self):
        with open(self.settings_path, "w") as f:
            json.dump(self.settings, f, indent=2)

    def _load_ota(self) -> dict:
        if os.path.exists(self.ota_path):
            try:
                with open(self.ota_path, "r") as f:
                    data = json.load(f)
                AD_AND_TRACKER_DOMAINS.update(data.get("extra_block_domains", []))
                return data
            except Exception:
                pass
        return {"ota_version": "2.0.0", "announcement": "", "extra_themes": {}, "extra_block_domains": []}

    def _sync_ota(self, browser: QWebEngineView):
        base_raw = "https://githubusercontent.com"
        try:
            req = urllib.request.Request(base_raw + "ota_manifest.json", headers={"User-Agent": "CORE-Browser-OTA"})
            with urllib.request.urlopen(req, timeout=8) as resp:
                data = json.loads(resp.read().decode("utf-8"))
            for mod_name in data.get("code_modules", []):
                m_req = urllib.request.Request(base_raw + mod_name, headers={"User-Agent": "CORE-Browser-OTA"})
                with urllib.request.urlopen(m_req, timeout=8) as m_resp:
                    with open(os.path.join(OTA_DIR, mod_name), "wb") as mf:
                        mf.write(m_resp.read())
            with open(self.ota_path, "w") as f:
                json.dump(data, f, indent=2)
            self.ota_info = self._load_ota()
            self._apply_settings_state()
            QMessageBox.information(self, "CORE Live Update", f"Synced v{self.ota_info.get('ota_version', '2.0')}! Restart CORE to activate new modules.")
        except Exception as e:
            QMessageBox.warning(self, "OTA Sync", f"Update check failed or offline:\n{e}")
        self.load_core_settings(browser)

    def _apply_settings_state(self):
        self.setStyleSheet(build_qt_stylesheet(self.settings.get("theme", "Midnight Slate"), self.ota_info.get("extra_themes", {})))
        engine = self.settings.get("engine", "Chromium")
        profile = BROWSER_PROFILES.get(engine, BROWSER_PROFILES["Chromium"])
        base_ua = QWebEngineProfile.defaultProfile().httpUserAgent()
        if engine in ("Firefox", "Internet Explorer"):
            self.ram_profile.setHttpUserAgent(profile["ua"])
        elif profile["ua"]:
            self.ram_profile.setHttpUserAgent(base_ua + " " + profile["ua"])
        else:
            self.ram_profile.setHttpUserAgent(base_ua)
        self.blocker.enabled = self.settings.get("blocker_enabled", True)
        self.shield_badge.setText(f"{engine} • Shield {'ON' if self.blocker.enabled else 'OFF'}")

    def _init_tools_dock(self):
        self.dock = QDockWidget("CORE Vault & Inspector", self)
        self.dock.setAllowedAreas(Qt.DockWidgetArea.RightDockWidgetArea | Qt.DockWidgetArea.LeftDockWidgetArea)

        container = QWidget()
        container.setObjectName("DockBody")
        layout = QVBoxLayout(container)
        layout.setSpacing(8)

        layout.addWidget(QLabel("Encrypted Vault (AES-256)"))
        vault_btn_row = QHBoxLayout()
        unlock_btn = QPushButton("Unlock / Create")
        unlock_btn.setProperty("class", "DockBtn")
        unlock_btn.clicked.connect(self.unlock_vault)
        save_notes_btn = QPushButton("Save Vault")
        save_notes_btn.setProperty("class", "DockBtn")
        save_notes_btn.clicked.connect(self.save_vault_state)
        vault_btn_row.addWidget(unlock_btn)
        vault_btn_row.addWidget(save_notes_btn)
        layout.addLayout(vault_btn_row)

        self.bookmark_list = QListWidget()
        self.bookmark_list.itemDoubleClicked.connect(
            lambda item: self.add_new_tab(QUrl(item.text()), "Vault Link")
        )
        layout.addWidget(QLabel("Saved Bookmarks:"))
        layout.addWidget(self.bookmark_list)

        layout.addWidget(QLabel("Encrypted Notes:"))
        self.vault_notes = QTextEdit()
        self.vault_notes.setPlaceholderText("Unlock vault to edit encrypted notes...")
        layout.addWidget(self.vault_notes)

        layout.addWidget(QLabel("Page Source Inspector"))
        inspect_btn = QPushButton("Inspect Current HTML")
        inspect_btn.setProperty("class", "DockBtn")
        inspect_btn.clicked.connect(self.grab_page_source)
        layout.addWidget(inspect_btn)

        self.source_view = QTextEdit()
        self.source_view.setReadOnly(True)
        layout.addWidget(self.source_view)

        self.dock.setWidget(container)
        self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, self.dock)
        self.dock.hide()

    def open_core_home(self):
        browser = self.add_new_tab(None, "New Tab")
        self.load_core_home(browser)

    def load_core_home(self, browser: QWebEngineView):
        browser.setProperty("core_page", "home")
        browser.setHtml(render_home_html(self.settings, self.blocker.blocked_count, self.ota_info), QUrl("about:blank"))
        self.url_bar.setText("core://home")
        idx = self.tabs.indexOf(browser)
        if idx != -1:
            self.tabs.setTabText(idx, "New Tab")
            self.tabs.setTabIcon(idx, self._core_tab_icon())

    def load_core_settings(self, browser: QWebEngineView):
        browser.setProperty("core_page", "settings")
        browser.setHtml(render_settings_html(self.settings, self.blocker.blocked_count, self.ota_info), QUrl("about:blank"))
        self.url_bar.setText("core://settings")
        idx = self.tabs.indexOf(browser)
        if idx != -1:
            self.tabs.setTabText(idx, "Settings")
            self.tabs.setTabIcon(idx, self._core_tab_icon())

    def load_core_desktop(self, browser: QWebEngineView):
        browser.setProperty("core_page", "desktop")
        browser.setHtml(render_desktop_html(self.settings, self.blocker.blocked_count), QUrl("about:blank"))
        self.url_bar.setText("core://desktop")
        idx = self.tabs.indexOf(browser)
        if idx != -1:
            self.tabs.setTabText(idx, "CORE Desktop")
            self.tabs.setTabIcon(idx, self._core_tab_icon())

    def _search_url_for_query(self, query: str) -> str:
        engine = self.settings.get("engine", "Chromium")
        template = BROWSER_PROFILES.get(engine, BROWSER_PROFILES["Chromium"])["search_url"]
        return template + quote_plus(query)

    def add_new_tab(self, qurl: QUrl = None, label="New Tab") -> QWebEngineView:
        browser = QWebEngineView()
        owner = self

        class CorePage(QWebEnginePage):
            def acceptNavigationRequest(self, url, nav_type, is_main_frame):
                u = url.toString()
                if u == "core://home":
                    QTimer.singleShot(0, lambda: owner.load_core_home(browser))
                    return False
                if u == "core://settings":
                    QTimer.singleShot(0, lambda: owner.load_core_settings(browser))
                    return False
                if u == "core://desktop":
                    QTimer.singleShot(0, lambda: owner.load_core_desktop(browser))
                    return False
                if u.startswith("core-engine:"):
                    eng = unquote(u.split("core-engine:", 1).pop())
                    if eng in BROWSER_PROFILES:
                        owner.settings["engine"] = eng
                        owner._save_settings()
                        owner._apply_settings_state()
                    QTimer.singleShot(0, lambda: owner.load_core_home(browser))
                    return False
                if u.startswith("core-save:"):
                    raw = unquote(u.split("core-save:", 1).pop())
                    owner.settings.update(json.loads(raw))
                    owner._save_settings()
                    owner._apply_settings_state()
                    QTimer.singleShot(0, lambda: owner.load_core_home(browser))
                    return False
                if u == "core-ota:sync":
                    QTimer.singleShot(0, lambda: owner._sync_ota(browser))
                    return False
                return super().acceptNavigationRequest(url, nav_type, is_main_frame)

        page = CorePage(self.ram_profile, browser)
        all_themes = {**THEMES, **self.ota_info.get("extra_themes", {})}
        bg = all_themes.get(self.settings.get("theme", "Midnight Slate"), THEMES["Midnight Slate"])["bg"]
        page.setBackgroundColor(QColor(bg))
        browser.setPage(page)

        idx = self.tabs.addTab(browser, label)
        self.tabs.setCurrentIndex(idx)

        browser.urlChanged.connect(lambda q, b=browser: self._on_url_changed(q, b))
        browser.loadFinished.connect(lambda ok, b=browser: self._on_load_finished(ok, b))
        browser.iconChanged.connect(lambda icon, b=browser: self._on_icon_changed(icon, b))

        if qurl:
            browser.setProperty("core_page", "web")
            browser.setUrl(qurl)
        return browser

    def _core_tab_icon(self) -> QIcon:
        pix = QPixmap(24, 24)
        pix.fill(Qt.GlobalColor.transparent)
        p = QPainter(pix)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        all_themes = {**THEMES, **self.ota_info.get("extra_themes", {})}
        accent = all_themes.get(self.settings.get("theme", "Midnight Slate"), THEMES["Midnight Slate"])["accent"]
        p.setBrush(QColor(accent))
        p.setPen(Qt.PenStyle.NoPen)
        p.drawRoundedRect(2, 2, 20, 20, 6, 6)
        p.setPen(QColor("#ffffff"))
        p.setFont(QFont("Sans", 11, QFont.Weight.Bold))
        p.drawText(pix.rect(), Qt.AlignmentFlag.AlignCenter, "C")
        p.end()
        return QIcon(pix)

    def _on_icon_changed(self, icon, browser: QWebEngineView):
        idx = self.tabs.indexOf(browser)
        if idx == -1:
            return
        u = browser.url().toString()
        if "duckduckgo.com" in u or u in ("about:blank", ""):
            self.tabs.setTabIcon(idx, self._core_tab_icon())
        elif not icon.isNull():
            self.tabs.setTabIcon(idx, icon)

    def close_tab(self, index: int):
        if self.tabs.count() > 1:
            widget = self.tabs.widget(index)
            self.tabs.removeTab(index)
            if widget:
                widget.page().deleteLater()
                widget.deleteLater()

    def closeEvent(self, event):
        while self.tabs.count() > 0:
            w = self.tabs.widget(0)
            self.tabs.removeTab(0)
            if w:
                w.page().deleteLater()
                w.deleteLater()
        super().closeEvent(event)

    def current_browser(self) -> QWebEngineView:
        return self.tabs.currentWidget()

    def navigate_to_url(self):
        text = self.url_bar.text().strip()
        if not text or text == "core://home":
            self.load_core_home(self.current_browser())
            return
        if text == "core://settings":
            self.load_core_settings(self.current_browser())
            return
        if text == "core://desktop":
            self.load_core_desktop(self.current_browser())
            return
        self.current_browser().setProperty("core_page", "web")
        if " " in text or ("." not in text and not text.startswith("localhost")):
            self.current_browser().setUrl(QUrl(self._search_url_for_query(text)))
            return
        self.current_browser().setUrl(QUrl(clean_url(text)))

    def _format_display_url(self, browser: QWebEngineView, url_str: str) -> str:
        if url_str in ("about:blank", ""):
            page_type = browser.property("core_page")
            if page_type == "settings":
                return "core://settings"
            if page_type == "desktop":
                return "core://desktop"
            return "core://home"
        if "duckduckgo.com" in url_str and "q=" in url_str:
            q = next(iter(parse_qs(urlparse(url_str).query).get("q", [""])), "")
            return f"core://search?q={q}"
        return url_str

    def _on_url_changed(self, qurl: QUrl, browser: QWebEngineView):
        if browser == self.current_browser():
            self.url_bar.setText(self._format_display_url(browser, qurl.toString()))

    def _on_load_finished(self, ok: bool, browser: QWebEngineView):
        idx = self.tabs.indexOf(browser)
        url_str = browser.url().toString()
        if idx == -1:
            return
        if url_str in ("about:blank", ""):
            page_type = browser.property("core_page")
            if page_type == "settings":
                self.tabs.setTabText(idx, "Settings")
            elif page_type == "desktop":
                self.tabs.setTabText(idx, "CORE Desktop")
            else:
                self.tabs.setTabText(idx, "New Tab")
        else:
            title = (browser.page().title() or "Tab").replace("at DuckDuckGo", "- CORE").replace("DuckDuckGo", "CORE")
            self.tabs.setTabText(idx, title[:22])
        if browser == self.current_browser():
            self.url_bar.setText(self._format_display_url(browser, url_str))

    def update_url_bar(self):
        browser = self.current_browser()
        if browser:
            self.url_bar.setText(self._format_display_url(browser, browser.url().toString()))

    def toggle_tools_dock(self):
        self.dock.setVisible(not self.dock.isVisible())

    def unlock_vault(self):
        pwd, ok = QInputDialog.getText(self, "CORE Vault", "Enter Master Password:", QLineEdit.EchoMode.Password)
        if ok and pwd:
            if self.vault.unlock(pwd):
                data = self.vault.load_data()
                self.bookmark_list.clear()
                self.bookmark_list.addItems(data.get("bookmarks", []))
                self.vault_notes.setPlainText(data.get("notes", ""))
                QMessageBox.information(self, "Unlocked", "CORE AES-256 Vault unlocked.")
            else:
                QMessageBox.critical(self, "Error", "Incorrect password or corrupted vault.")

    def save_current_bookmark(self):
        if not self.vault.fernet:
            self.dock.show()
            QMessageBox.warning(self, "Locked", "Unlock your CORE Vault first.")
            return
        url = self.current_browser().url().toString()
        if url in ("about:blank", ""):
            return
        self.bookmark_list.addItem(url)
        self.save_vault_state()

    def save_vault_state(self):
        if not self.vault.fernet:
            QMessageBox.warning(self, "Locked", "Unlock the vault first.")
            return
        bookmarks = [self.bookmark_list.item(i).text() for i in range(self.bookmark_list.count())]
        notes = self.vault_notes.toPlainText()
        self.vault.save_data({"bookmarks": bookmarks, "notes": notes})
        QMessageBox.information(self, "Saved", "Encrypted and saved to core_vault.enc.")

    def grab_page_source(self):
        self.current_browser().page().toHtml(lambda html_src: self.source_view.setPlainText(html_src))


if __name__ == "__main__":
    sys.argv.append("--no-sandbox")
    app = QApplication(sys.argv)
    window = CoreBrowser()
    window.show()
    sys.exit(app.exec())
