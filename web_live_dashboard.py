#!/usr/bin/env python3
"""
🧠 SYMBIOSIS LIVE WEB DASHBOARD
================================
Real-time visualization of the cognitive stack.

Kjør: python web_live_dashboard.py
Åpne: http://localhost:8080
"""

import sys
import os
import json
import asyncio
from datetime import datetime
from typing import Dict, Any

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.chdir(os.path.dirname(os.path.abspath(__file__)))

from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
import uvicorn

# Import cognitive modules
from tools.cognitive_router import CognitiveRouter

app = FastAPI(title="Symbiosis Live Dashboard")

# Initialize router
router = CognitiveRouter()

# HTML Template
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="no">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>🧠 Symbiosis Live Dashboard</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: 'SF Pro Display', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #0a0a1a 0%, #1a1a2e 50%, #16213e 100%);
            color: #e0e0e0;
            min-height: 100vh;
            overflow-x: hidden;
        }
        
        .header {
            background: rgba(0, 0, 0, 0.3);
            backdrop-filter: blur(10px);
            padding: 1rem 2rem;
            border-bottom: 1px solid rgba(255, 255, 255, 0.1);
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        
        .header h1 {
            font-size: 1.5rem;
            background: linear-gradient(90deg, #00d4ff, #7b2cbf);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }
        
        .status-indicator {
            display: flex;
            align-items: center;
            gap: 0.5rem;
        }
        
        .status-dot {
            width: 10px;
            height: 10px;
            border-radius: 50%;
            background: #00ff88;
            animation: pulse 2s infinite;
        }
        
        @keyframes pulse {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.5; }
        }
        
        .container {
            display: grid;
            grid-template-columns: 1fr 2fr;
            gap: 1rem;
            padding: 1rem;
            max-width: 1800px;
            margin: 0 auto;
        }
        
        .input-section {
            background: rgba(255, 255, 255, 0.05);
            border-radius: 12px;
            padding: 1.5rem;
            border: 1px solid rgba(255, 255, 255, 0.1);
        }
        
        .input-section h2 {
            margin-bottom: 1rem;
            font-size: 1.1rem;
            color: #00d4ff;
        }
        
        .input-group {
            margin-bottom: 1rem;
        }
        
        .input-group label {
            display: block;
            margin-bottom: 0.5rem;
            font-size: 0.9rem;
            color: #888;
        }
        
        .input-group textarea, .input-group input {
            width: 100%;
            padding: 0.75rem;
            background: rgba(0, 0, 0, 0.3);
            border: 1px solid rgba(255, 255, 255, 0.1);
            border-radius: 8px;
            color: #fff;
            font-size: 0.95rem;
            resize: vertical;
        }
        
        .input-group textarea:focus, .input-group input:focus {
            outline: none;
            border-color: #00d4ff;
        }
        
        .btn {
            width: 100%;
            padding: 0.75rem;
            background: linear-gradient(90deg, #00d4ff, #7b2cbf);
            border: none;
            border-radius: 8px;
            color: #fff;
            font-size: 1rem;
            font-weight: 600;
            cursor: pointer;
            transition: transform 0.2s, box-shadow 0.2s;
        }
        
        .btn:hover {
            transform: translateY(-2px);
            box-shadow: 0 5px 20px rgba(0, 212, 255, 0.3);
        }
        
        .btn:disabled {
            opacity: 0.5;
            cursor: not-allowed;
        }
        
        .phases-grid {
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 1rem;
        }
        
        .phase-card {
            background: rgba(255, 255, 255, 0.05);
            border-radius: 12px;
            padding: 1rem;
            border: 1px solid rgba(255, 255, 255, 0.1);
            transition: all 0.3s ease;
        }
        
        .phase-card.active {
            border-color: #00d4ff;
            box-shadow: 0 0 20px rgba(0, 212, 255, 0.2);
        }
        
        .phase-card.processing {
            animation: glow 1s ease-in-out infinite;
        }
        
        @keyframes glow {
            0%, 100% { box-shadow: 0 0 10px rgba(0, 212, 255, 0.3); }
            50% { box-shadow: 0 0 30px rgba(0, 212, 255, 0.6); }
        }
        
        .phase-header {
            display: flex;
            align-items: center;
            gap: 0.5rem;
            margin-bottom: 0.75rem;
            padding-bottom: 0.75rem;
            border-bottom: 1px solid rgba(255, 255, 255, 0.1);
        }
        
        .phase-icon {
            font-size: 1.5rem;
        }
        
        .phase-title {
            font-size: 0.9rem;
            font-weight: 600;
        }
        
        .phase-number {
            font-size: 0.7rem;
            background: rgba(255, 255, 255, 0.1);
            padding: 0.2rem 0.5rem;
            border-radius: 4px;
            margin-left: auto;
        }
        
        .phase-content {
            font-size: 0.85rem;
        }
        
        .metric {
            display: flex;
            justify-content: space-between;
            padding: 0.4rem 0;
            border-bottom: 1px solid rgba(255, 255, 255, 0.05);
        }
        
        .metric:last-child {
            border-bottom: none;
        }
        
        .metric-label {
            color: #888;
        }
        
        .metric-value {
            font-weight: 500;
            color: #00d4ff;
        }
        
        .metric-value.high { color: #00ff88; }
        .metric-value.medium { color: #ffbb00; }
        .metric-value.low { color: #ff4757; }
        
        .tag {
            display: inline-block;
            padding: 0.2rem 0.5rem;
            background: rgba(0, 212, 255, 0.2);
            border-radius: 4px;
            font-size: 0.75rem;
            margin: 0.2rem;
        }
        
        .tag.protection { background: rgba(255, 71, 87, 0.2); color: #ff4757; }
        .tag.learning { background: rgba(0, 255, 136, 0.2); color: #00ff88; }
        .tag.identity { background: rgba(123, 44, 191, 0.2); color: #b388ff; }
        
        .progress-bar {
            height: 8px;
            background: rgba(255, 255, 255, 0.1);
            border-radius: 4px;
            overflow: hidden;
            margin-top: 0.5rem;
        }
        
        .progress-fill {
            height: 100%;
            background: linear-gradient(90deg, #00d4ff, #7b2cbf);
            transition: width 0.5s ease;
        }
        
        .routing-section {
            grid-column: span 3;
            background: linear-gradient(135deg, rgba(0, 212, 255, 0.1), rgba(123, 44, 191, 0.1));
            border: 1px solid rgba(0, 212, 255, 0.3);
        }
        
        .routing-grid {
            display: grid;
            grid-template-columns: repeat(5, 1fr);
            gap: 1rem;
            margin-top: 1rem;
        }
        
        .routing-metric {
            text-align: center;
            padding: 1rem;
            background: rgba(0, 0, 0, 0.2);
            border-radius: 8px;
        }
        
        .routing-metric .value {
            font-size: 1.5rem;
            font-weight: 700;
            color: #00d4ff;
        }
        
        .routing-metric .label {
            font-size: 0.75rem;
            color: #888;
            margin-top: 0.25rem;
        }
        
        .recommendations {
            margin-top: 1rem;
            padding: 1rem;
            background: rgba(0, 0, 0, 0.2);
            border-radius: 8px;
        }
        
        .recommendations h4 {
            font-size: 0.9rem;
            margin-bottom: 0.5rem;
            color: #ffbb00;
        }
        
        .recommendations ul {
            list-style: none;
            font-size: 0.85rem;
        }
        
        .recommendations li {
            padding: 0.25rem 0;
            padding-left: 1.5rem;
            position: relative;
        }
        
        .recommendations li::before {
            content: "→";
            position: absolute;
            left: 0;
            color: #00d4ff;
        }
        
        .history {
            margin-top: 1rem;
            max-height: 300px;
            overflow-y: auto;
        }
        
        .history-item {
            padding: 0.75rem;
            background: rgba(0, 0, 0, 0.2);
            border-radius: 8px;
            margin-bottom: 0.5rem;
            font-size: 0.85rem;
        }
        
        .history-item .time {
            font-size: 0.7rem;
            color: #666;
        }
        
        .balance-viz {
            display: flex;
            align-items: center;
            gap: 0.5rem;
            margin-top: 0.5rem;
        }
        
        .balance-bar {
            flex: 1;
            height: 20px;
            background: linear-gradient(90deg, #ff4757 0%, #00d4ff 50%, #00ff88 100%);
            border-radius: 10px;
            position: relative;
        }
        
        .balance-indicator {
            position: absolute;
            width: 4px;
            height: 24px;
            background: #fff;
            border-radius: 2px;
            top: -2px;
            transition: left 0.5s ease;
            box-shadow: 0 0 10px rgba(255, 255, 255, 0.5);
        }
        
        .balance-labels {
            display: flex;
            justify-content: space-between;
            font-size: 0.7rem;
            color: #666;
            margin-top: 0.25rem;
        }
        
        .empty-state {
            text-align: center;
            padding: 2rem;
            color: #666;
        }
        
        .empty-state .icon {
            font-size: 3rem;
            margin-bottom: 1rem;
        }
    </style>
</head>
<body>
    <header class="header">
        <h1>🧠 Symbiosis Cognitive Dashboard</h1>
        <div class="status-indicator">
            <div class="status-dot" id="statusDot"></div>
            <span id="statusText">Tilkoblet</span>
        </div>
    </header>
    
    <div class="container">
        <div class="input-section">
            <h2>💬 Send Melding</h2>
            <div class="input-group">
                <label>Brukermelding</label>
                <textarea id="userMessage" rows="3" placeholder="Skriv en melding...">Hva heter jeg?</textarea>
            </div>
            <div class="input-group">
                <label>Assistentutkast (valgfritt)</label>
                <textarea id="assistantDraft" rows="2" placeholder="LLM-respons å evaluere..."></textarea>
            </div>
            <button class="btn" id="sendBtn" onclick="sendMessage()">
                ⚡ Prosesser gjennom Kognitiv Stakk
            </button>
            
            <div class="history" id="history">
                <h3 style="margin-bottom: 0.5rem; font-size: 0.9rem; color: #888;">📜 Historikk</h3>
            </div>
        </div>
        
        <div class="phases-grid" id="phasesGrid">
            <!-- Phase 1: Intent -->
            <div class="phase-card" id="phase1">
                <div class="phase-header">
                    <span class="phase-icon">🎯</span>
                    <span class="phase-title">Intent Layer</span>
                    <span class="phase-number">Phase 1</span>
                </div>
                <div class="phase-content" id="phase1Content">
                    <div class="empty-state">
                        <div class="icon">💭</div>
                        <div>Venter på input...</div>
                    </div>
                </div>
            </div>
            
            <!-- Phase 2: Value -->
            <div class="phase-card" id="phase2">
                <div class="phase-header">
                    <span class="phase-icon">⚖️</span>
                    <span class="phase-title">Value Layer</span>
                    <span class="phase-number">Phase 2</span>
                </div>
                <div class="phase-content" id="phase2Content">
                    <div class="empty-state">
                        <div class="icon">💭</div>
                        <div>Venter på input...</div>
                    </div>
                </div>
            </div>
            
            <!-- Phase 3: Motivation -->
            <div class="phase-card" id="phase3">
                <div class="phase-header">
                    <span class="phase-icon">🔥</span>
                    <span class="phase-title">Motivational Dynamics</span>
                    <span class="phase-number">Phase 3</span>
                </div>
                <div class="phase-content" id="phase3Content">
                    <div class="empty-state">
                        <div class="icon">💭</div>
                        <div>Venter på input...</div>
                    </div>
                </div>
            </div>
            
            <!-- Phase 4: Balance -->
            <div class="phase-card" id="phase4">
                <div class="phase-header">
                    <span class="phase-icon">⚡</span>
                    <span class="phase-title">Top-Down / Bottom-Up</span>
                    <span class="phase-number">Phase 4</span>
                </div>
                <div class="phase-content" id="phase4Content">
                    <div class="empty-state">
                        <div class="icon">💭</div>
                        <div>Venter på input...</div>
                    </div>
                </div>
            </div>
            
            <!-- Phase 5: Stability -->
            <div class="phase-card" id="phase5">
                <div class="phase-header">
                    <span class="phase-icon">🛡️</span>
                    <span class="phase-title">Stability Monitor</span>
                    <span class="phase-number">Phase 5</span>
                </div>
                <div class="phase-content" id="phase5Content">
                    <div class="empty-state">
                        <div class="icon">💭</div>
                        <div>Venter på input...</div>
                    </div>
                </div>
            </div>
            
            <!-- Phase 6: Summary -->
            <div class="phase-card" id="phase6">
                <div class="phase-header">
                    <span class="phase-icon">📊</span>
                    <span class="phase-title">Sammendrag</span>
                    <span class="phase-number">Phase 6</span>
                </div>
                <div class="phase-content" id="phase6Content">
                    <div class="empty-state">
                        <div class="icon">💭</div>
                        <div>Venter på input...</div>
                    </div>
                </div>
            </div>
            
            <!-- Routing Decision (spans all columns) -->
            <div class="phase-card routing-section" id="routingSection">
                <div class="phase-header">
                    <span class="phase-icon">🧭</span>
                    <span class="phase-title">Final Routing Decision</span>
                </div>
                <div id="routingContent">
                    <div class="empty-state">
                        <div class="icon">🎛️</div>
                        <div>Routing-beslutning vises her etter prosessering</div>
                    </div>
                </div>
            </div>
        </div>
    </div>
    
    <script>
        let ws = null;
        let processing = false;
        
        function connectWebSocket() {
            ws = new WebSocket(`ws://${window.location.host}/ws`);
            
            ws.onopen = () => {
                document.getElementById('statusDot').style.background = '#00ff88';
                document.getElementById('statusText').textContent = 'Tilkoblet';
            };
            
            ws.onclose = () => {
                document.getElementById('statusDot').style.background = '#ff4757';
                document.getElementById('statusText').textContent = 'Frakoblet';
                setTimeout(connectWebSocket, 3000);
            };
            
            ws.onmessage = (event) => {
                const data = JSON.parse(event.data);
                handleResponse(data);
            };
        }
        
        function sendMessage() {
            if (processing) return;
            
            const userMessage = document.getElementById('userMessage').value.trim();
            const assistantDraft = document.getElementById('assistantDraft').value.trim();
            
            if (!userMessage) {
                alert('Skriv en melding først!');
                return;
            }
            
            processing = true;
            document.getElementById('sendBtn').disabled = true;
            document.getElementById('sendBtn').textContent = '⏳ Prosesserer...';
            
            // Add processing animation to all phases
            for (let i = 1; i <= 6; i++) {
                document.getElementById(`phase${i}`).classList.add('processing');
            }
            document.getElementById('routingSection').classList.add('processing');
            
            ws.send(JSON.stringify({
                user_message: userMessage,
                assistant_draft: assistantDraft
            }));
            
            // Add to history
            addToHistory(userMessage);
        }
        
        function addToHistory(message) {
            const history = document.getElementById('history');
            const item = document.createElement('div');
            item.className = 'history-item';
            item.innerHTML = `
                <div class="time">${new Date().toLocaleTimeString()}</div>
                <div>${message}</div>
            `;
            history.insertBefore(item, history.firstChild.nextSibling);
        }
        
        function handleResponse(data) {
            processing = false;
            document.getElementById('sendBtn').disabled = false;
            document.getElementById('sendBtn').textContent = '⚡ Prosesser gjennom Kognitiv Stakk';
            
            // Remove processing animation
            for (let i = 1; i <= 6; i++) {
                const phase = document.getElementById(`phase${i}`);
                phase.classList.remove('processing');
                phase.classList.add('active');
            }
            document.getElementById('routingSection').classList.remove('processing');
            document.getElementById('routingSection').classList.add('active');
            
            // Update each phase with animation
            setTimeout(() => updatePhase1(data.intent), 100);
            setTimeout(() => updatePhase2(data.value), 300);
            setTimeout(() => updatePhase3(data.motivation), 500);
            setTimeout(() => updatePhase4(data.balance), 700);
            setTimeout(() => updatePhase5(data.stability), 900);
            setTimeout(() => updatePhase6(data), 1100);
            setTimeout(() => updateRouting(data.routing_decision, data.recommendations), 1300);
        }
        
        function updatePhase1(intent) {
            if (!intent) return;
            const mode = intent.mode || 'unknown';
            const modeClass = mode === 'protection' ? 'protection' : 'learning';
            
            document.getElementById('phase1Content').innerHTML = `
                <div class="metric">
                    <span class="metric-label">Modus</span>
                    <span class="tag ${modeClass}">${mode.toUpperCase()}</span>
                </div>
                <div class="metric">
                    <span class="metric-label">Aktive Domener</span>
                    <div>${(intent.active_domains || []).map(d => `<span class="tag ${d}">${d}</span>`).join('')}</div>
                </div>
                <div class="metric">
                    <span class="metric-label">Styrke</span>
                    <span class="metric-value">${(intent.strength || 0).toFixed(2)}</span>
                </div>
                <div class="progress-bar">
                    <div class="progress-fill" style="width: ${(intent.strength || 0) * 100}%"></div>
                </div>
            `;
        }
        
        function updatePhase2(value) {
            const v = value || {};
            document.getElementById('phase2Content').innerHTML = `
                <div class="metric">
                    <span class="metric-label">Verdinivå</span>
                    <span class="metric-value">${v.value_level || 'unknown'}</span>
                </div>
                <div class="metric">
                    <span class="metric-label">Prioritet</span>
                    <span class="metric-value">${(v.final_priority || 0).toFixed(2)}</span>
                </div>
                <div class="metric">
                    <span class="metric-label">Harm Detected</span>
                    <span class="metric-value ${v.harm_detected ? 'low' : 'high'}">${v.harm_detected ? '⚠️ JA' : '✅ NEI'}</span>
                </div>
                <div class="progress-bar">
                    <div class="progress-fill" style="width: ${(v.final_priority || 0) * 100}%"></div>
                </div>
            `;
        }
        
        function updatePhase3(motivation) {
            const m = motivation || {};
            const goals = (m.active_goals || []).slice(0, 2);
            const prefs = (m.active_preferences || []).slice(0, 2);
            
            document.getElementById('phase3Content').innerHTML = `
                <div class="metric">
                    <span class="metric-label">Motivasjonsstyrke</span>
                    <span class="metric-value ${m.motivation_strength > 0.7 ? 'high' : 'medium'}">${(m.motivation_strength || 0).toFixed(2)}</span>
                </div>
                <div class="metric">
                    <span class="metric-label">Aktive Mål</span>
                    <div>${goals.map(g => `<span class="tag">${g.goal_type || g}</span>`).join('')}</div>
                </div>
                <div class="metric">
                    <span class="metric-label">Preferanser</span>
                    <div>${prefs.map(p => `<span class="tag">${p.name || p}</span>`).join('')}</div>
                </div>
                <div class="progress-bar">
                    <div class="progress-fill" style="width: ${(m.motivation_strength || 0) * 100}%"></div>
                </div>
            `;
        }
        
        function updatePhase4(balance) {
            const b = balance || {};
            const topDown = b.top_down_weight || 0.5;
            const bottomUp = b.bottom_up_weight || 0.5;
            const position = topDown * 100;
            
            document.getElementById('phase4Content').innerHTML = `
                <div class="metric">
                    <span class="metric-label">Tilstand</span>
                    <span class="tag ${b.state === 'top_down_dominant' ? 'protection' : 'learning'}">${b.state || 'balanced'}</span>
                </div>
                <div class="balance-viz">
                    <span style="font-size: 0.8rem">↓</span>
                    <div class="balance-bar">
                        <div class="balance-indicator" style="left: calc(${position}% - 2px)"></div>
                    </div>
                    <span style="font-size: 0.8rem">↑</span>
                </div>
                <div class="balance-labels">
                    <span>Bottom-Up: ${(bottomUp * 100).toFixed(0)}%</span>
                    <span>Top-Down: ${(topDown * 100).toFixed(0)}%</span>
                </div>
            `;
        }
        
        function updatePhase5(stability) {
            const s = stability || {};
            const levelClass = s.level === 'stable' ? 'high' : s.level === 'warning' ? 'medium' : 'low';
            
            document.getElementById('phase5Content').innerHTML = `
                <div class="metric">
                    <span class="metric-label">Stabilitet</span>
                    <span class="metric-value ${levelClass}">${s.level || 'unknown'}</span>
                </div>
                <div class="metric">
                    <span class="metric-label">Drift Score</span>
                    <span class="metric-value">${(s.drift_score || 0).toFixed(3)}</span>
                </div>
                <div class="metric">
                    <span class="metric-label">Oscillation</span>
                    <span class="metric-value">${(s.oscillation_rate || 0).toFixed(3)}</span>
                </div>
                ${(s.issues || []).length > 0 ? `
                    <div class="metric">
                        <span class="metric-label">Issues</span>
                        <span class="metric-value low">${s.issues.length} problemer</span>
                    </div>
                ` : ''}
            `;
        }
        
        function updatePhase6(data) {
            const intent = data.intent || {};
            const motivation = data.motivation || {};
            
            document.getElementById('phase6Content').innerHTML = `
                <div class="metric">
                    <span class="metric-label">Modus</span>
                    <span class="tag ${intent.mode === 'protection' ? 'protection' : 'learning'}">${(intent.mode || 'unknown').toUpperCase()}</span>
                </div>
                <div class="metric">
                    <span class="metric-label">Topp-mål</span>
                    <span class="metric-value">${motivation.active_goals?.[0]?.goal_type || 'N/A'}</span>
                </div>
                <div class="metric">
                    <span class="metric-label">Motivasjon</span>
                    <span class="metric-value ${motivation.motivation_strength > 0.7 ? 'high' : 'medium'}">${(motivation.motivation_strength || 0).toFixed(2)}</span>
                </div>
            `;
        }
        
        function updateRouting(routing, recommendations) {
            const r = routing || {};
            
            document.getElementById('routingContent').innerHTML = `
                <div class="routing-grid">
                    <div class="routing-metric">
                        <div class="value">${(r.memory_retrieval_weight || 0).toFixed(2)}</div>
                        <div class="label">Memory Retrieval</div>
                    </div>
                    <div class="routing-metric">
                        <div class="value">${(r.canonical_override_strength || 0).toFixed(2)}</div>
                        <div class="label">Canonical Override</div>
                    </div>
                    <div class="routing-metric">
                        <div class="value">${(r.llm_temperature || 0).toFixed(2)}</div>
                        <div class="label">LLM Temperature</div>
                    </div>
                    <div class="routing-metric">
                        <div class="value" style="color: ${r.self_optimization_trigger ? '#00ff88' : '#ff4757'}">${r.self_optimization_trigger ? 'ON' : 'OFF'}</div>
                        <div class="label">Self-Optimization</div>
                    </div>
                    <div class="routing-metric">
                        <div class="value" style="color: ${r.self_healing_trigger ? '#00ff88' : '#ff4757'}">${r.self_healing_trigger ? 'ON' : 'OFF'}</div>
                        <div class="label">Self-Healing</div>
                    </div>
                </div>
                ${(recommendations || []).length > 0 ? `
                    <div class="recommendations">
                        <h4>📋 Anbefalinger</h4>
                        <ul>
                            ${(recommendations || []).slice(0, 5).map(r => `<li>${r}</li>`).join('')}
                        </ul>
                    </div>
                ` : ''}
                ${(r.reasoning || []).length > 0 ? `
                    <div class="recommendations" style="margin-top: 0.5rem;">
                        <h4>🧠 Reasoning</h4>
                        <ul>
                            ${(r.reasoning || []).map(r => `<li>${r}</li>`).join('')}
                        </ul>
                    </div>
                ` : ''}
            `;
        }
        
        // Poll backend status every 2 seconds
        let pollInterval = null;
        
        function startPolling() {
            pollInterval = setInterval(async () => {
                try {
                    const resp = await fetch('/api/state');
                    const data = await resp.json();
                    if (data.cognitive_context) {
                        updateStatusDisplay(data.cognitive_context);
                    }
                } catch (e) {
                    console.log('Poll error:', e);
                }
            }, 2000);
        }
        
        function updateStatusDisplay(ctx) {
            // Update meta info
            const meta = ctx.meta || {};
            if (meta.turn_count > 0) {
                document.getElementById('statusText').textContent = 
                    `Turn ${meta.turn_count} | ${meta.was_overridden ? '⚡ Override' : '✓'}`;
            }
            
            // Update intent display if exists
            const intent = ctx.intent || {};
            const intentEl = document.getElementById('intentMode');
            if (intentEl) {
                intentEl.textContent = intent.mode || 'idle';
            }
            
            // Update value level
            const value = ctx.value || {};
            const valueEl = document.getElementById('valueLevel');
            if (valueEl) {
                valueEl.textContent = value.value_level || 'unknown';
            }
        }
        
        // Initialize
        connectWebSocket();
        startPolling();
        
        // Enter key to send
        document.getElementById('userMessage').addEventListener('keydown', (e) => {
            if (e.key === 'Enter' && e.ctrlKey) {
                sendMessage();
            }
        });
    </script>
</body>
</html>
"""

@app.get("/", response_class=HTMLResponse)
async def get_dashboard():
    return HTML_TEMPLATE

@app.get("/api/state")
async def get_backend_state():
    """Proxy to backend cognitive status - for polling fallback."""
    import httpx
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get("http://localhost:8000/chat/cognitive/status", timeout=5.0)
            return resp.json()
    except Exception as e:
        return {"error": str(e), "status": "backend_unavailable"}

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            data = await websocket.receive_json()
            
            # Check if this is a status poll request
            if data.get("type") == "poll":
                # Fetch from backend API
                import httpx
                try:
                    async with httpx.AsyncClient() as client:
                        resp = await client.get("http://localhost:8000/chat/cognitive/status", timeout=5.0)
                        backend_data = resp.json()
                        await websocket.send_json({
                            "type": "status_update",
                            "data": backend_data.get("cognitive_context", {}),
                            "source": "backend"
                        })
                except Exception as e:
                    await websocket.send_json({"type": "error", "message": str(e)})
                continue
            
            user_message = data.get("user_message", "")
            assistant_draft = data.get("assistant_draft", "")
            
            # Build context for cognitive router
            session_context = {
                "user_message": user_message,
                "assistant_draft": assistant_draft,
                "session_id": "web_dashboard",
                "turn_number": 1
            }
            system_metrics = {
                "drift_score": 0.0,
                "oscillation_rate": 0.0,
                "degradation_rate": 0.0,
                "health_score": 1.0
            }
            
            # Process through cognitive stack
            result = router.process_and_route(user_message, session_context, system_metrics)
            
            # Send result back
            await websocket.send_json(result)
            
    except WebSocketDisconnect:
        pass

if __name__ == "__main__":
    print("\n🧠 Starting Symbiosis Live Web Dashboard...")
    print("📡 Open http://localhost:8080 in your browser\n")
    uvicorn.run(app, host="0.0.0.0", port=8080)
