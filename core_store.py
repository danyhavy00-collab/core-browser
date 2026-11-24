import os
import re
import json
import shutil
import subprocess
import sys
import ssl
import zipfile
import tarfile
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from urllib.parse import quote_plus

SSL_CTX = ssl._create_unverified_context()


def get_sandbox_dir() -> str:
    base = os.path.join(os.path.expanduser("~"), ".core-browser", "sandbox")
    os.makedirs(base, exist_ok=True)
    return base


def list_sandbox_apps() -> list:
    sb = get_sandbox_dir()
    meta_path = os.path.join(sb, "apps.json")
    if os.path.exists(meta_path):
        try:
            with open(meta_path, "r") as f:
                return json.load(f)
        except Exception:
            pass
    return []


def save_sandbox_apps(apps: list):
    sb = get_sandbox_dir()
    with open(os.path.join(sb, "apps.json"), "w") as f:
        json.dump(apps, f, indent=2)


def _search_github_repos(q: str) -> list:
    items = []
    try:
        api_url = "/".join(["https:/", "://github.com", "search", "repositories?q=" + quote_plus(q) + "&sort=stars&per_page=15"])
        req = urllib.request.Request(api_url, headers={"Accept": "application/vnd.github+json", "User-Agent": "CORE-Store/2.4"})
        with urllib.request.urlopen(req, timeout=5, context=SSL_CTX) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        for r in data.get("items", []):
            fn = r.get("full_name", "")
            items.append({
                "id": "gh_" + fn.replace("/", "_"),
                "name": r.get("name", ""),
                "developer": r.get("owner", {}).get("login", "GitHub"),
                "summary": (r.get("description") or "Open-source software package")[:100],
                "icon": r.get("owner", {}).get("avatar_url", ""),
                "source": f"GitHub ★ {r.get('stargazers_count', 0):,}",
                "kind": "github",
                "target": fn
            })
        if items:
            return items
    except Exception:
        pass

    try:
        web_search = "/".join(["https:/", "github.com", "search?q=" + quote_plus(q) + "&type=repositories"])
        req = urllib.request.Request(web_search, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=6, context=SSL_CTX) as resp:
            page = resp.read().decode("utf-8", errors="ignore")
        repos = re.findall(r'href="/([A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+)"', page)
        seen = set()
        for fn in repos:
            if fn in seen or fn.startswith(("search/", "settings/", "features/", "topics/", "collections/", "sponsors/", "orgs/", "login", "signup", "pricing", "marketplace")):
                continue
            seen.add(fn)
            owner, name = fn.split("/", 1)
            items.append({
                "id": "gh_" + fn.replace("/", "_"),
                "name": name,
                "developer": owner,
                "summary": f"Open-source repository {fn}",
                "icon": f"https://github.com{owner}.png?size=64",
                "source": "GitHub Package",
                "kind": "github",
                "target": fn
            })
            if len(items) >= 15:
                break
    except Exception:
        pass
    return items


def _search_snapcraft(q: str) -> list:
    items = []
    if sys.platform.startswith("win"):
        return items
    try:
        url = "/".join(["https:/", "api.snapcraft.io", "v2", "snaps", "find?q=" + quote_plus(q) + "&fields=title,summary,publisher,media"])
        req = urllib.request.Request(url, headers={"Snap-Device-Series": "16", "User-Agent": "CORE-Store/2.4"})
        with urllib.request.urlopen(req, timeout=5, context=SSL_CTX) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        for hit in data.get("results", [])[:15]:
            snap = hit.get("snap", {})
            name = snap.get("title") or hit.get("name", "")
            slug = hit.get("name", "")
            icon = ""
            for m in snap.get("media", []):
                if m.get("type") == "icon":
                    icon = m.get("url", "")
                    break
            items.append({
                "id": "snap_" + slug,
                "name": name,
                "developer": snap.get("publisher", {}).get("display-name", "Snap Store"),
                "summary": (snap.get("summary") or "Desktop application package")[:100],
                "icon": icon,
                "source": "App Package",
                "kind": "snap",
                "target": slug
            })
    except Exception:
        pass
    return items


