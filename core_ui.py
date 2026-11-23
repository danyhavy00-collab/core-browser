import html
import json

THEMES = {
    "Midnight Slate": {
        "bg": "#0f1217", "bar": "#171c24", "tab_bg": "#0a0c10",
        "border": "#252c38", "text": "#f1f5f9", "muted": "#8b949e",
        "accent": "#3b82f6", "input": "#0c0f14"
    },
    "Emerald Matrix": {
        "bg": "#0a110d", "bar": "#111c16", "tab_bg": "#060b08",
        "border": "#1d3528", "text": "#ecfdf5", "muted": "#7ea38e",
        "accent": "#10b981", "input": "#080e0b"
    },
    "Crimson Obsidian": {
        "bg": "#130b0e", "bar": "#1d1216", "tab_bg": "#0a0608",
        "border": "#361d26", "text": "#fff1f2", "muted": "#a3828e",
        "accent": "#f43f5e", "input": "#0e080a"
    },
    "Arctic Light": {
        "bg": "#f1f5f9", "bar": "#ffffff", "tab_bg": "#e2e8f0",
        "border": "#cbd5e1", "text": "#0f172a", "muted": "#64748b",
        "accent": "#2563eb", "input": "#f8fafc"
    }
}

g_url = "https://" + "www.google." + "com/search?q="
br_url = "https://" + "search.brave." + "com/search?q="
bi_url = "https://" + "www.bing." + "com/search?q="
dd_url = "https://" + "duckduckgo." + "com/?kae=d&k1=-1&q="

BROWSER_PROFILES = {
    "Chromium": {"search_url": g_url, "ua": "", "label": "Chromium (Google Search)"},
    "Chrome": {"search_url": g_url, "ua": "", "label": "Google Chrome"},
    "Brave": {"search_url": br_url, "ua": "", "label": "Brave (Brave Search)"},
    "Firefox": {"search_url": g_url, "ua": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:132.0) Gecko/20100101 Firefox/132.0", "label": "Mozilla Firefox (Google)"},
    "Edge": {"search_url": bi_url, "ua": "Edg/131.0.0.0", "label": "Microsoft Edge (Bing)"},
    "Bing": {"search_url": bi_url, "ua": "Edg/131.0.0.0", "label": "Microsoft Bing"},
    "Opera": {"search_url": g_url, "ua": "OPR/115.0.0.0", "label": "Opera (Google Search)"},
    "DuckDuckGo": {"search_url": dd_url, "ua": "", "label": "DuckDuckGo (Ad-Filtered)"},
    "Internet Explorer": {"search_url": bi_url, "ua": "Mozilla/5.0 (Windows NT 10.0; WOW64; Trident/7.0; rv:11.0) like Gecko", "label": "Internet Explorer 11 (Bing)"}
}


