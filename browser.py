import sys
import os
import json
import base64
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse, quote_plus

from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

from PyQt6.QtCore import QUrl, Qt, QSize
from PyQt6.QtGui import QAction, QColor, QIcon, QPixmap, QPainter, QFont
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QTabWidget, QToolBar, QLineEdit,
    QPushButton, QDockWidget, QWidget, QVBoxLayout, QHBoxLayout,
    QTextEdit, QLabel, QInputDialog, QMessageBox, QListWidget
)
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtWebEngineCore import QWebEngineProfile, QWebEnginePage, QWebEngineScript



def get_resource_path(filename: str) -> str:
    if hasattr(sys, "_MEIPASS"):
        return os.path.join(sys._MEIPASS, filename)
    return os.path.join(get_app_dir(), filename)

def get_app_dir() -> str:
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))


def build_core_search_url(query: str) -> str:
    return (
        f"https://duckduckgo.com{quote_plus(query)}"
        "&kae=d&k1=-1&kak=-1&kax=-1&kaq=-1&kap=-1&kao=-1&kau=-1"
    )


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


APP_STYLESHEET = """
QMainWindow {
    background-color: #14171c;
}
QTabWidget::pane {
    border: none;
    background-color: #14171c;
}
QTabBar {
    background-color: #0d0f12;
    qproperty-drawBase: 0;
}
QTabBar::tab {
    background-color: #0d0f12;
    color: #8b949e;
    padding: 8px 14px;
    margin-top: 5px;
    margin-left: 3px;
    border-top-left-radius: 8px;
    border-top-right-radius: 8px;
    min-width: 130px;
    max-width: 210px;
    font-size: 12px;
}
QTabBar::tab:selected {
    background-color: #1c2026;
    color: #f0f6fc;
}
QTabBar::tab:hover:!selected {
    background-color: #15181e;
    color: #c9d1d9;
}
QPushButton#NewTabBtn {
    background: transparent;
    color: #8b949e;
    border: none;
    border-radius: 6px;
    font-size: 16px;
    font-weight: 600;
    padding: 2px 9px;
    margin: 5px 4px 2px 4px;
}
QPushButton#NewTabBtn:hover {
    background-color: #1c2026;
    color: #f0f6fc;
}
QWidget#NavBar {
    background-color: #1c2026;
    border-bottom: 1px solid #282d35;
}
QPushButton.NavBtn {
    background: transparent;
    color: #b1bac4;
    border: none;
    border-radius: 6px;
    padding: 5px 8px;
    font-size: 14px;
}
QPushButton.NavBtn:hover {
    background-color: #282d35;
    color: #ffffff;
}
QLineEdit#UrlBar {
    background-color: #111317;
    color: #e6edf3;
    border: 1px solid #2b313a;
    border-radius: 15px;
    padding: 5px 14px;
    font-size: 13px;
}
QLineEdit#UrlBar:focus {
    border: 1px solid #4c8bf5;
    background-color: #0d0f12;
}
QLabel#ShieldBadge {
    color: #8b949e;
    background-color: #14171c;
    border: 1px solid #2b313a;
    border-radius: 11px;
    padding: 3px 10px;
    font-size: 11px;
    font-weight: 600;
}
QDockWidget {
    color: #e6edf3;
    font-weight: 600;
}
QDockWidget::title {
    background-color: #1c2026;
    padding: 9px;
    border-bottom: 1px solid #282d35;
}
QWidget#DockBody {
    background-color: #14171c;
    color: #e6edf3;
}
QWidget#DockBody QLabel {
    color: #e6edf3;
    font-weight: 600;
    margin-top: 4px;
}
QPushButton.DockBtn {
    background-color: #21262d;
    color: #e6edf3;
    border: 1px solid #30363d;
    border-radius: 6px;
    padding: 6px 12px;
    font-size: 12px;
}
QPushButton.DockBtn:hover {
    background-color: #30363d;
}
QTextEdit, QListWidget {
    background-color: #0d0f12;
    color: #e6edf3;
    border: 1px solid #282d35;
    border-radius: 6px;
    padding: 6px;
}
"""

