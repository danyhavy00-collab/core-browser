import html
import json
from core_ui import THEMES
from core_store import list_sandbox_apps


def render_desktop_html(settings: dict, blocked_count: int) -> str:
    t = THEMES.get(settings.get("theme", "Midnight Slate"), THEMES["Midnight Slate"])
    engine = html.escape(settings.get("engine", "Chromium"))
    sandbox_json = json.dumps(list_sandbox_apps())

    return f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<title>Desktop</title>
<style>
  * {{ box-sizing: border-box; user-select: none; }}
  body {{
    margin: 0; overflow: hidden; height: 100vh; width: 100vw;
    font-family: -apple-system, BlinkMacSystemFont, 'Inter', 'Segoe UI', sans-serif;
    background: {t['bg']}; color: {t['text']};
  }}
  #desktop {{
    position: relative; width: 100%; height: calc(100vh - 46px); padding: 22px;
    display: flex; flex-direction: column; flex-wrap: wrap; align-content: flex-start; gap: 14px;
  }}
  .icon {{
    width: 82px; padding: 10px 4px; border-radius: 10px; text-align: center;
    cursor: pointer; transition: background 0.12s;
  }}
  .icon:hover {{ background: rgba(255,255,255,0.06); }}
  .icon-box {{
    width: 46px; height: 46px; margin: 0 auto 7px; border-radius: 12px;
    background: {t['bar']}; border: 1px solid {t['border']};
    display: flex; align-items: center; justify-content: center; color: {t['text']};
  }}
  .icon span {{ font-size: 11px; font-weight: 500; color: {t['text']}; letter-spacing: 0.1px; }}
  .win {{
    position: absolute; min-width: 420px; min-height: 280px; width: 680px; height: 460px;
    background: {t['bar']}; border: 1px solid {t['border']}; border-radius: 12px;
    box-shadow: 0 24px 60px rgba(0,0,0,0.55); display: flex; flex-direction: column; overflow: hidden;
  }}
  .win-bar {{
    height: 38px; background: {t['tab_bg']}; border-bottom: 1px solid {t['border']};
    display: flex; align-items: center; padding: 0 14px; cursor: move; gap: 10px;
  }}
  .win-dots {{ display: flex; gap: 6px; }}
  .dot {{ width: 11px; height: 11px; border-radius: 50%; border: none; cursor: pointer; padding: 0; }}
  .dot.close {{ background: #ef4444; }}
  .dot.min {{ background: #f59e0b; }}
  .dot.max {{ background: #10b981; }}
  .win-title {{ flex: 1; font-size: 12px; font-weight: 600; color: {t['muted']}; text-align: center; margin-right: 28px; }}
  .win-body {{ flex: 1; overflow: auto; user-select: text; background: {t['bg']}; }}
  #taskbar {{
    height: 46px; width: 100%; background: {t['tab_bg']}; border-top: 1px solid {t['border']};
    display: flex; align-items: center; padding: 0 14px; gap: 8px;
  }}
  #start-btn {{
    background: {t['bar']}; color: {t['text']}; border: 1px solid {t['border']}; border-radius: 8px;
    padding: 6px 13px; font-weight: 700; font-size: 12px; letter-spacing: 1px; cursor: pointer;
  }}
  #start-btn:hover {{ border-color: {t['accent']}; }}
  #task-apps {{ flex: 1; display: flex; gap: 6px; overflow-x: auto; }}
  .task-pill {{
    background: {t['bar']}; color: {t['muted']}; border: 1px solid {t['border']};
    border-radius: 7px; padding: 5px 12px; font-size: 12px; font-weight: 500; cursor: pointer;
  }}
  .task-pill.active {{ color: {t['text']}; border-color: {t['accent']}; }}
  #tray {{ font-size: 11px; color: {t['muted']}; font-weight: 500; }}
  #start-menu {{
    position: absolute; bottom: 54px; left: 14px; width: 220px;
    background: {t['bar']}; border: 1px solid {t['border']}; border-radius: 12px;
    padding: 6px; box-shadow: 0 18px 40px rgba(0,0,0,0.6); display: none; z-index: 9999;
  }}
  .menu-item {{ padding: 8px 12px; border-radius: 8px; font-size: 12px; font-weight: 500; cursor: pointer; }}
  .menu-item:hover {{ background: {t['accent']}; color: #fff; }}
  /* Native App Store Layout */
  .store-shell {{ display: flex; height: 100%; }}
  .store-nav {{ width: 165px; background: {t['bar']}; border-right: 1px solid {t['border']}; padding: 14px 10px; }}
  .store-nav-item {{ padding: 8px 10px; border-radius: 7px; font-size: 12px; font-weight: 500; color: {t['muted']}; cursor: pointer; margin-bottom: 3px; }}
  .store-nav-item:hover, .store-nav-item.active {{ background: {t['input']}; color: {t['text']}; }}
  .store-main {{ flex: 1; padding: 18px 22px; overflow-y: auto; }}
  .store-search {{
    width: 100%; padding: 9px 14px; border-radius: 8px; border: 1px solid {t['border']};
    background: {t['input']}; color: {t['text']}; font-size: 13px; outline: none; margin-bottom: 16px;
  }}
  .store-search:focus {{ border-color: {t['accent']}; }}
  .app-grid {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(220px, 1fr)); gap: 12px; }}
  .app-card {{
    background: {t['bar']}; border: 1px solid {t['border']}; border-radius: 10px;
    padding: 14px; display: flex; flex-direction: column; justify-content: space-between; gap: 10px;
  }}
  .app-head {{ display: flex; align-items: center; gap: 10px; }}
  .app-ico {{ width: 36px; height: 36px; border-radius: 8px; background: {t['input']}; object-fit: cover; }}
  .get-btn {{
    background: {t['accent']}; color: #fff; border: none; border-radius: 14px;
    padding: 5px 14px; font-size: 11px; font-weight: 600; cursor: pointer;
  }}
  .get-btn.sec {{ background: {t['input']}; color: {t['text']}; border: 1px solid {t['border']}; }}
  textarea.note-area {{
    width: 100%; height: 100%; background: {t['bg']}; color: {t['text']};
    border: none; padding: 16px; font-family: 'JetBrains Mono', monospace; font-size: 13px; resize: none; outline: none;
  }}
