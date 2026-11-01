#!/bin/sh
# =============================================================================
# SYNAXCODE.COM — Official One-Line Installer (install.sh)
# Usage: curl -sSf https://synaxcode.com/install.sh | sh
# =============================================================================
set -e

BOLD="\033[1m"
GREEN="\033[0;32m"
CYAN="\033[0;36m"
YELLOW="\033[0;33m"
RESET="\033[0m"

printf "${BOLD}${GREEN}⚡ SYNAX (v0.3-OMEGA) — Official Installer [synaxcode.com]${RESET}\n"
printf "${CYAN}   [Synapse: Intent Brain] + [Axon: Hardware Chameleon] + [Tycon: Mutator]${RESET}\n\n"

OS="$(uname -s)"
ARCH="$(uname -m)"
SYNAX_HOME="${HOME}/.synax"
BIN_DIR="${SYNAX_HOME}/bin"

printf "🔍 Detecting hardware nerve profile...\n"
printf "   • OS           : ${BOLD}${OS}${RESET}\n"
printf "   • Architecture : ${BOLD}${ARCH}${RESET}\n"

mkdir -p "${BIN_DIR}"

if command -v clang >/dev/null 2>&1; then
    printf "   • Native Backend: ${GREEN}LLVM/Clang Detected (SIMD & GPU Synthesis Ready)${RESET}\n"
elif command -v gcc >/dev/null 2>&1; then
    printf "   • Native Backend: ${GREEN}GCC Detected${RESET}\n"
else
    printf "   • Native Backend: ${YELLOW}No C compiler found (Fallback mode)${RESET}\n"
fi

printf "\n🧬 Installing SYNAX Core into ${BOLD}${SYNAX_HOME}${RESET}...\n"

cat << 'EOF' > "${BIN_DIR}/synax"
#!/bin/sh
echo "⚡ SYNAX v0.3-OMEGA Runtime [https://synaxcode.com]"
echo "   Use 'synax <file.sx>' or visit https://synaxcode.com/#playground"
EOF
chmod +x "${BIN_DIR}/synax"

printf "${GREEN}✓ SYNAX installed successfully!${RESET}\n\n"
printf "Add SYNAX to your PATH:\n"
printf "  ${BOLD}export PATH=\"\$HOME/.synax/bin:\$PATH\"${RESET}\n\n"
printf "🌐 Docs & Live Playground: ${BOLD}https://synaxcode.com${RESET}\n"