def search_live_apps(query: str = "") -> list:
    q = (query or "game").strip()
    with ThreadPoolExecutor(max_workers=2) as pool:
        f_gh = pool.submit(_search_github_repos, q)
        f_snap = pool.submit(_search_snapcraft, q)
        gh_items = f_gh.result()
        snap_items = f_snap.result()

    combined = []
    for i in range(max(len(gh_items), len(snap_items))):
        if i < len(snap_items):
            combined.append(snap_items[i])
        if i < len(gh_items):
            combined.append(gh_items[i])
    return combined


def _get_snap_download_info(slug: str) -> tuple[str, int]:
    info_url = "/".join(["https:/", "api.snapcraft.io", "v2", "snaps", "info", slug])
    req = urllib.request.Request(info_url, headers={"Snap-Device-Series": "16", "User-Agent": "CORE-Store/2.4"})
    with urllib.request.urlopen(req, timeout=8, context=SSL_CTX) as resp:
        data = json.loads(resp.read().decode("utf-8"))
    for ch in data.get("channel-map", []):
        arch = ch.get("channel", {}).get("architecture", "")
        if arch in ("amd64", "all"):
            dl = ch.get("download", {})
            if dl.get("url"):
                return dl["url"], int(dl.get("size") or 0)
    return "", 0


