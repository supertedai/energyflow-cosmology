#!/usr/bin/env python3
"""
Simple Cognitive Monitor - Viser live data fra Backend API
"""
from fastapi import FastAPI
from fastapi.responses import HTMLResponse
import uvicorn
import httpx

app = FastAPI()

HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>🧠 Cognitive Monitor</title>
    <meta charset="UTF-8">
    <style>
        body {
            font-family: 'Monaco', monospace;
            background: #0a0a1a;
            color: #00ff88;
            padding: 20px;
        }
        .container { max-width: 1200px; margin: 0 auto; }
        h1 { color: #00d4ff; }
        .card {
            background: rgba(0,212,255,0.1);
            border: 1px solid #00d4ff;
            padding: 15px;
            margin: 10px 0;
            border-radius: 5px;
        }
        .status { font-size: 24px; margin: 10px 0; }
        pre { background: #000; padding: 10px; overflow-x: auto; }
    </style>
    <script>
        async function updateStatus() {
            try {
                const resp = await fetch('/api/backend');
                const data = await resp.json();
                document.getElementById('status').innerHTML = `
                    <div class="card">
                        <h2>🎯 Intent</h2>
                        <p>Mode: ${data.intent?.mode || 'N/A'}</p>
                        <p>Domains: ${JSON.stringify(data.intent?.active_domains || [])}</p>
                    </div>
                    <div class="card">
                        <h2>💎 Value</h2>
                        <p>Level: ${data.value?.value_level || 'N/A'}</p>
                        <p>Harm: ${data.value?.harm_detected || false}</p>
                    </div>
                    <div class="card">
                        <h2>🎚️ Routing</h2>
                        <p>Override: ${data.routing?.canonical_override_strength || 0}</p>
                        <p>LLM Temp: ${data.routing?.llm_temperature || 0.7}</p>
                    </div>
                    <div class="card">
                        <h2>📊 Meta</h2>
                        <p>Turn: ${data.meta?.turn_count || 0}</p>
                        <p>Last: ${data.meta?.last_user_message || 'None'}</p>
                        <p>Override: ${data.meta?.was_overridden || false}</p>
                    </div>
                    <div class="card">
                        <h2>🔍 Raw Data</h2>
                        <pre>${JSON.stringify(data, null, 2)}</pre>
                    </div>
                `;
            } catch (e) {
                document.getElementById('status').innerHTML = 
                    '<div class="card" style="border-color:red;"><p>❌ Backend error: ' + e + '</p></div>';
            }
        }
        
        setInterval(updateStatus, 2000);
        updateStatus();
    </script>
</head>
<body>
    <div class="container">
        <h1>🧠 Cognitive Monitor (Live)</h1>
        <p>Updates every 2 seconds from http://localhost:8000/chat/cognitive/status</p>
        <div id="status">Loading...</div>
    </div>
</body>
</html>
"""

@app.get("/", response_class=HTMLResponse)
async def root():
    return HTML

@app.get("/api/backend")
async def get_backend():
    """Proxy to backend cognitive status"""
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get("http://localhost:8000/chat/cognitive/status", timeout=5.0)
            data = resp.json()
            return data.get("cognitive_context", {})
    except Exception as e:
        return {"error": str(e)}

if __name__ == "__main__":
    print("\n🧠 Starting Simple Cognitive Monitor...")
    print("📡 Open http://localhost:8080\n")
    uvicorn.run(app, host="0.0.0.0", port=8080)
