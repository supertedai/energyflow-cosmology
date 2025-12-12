#!/bin/bash
# Cleanup old/unused versions - Keep only active code

echo "🧹 Cleaning up old versions..."
echo

# Create archive directory for old versions
mkdir -p archive/old_versions/mcp
mkdir -p archive/old_versions/tools

# MCP: Keep v5_minimal and v6_efc, archive rest
echo "📦 Archiving old MCP versions..."
mv mcp/symbiosis_mcp_server_v3.py archive/old_versions/mcp/ 2>/dev/null && echo "  ✅ Archived v3"
mv mcp/symbiosis_mcp_server_v4_backend_proxy.py archive/old_versions/mcp/ 2>/dev/null && echo "  ✅ Archived v4"
mv mcp/test_*.py archive/old_versions/mcp/ 2>/dev/null && echo "  ✅ Archived test files"

# Tools: Keep v4 router, archive old routers
echo "📦 Archiving old router versions..."
mv tools/symbiosis_router_v2.py archive/old_versions/tools/ 2>/dev/null && echo "  ✅ Archived router v2"
mv tools/symbiosis_router_v3.py archive/old_versions/tools/ 2>/dev/null && echo "  ✅ Archived router v3"

# Archive old memory/domain versions
echo "📦 Archiving old memory versions..."
mv tools/domain_engine_v2.py archive/old_versions/tools/ 2>/dev/null && echo "  ✅ Archived domain_engine_v2"
mv tools/memory_classifier_v2.py archive/old_versions/tools/ 2>/dev/null && echo "  ✅ Archived memory_classifier_v2"
mv tools/memory_model_v3.py archive/old_versions/tools/ 2>/dev/null && echo "  ✅ Archived memory_model_v3"

echo
echo "✅ Cleanup complete!"
echo
echo "Active versions kept:"
echo "  MCP: v5_minimal.py, v6_efc.py"
echo "  Router: symbiosis_router_v4.py"
echo "  Memory: optimal_memory_system.py (9 layers)"
echo
echo "Archived to: archive/old_versions/"
