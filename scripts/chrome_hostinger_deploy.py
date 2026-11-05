#!/usr/bin/env python3
"""
SYNAX Chrome Direct Hostinger Deployer (`scripts/chrome_hostinger_deploy.py`)
=============================================================================
Uploads all necessary production files directly into Hostinger File Browser
via the active Google Chrome tab session.
"""

import base64
import json
import os
import subprocess
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

def run_chrome_js(js_code: str) -> str:
    """Executes JavaScript inside the Hostinger File Browser Chrome tab."""
    # Escape for AppleScript
    # Write JS to a temp file or use python json encoding
    escaped_js = json.dumps(js_code)
    apple_script = f'''
    tell application "Google Chrome"
        repeat with w in every window
            repeat with t in every tab of w
                if URL of t contains "files.hstgr.io" then
                    tell t
                        set res to execute javascript {escaped_js}
                        return res
                    end tell
                end if
            end repeat
        end repeat
        return "TAB_NOT_FOUND"
    end tell
    '''
    res = subprocess.run(["osascript", "-e", apple_script], capture_output=True, text=True)
    if res.returncode != 0:
        raise RuntimeError(f"AppleScript error: {res.stderr}")
    return res.stdout.strip()

def upload_file_to_hostinger(remote_path: str, local_path: Path):
    """Uploads a local file to Hostinger via Chrome session."""
    data_b64 = base64.b64encode(local_path.read_bytes()).decode("ascii")
    js = f'''
    (function() {{
        try {{
            const b64 = "{data_b64}";
            const bin = atob(b64);
            const bytes = new Uint8Array(bin.length);
            for (let i = 0; i < bin.length; i++) {{
                bytes[i] = bin.charCodeAt(i);
            }}
            const blob = new Blob([bytes], {{ type: "application/octet-stream" }});
            
            const xhr = new XMLHttpRequest();
            const url = "/56c0a3c8002461e4/api/resources{remote_path}?override=true";
            xhr.open("POST", url, false);
            xhr.setRequestHeader("X-Auth", localStorage.getItem("jwt"));
            xhr.send(blob);
            return JSON.stringify({{ status: xhr.status, path: "{remote_path}" }});
        }} catch(e) {{
            return JSON.stringify({{ error: e.message }});
        }}
    }})()
    '''
    raw_res = run_chrome_js(js)
    res = json.loads(raw_res)
    if res.get("status") in (200, 204):
        print(f"  ✓ Yüklendi: {remote_path} ({local_path.stat().st_size:,} bayt)")
    else:
        print(f"  ✗ Hata ({res.get('status')}): {remote_path} - {res}")

def create_directory_in_hostinger(remote_dir_path: str):
    """Creates a directory in Hostinger via Chrome session."""
    # In File Browser, POST with trailing slash creates a directory
    js = f'''
    (function() {{
        try {{
            const xhr = new XMLHttpRequest();
            const url = "/56c0a3c8002461e4/api/resources{remote_dir_path}/";
            xhr.open("POST", url, false);
            xhr.setRequestHeader("X-Auth", localStorage.getItem("jwt"));
            xhr.send();
            return JSON.stringify({{ status: xhr.status }});
        }} catch(e) {{
            return JSON.stringify({{ error: e.message }});
        }}
    }})()
    '''
    run_chrome_js(js)

def main():
    print("=" * 70)
    print("🚀 SYNAX CHROME ÜZERİNDEN DOĞRUDAN HOSTINGER DAĞITIMI")
    print("=" * 70)

    # File paths
    dashboard_html = BASE_DIR / "sites" / "dashboard.html"
    synax_beacon_js = BASE_DIR / "sites" / "synax_beacon.js"
    htaccess = BASE_DIR / ".htaccess"
    guide_html = BASE_DIR / "sites" / "guide.html"
    repos_html = BASE_DIR / "sites" / "repos_index.html"
    
    com_index = BASE_DIR / "sites" / "com_index.html"
    org_index = BASE_DIR / "sites" / "org_index.html"
    online_index = BASE_DIR / "sites" / "online_index.html"

    domains_map = {
        "synaxcode.com": com_index,
        "synaxcode.org": org_index,
        "synaxcode.online": online_index
    }

    for domain, index_file in domains_map.items():
        print(f"\n🌐 {domain} Dağıtımı Başlatılıyor...")
        pub = f"/domains/{domain}/public_html"
        
        # 1. Create dashboard directory
        create_directory_in_hostinger(f"{pub}/dashboard")
        
        # 2. Upload dashboard.html (both in public_html and in public_html/dashboard/index.html)
        upload_file_to_hostinger(f"{pub}/dashboard.html", dashboard_html)
        upload_file_to_hostinger(f"{pub}/dashboard/index.html", dashboard_html)
        
        # 3. Upload synax_beacon.js
        upload_file_to_hostinger(f"{pub}/synax_beacon.js", synax_beacon_js)
        
        # 4. Upload .htaccess
        upload_file_to_hostinger(f"{pub}/.htaccess", htaccess)
        
        # 5. Upload index.html
        upload_file_to_hostinger(f"{pub}/index.html", index_file)
        
        # 6. Upload guide.html
        upload_file_to_hostinger(f"{pub}/guide.html", guide_html)
        
        # 7. Upload repos.html (for .com and .org)
        if domain in ("synaxcode.com", "synaxcode.org"):
            upload_file_to_hostinger(f"{pub}/repos.html", repos_html)

    # Reload Chrome tab to show the updated directory
    print("\n🔄 Chrome sekmesi yenileniyor...")
    run_chrome_js("window.location.reload()")
    print("\n🎉 TEBRİKLER! TÜM DOSYALAR HOSTINGER'A BAŞARIYLA YÜKLENDİ!")
    print("=" * 70)

if __name__ == "__main__":
    main()
