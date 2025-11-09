#!/bin/bash
# -----------------------------------------------
# update-schema.sh
# Oppdaterer schema-filer basert på sitemap.
# -----------------------------------------------

BASE_DIR="$(cd "$(dirname "$0")" && pwd)"
SITEMAP_URL="https://energyflow-cosmology.com/sitemap.xml"
OUTPUT_JSON="$BASE_DIR/sitemap-links.json"

echo "🔄 Henter sitemap fra $SITEMAP_URL ..."
curl -s "$SITEMAP_URL" \
  | grep -Eo '<loc>[^<]+' \
  | sed 's/<loc>//' \
  | jq -R . | jq -s . > "$OUTPUT_JSON"

echo "✅ Lagret sitemap-links.json med $(jq length "$OUTPUT_JSON") lenker."
git -C "$BASE_DIR/.." add schema/
git -C "$BASE_DIR/.." commit -m "Auto-update sitemap-links.json"
git -C "$BASE_DIR/.." push

