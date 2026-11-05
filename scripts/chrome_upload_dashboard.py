#!/usr/bin/env python3
"""Uploads the honest dashboard files into the Hostinger File Browser tab that is
currently open in Chrome (user's own logged-in session). The tab's site is
detected from the page; only public_html of that site is touched.

usage: chrome_upload_dashboard.py
"""
import base64, json, subprocess, sys
from pathlib import Path

SITES = Path(__file__).resolve().parent.parent / "sites"
FILES = {"dashboard.html": SITES / "dashboard.html",
         "dashboard/index.html": SITES / "dashboard.html",
         "dashboard_data.json": SITES / "dashboard_data.json"}


def chrome_js(js: str) -> str:
    script = ('tell application "Google Chrome"\n'
              ' repeat with w in every window\n  repeat with t in every tab of w\n'
              '   if URL of t contains "files.hstgr.io" then\n    tell t\n'
              f'     set res to execute javascript {json.dumps(js)}\n     return res\n    end tell\n'
              '   end if\n  end repeat\n end repeat\n return "TAB_NOT_FOUND"\nend tell')
    r = subprocess.run(["osascript", "-e", script], capture_output=True, text=True)
    if r.returncode:
        raise RuntimeError(r.stderr)
    return r.stdout.strip()


def put(remote: str, local: Path) -> dict:
    b64 = base64.b64encode(local.read_bytes()).decode()
    js = ("(function(){var p=location.pathname.split('/')[1];var bin=atob('%s');var u=new Uint8Array(bin.length);"
          "for(var i=0;i<bin.length;i++)u[i]=bin.charCodeAt(i);var x=new XMLHttpRequest();"
          "x.open('POST','/'+p+'/api/resources/public_html/%s?override=true',false);"
          "x.setRequestHeader('X-Auth',localStorage.getItem('jwt'));x.send(new Blob([u]));"
          "return JSON.stringify({status:x.status})})()") % (b64, remote)
    return json.loads(chrome_js(js))


if __name__ == "__main__":
    print("tab:", chrome_js("document.title+' | '+location.pathname"))
    for remote, local in FILES.items():
        print(remote, put(remote, local))
