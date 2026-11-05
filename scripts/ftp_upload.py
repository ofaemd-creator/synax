#!/usr/bin/env python3
"""
SYNAX Automated FTP / SFTP Deployment Script (`scripts/ftp_upload.py`)
=====================================================================
Uploads updated production files (dashboard.html, synax_beacon.js, index.html)
directly to Hostinger / Remote Web Server via FTP.

Usage:
    python3 scripts/ftp_upload.py --host <FTP_HOST> --user <FTP_USER> --password <FTP_PASS> [--site synaxcode.com]
Or via environment variables:
    FTP_HOST=... FTP_USER=... FTP_PASS=... python3 scripts/ftp_upload.py
"""

import argparse
import ftplib
import os
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DEPLOY_BASE = BASE_DIR / "releases" / "hostinger_production_deploy"


def upload_directory_ftp(ftp: ftplib.FTP, local_dir: Path, remote_dir: str = "public_html") -> None:
    """Recursively uploads a local directory to an FTP server."""
    print(f"📁 Uzak dizine geçiliyor: {remote_dir}")
    try:
        ftp.cwd(remote_dir)
    except ftplib.error_perm:
        try:
            ftp.mkd(remote_dir)
            ftp.cwd(remote_dir)
        except Exception as e:
            print(f"Dizin oluşturulamadı: {remote_dir} ({e})")
            return

    for item in local_dir.iterdir():
        if item.name.startswith("."):
            continue
        if item.is_file():
            print(f"  ⬆️ Yükleniyor: {item.name} ({item.stat().st_size} bayt)...", end=" ", flush=True)
            with open(item, "rb") as f:
                ftp.storbinary(f"STOR {item.name}", f)
            print("✓ Tamamlandı")
        elif item.is_dir():
            upload_directory_ftp(ftp, item, item.name)
            ftp.cwd("..")


def main() -> None:
    ap = argparse.ArgumentParser(description="SYNAX Production FTP Uploader")
    ap.add_argument("--host", default=os.getenv("FTP_HOST", ""), help="FTP Host (örn: ftp.synaxcode.com veya Hostinger IP)")
    ap.add_argument("--user", default=os.getenv("FTP_USER", ""), help="FTP Kullanıcı Adı")
    ap.add_argument("--password", default=os.getenv("FTP_PASS", ""), help="FTP Parolası")
    ap.add_argument("--port", type=int, default=int(os.getenv("FTP_PORT", 21)), help="FTP Portu (varsayılan: 21)")
    ap.add_argument("--site", default="synaxcode.com", choices=["synaxcode.com", "synaxcode.org", "synaxcode.online", "all"], help="Yüklenecek site")
    args = ap.parse_args()

    if not args.host or not args.user or not args.password:
        print("=" * 70)
        print("⚠️  FTP BİLGİLERİ GEREKLİ")
        print("=" * 70)
        print("Otomatik yükleme için FTP bağlantı bilgilerini parametre olarak verebilirsiniz:")
        print("  python3 scripts/ftp_upload.py --host <FTP_HOST> --user <FTP_USER> --password <SIFRE>")
        print("\nAlternatif olarak Hostinger Dosya Yöneticisi (Chrome) açık olduğundan:")
        print("  1. 'public_html' klasörüne doğrudan şu dosyaları sürükleyip bırakabilirsiniz:")
        print(f"     - {BASE_DIR}/sites/dashboard.html")
        print(f"     - {BASE_DIR}/sites/synax_beacon.js")
        print(f"     - {BASE_DIR}/sites/com_index.html (index.html olarak)")
        print("\n  2. Veya hazır ZIP arşivini yükleyip tek tıkla 'Extract' yapabilirsiniz:")
        print(f"     - {BASE_DIR}/releases/DASHBOARD_AND_BEACON_UPDATE.zip (Yalnızca 14 KB)")
        print(f"     - {BASE_DIR}/releases/synaxcode.com_public_html.zip")
        print("=" * 70)
        sys.exit(1)

    print(f"🔌 FTP Sunucusuna Bağlanılıyor: {args.host}:{args.port} ({args.user})...")
    try:
        ftp = ftplib.FTP()
        ftp.connect(args.host, args.port, timeout=30)
        ftp.login(args.user, args.password)
        print(f"✓ Başarıyla giriş yapıldı: {ftp.getwelcome()}")

        sites_to_deploy = ["synaxcode.com", "synaxcode.org", "synaxcode.online"] if args.site == "all" else [args.site]
        for s in sites_to_deploy:
            local_pub = DEPLOY_BASE / s / "public_html"
            print(f"\n🚀 {s} Dağıtımı Başlatılıyor...")
            upload_directory_ftp(ftp, local_pub, "public_html")
            print(f"🎉 {s} Başarıyla Güncellendi!")

        ftp.quit()
        print("\n✅ Tüm dosyalar FTP sunucusuna başarıyla yüklendi!")
    except Exception as exc:
        print(f"\n✗ FTP Yükleme Hatası: {exc}", file=sys.stderr)
        sys.exit(2)


if __name__ == "__main__":
    main()