def build_qt_stylesheet(theme_name: str, extra_themes: dict = None) -> str:
    all_themes = {**THEMES, **(extra_themes or {})}
    t = all_themes.get(theme_name, THEMES["Midnight Slate"])
    return f"""
    QMainWindow {{ background-color: {t['bg']}; }}
    QTabWidget::pane {{ border: none; background-color: {t['bg']}; }}
    QTabBar {{ background-color: {t['tab_bg']}; qproperty-drawBase: 0; }}
    QTabBar::tab {{
        background-color: {t['tab_bg']}; color: {t['muted']};
        padding: 8px 14px; margin-top: 5px; margin-left: 3px;
        border-top-left-radius: 8px; border-top-right-radius: 8px;
        min-width: 120px; max-width: 200px; font-size: 12px; font-weight: 500;
    }}
    QTabBar::tab:selected {{ background-color: {t['bar']}; color: {t['text']}; border-top: 2px solid {t['accent']}; }}
    QTabBar::tab:hover:!selected {{ color: {t['text']}; background-color: {t['bg']}; }}
    QPushButton#NewTabBtn {{
        background: transparent; color: {t['muted']}; border: none; border-radius: 6px;
        font-size: 16px; font-weight: 600; padding: 2px 9px; margin: 5px 4px 2px 4px;
    }}
    QPushButton#NewTabBtn:hover {{ background-color: {t['bar']}; color: {t['text']}; }}
    QWidget#NavBar {{ background-color: {t['bar']}; border-bottom: 1px solid {t['border']}; }}
    QPushButton.NavBtn {{
        background: transparent; color: {t['muted']}; border: none; border-radius: 6px;
        padding: 5px 8px; font-size: 14px;
    }}
    QPushButton.NavBtn:hover {{ background-color: {t['border']}; color: {t['text']}; }}
    QLineEdit#UrlBar {{
        background-color: {t['input']}; color: {t['text']}; border: 1px solid {t['border']};
        border-radius: 15px; padding: 5px 14px; font-size: 13px;
    }}
    QLineEdit#UrlBar:focus {{ border: 1px solid {t['accent']}; }}
    QLabel#ShieldBadge {{
        color: {t['accent']}; background-color: {t['input']}; border: 1px solid {t['border']};
        border-radius: 11px; padding: 3px 10px; font-size: 11px; font-weight: 600;
    }}
    QDockWidget {{ color: {t['text']}; font-weight: 600; }}
    QDockWidget::title {{ background-color: {t['bar']}; padding: 9px; border-bottom: 1px solid {t['border']}; }}
    QWidget#DockBody {{ background-color: {t['bg']}; color: {t['text']}; }}
    QWidget#DockBody QLabel {{ color: {t['text']}; font-weight: 600; margin-top: 4px; }}
    QPushButton.DockBtn {{
        background-color: {t['bar']}; color: {t['text']}; border: 1px solid {t['border']};
        border-radius: 6px; padding: 6px 12px; font-size: 12px;
    }}
    QPushButton.DockBtn:hover {{ border-color: {t['accent']}; }}
    QTextEdit, QListWidget {{
        background-color: {t['input']}; color: {t['text']}; border: 1px solid {t['border']};
        border-radius: 6px; padding: 6px;
    }}
    """


