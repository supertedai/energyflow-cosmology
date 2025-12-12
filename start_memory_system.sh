#!/bin/bash
# Quick start script for Symbiosis Memory System

echo "🚀 Starting Symbiosis Memory System"
echo "=" * 60

# Check if API is already running
if lsof -ti:8000 > /dev/null 2>&1; then
    echo "⚠️  API already running on port 8000"
    echo "   Restarting..."
    lsof -ti:8000 | xargs kill -9 2>/dev/null
    sleep 2
fi

# Start API
echo "🔧 Starting Backend API..."
cd apis/unified_api
python -m uvicorn main:app --port 8000 > /tmp/symbiosis_api.log 2>&1 &
cd ../..

# Wait for API to start
sleep 5

if lsof -ti:8000 > /dev/null 2>&1; then
    echo "✅ Backend API running on http://localhost:8000"
else
    echo "❌ Failed to start API"
    echo "   Check logs: tail -f /tmp/symbiosis_api.log"
    exit 1
fi

echo
echo "✅ System ready!"
echo
echo "📋 Next steps:"
echo "   1. Configure LM Studio with MCP config from MEMORY_SYSTEM_PRODUCTION.md"
echo "   2. Restart LM Studio"
echo "   3. Test: Ask 'Hva heter jeg?' (should answer: 'Du heter Morten')"
echo
echo "📊 Test API directly:"
echo "   curl -X POST http://localhost:8000/chat/turn \\"
echo "     -H 'Content-Type: application/json' \\"
echo "     -d '{\"user_message\": \"Hva heter jeg?\", \"assistant_draft\": \"Jeg vet ikke\"}'"
echo
echo "🛑 To stop: kill \$(lsof -ti:8000)"
echo
