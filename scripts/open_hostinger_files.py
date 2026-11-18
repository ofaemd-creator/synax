#!/usr/bin/env python3
"""Checks Safari hPanel tab and opens File Manager."""
import subprocess

APPLE = '''
tell application "Safari"
    repeat with w in every window
        repeat with t in every tab of w
            if URL of t contains "hpanel.hostinger.com" then
                tell t
                    set res to do JavaScript "Array.from(document.querySelectorAll('a,button')).map(x => x.innerText.trim()).filter(x => x.length > 0 && x.length < 40).join(' | ')"
                    return res
                end tell
            end if
        end repeat
    end repeat
    return "NONE"
end tell
'''

if __name__ == "__main__":
    r = subprocess.run(["osascript", "-e", APPLE], capture_output=True, text=True)
    print("OUT:", r.stdout.strip())
    print("ERR:", r.stderr.strip())