def render_home_html(settings: dict, blocked_count: int, ota_info: dict = None) -> str:
    all_themes = {**THEMES, **(ota_info or {}).get("extra_themes", {})}
    t = all_themes.get(settings.get("theme", "Midnight Slate"), THEMES["Midnight Slate"])
    selected_engine = settings.get("engine", "Chromium")
    widgets = settings.get("widgets", {"clock": True, "shield": True, "notes": True, "shortcuts": True})
    active_base = BROWSER_PROFILES.get(selected_engine, BROWSER_PROFILES["Chromium"])["search_url"]
    banner = (ota_info or {}).get("announcement", "")

    banner_html = f'<div class="banner">{html.escape(banner)}</div>' if banner else ""
    pills_html = "".join(
        f'<a class="pill {"active" if key == selected_engine else ""}" href="core-engine:{html.escape(key)}">{html.escape(key)}</a>'
        for key in BROWSER_PROFILES
    )

    clock_html = '<div class="widget"><div class="w-title">LOCAL TIME</div><div id="clock" class="clock">--:--</div><div id="date" class="w-sub">Loading...</div></div>' if widgets.get("clock", True) else ""
    shield_html = f'<div class="widget"><div class="w-title">CORE SHIELD</div><div class="stat">{blocked_count}</div><div class="w-sub">Ads &amp; Trackers Blocked</div></div>' if widgets.get("shield", True) else ""
    notes_html = '<div class="widget"><div class="w-title">QUICK SCRATCHPAD</div><textarea id="pad" placeholder="Type quick session notes..."></textarea></div>' if widgets.get("notes", True) else ""
    shortcuts_html = '<div class="shortcuts"><a href="https://wikipedia.org">Wikipedia</a><a href="https://github.com">GitHub</a><a href="https://archive.org">Internet Archive</a><a href="core://desktop">🖥 CORE Desktop</a><a href="core://settings">⚙ Settings</a></div>' if widgets.get("shortcuts", True) else ""

    return f"""<!DOCTYPE html>
<html><head><meta charset="utf-8"><title>New Tab</title><style>
*{{box-sizing:border-box}}
body{{background:{t['bg']};color:{t['text']};font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;margin:0;display:flex;flex-direction:column;align-items:center;justify-content:center;min-height:92vh;padding:24px}}
.wrap{{width:100%;max-width:740px;text-align:center}}
.banner{{background:{t['bar']};border:1px solid {t['accent']};color:{t['text']};padding:8px 16px;border-radius:10px;font-size:12px;margin-bottom:18px}}
.logo{{font-size:42px;font-weight:800;letter-spacing:9px;margin-bottom:14px}}
.pills{{display:flex;flex-wrap:wrap;gap:6px;justify-content:center;margin-bottom:16px}}
.pill{{text-decoration:none;font-size:11px;font-weight:600;padding:5px 12px;border-radius:14px;background:{t['bar']};color:{t['muted']};border:1px solid {t['border']};transition:0.15s}}
.pill:hover{{color:{t['text']};border-color:{t['accent']}}}
.pill.active{{background:{t['accent']};color:#fff;border-color:{t['accent']}}}
.search-bar{{display:flex;align-items:center;background:{t['bar']};border:1px solid {t['border']};border-radius:26px;padding:5px 8px 5px 18px;box-shadow:0 8px 24px rgba(0,0,0,0.2)}}
.search-bar:focus-within{{border-color:{t['accent']}}}
input[type="text"]{{flex:1;padding:10px 6px;border:none;background:transparent;color:{t['text']};font-size:15px;outline:none}}
button{{padding:9px 22px;border-radius:18px;border:none;background:{t['accent']};color:#fff;font-weight:600;font-size:13px;cursor:pointer}}
.shortcuts{{margin-top:18px;display:flex;gap:10px;justify-content:center;flex-wrap:wrap}}
.shortcuts a{{color:{t['muted']};text-decoration:none;font-size:12px;padding:6px 14px;background:{t['bar']};border:1px solid {t['border']};border-radius:16px}}
.shortcuts a:hover{{color:{t['text']};border-color:{t['accent']}}}
.grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:14px;margin-top:26px;text-align:left}}
.widget{{background:{t['bar']};border:1px solid {t['border']};border-radius:14px;padding:16px}}
.w-title{{font-size:10px;font-weight:700;letter-spacing:1px;color:{t['muted']};margin-bottom:8px}}
.clock,.stat{{font-size:26px;font-weight:700}}
.w-sub{{font-size:12px;color:{t['muted']};margin-top:4px}}
textarea{{width:100%;height:62px;background:{t['input']};color:{t['text']};border:1px solid {t['border']};border-radius:8px;padding:8px;font-family:inherit;font-size:12px;resize:none;outline:none}}
</style></head><body><div class="wrap">
{banner_html}<div class="logo">CORE</div><div class="pills">{pills_html}</div>
<form class="search-bar" onsubmit="doSearch(event)">
<input id="qInput" type="text" placeholder="Search with {html.escape(selected_engine)} or enter URL..." autofocus>
<button type="submit">Search</button></form>
{shortcuts_html}<div class="grid">{clock_html}{shield_html}{notes_html}</div></div>
<script>
const SEARCH_BASE = {json.dumps(active_base)};
function doSearch(e){{e.preventDefault();const val=document.getElementById('qInput').value.trim();if(!val)return;
if(val.includes('.')&&!val.includes(' ')){{window.location.href=val.startsWith('http')?val:'https://'+val;}}
else{{window.location.href=SEARCH_BASE+encodeURIComponent(val);}}}}
function updateClock(){{const c=document.getElementById('clock'),d=document.getElementById('date');if(!c)return;
const now=new Date();c.textContent=now.toLocaleTimeString([],{{hour:'2-digit',minute:'2-digit'}});
d.textContent=now.toLocaleDateString([],{{weekday:'short',month:'short',day:'numeric'}});}}
updateClock();setInterval(updateClock,1000);
</script></body></html>"""


