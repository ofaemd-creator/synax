#!/usr/bin/env python3
"""
SYNAX Sovereign Founder Credential Provisioner (v7.2)
=====================================================
Generates the founder-only credentials LOCALLY and never prints secrets.

Outputs (both chmod 600, outside the git repo):
  ~/.synax/sovereign_credentials.json   -> passkey, TOTP secret, otpauth URI (YOU keep this)
  ~/.synax/.synax_sovereign.php         -> server-side verifier material (PBKDF2 hash only,
                                           NOT the plaintext passkey) uploaded to Hostinger

Use --rotate to invalidate everything and issue brand-new credentials.
"""
import base64
import hashlib
import json
import os
import secrets
import sys
from pathlib import Path

HOME = Path.home() / ".synax"
CRED = HOME / "sovereign_credentials.json"
PHP = HOME / ".synax_sovereign.php"
ITER = 250000


def write_private(path: Path, text: str) -> None:
    HOME.mkdir(parents=True, exist_ok=True)
    fd = os.open(str(path), os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(fd, "w") as f:
        f.write(text)
    os.chmod(path, 0o600)


def main() -> int:
    rotate = "--rotate" in sys.argv
    if CRED.exists() and not rotate:
        cred = json.loads(CRED.read_text())
        print("Mevcut kurucu kimlik bilgileri korunuyor (yenilemek için --rotate).")
    else:
        passkey = secrets.token_urlsafe(18)
        totp_secret = base64.b32encode(os.urandom(20)).decode()
        cred = {
            "founder": "Dr. Omer Faruk Aydin (@ofaemd-creator)",
            "passkey": passkey,
            "totp_secret_base32": totp_secret,
            "totp_otpauth_uri": f"otpauth://totp/SYNAX:Founder?secret={totp_secret}&issuer=SYNAX&digits=6&period=30",
            "pbkdf2_salt": secrets.token_hex(16),
            "session_secret": secrets.token_hex(32),
        }
        write_private(CRED, json.dumps(cred, indent=2))
        print("Yeni kurucu kimlik bilgileri üretildi.")

    digest = hashlib.pbkdf2_hmac(
        "sha256", cred["passkey"].encode(), cred["pbkdf2_salt"].encode(), ITER, 32
    ).hex()
    php = (
        "<?php\n"
        f"$sovereign_pass_salt = '{cred['pbkdf2_salt']}';\n"
        f"$sovereign_pass_hash = '{digest}';\n"
        f"$sovereign_totp_secret = '{cred['totp_secret_base32']}';\n"
        f"$sovereign_session_secret = '{cred['session_secret']}';\n"
    )
    write_private(PHP, php)
    write_private(HOME / "empty.json", "{}")
    print(f"Kimlik dosyası : {CRED}  (chmod 600)")
    print(f"Sunucu doğrulayıcı: {PHP}  (yalnızca PBKDF2 özeti, düz şifre yok)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
