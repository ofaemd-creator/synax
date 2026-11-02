#!/bin/sh
# =============================================================================
# SYNAXCODE.COM — Official Sovereign Installer (v2.0-AUTOPOIESIS)
# Usage: curl -fsSL https://synaxcode.com/install.sh | sh
# =============================================================================
set -e

BOLD="\033[1m"
GREEN="\033[0;32m"
CYAN="\033[0;36m"
YELLOW="\033[0;33m"
RESET="\033[0m"

printf "${BOLD}${GREEN}⚡ SYNAX (v2.0-AUTOPOIESIS) — Sovereign Zero-Trust Installer [synaxcode.com]${RESET}\n"
printf "${CYAN}   [Synapse: Self-Evolving AST] + [Axon: Tier-0..5 Silicon] + [Tycon: RLSF Mutator]${RESET}\n\n"

OS="$(uname -s)"
ARCH="$(uname -m)"
SYNAX_HOME="${HOME}/.synax"
BIN_DIR="${SYNAX_HOME}/bin"
SRC_URL="https://synaxcode.org/src"

printf "🔍 Detecting hardware nerve profile...\n"
printf "   • OS           : ${BOLD}${OS}${RESET}\n"
printf "   • Architecture : ${BOLD}${ARCH}${RESET}\n"

mkdir -p "${BIN_DIR}" "${SYNAX_HOME}/src"

if command -v clang >/dev/null 2>&1; then
    printf "   • Native Backend: ${GREEN}LLVM/Clang Detected (Tier-0 Q16.16, SIMD & GPU Ready)${RESET}\n"
elif command -v gcc >/dev/null 2>&1; then
    printf "   • Native Backend: ${GREEN}GCC Detected${RESET}\n"
else
    printf "   • Native Backend: ${YELLOW}No C compiler found (AST Fallback mode)${RESET}\n"
fi

printf "\n🧬 Downloading SYNAX v2.0 Core from Sovereign Forge (${SRC_URL})...\n"

# Pinned SHA-256 checksums: installation aborts if any file does not match.
CHECKSUMS="91c4fc2b9ab3244084d25a06e9143eb9b06c33f1200f5b711e22cc96219b3816  synax_security.py
6446a8fe0fddab8dca602cf57d2f84ca7a2ac3dab6e4a9ced6741ccaf3fc13ae  synapse_neural_model.py
741552b6876a5a252d56573fffc1732130cdd73e789c2b311d327cb66987afbb  synax_autopoiesis.py
bbd1010524a69d148011c0fbe4e7ef2ac338a1d4df4773fd4ce280bdaff877cb  synax_core.py
3f5379f9b1e97934abf46c70cd8d0cf1fcc855822fdd2138de403803cdfda73c  synaxc.py
e7a880f5782368f5e63649a10a554c378386a32714fdb5375da72a3fcde05fcd  synapse_brain.json
cdfb9a370752345d6cc32321285c3724eaf378b6d227c66f6092e26f44cf41bd  synapse_weights.json"

if command -v shasum >/dev/null 2>&1; then
    SHA_CMD="shasum -a 256"
elif command -v sha256sum >/dev/null 2>&1; then
    SHA_CMD="sha256sum"
else
    printf "${YELLOW}✗ No SHA-256 tool found (shasum/sha256sum). Aborting for safety.${RESET}\n"
    exit 1
fi

echo "${CHECKSUMS}" | while read -r expected f; do
    curl -fsSL "${SRC_URL}/${f}" -o "${SYNAX_HOME}/src/${f}"
    actual="$(${SHA_CMD} "${SYNAX_HOME}/src/${f}" | awk '{print $1}')"
    if [ "${actual}" != "${expected}" ]; then
        printf "${YELLOW}✗ Checksum mismatch for ${f}. Removing and aborting.${RESET}\n"
        rm -f "${SYNAX_HOME}/src/${f}"
        exit 1
    fi
    printf "   ✓ ${f}\n"
done

cat << 'EOF' > "${BIN_DIR}/synax"
#!/bin/sh
exec python3 "$HOME/.synax/src/synaxc.py" "$@"
EOF
chmod +x "${BIN_DIR}/synax"

printf "${GREEN}✓ SYNAX v2.0-AUTOPOIESIS installed successfully!${RESET}\n\n"
printf "Add SYNAX to your PATH:\n"
printf "  ${BOLD}export PATH=\"\$HOME/.synax/bin:\$PATH\"${RESET}\n\n"
printf "🌐 Sovereign Code Forge : ${BOLD}https://synaxcode.org/repos.html${RESET}\n"
printf "🌐 Live Cloud Studio IDE: ${BOLD}https://synaxcode.online${RESET}\n"