def render_settings_html(settings: dict, blocked_count: int, ota_info: dict = None) -> str:
    all_themes = {**THEMES, **(ota_info or {}).get("extra_themes", {})}
    t = all_themes.get(settings.get("theme", "Midnight Slate"), THEMES["Midnight Slate"])
    cur_theme = settings.get("theme", "Midnight Slate")
    cur_engine = settings.get("engine", "Chromium")
    blocker_on = settings.get("blocker_enabled", True)
    widgets = settings.get("widgets", {"clock": True, "shield": True, "notes": True, "shortcuts": True})
    ota_ver = (ota_info or {}).get("ota_version", "2.0.0 (Base)")

    theme_opts = "".join(f'<option value="{html.escape(k)}" {"selected" if k == cur_theme else ""}>{html.escape(k)}</option>' for k in all_themes)
    engine_opts = "".join(f'<option value="{html.escape(k)}" {"selected" if k == cur_engine else ""}>{html.escape(v["label"])}</option>' for k, v in BROWSER_PROFILES.items())

    return f"""<!DOCTYPE html>
<html><head><meta charset="utf-8"><title>CORE Settings</title><style>
body{{background:{t['bg']};color:{t['text']};font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;margin:0;padding:34px 20px;display:flex;justify-content:center}}
.container{{width:100%;max-width:640px}}
h1{{font-size:24px;margin-bottom:20px;letter-spacing:1px}}
.card{{background:{t['bar']};border:1px solid {t['border']};border-radius:12px;padding:18px 20px;margin-bottom:16px}}
.card h2{{font-size:14px;margin:0 0 12px 0;color:{t['accent']};text-transform:uppercase;letter-spacing:0.6px}}
.row{{display:flex;justify-content:space-between;align-items:center;margin-bottom:10px}}
select{{background:{t['input']};color:{t['text']};border:1px solid {t['border']};border-radius:8px;padding:7px 12px;font-size:13px}}
label{{font-size:13px;display:flex;align-items:center;gap:8px;cursor:pointer;margin-bottom:8px}}
.btn-row{{display:flex;gap:12px;margin-top:8px}}
button{{background:{t['accent']};color:#fff;border:none;border-radius:8px;padding:10px 20px;font-weight:600;font-size:13px;cursor:pointer}}
button.sec{{background:{t['bar']};color:{t['text']};border:1px solid {t['border']}}}
</style></head><body><div class="container">
<h1>CORE Settings</h1>
<div class="card"><h2>Appearance &amp; Theme</h2>
<div class="row"><span>Interface Theme</span><select id="themeSel">{theme_opts}</select></div></div>
<div class="card"><h2>Default Browser &amp; Search Engine</h2>
<div class="row"><span>Active Browser Profile</span><select id="engSel">{engine_opts}</select></div></div>
<div class="card"><h2>Built-In Ad &amp; Tracker Blocker ({blocked_count} Blocked)</h2>
<label><input type="checkbox" id="blkChk" {"checked" if blocker_on else ""}> Enable Network-Level Ad &amp; Tracker Blocking</label></div>
<div class="card"><h2>Home Page Widgets</h2>
<label><input type="checkbox" id="wClock" {"checked" if widgets.get("clock", True) else ""}> Live Clock &amp; Date Widget</label>
<label><input type="checkbox" id="wShield" {"checked" if widgets.get("shield", True) else ""}> Ad-Blocker Shield Stats Widget</label>
<label><input type="checkbox" id="wNotes" {"checked" if widgets.get("notes", True) else ""}> Quick Session Scratchpad Widget</label>
<label><input type="checkbox" id="wShort" {"checked" if widgets.get("shortcuts", True) else ""}> Quick Links Bar</label></div>
<div class="card"><h2>Live Over-The-Air (OTA) Updates</h2>
<div class="row"><span>Current Live Patch Version: <b>{html.escape(str(ota_ver))}</b></span>
<button type="button" class="sec" onclick="window.location.href='core-ota:sync'">Check &amp; Sync Live Updates</button></div></div>
<div class="btn-row"><button type="button" onclick="saveAll()">Save &amp; Apply Settings</button></div>
</div>
<script>
function saveAll(){{
  const payload = {{
    theme: document.getElementById('themeSel').value,
    engine: document.getElementById('engSel').value,
    blocker_enabled: document.getElementById('blkChk').checked,
    widgets: {{
      clock: document.getElementById('wClock').checked,
      shield: document.getElementById('wShield').checked,
      notes: document.getElementById('wNotes').checked,
      shortcuts: document.getElementById('wShort').checked
    }}
  }};
  window.location.href = 'core-save:' + encodeURIComponent(JSON.stringify(payload));
}}
</script></body></html>"""
