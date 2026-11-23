#!/usr/bin/env python3
"""Deploys the v7.2 barrier: sovereign verifier file first, then api.php / chat.html, then neutralises the legacy public JSON."""
from pathlib import Path

from scripts.chrome_hostinger_deploy import ensure_file_manager_tab, upload_file_famulus

HOME = Path.home() / ".synax"
S = Path("sites")
DIRS = [
    "/domains/synaxcode.com/public_html",
    "/domains/synaxcode.org/public_html",
    "/domains/synaxcode.online/public_html",
    "/domains/synaxcode.com/public_html/chat",
    "/domains/synaxcode.com/public_html/office",
    "/domains/synaxcode.com/public_html/code",
    "/domains/synaxcode.com/public_html/terminal",
]
HTML_TARGETS = [
    "/domains/synaxcode.com/public_html/chat.html",
    "/domains/synaxcode.org/public_html/chat.html",
    "/domains/synaxcode.online/public_html/chat.html",
    "/domains/synaxcode.com/public_html/chat/index.html",
    "/domains/synaxcode.com/public_html/chat/chat.html",
]

ensure_file_manager_tab()
for d in DIRS:                       # 1) verifier material first (fail-closed until present)
    upload_file_famulus(f"{d}/.synax_sovereign.php", HOME / ".synax_sovereign.php")
for d in DIRS:                       # 2) new api.php
    upload_file_famulus(f"{d}/api.php", S / "api.php")
for t in HTML_TARGETS:               # 3) sanitized public UI
    upload_file_famulus(t, S / "chat_index.html")
upload_file_famulus("/domains/synaxcode.com/public_html/telegram_webhook.php", S / "telegram_webhook.php")
for d in DIRS:                       # 4) wipe legacy publicly-downloadable memory file
    upload_file_famulus(f"{d}/synax_memory_cortex.json", HOME / "empty.json")
print("DEPLOY_V72_DONE")
