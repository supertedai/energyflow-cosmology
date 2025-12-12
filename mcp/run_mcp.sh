#!/bin/bash
# MCP Server Wrapper with logging

export PYTHONPATH="/Users/morpheus/energyflow-cosmology"
export SYMBIOSIS_API_URL="http://localhost:8000"

cd /Users/morpheus/energyflow-cosmology

# Log startup
echo "$(date): Starting MCP server" >> /tmp/mcp_debug.log
echo "  PWD: $(pwd)" >> /tmp/mcp_debug.log
echo "  PYTHONPATH: $PYTHONPATH" >> /tmp/mcp_debug.log
echo "  SYMBIOSIS_API_URL: $SYMBIOSIS_API_URL" >> /tmp/mcp_debug.log

# Run the server
exec /Users/morpheus/energyflow-cosmology/.venv/bin/python /Users/morpheus/energyflow-cosmology/mcp/symbiosis_mcp_server_v5_minimal.py 2>> /tmp/mcp_debug.log
