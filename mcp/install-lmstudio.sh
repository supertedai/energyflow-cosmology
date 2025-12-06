#!/bin/bash

# Symbiosis MCP Server installer for LM Studio
# Kopierer MCP konfigurasjon til LM Studio

set -e

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
CONFIG_FILE="$SCRIPT_DIR/lm-studio-config.json"
LM_STUDIO_CONFIG="$HOME/.lmstudio/mcp-config.json"

echo "🔧 Symbiosis MCP Server Installer"
echo "=================================="

# Sjekk om LM Studio config finnes
if [ ! -d "$HOME/.lmstudio" ]; then
    echo "📁 Oppretter LM Studio konfigurasjonsmappen..."
    mkdir -p "$HOME/.lmstudio"
fi

# Backup eksisterende config
if [ -f "$LM_STUDIO_CONFIG" ]; then
    echo "💾 Backup av eksisterende konfigurasjon..."
    cp "$LM_STUDIO_CONFIG" "$LM_STUDIO_CONFIG.backup.$(date +%Y%m%d_%H%M%S)"
    
    # Merge med eksisterende config
    if command -v jq &> /dev/null; then
        echo "🔀 Merger med eksisterende konfigurasjon..."
        jq -s '.[0] * .[1]' "$LM_STUDIO_CONFIG" "$CONFIG_FILE" > "$LM_STUDIO_CONFIG.tmp"
        mv "$LM_STUDIO_CONFIG.tmp" "$LM_STUDIO_CONFIG"
    else
        echo "⚠️  jq ikke funnet - overskriver eksisterende konfigurasjon"
        cp "$CONFIG_FILE" "$LM_STUDIO_CONFIG"
    fi
else
    echo "📝 Oppretter ny LM Studio konfigurasjon..."
    cp "$CONFIG_FILE" "$LM_STUDIO_CONFIG"
fi

echo ""
echo "✅ Installasjon fullført!"
echo ""
echo "📋 Neste steg:"
echo "1. Start Symbiosis API: python apis/unified_api/main.py"
echo "2. Restart LM Studio for å laste inn MCP server"
echo "3. Sjekk at 'symbiosis' vises i LM Studio sin tool-liste"
echo ""
echo "🔍 Tilgjengelige tools:"
echo "  - symbiosis_vector_search: Søk i vektordatabase"
echo "  - symbiosis_graph_query: Kjør Cypher queries mot Neo4j"
echo "  - symbiosis_hybrid_search: Hybrid Graf+Vektor søk"
echo "  - symbiosis_get_concepts: Hent konsept-grafen"
echo ""