CORE_HOME_HTML = """<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<title>New Tab</title>
<style>
    * { box-sizing: border-box; }
    body {
        background-color: #14171c;
        color: #e6edf3;
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
        margin: 0; display: flex; flex-direction: column; align-items: center;
        justify-content: center; height: 86vh;
    }
    .wrap { width: 90%; max-width: 560px; text-align: center; }
    .logo {
        font-size: 38px; font-weight: 700; letter-spacing: 6px;
        color: #f0f6fc; margin-bottom: 24px;
    }
    .search-box {
        display: flex; align-items: center; background: #1c2026;
        border: 1px solid #2d333b; border-radius: 24px; padding: 4px 8px 4px 18px;
    }
    .search-box:focus-within {
        border-color: #4c8bf5; background: #181b20;
    }
    input[type="text"] {
        flex: 1; padding: 10px 8px; border: none; background: transparent;
        color: #f0f6fc; font-size: 15px; outline: none;
    }
    button {
        padding: 8px 18px; border-radius: 18px; border: none; background: #2d333b;
        color: #e6edf3; font-weight: 500; font-size: 13px; cursor: pointer;
    }
    button:hover { background: #3b424c; }
    .shortcuts { margin-top: 26px; display: flex; gap: 12px; justify-content: center; flex-wrap: wrap; }
    .shortcuts a {
        color: #8b949e; text-decoration: none; font-size: 12px;
        padding: 6px 14px; background: #1c2026; border: 1px solid #282d35; border-radius: 16px;
    }
    .shortcuts a:hover { color: #f0f6fc; border-color: #444c56; }
</style>
</head>
<body>
    <div class="wrap">
        <div class="logo">CORE</div>
        <form class="search-box" action="https://duckduckgo.com" method="get">
            <input type="hidden" name="kae" value="d">
            <input type="hidden" name="k1" value="-1">
            <input type="hidden" name="kak" value="-1">
            <input type="hidden" name="kax" value="-1">
            <input type="hidden" name="kaq" value="-1">
            <input type="hidden" name="kap" value="-1">
            <input type="hidden" name="kao" value="-1">
            <input type="hidden" name="kau" value="-1">
            <input type="text" name="q" placeholder="Search the web or type a URL" autofocus>
            <button type="submit">Search</button>
        </form>
        <div class="shortcuts">
            <a href="https://wikipedia.org">Wikipedia</a>
            <a href="https://github.com">GitHub</a>
            <a href="https://archive.org">Internet Archive</a>
            <a href="https://ycombinator.com">Hacker News</a>
        </div>
    </div>
</body>
</html>"""

CORE_SKIN_JS = """
(function() {
    const css = `
        html, body, .site-wrapper, .header-wrap, #header_wrapper {
            background-color: #14171c !important;
        }
        /* Hide only Duck.ai, Share Feedback, and footer promos */
        a[href*="duck.ai"], [data-testid="duckai-button"], [aria-label*="Duck.ai" i],
        button[aria-label*="feedback" i], [data-testid="feedback-prompt"],
        .js-badge-link, .badge-link, .header--aside, .nav-menu--theme, .footer {
            display: none !important;
        }
    `;
    const scrub = () => {
        if (!window.location.href.includes('duckduckgo.com')) return;
        const head = document.head || document.documentElement;
        if (head && !document.getElementById('core-skin-css')) {
            const s = document.createElement('style');
            s.id = 'core-skin-css';
            s.textContent = css;
            head.appendChild(s);
        }
        // Replace DuckDuckGo SVG/IMG logo inside the header link without hiding the header bar
        document.querySelectorAll('header a[href="/"], header a[href^="/?"], [data-testid="header-logo"]').forEach(link => {
            if (!link.dataset.coreSwapped) {
                link.dataset.coreSwapped = '1';
                link.removeAttribute('title');
                link.removeAttribute('aria-label');
                link.innerHTML = '<span style="color:#f0f6fc;font-weight:800;font-size:18px;letter-spacing:4px;font-family:sans-serif;padding:0 8px;">CORE</span>';
            }
        });
        // Hide Ask Duck.ai & Share Feedback using exact leaf elements only
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
        if (!document.documentElement) {
            requestAnimationFrame(start);
            return;
        }
        scrub();
        const observer = new MutationObserver(scrub);
        observer.observe(document.documentElement, { childList: true, subtree: true });
    };
    start();
})();
"""


