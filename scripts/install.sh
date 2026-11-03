#!/usr/bin/env sh
# =============================================================================
# SYNAX Official Installer (macOS & Linux — ARM64 / x86_64)
# SPDX-License-Identifier: Apache-2.0
#
# Usage:
#   curl -fsSL https://raw.githubusercontent.com/ofaemd-creator/synax/main/scripts/install.sh | sh
#   SYNAX_VERSION=v0.5.0 sh scripts/install.sh
# =============================================================================
set -eu

REPO="ofaemd-creator/synax"
INSTALL_PREFIX="${SYNAX_INSTALL_DIR:-$HOME/.local}"
BIN_DIR="$INSTALL_PREFIX/bin"
LIB_DIR="$INSTALL_PREFIX/lib"
INCLUDE_DIR="$INSTALL_PREFIX/include"
VERSION="${SYNAX_VERSION:-latest}"

log() {
    printf "\033[1;36m[SYNAX]\033[0m %s\n" "$1"
}

err() {
    printf "\033[1;31m[SYNAX ERROR]\033[0m %s\n" "$1" >&2
    exit 1
}

detect_platform() {
    OS_RAW="$(uname -s)"
    ARCH_RAW="$(uname -m)"

    case "$OS_RAW" in
        Darwin) OS="macos" ;;
        Linux)  OS="linux" ;;
        *)      err "Unsupported OS: $OS_RAW (use pip install synax or Windows release zip)" ;;
    esac

    case "$ARCH_RAW" in
        arm64|aarch64) ARCH="arm64" ;;
        x86_64|amd64)  ARCH="x86_64" ;;
        *)             err "Unsupported CPU architecture: $ARCH_RAW" ;;
    esac

    ASSET_TAR="synax-${OS}-${ARCH}.tar.gz"
}

verify_sha256() {
    FILE_PATH="$1"
    SUMS_PATH="$2"
    EXPECTED="$(grep "$(basename "$FILE_PATH")" "$SUMS_PATH" | awk '{print $1}')"
    if [ -z "$EXPECTED" ]; then
        err "Checksum entry for $(basename "$FILE_PATH") not found in SHA256SUMS.txt"
    fi

    if command -v shasum >/dev/null 2>&1; then
        ACTUAL="$(shasum -a 256 "$FILE_PATH" | awk '{print $1}')"
    elif command -v sha256sum >/dev/null 2>&1; then
        ACTUAL="$(sha256sum "$FILE_PATH" | awk '{print $1}')"
    else
        err "Neither shasum nor sha256sum found; refusing unverified binary installation."
    fi

    if [ "$EXPECTED" != "$ACTUAL" ]; then
        err "SHA-256 mismatch! Expected $EXPECTED, got $ACTUAL"
    fi
    log "SHA-256 cryptographic checksum verified ($ACTUAL)"
}

install_from_release() {
    detect_platform
    TMP_DIR="$(mktemp -d)"
    trap 'rm -rf "$TMP_DIR"' EXIT INT TERM

    if [ "$VERSION" = "latest" ]; then
        BASE_URL="https://github.com/${REPO}/releases/latest/download"
    else
        BASE_URL="https://github.com/${REPO}/releases/download/${VERSION}"
    fi

    log "Detected platform: ${OS}-${ARCH}"
    log "Attempting binary release download from ${BASE_URL}/${ASSET_TAR} ..."

    if curl -fsSL "${BASE_URL}/${ASSET_TAR}" -o "${TMP_DIR}/${ASSET_TAR}" 2>/dev/null && \
       curl -fsSL "${BASE_URL}/SHA256SUMS.txt" -o "${TMP_DIR}/SHA256SUMS.txt" 2>/dev/null; then
        verify_sha256 "${TMP_DIR}/${ASSET_TAR}" "${TMP_DIR}/SHA256SUMS.txt"
        mkdir -p "$BIN_DIR" "$LIB_DIR" "$INCLUDE_DIR"
        tar -xzf "${TMP_DIR}/${ASSET_TAR}" -C "${TMP_DIR}"
        if [ -f "${TMP_DIR}/bin/synax" ]; then
            cp "${TMP_DIR}/bin/synax"* "$BIN_DIR/"
            chmod +x "$BIN_DIR/synax"*
        fi
        if [ -d "${TMP_DIR}/lib" ]; then
            cp -R "${TMP_DIR}/lib/"* "$LIB_DIR/" 2>/dev/null || true
        fi
        if [ -d "${TMP_DIR}/include" ]; then
            cp -R "${TMP_DIR}/include/"* "$INCLUDE_DIR/" 2>/dev/null || true
        fi
        log "Installed native release into ${INSTALL_PREFIX}"
        return 0
    fi
    return 1
}

install_from_pip_fallback() {
    log "Release archive not published for ${VERSION} yet; installing via Python pip from GitHub..."
    if ! command -v python3 >/dev/null 2>&1; then
        err "python3 is required for source installation."
    fi
    python3 -m pip install --user --upgrade "git+https://github.com/${REPO}.git"
    log "Installed 'synax' CLI and Python SDK via pip (--user)."
}

main() {
    if ! install_from_release; then
        install_from_pip_fallback
    fi

    log "Installation complete! Verify with: synax version"
}

main "$@"
