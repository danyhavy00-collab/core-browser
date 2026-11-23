import html
from core_ui import THEMES


def render_desktop_html(settings: dict, blocked_count: int) -> str:
    t = THEMES.get(settings.get("theme", "Midnight Slate"), THEMES["Midnight Slate"])
    engine = html.escape(settings.get("engine", "Chromium"))

    return f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<title>CORE OS Desktop</title>
<style>
  * {{ box-sizing: border-box; user-select: none; }}
  body {{
    margin: 0; overflow: hidden; height: 100vh; width: 100vw;
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    background: radial-gradient(circle at 20% 20%, {t['bar']} 0%, {t['bg']} 70%);
    color: {t['text']};
  }}
  #desktop {{
    position: relative; width: 100%; height: calc(100vh - 44px); padding: 18px;
    display: flex; flex-direction: column; flex-wrap: wrap; align-content: flex-start; gap: 16px;
  }}
  .icon {{
    width: 84px; padding: 10px 6px; border-radius: 10px; text-align: center;
    cursor: pointer; transition: background 0.15s;
  }}
  .icon:hover {{ background: rgba(255,255,255,0.08); }}
  .icon-box {{
    width: 44px; height: 44px; margin: 0 auto 6px; border-radius: 12px;
    background: {t['bar']}; border: 1px solid {t['border']};
    display: flex; align-items: center; justify-content: center;
    font-size: 20px; color: {t['accent']}; font-weight: 700;
  }}
  .icon span {{ font-size: 11px; font-weight: 600; color: {t['text']}; }}
  .win {{
    position: absolute; min-width: 340px; min-height: 220px; width: 460px; height: 310px;
    background: {t['bar']}; border: 1px solid {t['border']}; border-radius: 10px;
    box-shadow: 0 18px 40px rgba(0,0,0,0.45); display: flex; flex-direction: column; overflow: hidden;
  }}
  .win-bar {{
    height: 34px; background: {t['tab_bg']}; border-bottom: 1px solid {t['border']};
    display: flex; align-items: center; padding: 0 10px; cursor: move; gap: 8px;
  }}
  .win-title {{ flex: 1; font-size: 12px; font-weight: 700; color: {t['text']}; }}
  .win-btn {{
    width: 22px; height: 22px; border: none; border-radius: 6px; background: transparent;
    color: {t['muted']}; font-weight: 700; cursor: pointer;
  }}
  .win-btn:hover {{ background: {t['border']}; color: {t['text']}; }}
  .win-btn.close:hover {{ background: #ef4444; color: #fff; }}
  .win-body {{ flex: 1; padding: 12px; overflow: auto; user-select: text; background: {t['bg']}; }}
  #taskbar {{
    height: 44px; width: 100%; background: {t['tab_bg']}; border-top: 1px solid {t['border']};
    display: flex; align-items: center; padding: 0 12px; gap: 8px;
  }}
  #start-btn {{
    background: {t['accent']}; color: #fff; border: none; border-radius: 8px;
    padding: 6px 14px; font-weight: 800; font-size: 12px; letter-spacing: 1px; cursor: pointer;
  }}
  #task-apps {{ flex: 1; display: flex; gap: 6px; overflow-x: auto; }}
  .task-pill {{
    background: {t['bar']}; color: {t['text']}; border: 1px solid {t['border']};
    border-radius: 6px; padding: 5px 12px; font-size: 11px; font-weight: 600; cursor: pointer;
  }}
  .task-pill.active {{ border-color: {t['accent']}; }}
  #tray {{ font-size: 11px; color: {t['muted']}; font-weight: 600; padding-left: 8px; }}
  #start-menu {{
    position: absolute; bottom: 52px; left: 12px; width: 230px;
    background: {t['bar']}; border: 1px solid {t['border']}; border-radius: 12px;
    padding: 10px; box-shadow: 0 14px 32px rgba(0,0,0,0.5); display: none; z-index: 9999;
  }}
  .menu-item {{ padding: 9px 12px; border-radius: 8px; font-size: 13px; font-weight: 600; cursor: pointer; }}
  .menu-item:hover {{ background: {t['accent']}; color: #fff; }}
  textarea.note-area {{
    width: 100%; height: 100%; background: {t['input']}; color: {t['text']};
    border: 1px solid {t['border']}; border-radius: 8px; padding: 10px;
    font-family: monospace; font-size: 13px; resize: none; outline: none;
  }}
  .term-out {{ font-family: monospace; font-size: 12px; color: #3fb950; white-space: pre-wrap; margin-bottom: 8px; }}
  .term-row {{ display: flex; gap: 6px; font-family: monospace; font-size: 12px; }}
  .term-in {{
    flex: 1; background: transparent; border: none; border-bottom: 1px solid {t['border']};
    color: {t['text']}; font-family: monospace; outline: none;
  }}
</style>
</head>
<body>
  <div id="desktop" onclick="hideStart()">
    <div class="icon" onclick="openApp('terminal')"><div class="icon-box">&gt;_</div><span>Terminal</span></div>
    <div class="icon" onclick="openApp('notepad')"><div class="icon-box">✎</div><span>Notepad</span></div>
    <div class="icon" onclick="openApp('monitor')"><div class="icon-box">⚡</div><span>System</span></div>
    <div class="icon" onclick="openApp('browser')"><div class="icon-box">🌐</div><span>Mini Web</span></div>
    <div class="icon" onclick="window.location.href='core://home'"><div class="icon-box">⌂</div><span>CORE Home</span></div>
  </div>

  <div id="start-menu">
    <div style="font-size:11px;color:{t['muted']};padding:4px 10px 8px;font-weight:700;">CORE OS DESKTOP</div>
    <div class="menu-item" onclick="openApp('terminal');hideStart()">&gt;_ Isolated Terminal</div>
    <div class="menu-item" onclick="openApp('notepad');hideStart()">✎ CORE Notepad</div>
    <div class="menu-item" onclick="openApp('monitor');hideStart()">⚡ System &amp; Shield Info</div>
    <div class="menu-item" onclick="openApp('browser');hideStart()">🌐 Floating Mini Browser</div>
    <hr style="border:0;border-top:1px solid {t['border']};margin:6px 0;">
    <div class="menu-item" onclick="window.location.href='core://settings'">⚙ CORE Settings</div>
    <div class="menu-item" onclick="window.location.href='core://home'">⌂ Exit to CORE Home</div>
  </div>

  <div id="taskbar">
    <button id="start-btn" onclick="toggleStart(event)">CORE</button>
    <div id="task-apps"></div>
    <div id="tray">{engine} &bull; {blocked_count} Blocked &bull; <span id="tb-clock">--:--</span></div>
  </div>

<script>
  let zTop = 10, winCount = 0;
  const vfs = {{ "readme.txt": "Welcome to CORE OS Desktop!\\nAll files live in isolated RAM.", "notes.md": "# Project Plan\\n- Build CORE OS" }};

  function toggleStart(e) {{ e.stopPropagation(); const m = document.getElementById('start-menu'); m.style.display = m.style.display === 'block' ? 'none' : 'block'; }}
  function hideStart() {{ document.getElementById('start-menu').style.display = 'none'; }}

  function focusWin(id) {{
    const w = document.getElementById(id); if (!w) return;
    w.style.display = 'flex'; w.style.zIndex = ++zTop;
    document.querySelectorAll('.task-pill').forEach(p => p.classList.remove('active'));
    const pill = document.getElementById('pill-' + id); if (pill) pill.classList.add('active');
  }}

  function minWin(id) {{
    const w = document.getElementById(id); if (w) w.style.display = 'none';
    const pill = document.getElementById('pill-' + id); if (pill) pill.classList.remove('active');
  }}

  function closeWin(id) {{
    const w = document.getElementById(id); if (w) w.remove();
    const p = document.getElementById('pill-' + id); if (p) p.remove();
  }}

  function openApp(type) {{
    const id = 'win-' + (++winCount);
    let title = 'App', body = '';
    if (type === 'terminal') {{
      title = 'CORE Virtual Terminal';
      body = `<div class="term-out" id="out-${{id}}">CORE OS Shell v2.0 (Isolated RAM VFS)\\nType 'help' for commands.\\n</div>
              <div class="term-row"><span style="color:#3fb950">core@os:~$</span>
              <input class="term-in" onkeydown="runCmd(event, '${{id}}', this)" autofocus></div>`;
    }} else if (type === 'notepad') {{
      title = 'CORE Notepad';
      body = `<textarea class="note-area" placeholder="Write notes in RAM..."></textarea>`;
    }} else if (type === 'monitor') {{
      title = 'System & Shield Monitor';
      body = `<div style="font-size:13px;line-height:1.8;"><b>Environment:</b> CORE OS Desktop<br><b>Profile:</b> {engine}<br><b>Blocked:</b> {blocked_count}<br><b>Storage:</b> Ephemeral RAM</div>`;
    }} else if (type === 'browser') {{
      title = 'Mini Web Window';
      body = `<div style="display:flex;gap:6px;margin-bottom:8px;">
                <input id="u-${{id}}" value="https://wikipedia.org" style="flex:1;padding:5px 8px;border-radius:6px;border:1px solid {t['border']};background:{t['input']};color:{t['text']};">
                <button onclick="document.getElementById('f-${{id}}').src=document.getElementById('u-${{id}}').value" style="padding:5px 12px;border:none;border-radius:6px;background:{t['accent']};color:#fff;cursor:pointer;">Go</button>
              </div><iframe id="f-${{id}}" src="https://wikipedia.org" style="width:100%;height:calc(100% - 38px);border:none;border-radius:6px;background:#fff;"></iframe>`;
    }}

    const win = document.createElement('div');
    win.className = 'win'; win.id = id;
    win.style.left = (90 + (winCount % 5) * 28) + 'px';
    win.style.top = (36 + (winCount % 5) * 24) + 'px';
    win.style.zIndex = ++zTop;
    win.onmousedown = () => focusWin(id);
    win.innerHTML = `<div class="win-bar" onmousedown="startDrag(event, '${{id}}')">
      <div class="win-title">${{title}}</div>
      <button class="win-btn" onclick="minWin('${{id}}')">_</button>
      <button class="win-btn close" onclick="closeWin('${{id}}')">×</button>
    </div><div class="win-body">${{body}}</div>`;
    document.getElementById('desktop').appendChild(win);

    const pill = document.createElement('button');
    pill.className = 'task-pill active'; pill.id = 'pill-' + id; pill.textContent = title;
    pill.onclick = () => focusWin(id);
    document.getElementById('task-apps').appendChild(pill);
    focusWin(id);
  }}

  function runCmd(e, id, inp) {{
    if (e.key !== 'Enter') return;
    const raw = inp.value.trim(); inp.value = '';
    const out = document.getElementById('out-' + id);
    out.textContent += `\\ncore@os:~$ ${{raw}}\\n`;
    const parts = raw.split(' '), cmd = parts[0].toLowerCase();
    if (cmd === 'help') out.textContent += 'Commands: help, ls, cat <file>, touch <file>, rm <file>, sysinfo, clear\\n';
    else if (cmd === 'ls') out.textContent += Object.keys(vfs).join('   ') + '\\n';
    else if (cmd === 'cat') out.textContent += (vfs[parts[1]] || 'File not found') + '\\n';
    else if (cmd === 'touch' && parts[1]) {{ vfs[parts[1]] = ''; out.textContent += `Created ${{parts[1]}}\\n`; }}
    else if (cmd === 'rm' && parts[1]) {{ delete vfs[parts[1]]; out.textContent += `Removed ${{parts[1]}}\\n`; }}
    else if (cmd === 'sysinfo') out.textContent += 'CORE OS Desktop • RAM-Only Isolation • Shield Active\\n';
    else if (cmd === 'clear') out.textContent = '';
    else if (raw) out.textContent += `Unknown command: ${{cmd}}\\n`;
    out.parentElement.scrollTop = out.parentElement.scrollHeight;
  }}

  function startDrag(e, id) {{
    if (e.target.tagName === 'BUTTON') return;
    const w = document.getElementById(id);
    const ox = e.clientX - w.offsetLeft, oy = e.clientY - w.offsetTop;
    const move = ev => {{ w.style.left = (ev.clientX - ox) + 'px'; w.style.top = Math.max(0, ev.clientY - oy) + 'px'; }};
    const up = () => {{ document.removeEventListener('mousemove', move); document.removeEventListener('mouseup', up); }};
    document.addEventListener('mousemove', move); document.addEventListener('mouseup', up);
  }}

  setInterval(() => {{
    document.getElementById('tb-clock').textContent = new Date().toLocaleTimeString([], {{hour:'2-digit', minute:'2-digit'}});
  }}, 1000);
</script>
</body>
</html>"""
