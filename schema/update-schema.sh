#!/bin/bash
# -----------------------------------------------
# update-schema.sh
# Oppdaterer schema-filer basert på sitemap.xml
# -----------------------------------------------

set -euo pipefail

BASE_DIR="$(cd "$(dirname "$0")" && pwd)"
SITEMAP_URL="https://energyflow-cosmology.com/sitemap.xml"
OUTPUT_JSON="$BASE_DIR/sitemap-links.json"

echo "🔄 Henter sitemap fra $SITEMAP_URL ..."

# Sjekk at jq finnes
if ! command -v jq >/dev/null 2>&1; then
  echo "❌ jq er ikke installert. Installer med: brew install jq"
  exit 1
fi

# Hent og prosesser sitemap
if curl -fsSL "$SITEMAP_URL" -o /tmp/sitemap.xml; then
  grep -oP '(?<=<loc>)[^<]+' /tmp/sitemap.xml \
    | jq -R . | jq -s . > "$OUTPUT_JSON"
  COUNT=$(jq length "$OUTPUT_JSON")
  echo "✅ Lagret sitemap-links.json med $COUNT lenker."
else
  echo "❌ Kunne ikke hente sitemap fra $SITEMAP_URL"
  exit 1
fi

# Commit og push bare hvis det er endringer
cd "$BASE_DIR/.."
git add "$OUTPUT_JSON" >/dev/null 2>&1
if ! git diff --cached --quiet; then
  git commit -m "Auto-update sitemap-links.json"
  git push
  echo "🚀 Endringer pushet til GitHub."
else
  echo "ℹ️ Ingen endringer å pushe."
fi
