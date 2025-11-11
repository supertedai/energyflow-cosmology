#!/bin/bash
# -----------------------------------------------
# update-schema.sh
# Henter sitemap fra energyflow-cosmology.com
# og konverterer alle <loc>-lenker til JSON-format.
# Feiler ikke dersom sitemap ikke kan lastes.
# -----------------------------------------------

set -euo pipefail

BASE_DIR="$(cd "$(dirname "$0")" && pwd)"
SITEMAP_URL="https://energyflow-cosmology.com/sitemap.xml"
OUTPUT_JSON="$BASE_DIR/sitemap-links.json"

echo "🔄 Henter sitemap fra $SITEMAP_URL ..."

# Sjekk at jq finnes
if ! command -v jq >/dev/null 2>&1; then
  echo "❌ jq er ikke installert. Installer med: sudo apt-get install -y jq"
  exit 0
fi

# Forsøk å hente sitemap
if curl -fsSL -L "$SITEMAP_URL" -o /tmp/sitemap.xml; then
  echo "📦 Sitemap lastet ned, konverterer til JSON ..."
  grep -oP '(?<=<loc>)[^<]+' /tmp/sitemap.xml \
    | jq -R . | jq -s . > "$OUTPUT_JSON"

  COUNT=$(jq length "$OUTPUT_JSON")
  echo "✅ Lagret sitemap-links.json med $COUNT lenker."
else
  echo "⚠️  Kunne ikke hente sitemap fra $SITEMAP_URL — hopper over oppdatering."
  exit 0  # Ikke feil, lar GitHub Actions fullføre uten stopp
fi
