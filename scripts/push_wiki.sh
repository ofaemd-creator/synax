#!/bin/zsh
# Pushes all markdown pages in ./wiki/ to https://github.com/ofaemd-creator/synax.wiki.git
set -e
REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
TMP_WIKI="/tmp/synax_wiki_push_$$"
rm -rf "$TMP_WIKI"

echo "📚 Cloning https://github.com/ofaemd-creator/synax.wiki.git ..."
if ! git clone https://github.com/ofaemd-creator/synax.wiki.git "$TMP_WIKI"; then
  echo "⚠️  GitHub Wiki git deposu henüz GitHub web arayüzünde başlatılmamış."
  echo "👉 Lütfen tarayıcıda https://github.com/ofaemd-creator/synax/wiki adresine gidip"
  echo "   bir kez 'Create the first page' -> 'Save Page' butonuna tıklayın, ardından bu betiği tekrar çalıştırın:"
  echo "   ./scripts/push_wiki.sh"
  exit 1
fi

cp -f "$REPO_ROOT"/wiki/*.md "$TMP_WIKI"/
cd "$TMP_WIKI"
git add -A
if git diff --cached --quiet; then
  echo "✓ Wiki zaten güncel."
else
  git commit -m "docs(wiki): publish complete SYNAX v1.0.0 Wiki (Language, E-Graph, Formal Prover, Studio App, Ecosystem)"
  git push origin master || git push origin main
  echo "🎉 GitHub Wiki başarıyla güncellendi: https://github.com/ofaemd-creator/synax/wiki"
fi
rm -rf "$TMP_WIKI"
