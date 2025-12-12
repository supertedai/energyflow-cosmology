#!/usr/bin/env python3
"""Start backend + dashboard og test at alt fungerer."""

import subprocess
import time
import requests
import os
import signal

os.chdir("/Users/morpheus/energyflow-cosmology")

# Kill existing
print("🔄 Stopper gamle prosesser...")
subprocess.run("pkill -9 -f 'uvicorn.*8000' 2>/dev/null", shell=True)
subprocess.run("pkill -9 -f 'web_monitor' 2>/dev/null", shell=True)
time.sleep(1)

# Start backend
print("🚀 Starter backend på port 8000...")
backend = subprocess.Popen(
    ["python", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"],
    cwd="/Users/morpheus/energyflow-cosmology/apis/unified_api",
    stdout=subprocess.DEVNULL,
    stderr=subprocess.DEVNULL
)
print(f"   PID: {backend.pid}")

# Wait for backend
print("⏳ Venter på backend...")
for i in range(10):
    time.sleep(1)
    try:
        r = requests.get("http://localhost:8000/health", timeout=2)
        if r.status_code == 200:
            print("✅ Backend OK!")
            break
    except:
        pass
else:
    print("❌ Backend startet ikke!")
    backend.kill()
    exit(1)

# Start dashboard
print("🚀 Starter dashboard på port 8080...")
dashboard = subprocess.Popen(
    ["python", "web_monitor_dashboard.py"],
    cwd="/Users/morpheus/energyflow-cosmology",
    stdout=subprocess.DEVNULL,
    stderr=subprocess.DEVNULL
)
print(f"   PID: {dashboard.pid}")

time.sleep(2)

# Test dashboard
print("🧪 Tester dashboard...")
try:
    r = requests.get("http://localhost:8080/api/state", timeout=10)
    data = r.json()
    if "error" in data and data["error"]:
        print(f"❌ Dashboard error: {data['error']}")
    else:
        print("✅ Dashboard får data fra backend!")
        print(f"   Mode: {data.get('cognitive_context', {}).get('intent', {}).get('mode', 'N/A')}")
except Exception as e:
    print(f"❌ Dashboard feil: {e}")

print("\n" + "="*50)
print("🌐 Backend:   http://localhost:8000")
print("🌐 Dashboard: http://localhost:8080")
print("="*50)
print("\nTrykk Ctrl+C for å stoppe...")

try:
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    print("\n🛑 Stopper...")
    backend.kill()
    dashboard.kill()
