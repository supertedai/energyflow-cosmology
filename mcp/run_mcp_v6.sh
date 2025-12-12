#!/bin/bash
# MCP Server v6 Auto-Bridge Wrapper

export PYTHONPATH="/Users/morpheus/energyflow-cosmology"
export SYMBIOSIS_API_URL="http://localhost:8000"

cd /Users/morpheus/energyflow-cosmology

# Log startup
echo "$(date): Starting MCP v6 Auto-Bridge" >> /tmp/mcp_v6_debug.log
echo "  PWD: $(pwd)" >> /tmp/mcp_v6_debug.log
echo "  Backend: $SYMBIOSIS_API_URL" >> /tmp/mcp_v6_debug.log

# Run the server
exec /Users/morpheus/energyflow-cosmology/.venv/bin/python /Users/morpheus/energyflow-cosmology/mcp/symbiosis_mcp_server_v6_autobridge.py 2>> /tmp/mcp_v6_debug.log