class CoreBrowser(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("CORE")
        icon_file = get_resource_path("core_icon.png")
        if os.path.exists(icon_file):
            self.setWindowIcon(QIcon(icon_file))
        self.resize(1280, 820)
        self.setStyleSheet(APP_STYLESHEET)

        self.ram_profile = QWebEngineProfile()
        self.ram_profile.setHttpCacheType(QWebEngineProfile.HttpCacheType.MemoryHttpCache)
        self.ram_profile.setPersistentCookiesPolicy(
            QWebEngineProfile.PersistentCookiesPolicy.NoPersistentCookies
        )

        script = QWebEngineScript()
        script.setName("CoreInstantSkin")
        script.setSourceCode(CORE_SKIN_JS)
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

        shield = QLabel("RAM • AES-256")
        shield.setObjectName("ShieldBadge")
        nav_layout.addWidget(shield)

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
        self.open_core_home()

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
        browser.setHtml(CORE_HOME_HTML, QUrl("about:blank"))
        self.url_bar.setText("core://home")
        idx = self.tabs.indexOf(browser)
        if idx != -1:
            self.tabs.setTabIcon(idx, self._core_tab_icon())

    def add_new_tab(self, qurl: QUrl = None, label="New Tab") -> QWebEngineView:
        browser = QWebEngineView()
        page = QWebEnginePage(self.ram_profile, browser)
        page.setBackgroundColor(QColor("#14171c"))
        browser.setPage(page)

        idx = self.tabs.addTab(browser, label)
        self.tabs.setCurrentIndex(idx)

        browser.urlChanged.connect(lambda q, b=browser: self._on_url_changed(q, b))
        browser.loadFinished.connect(lambda ok, b=browser: self._on_load_finished(ok, b))
        browser.iconChanged.connect(lambda icon, b=browser: self._on_icon_changed(icon, b))

        if qurl:
            browser.setUrl(qurl)
        return browser

    def _core_tab_icon(self) -> QIcon:
        pix = QPixmap(24, 24)
        pix.fill(Qt.GlobalColor.transparent)
        p = QPainter(pix)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.setBrush(QColor("#2563eb"))
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
        if text.startswith("core://search?q="):
            q = text.split("core://search?q=", 1).pop()
            self.current_browser().setUrl(QUrl(build_core_search_url(q)))
            return
        if " " in text or ("." not in text and not text.startswith("localhost")):
            self.current_browser().setUrl(QUrl(build_core_search_url(text)))
            return
        cleaned = clean_url(text)
        self.current_browser().setUrl(QUrl(cleaned))

    def _format_display_url(self, url_str: str) -> str:
        if url_str in ("about:blank", ""):
            return "core://home"
        if "duckduckgo.com" in url_str and "q=" in url_str:
            q = next(iter(parse_qs(urlparse(url_str).query).get("q", [""])), "")
            return f"core://search?q={q}"
        return url_str

    def _on_url_changed(self, qurl: QUrl, browser: QWebEngineView):
        if browser == self.current_browser():
            self.url_bar.setText(self._format_display_url(qurl.toString()))

    def _on_load_finished(self, ok: bool, browser: QWebEngineView):
        idx = self.tabs.indexOf(browser)
        url_str = browser.url().toString()
        if idx == -1:
            return
        if url_str in ("about:blank", ""):
            self.tabs.setTabText(idx, "New Tab")
        else:
            title = (browser.page().title() or "Tab").replace("at DuckDuckGo", "- CORE").replace("DuckDuckGo", "CORE")
            self.tabs.setTabText(idx, title[:22])
        if browser == self.current_browser():
            self.url_bar.setText(self._format_display_url(url_str))

    def update_url_bar(self):
        browser = self.current_browser()
        if browser:
            self.url_bar.setText(self._format_display_url(browser.url().toString()))

    def toggle_tools_dock(self):
        self.dock.setVisible(not self.dock.isVisible())

    def unlock_vault(self):
        pwd, ok = QInputDialog.getText(
            self, "CORE Vault", "Enter Master Password:",
            QLineEdit.EchoMode.Password
        )
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
