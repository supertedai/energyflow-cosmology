
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
  | tr -d '\n' \
  | sed 's/<loc>/\n<loc>/g' \
  | grep '<loc>' \
  | sed -E 's/.*<loc>([^<]+)<\/loc>.*/\1/' \
  | jq -R . | jq -s . > "$OUTPUT_JSON"


echo "✅ Lagret sitemap-links.json med $(jq length "$OUTPUT_JSON") lenker."

# Commit & push hvis det er endringer
cd "$BASE_DIR/.."
git add "$OUTPUT_JSON" >/dev/null 2>&1
if ! git diff --cached --quiet; then
  git commit -m "Auto-update sitemap-links.json"
  git push
else
  echo "ℹ️  Ingen endringer å pushe."
fi