</style>
</head>
<body>
  <div id="desktop" onclick="hideStart()"></div>

  <div id="start-menu">
    <div class="menu-item" onclick="openApp('store');hideStart()">App Store</div>
    <div class="menu-item" onclick="openApp('terminal');hideStart()">Terminal</div>
    <div class="menu-item" onclick="openApp('notepad');hideStart()">Notes</div>
    <div class="menu-item" onclick="openApp('browser');hideStart()">Web Window</div>
    <hr style="border:0;border-top:1px solid {t['border']};margin:5px 0;">
    <div class="menu-item" onclick="window.location.href='core://settings'">Settings</div>
    <div class="menu-item" onclick="window.location.href='core://home'">Exit Desktop</div>
  </div>

  <div id="taskbar">
    <button id="start-btn" onclick="toggleStart(event)">CORE</button>
    <div id="task-apps"></div>
    <div id="tray">{engine} &bull; <span id="tb-clock">--:--</span></div>
  </div>

<script>
  let zTop = 10, winCount = 0;
  let sandboxApps = {sandbox_json};
  let storeResults = [];
  const vfs = {{ "welcome.txt": "CORE Workspace\\nAll sandboxed apps run in user-space without admin privileges." }};

  const SVG = {{
    store: '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><path d="M6 2L3 6v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2V6l-3-4z"/><line x1="3" y1="6" x2="21" y2="6"/><path d="M16 10a4 4 0 0 1-8 0"/></svg>',
    term: '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><polyline points="4 17 10 11 4 5"/><line x1="12" y1="19" x2="20" y2="19"/></svg>',
    notes: '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/></svg>',
    web: '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><circle cx="12" cy="12" r="10"/><line x1="2" y1="12" x2="22" y2="12"/><path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z"/></svg>',
    app: '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><rect x="3" y="3" width="18" height="18" rx="4"/></svg>',
    home: '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/></svg>'
  }};

  function renderDesktopIcons() {{
    const desk = document.getElementById('desktop');
    let h = `
      <div class="icon" onclick="openApp('store')"><div class="icon-box">${{SVG.store}}</div><span>App Store</span></div>
      <div class="icon" onclick="openApp('terminal')"><div class="icon-box">${{SVG.term}}</div><span>Terminal</span></div>
      <div class="icon" onclick="openApp('notepad')"><div class="icon-box">${{SVG.notes}}</div><span>Notes</span></div>
      <div class="icon" onclick="openApp('browser')"><div class="icon-box">${{SVG.web}}</div><span>Browser</span></div>
    `;
    sandboxApps.forEach(a => {{
      h += `<div class="icon" onclick="window.location.href='core-sb-run:'+encodeURIComponent('${{a.id}}')"><div class="icon-box">${{SVG.app}}</div><span>${{a.name}}</span></div>`;
    }});
    h += `<div class="icon" onclick="window.location.href='core://home'"><div class="icon-box">${{SVG.home}}</div><span>Home</span></div>`;
    desk.innerHTML = h;
  }}

  function renderStoreResults(gridId, items) {{
    storeResults = items;
    const grid = document.getElementById(gridId);
    if (!grid) return;
    if (!items || items.length === 0) {{
      grid.innerHTML = '<div style="color:{t["muted"]};font-size:13px;">No results found. Try another search term.</div>';
      return;
    }}
    grid.innerHTML = items.map((it, idx) => `
      <div class="app-card">
        <div>
          <div class="app-head">
            <img class="app-ico" src="${{it.icon || ''}}" onerror="this.style.display='none'">
            <div>
              <div style="font-size:13px;font-weight:600;">${{it.name}}</div>
              <div style="font-size:11px;color:{t['muted']};">${{it.developer}} &bull; ${{it.source}}</div>
            </div>
          </div>
          <div style="font-size:11px;color:{t['muted']};margin-top:8px;line-height:1.4;">${{it.summary}}</div>
        </div>
        <div>
          <div id="pwrap-${{it.id}}" style="display:none;width:100%;height:5px;background:{t['input']};border-radius:4px;overflow:hidden;margin-bottom:6px;">
            <div id="pbar-${{it.id}}" style="width:0%;height:100%;background:{t['accent']};transition:width 0.15s;"></div>
          </div>
          <div style="display:flex;gap:6px;justify-content:flex-end;">
            <button id="pbtn-${{it.id}}" class="get-btn" onclick="startStoreInstall('${{it.id}}','${{it.kind}}','${{it.target}}','${{it.name}}')">Get</button>
          </div>        </div>
      </div>
    `).join('');
  }}

  function startStoreInstall(cardId, kind, target, name) {{
    const wrap = document.getElementById('pwrap-' + cardId);
    const btn = document.getElementById('pbtn-' + cardId);
    if (wrap) wrap.style.display = 'block';
    if (btn) {{ btn.textContent = 'Starting...'; btn.disabled = true; }}
    window.location.href = 'core-store-install:' + encodeURIComponent(cardId + '|' + kind + '|' + target + '|' + name);
  }}
  function updateInstallProgress(cardId, pct, label) {{
    const bar = document.getElementById('pbar-' + cardId);
    const btn = document.getElementById('pbtn-' + cardId);
    if (bar) bar.style.width = pct + '%';
    if (btn) btn.textContent = label;
  }}
  function triggerStoreSearch(gridId, q) {{
    const grid = document.getElementById(gridId);
    if (grid) grid.innerHTML = '<div style="color:{t["muted"]};font-size:13px;">Searching live repositories...</div>';
    window.location.href = 'core-store-search:' + encodeURIComponent(gridId + '|' + q);
  }}

  function showInstalledTab(gridId) {{
    const grid = document.getElementById(gridId);
    if (!grid) return;
    if (sandboxApps.length === 0) {{
      grid.innerHTML = `<div style="color:{t['muted']};font-size:13px;">No apps installed in sandbox yet. Search for an app or click "+ Import File" in the sidebar.</div>`;
      return;
    }}
    grid.innerHTML = sandboxApps.map(a => `
      <div class="app-card">
        <div>
          <div style="font-size:13px;font-weight:600;">${{a.name}}</div>
          <div style="font-size:11px;color:{t['muted']};margin-top:4px;">Sandboxed User-Space App</div>
        </div>
        <div style="display:flex;gap:6px;justify-content:flex-end;">
          <button class="get-btn" onclick="window.location.href='core-sb-run:'+encodeURIComponent('${{a.id}}')">Open</button>
          <button class="get-btn sec" onclick="window.location.href='core-sb-wipe:'+encodeURIComponent('${{a.id}}')">Remove</button>
        </div>
      </div>
    `).join('');
  }}

  function toggleStart(e) {{ e.stopPropagation(); const m = document.getElementById('start-menu'); m.style.display = m.style.display === 'block' ? 'none' : 'block'; }}
  function hideStart() {{ document.getElementById('start-menu').style.display = 'none'; }}

  function focusWin(id) {{
    const w = document.getElementById(id); if (!w) return;
    w.style.display = 'flex'; w.style.zIndex = ++zTop;
    document.querySelectorAll('.task-pill').forEach(p => p.classList.remove('active'));
    const pill = document.getElementById('pill-' + id); if (pill) pill.classList.add('active');
  }}
  function minWin(id) {{ const w = document.getElementById(id); if (w) w.style.display = 'none'; }}
  function maxWin(id) {{ const w = document.getElementById(id); if (!w) return; if (w.dataset.max === '1') {{ w.style.left='110px'; w.style.top='32px'; w.style.width='680px'; w.style.height='460px'; w.dataset.max='0'; }} else {{ w.style.left='0px'; w.style.top='0px'; w.style.width='100%'; w.style.height='100%'; w.dataset.max='1'; }} }}
  function closeWin(id) {{ const w = document.getElementById(id); if (w) w.remove(); const p = document.getElementById('pill-' + id); if (p) p.remove(); }}

  function openApp(type) {{
    const id = 'win-' + (++winCount);
    const gridId = 'grid-' + id;
    let title = 'App', body = '';

    if (type === 'store') {{
      title = 'App Store';
      body = `<div class="store-shell">
        <div class="store-nav">
          <div class="store-nav-item active" onclick="triggerStoreSearch('${{gridId}}','game')">Discover Games</div>
          <div class="store-nav-item" onclick="triggerStoreSearch('${{gridId}}','app')">Productivity</div>
          <div class="store-nav-item" onclick="triggerStoreSearch('${{gridId}}','emulator')">Emulators</div>
          <div class="store-nav-item" onclick="showInstalledTab('${{gridId}}')">Installed (${{sandboxApps.length}})</div>
          <hr style="border:0;border-top:1px solid {t['border']};margin:10px 0;">
          <div class="store-nav-item" onclick="window.location.href='core-cloud:'+encodeURIComponent('Roblox Cloud|https://now.gg')">Roblox Cloud</div>
          <div class="store-nav-item" onclick="window.location.href='core-cloud:'+encodeURIComponent('Xbox Cloud|https://xbox.com')">Xbox Cloud</div>
          <div class="store-nav-item" onclick="window.location.href='core-cloud:'+encodeURIComponent('itch.io Web|https://itch.io')">itch.io Web</div>
          <div class="store-nav-item" onclick="window.location.href='core-sb-import:pick'">+ Import File</div>
        </div>
        <div class="store-main">
          <input class="store-search" placeholder="Search millions of apps and games..." onkeydown="if(event.key==='Enter')triggerStoreSearch('${{gridId}}',this.value)">
          <div id="${{gridId}}" class="app-grid"></div>
        </div>
      </div>`;
    }} else if (type === 'terminal') {{
      title = 'Terminal';
      body = `<div style="padding:14px;font-family:monospace;font-size:12px;">
        <div id="out-${{id}}" style="color:#94a3b8;white-space:pre-wrap;margin-bottom:8px;">CORE Shell &bull; Type 'help' for commands.</div>
        <div style="display:flex;gap:6px;"><span style="color:{t['accent']}">$</span>
        <input style="flex:1;background:transparent;border:none;color:{t['text']};font-family:monospace;outline:none;" onkeydown="runCmd(event,'${{id}}',this)" autofocus></div>
      </div>`;
    }} else if (type === 'notepad') {{
      title = 'Notes';
      body = `<textarea class="note-area" placeholder="Start typing..."></textarea>`;
    }} else if (type === 'browser') {{
      window.location.href = 'core-desk-browser:https://google.com';
      return;
    }}

    const win = document.createElement('div');
    win.className = 'win'; win.id = id;
    win.style.left = (110 + (winCount % 5) * 24) + 'px';
    win.style.top = (32 + (winCount % 5) * 20) + 'px';
    win.style.zIndex = ++zTop;
    win.onmousedown = () => focusWin(id);
    win.innerHTML = `<div class="win-bar" onmousedown="startDrag(event,'${{id}}')">
      <div class="win-dots"><button class="dot close" onclick="closeWin('${{id}}')"></button><button class="dot min" onclick="minWin('${{id}}')"></button><button class="dot max" onclick="maxWin('${{id}}')"></button></div>
      <div class="win-title">${{title}}</div>
    </div><div class="win-body">${{body}}</div>`;
    document.getElementById('desktop').appendChild(win);

    const pill = document.createElement('button');
    pill.className = 'task-pill active'; pill.id = 'pill-' + id; pill.textContent = title;
    pill.onclick = () => focusWin(id);
    document.getElementById('task-apps').appendChild(pill);
    focusWin(id);

    if (type === 'store') triggerStoreSearch(gridId, 'game');
  }}

  function runCmd(e, id, inp) {{
    if (e.key !== 'Enter') return;
    const raw = inp.value.trim(); inp.value = '';
    const out = document.getElementById('out-' + id);
    out.textContent += `\\n$ ${{raw}}\\n`;
    const parts = raw.split(' '), cmd = parts[0].toLowerCase();
    if (cmd === 'help') out.textContent += 'help, ls, cat <file>, touch <file>, apps, clear';
    else if (cmd === 'ls') out.textContent += Object.keys(vfs).join('  ');
    else if (cmd === 'apps') out.textContent += (sandboxApps.map(a=>a.name).join(', ') || 'None');
    else if (cmd === 'cat') out.textContent += (vfs[parts[1]] || 'Not found');
    else if (cmd === 'touch' && parts[1]) {{ vfs[parts[1]] = ''; out.textContent += `Created ${{parts[1]}}`; }}
    else if (cmd === 'clear') out.textContent = '';
    else if (raw) out.textContent += `Command not found: ${{cmd}}`;
  }}

  function startDrag(e, id) {{
    if (e.target.tagName === 'BUTTON') return;
    const w = document.getElementById(id), ox = e.clientX - w.offsetLeft, oy = e.clientY - w.offsetTop;
    const move = ev => {{ w.style.left = (ev.clientX - ox) + 'px'; w.style.top = Math.max(0, ev.clientY - oy) + 'px'; }};
    const up = () => {{ document.removeEventListener('mousemove', move); document.removeEventListener('mouseup', up); }};
    document.addEventListener('mousemove', move); document.addEventListener('mouseup', up);
  }}

  renderDesktopIcons();
  setInterval(() => {{ document.getElementById('tb-clock').textContent = new Date().toLocaleTimeString([], {{hour:'2-digit',minute:'2-digit'}}); }}, 1000);
</script>
</body>
</html>"""
