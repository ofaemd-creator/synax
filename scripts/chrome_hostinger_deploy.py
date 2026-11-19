#!/usr/bin/env python3
"""
SYNAX Hostinger Famulus Direct Deployer (`scripts/chrome_hostinger_deploy.py`)
==============================================================================
Uploads all production files (`index.html`, `office.html`, `repos.html`, `guide.html`,
`dashboard.html`, `dashboard_data.json`, `synax_beacon.js`, `studio.html`)
directly to `synaxcode.com`, `synaxcode.org`, and `synaxcode.online` on
Hostinger via the authenticated `famulusStore` client in Safari.
"""

import base64
import json
import subprocess
import sys
import time
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent


def safari_js(js_code: str) -> str:
    escaped = json.dumps(js_code)
    script = f"""
    tell application "Safari"
        repeat with w in every window
            repeat with t in every tab of w
                if URL of t contains "file-manager" then
                    tell t
                        return do JavaScript {escaped}
                    end tell
                end if
            end repeat
        end repeat
        error "Hostinger file-manager tab not found in Safari"
    end tell
    """
    r = subprocess.run(["osascript", "-e", script], capture_output=True, text=True)
    if r.returncode != 0:
        raise RuntimeError(f"Safari AppleScript error: {r.stderr.strip()}")
    return r.stdout.strip()


def upload_file_famulus(remote_path: str, local_path: Path) -> bool:
    b64 = base64.b64encode(local_path.read_bytes()).decode("ascii")
    js_start = f"""
    (function() {{
        window._upStatus = "PENDING";
        var el = Array.from(document.querySelectorAll('script,link')).find(function(x) {{
            return (x.src || x.href || '').includes('famulusStore.');
        }});
        var chunkUrl = el ? (el.src || el.href) : '/assets/chunk/famulusStore.FtnZJayN.js';
        import(chunkUrl).then(function(m) {{
            var fn = m.t || m.u || m.useFamulusStore || Object.values(m).find(function(v) {{ return typeof v === 'function'; }});
            var store = fn();
            var bin = atob("{b64}");
            var bytes = new Uint8Array(bin.length);
            for (var i = 0; i < bin.length; i++) {{
                bytes[i] = bin.charCodeAt(i);
            }}
            return store.client.writeFile("{remote_path}", bytes, {{}});
        }}).then(function(etag) {{
            window._upStatus = "OK:" + (etag || "200");
        }}).catch(function(err) {{
            window._upStatus = "ERR:" + (err.message || String(err));
        }});
        return "STARTED";
    }})()
    """
    safari_js(js_start)
    for _ in range(50):
        time.sleep(0.25)
        st = safari_js("window._upStatus")
        if st != "PENDING":
            if st.startswith("OK:"):
                print(f"  ✓ Yüklendi: {remote_path:<48} ({local_path.stat().st_size:,} bayt)")
                return True
            print(f"  ✗ Hata: {remote_path} -> {st}")
            return False
    print(f"  ✗ Zaman aşımı: {remote_path}")
    return False


def ensure_file_manager_tab() -> None:
    script = """
    tell application "Safari"
        repeat with w in every window
            repeat with t in every tab of w
                if URL of t contains "file-manager" then
                    return "ALREADY_OPEN"
                end if
            end repeat
        end repeat
        repeat with w in every window
            repeat with t in every tab of w
                if URL of t contains "hostinger.com" then
                    tell t
                        set URL to "https://hpanel.hostinger.com/websites/synaxcode.com/files/file-manager?redirectLocation=side_menu"
                    end tell
                    return "NAVIGATED"
                end if
            end repeat
        end repeat
        return "NO_TAB"
    end tell
    """
    r = subprocess.run(["osascript", "-e", script], capture_output=True, text=True)
    if "NAVIGATED" in r.stdout:
        print("⏳ Hostinger Dosya Yöneticisi sekmesi açılıyor (7 sn bekleniyor)...")
        time.sleep(7)


def main() -> int:
    ensure_file_manager_tab()
    print("=" * 74)
    print("🚀 SYNAX DOĞRUDAN HOSTINGER FAMULUS CANLI DAĞITIMI (3 SITE BİRDEN)")
    print("=" * 74)

    sites_dir = BASE_DIR / "sites"
    studio_html = BASE_DIR / "editors" / "vscode-synax" / "media" / "studio.html"

    domains_map = {
        "synaxcode.com": sites_dir / "com_index.html",
        "synaxcode.org": sites_dir / "org_index.html",
        "synaxcode.online": sites_dir / "online_index.html",
    }

    for domain, index_file in domains_map.items():
        print(f"\n🌐 {domain} güncelleniyor...")
        pub = f"/domains/{domain}/public_html"
        upload_file_famulus(f"{pub}/index.html", index_file)
        if (sites_dir / "office.html").exists():
            upload_file_famulus(f"{pub}/office.html", sites_dir / "office.html")
        upload_file_famulus(f"{pub}/dashboard.html", sites_dir / "dashboard.html")
        upload_file_famulus(f"{pub}/dashboard/index.html", sites_dir / "dashboard.html")
        if (BASE_DIR / "dashboard_data.json").exists():
            upload_file_famulus(f"{pub}/dashboard_data.json", BASE_DIR / "dashboard_data.json")
        upload_file_famulus(f"{pub}/guide.html", sites_dir / "guide.html")
        if (BASE_DIR / "synax_beacon.js").exists():
            upload_file_famulus(f"{pub}/synax_beacon.js", BASE_DIR / "synax_beacon.js")
        if domain in ("synaxcode.com", "synaxcode.org"):
            upload_file_famulus(f"{pub}/repos.html", sites_dir / "repos_index.html")
        if studio_html.exists():
            upload_file_famulus(f"{pub}/studio.html", studio_html)

    # Also update root /public_html on the primary domain
    print("\n📂 Ana /public_html dizini senkronize ediliyor...")
    upload_file_famulus("/public_html/index.html", sites_dir / "com_index.html")
    if (sites_dir / "office.html").exists():
        upload_file_famulus("/public_html/office.html", sites_dir / "office.html")
    if studio_html.exists():
        upload_file_famulus("/public_html/studio.html", studio_html)

    print("\n🎉 TÜM SİTELER (synaxcode.com, synaxcode.org, synaxcode.online) CANLI OLARAK GÜNCELLENDİ!")
    return 0


if __name__ == "__main__":
    sys.exit(main())
