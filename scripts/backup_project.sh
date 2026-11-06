#!/usr/bin/env bash
# ==============================================================================
# SYNAX Automatic Project Backup Utility
# ==============================================================================
# Creates an authenticated, timestamped snapshot archive of the SYNAX codebase
# in ~/synax_backups/ with SHA-256 integrity verification.
# ==============================================================================

set -euo pipefail

WORKSPACE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BACKUP_DIR="${HOME}/synax_backups"
TIMESTAMP="$(date +"%Y%m%d_%H%M%S")"
ARCHIVE_NAME="synax_backup_${TIMESTAMP}.tar.gz"
ARCHIVE_PATH="${BACKUP_DIR}/${ARCHIVE_NAME}"
CHECKSUM_PATH="${ARCHIVE_PATH}.sha256"

mkdir -p "${BACKUP_DIR}"

echo "======================================================================"
echo "🧬 SYNAX Otomatik Proje Yedekleme Sistemi"
echo "======================================================================"
echo "Kaynak Dizin  : ${WORKSPACE_DIR}"
echo "Hedef Dizin   : ${BACKUP_DIR}"
echo "Yedek Dosyası : ${ARCHIVE_NAME}"
echo "Zaman Damgası : ${TIMESTAMP}"
echo "----------------------------------------------------------------------"

# Tarball oluştur (geçici dosyalar hariç)
tar -czf "${ARCHIVE_PATH}" \
    --exclude=".git/logs" \
    --exclude="**/__pycache__" \
    --exclude="**/*.pyc" \
    --exclude="*.swp" \
    -C "$(dirname "${WORKSPACE_DIR}")" "$(basename "${WORKSPACE_DIR}")"

# SHA-256 sağlamasını üret
if command -v shasum >/dev/null 2>&1; then
    shasum -a 256 "${ARCHIVE_PATH}" > "${CHECKSUM_PATH}"
else
    sha256sum "${ARCHIVE_PATH}" > "${CHECKSUM_PATH}"
fi

FILE_SIZE="$(du -h "${ARCHIVE_PATH}" | cut -f1)"
SHA_DIGEST="$(awk '{print $1}' "${CHECKSUM_PATH}")"

echo "✓ Yedekleme başarıyla tamamlandı!"
echo "  Boyut       : ${FILE_SIZE}"
echo "  SHA-256     : ${SHA_DIGEST}"
echo "  Konum       : ${ARCHIVE_PATH}"
echo "----------------------------------------------------------------------"
echo "Mevcut Yerel Yedekler (${BACKUP_DIR}):"
ls -lh "${BACKUP_DIR}"/synax_backup_*.tar.gz 2>/dev/null | tail -n 5
echo "======================================================================"
