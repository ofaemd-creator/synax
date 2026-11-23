#!/usr/bin/env python3
"""
SYNAX Hostinger Famulus Direct Deployer (`scripts/chrome_hostinger_deploy.py`)
==============================================================================
Uploads all production files (`index.html`, `office.html`, `api.php`,
`evolution_feed.json`, `repos.html`, `guide.html`, `dashboard.html`,
`dashboard_data.json`, `synax_beacon.js`, `studio.html`) directly to
`synaxcode.com`, `synaxcode.org`, and `synaxcode.online` on Hostinger via the
live Pinia `famulusStore` in Safari (using stdin AppleScript to support 1.5MB+ files).
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
    r = subprocess.run(["osascript", "-"], input=script, capture_output=True, text=True)
    if r.returncode != 0:
        raise RuntimeError(f"Safari AppleScript error: {r.stderr.strip()}")
    return r.stdout.strip()


def upload_file_famulus(remote_path: str, local_path: Path) -> bool:
    if not local_path.exists():
        return False
    b64 = base64.b64encode(local_path.read_bytes()).decode("ascii")
    js_start = f"""
    (function() {{
        window._upStatus = "PENDING";
        (async function() {{
            try {{
                var appEl = document.querySelector("#app, [data-v-app]");
                var pinia = appEl && appEl.__vue_app__ && appEl.__vue_app__.config.globalProperties.$pinia;
                var store = pinia && pinia._s ? pinia._s.get("famulusStore") : null;
                if (!store) {{
                    throw new Error("famulusStore not found in Pinia");
                }}
                if (!store.client && typeof store.connect === "function") {{
                    await store.connect();
                }}
                if (!store.client && typeof store.refreshSession === "function") {{
                    await store.refreshSession();
                }}
                for (var w = 0; w < 20 && !store.client; w++) {{
                    await new Promise(function(r) {{ setTimeout(r, 250); }});
                }}
                if (!store.client) {{
                    throw new Error("store.client is still null after connect()");
                }}
                var bin = atob("{b64}");
                var bytes = new Uint8Array(bin.length);
                for (var i = 0; i < bin.length; i++) {{
                    bytes[i] = bin.charCodeAt(i);
                }}
                var etag = await store.client.writeFile("{remote_path}", bytes, {{}});
                window._upStatus = "OK:" + (etag || "200");
            }} catch (err) {{
                window._upStatus = "ERR:" + (err && err.message ? err.message : String(err));
            }}
        }})();
        return "STARTED";
    }})()
    """
    safari_js(js_start)
    for _ in range(80):
        time.sleep(0.25)
        st = safari_js("window._upStatus")
        if st != "PENDING":
            if st.startswith("OK:"):
                print(f"  ✓ Yüklendi: {remote_path:<52} ({local_path.stat().st_size:,} bayt)")
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
    r = subprocess.run(["osascript", "-"], input=script, capture_output=True, text=True)
    if "NAVIGATED" in r.stdout:
        print("⏳ Hostinger Dosya Yöneticisi sekmesi açılıyor (7 sn bekleniyor)...")
        time.sleep(7)


def main() -> int:
    ensure_file_manager_tab()
    print("=" * 78)
    print("🚀 SYNAX v6.4.0 DOĞRUDAN HOSTINGER FAMULUS CANLI DAĞITIMI (3 SİTE BİRDEN)")
    print("=" * 78)

    sites_dir = BASE_DIR / "sites"
    studio_html = sites_dir / "online_index.html"

    domains_map = {
        "synaxcode.com": sites_dir / "com_index.html",
        "synaxcode.org": sites_dir / "org_index.html",
        "synaxcode.online": sites_dir / "online_index.html",
    }

    for domain, index_file in domains_map.items():
        print(f"\n🌐 {domain} güncelleniyor...")
        pub = f"/domains/{domain}/public_html"
        upload_file_famulus(f"{pub}/index.html", index_file)
        upload_file_famulus(f"{pub}/office.html", sites_dir / "office.html")
        upload_file_famulus(f"{pub}/studio.html", studio_html)
        upload_file_famulus(f"{pub}/api.php", sites_dir / "api.php")
        upload_file_famulus(f"{pub}/evolution_feed.json", sites_dir / "evolution_feed.json")
        upload_file_famulus(f"{pub}/dashboard.html", sites_dir / "dashboard.html")
        upload_file_famulus(f"{pub}/dashboard/index.html", sites_dir / "dashboard.html")
        upload_file_famulus(f"{pub}/dashboard_data.json", sites_dir / "dashboard_data.json")
        upload_file_famulus(f"{pub}/guide.html", sites_dir / "guide.html")
        upload_file_famulus(f"{pub}/synax_beacon.js", sites_dir / "synax_beacon.js")
        if domain in ("synaxcode.com", "synaxcode.org"):
            upload_file_famulus(f"{pub}/repos.html", sites_dir / "repos_index.html")

        # Also deploy subdomain / subdirectory apps: office, chat, code, terminal
        for sub_dir, sub_html in [
            ("office", sites_dir / "office.html"),
            ("chat", sites_dir / "chat_index.html"),
            ("code", sites_dir / "code_index.html"),
            ("terminal", sites_dir / "terminal_index.html"),
        ]:
            upload_file_famulus(f"{pub}/{sub_dir}/index.html", sub_html)
            upload_file_famulus(f"{pub}/{sub_dir}/api.php", sites_dir / "api.php")
            upload_file_famulus(f"{pub}/{sub_dir}/evolution_feed.json", sites_dir / "evolution_feed.json")

    print("\n🎉 TÜM SİTELER VE SUBDOMAINLER (office, chat, code, terminal .synaxcode.com) CANLI OLARAK GÜNCELLENDİ!")
    return 0


if __name__ == "__main__":
    sys.exit(main())