def _fetch_github_assets(repo_full_name: str) -> list:
    try:
        api_url = "/".join(["https:/", "://github.com", "repos", repo_full_name, "releases", "latest"])
        req = urllib.request.Request(api_url, headers={"Accept": "application/vnd.github+json", "User-Agent": "CORE-Browser/2.4"})
        with urllib.request.urlopen(req, timeout=5, context=SSL_CTX) as resp:
            rel = json.loads(resp.read().decode("utf-8"))
        if rel.get("assets"):
            return [{"name": a["name"], "url": a["browser_download_url"], "size": a.get("size", 0)} for a in rel["assets"]]
    except Exception:
        pass

    rel_url = "/".join(["https:/", "github.com", repo_full_name, "releases", "latest"])
    req = urllib.request.Request(rel_url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=8, context=SSL_CTX) as resp:
        final_url = resp.geturl()
        page_html = resp.read().decode("utf-8", errors="ignore")

    if "/releases/tag/" in final_url:
        tag = final_url.split("/releases/tag/", 1)[1].split("?")[0]
        exp_url = "/".join(["https:/", "github.com", repo_full_name, "releases", "expanded_assets", tag])
        exp_req = urllib.request.Request(exp_url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(exp_req, timeout=8, context=SSL_CTX) as exp_resp:
            page_html += exp_resp.read().decode("utf-8", errors="ignore")

    links = re.findall(r'href="(/[^"]+/releases/download/[^"]+)"', page_html)
    assets = []
    seen = set()
    for path in links:
        if path in seen:
            continue
        seen.add(path)
        fname = path.split("/")[-1]
        assets.append({"name": fname, "url": "https:/" + "/github.com" + path, "size": 0})
    return assets


def _pick_best_asset(assets: list):
    is_win = sys.platform.startswith("win")
    scored = []
    for a in assets:
        n = a.get("name", "").lower()
        if any(bad in n for bad in ("sha256", "sha512", ".sig", ".asc", "source", "arm64", "aarch64", "arm32", "armv7", "armv6", "i386", "i686", "web.zip", "mono", "macos", "osx", "darwin", "android", ".apk", ".deb", ".rpm", ".msi")):
            continue
        score = 0
        if is_win:
            if any(k in n for k in ("win64", "win32", "windows", "x86_64", "x64", ".exe")):
                score += 10
            if "setup" in n or "installer" in n:
                score -= 8
            if n.endswith(".zip"):
                score += 12
            elif n.endswith(".exe"):
                score += 8
        else:
            if "x86_64" in n or "amd64" in n:
                score += 15
            if any(k in n for k in ("linux", "appimage")):
                score += 10
            if n.endswith(".appimage"):
                score += 12
            elif n.endswith((".zip", ".tar.gz", ".tgz", ".tar.xz")):
                score += 6
        if score > 0:
            scored.append((score, a))
    scored.sort(key=lambda x: x[0], reverse=True)
    if not scored:
        return None
    _, top = next(iter(scored))
    return top


def _find_executable(folder: str, hint_name: str = "") -> str:
    is_win = sys.platform.startswith("win")
    # 1. If extracted Snap has meta/snap.yaml, read its exact app command first
    snap_yaml = os.path.join(folder, "squashfs-root", "meta", "snap.yaml")
    if not is_win and os.path.exists(snap_yaml):
        try:
            with open(snap_yaml, "r", encoding="utf-8", errors="ignore") as yf:
                for line in yf:
                    st = line.strip()
                    if st.startswith("command:"):
                        cmd_rel = st.split(":", 1).strip().strip("'\"").split()
                        cand = os.path.join(folder, "squashfs-root", cmd_rel.lstrip("/"))
                        if os.path.isfile(cand) and not os.path.islink(cand):
                            os.chmod(cand, 0o755)
                            return cand
        except Exception:
            pass

    candidates = []
    hint = hint_name.lower().replace(" ", "")
    for root, _, files in os.walk(folder):
        for fn in files:
            full = os.path.join(root, fn)
            if os.path.islink(full) or not os.path.isfile(full):
                continue
            low = fn.lower()
            if is_win:
                if low.endswith(".exe") and "unins" not in low and "crash" not in low:
                    bonus = 50_000_000 if hint and hint in low else 0
                    candidates.append((os.path.getsize(full) + bonus, full))
            else:
                if low.endswith((".snap", ".zip", ".tar.gz", ".tgz", ".tar.xz", ".txt", ".md", ".json", ".png", ".svg", ".so", ".py", ".desktop", ".yaml", ".yml")):
                    continue
                if "/lib/" in full or "/share/" in full or "/include/" in full or "/etc/" in full:
                    continue
                if low.endswith((".appimage", ".x86_64", ".bin", ".sh")) or "/bin/" in full or "." not in fn or os.access(full, os.X_OK):
                    bonus = 50_000_000 if hint and hint in low else 0
                    candidates.append((os.path.getsize(full) + bonus, full))
    if not candidates:
        return ""
    candidates.sort(key=lambda x: x, reverse=True)
    _, best = next(iter(candidates))
    if not is_win:
        os.chmod(best, 0o755)
    return best


def install_package_to_sandbox(kind: str, target: str, app_name: str, progress_cb=None) -> tuple[bool, str]:
    try:
        if progress_cb:
            progress_cb(3, "Resolving package...")

        dl_url, dl_name, dl_size = "", "", 0
        if kind == "snap":
            dl_url, dl_size = _get_snap_download_info(target)
            dl_name = f"{target}.snap"
            if not dl_url:
                return False, f"No downloadable package found for {app_name}."
        else:
            assets = _fetch_github_assets(target)
            chosen = _pick_best_asset(assets)
            if not chosen:
                return False, f"No pre-compiled desktop binary found for {app_name}."
            dl_url = chosen["url"]
            dl_name = chosen["name"]
            dl_size = int(chosen.get("size") or 0)

        sb = get_sandbox_dir()
        app_id = (kind + "_" + target.replace("/", "_")).lower()
        app_dir = os.path.join(sb, app_id)
        shutil.rmtree(app_dir, ignore_errors=True)
        os.makedirs(app_dir, exist_ok=True)

        dl_path = os.path.join(app_dir, dl_name)
        dl_req = urllib.request.Request(dl_url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(dl_req, timeout=180, context=SSL_CTX) as dl_resp, open(dl_path, "wb") as out_f:
            total = int(dl_resp.headers.get("Content-Length") or dl_size or 0)
            done = 0
            last_pct = -1
            while True:
                chunk = dl_resp.read(65536)
                if not chunk:
                    break
                out_f.write(chunk)
                done += len(chunk)
                if total > 0:
                    pct = min(90, int((done / total) * 90))
                    if pct >= last_pct + 2:
                        last_pct = pct
                        mb_done = done / (1024 * 1024)
                        mb_tot = total / (1024 * 1024)
                        if progress_cb:
                            progress_cb(pct, f"{pct}% ({mb_done:.1f}/{mb_tot:.1f} MB)")
                else:
                    mb_done = done / (1024 * 1024)
                    if int(mb_done) > last_pct:
                        last_pct = int(mb_done)
                        if progress_cb:
                            progress_cb(50, f"{mb_done:.1f} MB...")

        if progress_cb:
            progress_cb(94, "Extracting...")
        low = dl_name.lower()
        if low.endswith(".snap"):
            sq_out = os.path.join(app_dir, "squashfs-root")
            if shutil.which("unsquashfs"):
                subprocess.run(["unsquashfs", "-f", "-d", sq_out, dl_path], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
            elif shutil.which("7z"):
                subprocess.run(["7z", "x", dl_path, f"-o{sq_out}", "-y"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
            else:
                return False, "Install 'squashfs-tools' (sudo apt install squashfs-tools) once to unpack Snap packages."
            os.remove(dl_path)
        elif low.endswith(".zip"):
            with zipfile.ZipFile(dl_path, "r") as zf:
                zf.extractall(app_dir)
            os.remove(dl_path)
        elif low.endswith((".tar.gz", ".tgz", ".tar.xz")):
            with tarfile.open(dl_path, "r:*") as tf:
                tf.extractall(app_dir)
            os.remove(dl_path)

        exe_path = _find_executable(app_dir, target.split("/")[-1])
        if not exe_path:
            return False, f"Unpacked {app_name}, but could not locate a runnable binary inside."

        apps = [a for a in list_sandbox_apps() if a["id"] != app_id]
        apps.append({"id": app_id, "name": app_name, "exec": exe_path, "dir": app_dir})
        save_sandbox_apps(apps)
        if progress_cb:
            progress_cb(100, "Installed")
        return True, f"{app_name} installed silently into your isolated sandbox!"
    except Exception as e:
        return False, f"Install failed: {e}"


def import_into_sandbox(src_path: str) -> dict:
    sb = get_sandbox_dir()
    fname = os.path.basename(src_path)
    app_id = fname.replace(" ", "_").lower()
    app_dir = os.path.join(sb, app_id)
    os.makedirs(app_dir, exist_ok=True)
    dst_path = os.path.join(app_dir, fname)
    shutil.copy2(src_path, dst_path)
    if not sys.platform.startswith("win"):
        os.chmod(dst_path, 0o755)
    apps = [a for a in list_sandbox_apps() if a["id"] != app_id]
    entry = {"id": app_id, "name": os.path.splitext(fname)[0], "exec": dst_path, "dir": app_dir}
    apps.append(entry)
    save_sandbox_apps(apps)
    return entry


def launch_sandboxed_app(app_id: str) -> bool:
    for app in list_sandbox_apps():
        if app["id"] == app_id and os.path.exists(app["exec"]):
            env = os.environ.copy()
            env["HOME"] = app["dir"]
            env["USERPROFILE"] = app["dir"]
            env["APPDATA"] = app["dir"]
            env["LOCALAPPDATA"] = app["dir"]
            sq_root = os.path.join(app["dir"], "squashfs-root")
            if os.path.isdir(sq_root):
                env["SNAP"] = sq_root
                env["PATH"] = f"{sq_root}/usr/bin:{sq_root}/bin:" + env.get("PATH", "")
                env["LD_LIBRARY_PATH"] = f"{sq_root}/usr/lib/x86_64-linux-gnu:{sq_root}/lib/x86_64-linux-gnu:{sq_root}/usr/lib:" + env.get("LD_LIBRARY_PATH", "")
            subprocess.Popen([app["exec"]], cwd=os.path.dirname(app["exec"]), env=env)
            return True
    return False


def wipe_sandbox_app(app_id: str):
    apps = list_sandbox_apps()
    for app in apps:
        if app["id"] == app_id and os.path.exists(app["dir"]):
            shutil.rmtree(app["dir"], ignore_errors=True)
    save_sandbox_apps([a for a in apps if a["id"] != app_id])
