#!/usr/bin/env python3
"""
web_monitor_dashboard.py - Full Cognitive Stack Monitoring Dashboard
=====================================================================

MONITORING ONLY - No input, bare observasjon av alle lag.

Viser live status for HELE kognitiv arkitekturen:

CORE MEMORY LAYERS (9):
1. CMC - Canonical Memory Core (absolute truth)
2. SMM - Semantic Mesh Memory (dynamic context)
3. Neo4j Graph Layer (structural relationships)
4. DDE - Dynamic Domain Engine (auto-domain)
5. AME - Adaptive Memory Enforcer (intelligent override)
6. MLC - Meta-Learning Cortex (user patterns)
7. MIR - Memory Interference Regulator (noise detection)
8. MCA - Memory Consistency Auditor (cross-layer validation)
9. MCE - Memory Compression Engine (recursive summarization)

META-SUPERVISOR LAYERS (6):
1. Intent Engine (hva er viktig nå?)
2. Value Layer (hva er VIKTIG?)
3. Motivational Dynamics (mål, preferanser, retning)
4. Balance Controller (top-down vs bottom-up)
5. Stability Monitor (drift detection)
6. Routing Decision (parameter tuning)

ADDITIONAL LAYERS:
- Priority Gate (intent-driven filtering)
- Identity Protection (canonical enforcement)
- Self-Healing Canonical (observation-based truth)
- Self-Optimizing Layer (autonomous tuning)
- Intention Gate (GNN-enhanced suggestions)
- Steering Layer (write-enabled management)
- EFC Theory Engine (domain-specific reasoning)

Usage:
    python web_monitor_dashboard.py
    # Open http://localhost:8080

"""

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
import uvicorn
import asyncio
import httpx
import json
from datetime import datetime
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__))))

app = FastAPI(title="EFC Cognitive Stack Monitor")

# Backend API
BACKEND_URL = "http://localhost:8000"

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="no">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>🧠 EFC Cognitive Stack Monitor</title>
    <style>
        :root {
            --bg-primary: #0d1117;
            --bg-secondary: #161b22;
            --bg-tertiary: #21262d;
            --border-color: #30363d;
            --text-primary: #e6edf3;
            --text-secondary: #8b949e;
            --accent-blue: #58a6ff;
            --accent-green: #3fb950;
            --accent-yellow: #d29922;
            --accent-red: #f85149;
            --accent-purple: #a371f7;
            --accent-cyan: #56d4dd;
            --accent-orange: #db6d28;
            --accent-pink: #db61a2;
        }
        
        * {
            box-sizing: border-box;
            margin: 0;
            padding: 0;
        }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, sans-serif;
            background: var(--bg-primary);
            color: var(--text-primary);
            min-height: 100vh;
            padding: 20px;
        }
        
        .header {
            text-align: center;
            margin-bottom: 30px;
            padding: 20px;
            background: linear-gradient(135deg, var(--bg-secondary), var(--bg-tertiary));
            border-radius: 12px;
            border: 1px solid var(--border-color);
        }
        
        .header h1 {
            font-size: 2.5em;
            margin-bottom: 10px;
            background: linear-gradient(90deg, var(--accent-cyan), var(--accent-purple));
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }
        
        .header .subtitle {
            color: var(--text-secondary);
            font-size: 1.1em;
        }
        
        .status-bar {
            display: flex;
            justify-content: center;
            gap: 30px;
            margin-bottom: 30px;
            flex-wrap: wrap;
        }
        
        .status-item {
            display: flex;
            align-items: center;
            gap: 8px;
            padding: 10px 20px;
            background: var(--bg-secondary);
            border-radius: 8px;
            border: 1px solid var(--border-color);
        }
        
        .status-dot {
            width: 12px;
            height: 12px;
            border-radius: 50%;
            animation: pulse 2s infinite;
        }
        
        .status-dot.green { background: var(--accent-green); }
        .status-dot.yellow { background: var(--accent-yellow); }
        .status-dot.red { background: var(--accent-red); }
        
        @keyframes pulse {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.5; }
        }
        
        .main-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
            gap: 20px;
            max-width: 1800px;
            margin: 0 auto;
        }
        
        .layer-card {
            background: var(--bg-secondary);
            border: 1px solid var(--border-color);
            border-radius: 12px;
            padding: 20px;
            transition: transform 0.2s, border-color 0.2s;
        }
        
        .layer-card:hover {
            transform: translateY(-2px);
            border-color: var(--accent-blue);
        }
        
        .layer-header {
            display: flex;
            align-items: center;
            gap: 12px;
            margin-bottom: 15px;
            padding-bottom: 10px;
            border-bottom: 1px solid var(--border-color);
        }
        
        .layer-icon {
            font-size: 1.8em;
        }
        
        .layer-title {
            font-size: 1.2em;
            font-weight: 600;
        }
        
        .layer-subtitle {
            font-size: 0.85em;
            color: var(--text-secondary);
        }
        
        .layer-content {
            font-size: 0.9em;
        }
        
        .metric-row {
            display: flex;
            justify-content: space-between;
            padding: 8px 0;
            border-bottom: 1px dashed var(--border-color);
        }
        
        .metric-row:last-child {
            border-bottom: none;
        }
        
        .metric-label {
            color: var(--text-secondary);
        }
        
        .metric-value {
            font-family: 'Monaco', 'Menlo', monospace;
            font-weight: 600;
        }
        
        .metric-value.green { color: var(--accent-green); }
        .metric-value.yellow { color: var(--accent-yellow); }
        .metric-value.red { color: var(--accent-red); }
        .metric-value.blue { color: var(--accent-blue); }
        .metric-value.purple { color: var(--accent-purple); }
        .metric-value.cyan { color: var(--accent-cyan); }
        .metric-value.orange { color: var(--accent-orange); }
        .metric-value.pink { color: var(--accent-pink); }
        
        .progress-bar {
            height: 8px;
            background: var(--bg-tertiary);
            border-radius: 4px;
            overflow: hidden;
            margin-top: 5px;
        }
        
        .progress-fill {
            height: 100%;
            border-radius: 4px;
            transition: width 0.5s ease-out;
        }
        
        .tag-list {
            display: flex;
            flex-wrap: wrap;
            gap: 6px;
            margin-top: 10px;
        }
        
        .tag {
            padding: 4px 10px;
            background: var(--bg-tertiary);
            border-radius: 12px;
            font-size: 0.8em;
            color: var(--text-secondary);
        }
        
        .tag.active {
            background: rgba(88, 166, 255, 0.2);
            color: var(--accent-blue);
        }
        
        .tag.warning {
            background: rgba(210, 153, 34, 0.2);
            color: var(--accent-yellow);
        }
        
        .section-title {
            grid-column: 1 / -1;
            font-size: 1.4em;
            padding: 15px 0;
            margin-top: 20px;
            border-bottom: 2px solid var(--border-color);
            color: var(--accent-cyan);
        }
        
        .goal-item {
            padding: 8px;
            background: var(--bg-tertiary);
            border-radius: 6px;
            margin: 5px 0;
        }
        
        .goal-name {
            font-weight: 600;
            color: var(--accent-purple);
        }
        
        .preference-bar {
            display: flex;
            align-items: center;
            gap: 10px;
            padding: 6px 0;
        }
        
        .preference-name {
            flex: 1;
            font-size: 0.85em;
        }
        
        .preference-strength {
            width: 100px;
        }
        
        .refresh-info {
            text-align: center;
            margin-top: 30px;
            color: var(--text-secondary);
            font-size: 0.9em;
        }
        
        .last-update {
            font-family: monospace;
            color: var(--accent-cyan);
        }
        
        .recommendations {
            margin-top: 10px;
            padding: 10px;
            background: rgba(63, 185, 80, 0.1);
            border-radius: 8px;
            border-left: 3px solid var(--accent-green);
        }
        
        .recommendation-item {
            padding: 4px 0;
            font-size: 0.85em;
            color: var(--accent-green);
        }
        
        .layer-card.memory { border-left: 3px solid var(--accent-blue); }
        .layer-card.intelligence { border-left: 3px solid var(--accent-purple); }
        .layer-card.advanced { border-left: 3px solid var(--accent-cyan); }
        .layer-card.meta { border-left: 3px solid var(--accent-orange); }
        .layer-card.support { border-left: 3px solid var(--accent-pink); }
        
        .empty-state {
            text-align: center;
            padding: 40px;
            color: var(--text-secondary);
        }
        
        .error-state {
            background: rgba(248, 81, 73, 0.1);
            border: 1px solid var(--accent-red);
            padding: 20px;
            border-radius: 8px;
            text-align: center;
            color: var(--accent-red);
        }
    </style>
</head>
<body>
    <div class="header">
        <h1>🧠 EFC Cognitive Stack Monitor</h1>
        <p class="subtitle">Real-time observation of all cognitive layers • Energy-Flow Cosmology System</p>
    </div>
    
    <div class="status-bar">
        <div class="status-item">
            <span class="status-dot" id="backend-status"></span>
            <span>Backend API</span>
        </div>
        <div class="status-item">
            <span class="status-dot" id="memory-status"></span>
            <span>Memory System</span>
        </div>
        <div class="status-item">
            <span class="status-dot" id="cognitive-status"></span>
            <span>Cognitive Engine</span>
        </div>
    </div>
    
    <div class="main-grid" id="dashboard-content">
        <div class="empty-state">
            <h2>Loading cognitive stack...</h2>
            <p>Waiting for first monitoring cycle</p>
        </div>
    </div>
    
    <div class="refresh-info">
        <p>Auto-refresh every 3 seconds • Last update: <span class="last-update" id="last-update">-</span></p>
    </div>
    
    <script>
        // Configuration
        const REFRESH_INTERVAL = 3000;
        let lastData = null;
        
        function formatValue(value, precision = 2) {
            if (typeof value === 'number') {
                return value.toFixed(precision);
            }
            if (typeof value === 'boolean') {
                return value ? '✓ Yes' : '✗ No';
            }
            if (Array.isArray(value)) {
                return value.length > 0 ? value.join(', ') : '(empty)';
            }
            if (value === null || value === undefined) {
                return '-';
            }
            return String(value);
        }
        
        function getColorClass(value, thresholds) {
            if (typeof value !== 'number') return '';
            if (thresholds.high && value >= thresholds.high) return thresholds.highColor || 'green';
            if (thresholds.low && value <= thresholds.low) return thresholds.lowColor || 'red';
            return thresholds.midColor || 'yellow';
        }
        
        function renderProgressBar(value, color) {
            const percent = Math.min(100, Math.max(0, value * 100));
            return `
                <div class="progress-bar">
                    <div class="progress-fill" style="width: ${percent}%; background: var(--accent-${color})"></div>
                </div>
            `;
        }
        
        function renderTags(items, activeCheck) {
            if (!items || items.length === 0) return '';
            return `
                <div class="tag-list">
                    ${items.map(item => {
                        const isActive = activeCheck ? activeCheck(item) : false;
                        return `<span class="tag ${isActive ? 'active' : ''}">${item}</span>`;
                    }).join('')}
                </div>
            `;
        }
        
        function renderMemoryLayers(data) {
            // These are inferred from system state - we'll need to add endpoints later
            return `
                <h2 class="section-title">📚 Core Memory Layers (1-3)</h2>
                
                <div class="layer-card memory">
                    <div class="layer-header">
                        <span class="layer-icon">1️⃣</span>
                        <div>
                            <div class="layer-title">CMC - Canonical Memory Core</div>
                            <div class="layer-subtitle">Absolute truth, never forgotten</div>
                        </div>
                    </div>
                    <div class="layer-content">
                        <div class="metric-row">
                            <span class="metric-label">Override Active</span>
                            <span class="metric-value ${data.was_overridden ? 'green' : 'yellow'}">${data.was_overridden ? 'YES' : 'NO'}</span>
                        </div>
                        <div class="metric-row">
                            <span class="metric-label">Canonical Override Strength</span>
                            <span class="metric-value cyan">${formatValue(data.cognitive_context?.routing?.canonical_override_strength)}</span>
                        </div>
                        ${renderProgressBar(data.cognitive_context?.routing?.canonical_override_strength || 0, 'cyan')}
                    </div>
                </div>
                
                <div class="layer-card memory">
                    <div class="layer-header">
                        <span class="layer-icon">2️⃣</span>
                        <div>
                            <div class="layer-title">SMM - Semantic Mesh Memory</div>
                            <div class="layer-subtitle">Dynamic context & synthesis</div>
                        </div>
                    </div>
                    <div class="layer-content">
                        <div class="metric-row">
                            <span class="metric-label">Retrieved Chunks</span>
                            <span class="metric-value blue">${data.retrieved_chunks?.length || 0}</span>
                        </div>
                        <div class="metric-row">
                            <span class="metric-label">Memory Retrieval Weight</span>
                            <span class="metric-value purple">${formatValue(data.cognitive_context?.routing?.memory_retrieval_weight)}</span>
                        </div>
                        ${renderProgressBar((data.cognitive_context?.routing?.memory_retrieval_weight || 0) / 2, 'purple')}
                    </div>
                </div>
                
                <div class="layer-card memory">
                    <div class="layer-header">
                        <span class="layer-icon">3️⃣</span>
                        <div>
                            <div class="layer-title">Neo4j Graph Layer</div>
                            <div class="layer-subtitle">Structural relationships & traversal</div>
                        </div>
                    </div>
                    <div class="layer-content">
                        <div class="metric-row">
                            <span class="metric-label">GNN Available</span>
                            <span class="metric-value ${data.gnn?.available ? 'green' : 'yellow'}">${data.gnn?.available ? 'YES' : 'NO'}</span>
                        </div>
                        <div class="metric-row">
                            <span class="metric-label">Active Domains</span>
                            <span class="metric-value blue">${data.cognitive_context?.intent?.active_domains?.join(', ') || '-'}</span>
                        </div>
                    </div>
                </div>
            `;
        }
        
        function renderIntelligenceLayers(data) {
            const intent = data.cognitive_context?.intent || {};
            const value = data.cognitive_context?.value || {};
            
            return `
                <h2 class="section-title">🧠 Intelligence Layers (4-6)</h2>
                
                <div class="layer-card intelligence">
                    <div class="layer-header">
                        <span class="layer-icon">4️⃣</span>
                        <div>
                            <div class="layer-title">DDE - Dynamic Domain Engine</div>
                            <div class="layer-subtitle">Auto-domain detection</div>
                        </div>
                    </div>
                    <div class="layer-content">
                        <div class="metric-row">
                            <span class="metric-label">Detected Domains</span>
                            <span class="metric-value purple">${intent.active_domains?.join(', ') || '-'}</span>
                        </div>
                        ${renderTags(intent.active_domains || [], () => true)}
                    </div>
                </div>
                
                <div class="layer-card intelligence">
                    <div class="layer-header">
                        <span class="layer-icon">5️⃣</span>
                        <div>
                            <div class="layer-title">AME - Adaptive Memory Enforcer</div>
                            <div class="layer-subtitle">Intelligent override</div>
                        </div>
                    </div>
                    <div class="layer-content">
                        <div class="metric-row">
                            <span class="metric-label">Was Overridden</span>
                            <span class="metric-value ${data.was_overridden ? 'green' : 'yellow'}">${data.was_overridden ? 'YES' : 'NO'}</span>
                        </div>
                        <div class="metric-row">
                            <span class="metric-label">Conflict Reason</span>
                            <span class="metric-value cyan">${data.conflict_reason || '-'}</span>
                        </div>
                    </div>
                </div>
                
                <div class="layer-card intelligence">
                    <div class="layer-header">
                        <span class="layer-icon">6️⃣</span>
                        <div>
                            <div class="layer-title">MLC - Meta-Learning Cortex</div>
                            <div class="layer-subtitle">User pattern learning</div>
                        </div>
                    </div>
                    <div class="layer-content">
                        <div class="metric-row">
                            <span class="metric-label">Value Level</span>
                            <span class="metric-value ${value.value_level === 'high' ? 'green' : value.value_level === 'low' ? 'yellow' : 'blue'}">${value.value_level || '-'}</span>
                        </div>
                        <div class="metric-row">
                            <span class="metric-label">Final Priority</span>
                            <span class="metric-value purple">${formatValue(value.final_priority)}</span>
                        </div>
                        ${renderProgressBar(value.final_priority || 0, 'purple')}
                    </div>
                </div>
            `;
        }
        
        function renderAdvancedLayers(data) {
            const stability = data.cognitive_context?.stability || {};
            const balance = data.cognitive_context?.balance || {};
            
            return `
                <h2 class="section-title">⚡ Advanced Layers (7-9)</h2>
                
                <div class="layer-card advanced">
                    <div class="layer-header">
                        <span class="layer-icon">7️⃣</span>
                        <div>
                            <div class="layer-title">MIR - Memory Interference Regulator</div>
                            <div class="layer-subtitle">Noise/conflict detection</div>
                        </div>
                    </div>
                    <div class="layer-content">
                        <div class="metric-row">
                            <span class="metric-label">Drift Score</span>
                            <span class="metric-value ${stability.drift_score > 0.3 ? 'red' : stability.drift_score > 0.1 ? 'yellow' : 'green'}">${formatValue(stability.drift_score)}</span>
                        </div>
                        ${renderProgressBar(stability.drift_score || 0, stability.drift_score > 0.3 ? 'red' : 'green')}
                        <div class="metric-row">
                            <span class="metric-label">Issues Detected</span>
                            <span class="metric-value ${stability.issues?.length > 0 ? 'red' : 'green'}">${stability.issues?.length || 0}</span>
                        </div>
                    </div>
                </div>
                
                <div class="layer-card advanced">
                    <div class="layer-header">
                        <span class="layer-icon">8️⃣</span>
                        <div>
                            <div class="layer-title">MCA - Memory Consistency Auditor</div>
                            <div class="layer-subtitle">Cross-layer validation</div>
                        </div>
                    </div>
                    <div class="layer-content">
                        <div class="metric-row">
                            <span class="metric-label">Oscillation Rate</span>
                            <span class="metric-value ${stability.oscillation_rate > 0.5 ? 'red' : 'green'}">${formatValue(stability.oscillation_rate)}</span>
                        </div>
                        ${renderProgressBar(stability.oscillation_rate || 0, stability.oscillation_rate > 0.5 ? 'red' : 'cyan')}
                        <div class="metric-row">
                            <span class="metric-label">Degradation Rate</span>
                            <span class="metric-value ${stability.degradation_rate > 0.2 ? 'red' : 'green'}">${formatValue(stability.degradation_rate)}</span>
                        </div>
                    </div>
                </div>
                
                <div class="layer-card advanced">
                    <div class="layer-header">
                        <span class="layer-icon">9️⃣</span>
                        <div>
                            <div class="layer-title">MCE - Memory Compression Engine</div>
                            <div class="layer-subtitle">Recursive summarization</div>
                        </div>
                    </div>
                    <div class="layer-content">
                        <div class="metric-row">
                            <span class="metric-label">Session ID</span>
                            <span class="metric-value cyan">${data.metadata?.session_id || '-'}</span>
                        </div>
                        <div class="metric-row">
                            <span class="metric-label">Turn Number</span>
                            <span class="metric-value blue">${data.metadata?.turn_number || '-'}</span>
                        </div>
                    </div>
                </div>
            `;
        }
        
        function renderMetaSupervisor(data) {
            const intent = data.cognitive_context?.intent || {};
            const value = data.cognitive_context?.value || {};
            const motivation = data.cognitive_context?.motivation || {};
            const balance = data.cognitive_context?.balance || {};
            const stability = data.cognitive_context?.stability || {};
            const routing = data.cognitive_context?.routing || {};
            
            return `
                <h2 class="section-title">🎛️ Meta-Supervisor Layers</h2>
                
                <div class="layer-card meta">
                    <div class="layer-header">
                        <span class="layer-icon">🎯</span>
                        <div>
                            <div class="layer-title">Intent Engine</div>
                            <div class="layer-subtitle">Hva er viktig nå?</div>
                        </div>
                    </div>
                    <div class="layer-content">
                        <div class="metric-row">
                            <span class="metric-label">Mode</span>
                            <span class="metric-value orange">${intent.mode?.toUpperCase() || '-'}</span>
                        </div>
                        <div class="metric-row">
                            <span class="metric-label">Strength</span>
                            <span class="metric-value cyan">${formatValue(intent.strength)}</span>
                        </div>
                        ${renderProgressBar(intent.strength || 0, 'orange')}
                        <div class="metric-row">
                            <span class="metric-label">Active Domains</span>
                            <span class="metric-value blue">${intent.active_domains?.join(', ') || '-'}</span>
                        </div>
                        ${renderTags(intent.ignore_patterns || [], () => false)}
                    </div>
                </div>
                
                <div class="layer-card meta">
                    <div class="layer-header">
                        <span class="layer-icon">💎</span>
                        <div>
                            <div class="layer-title">Value Layer</div>
                            <div class="layer-subtitle">Hva er VIKTIG?</div>
                        </div>
                    </div>
                    <div class="layer-content">
                        <div class="metric-row">
                            <span class="metric-label">Value Level</span>
                            <span class="metric-value ${value.value_level === 'high' ? 'green' : value.value_level === 'critical' ? 'red' : 'yellow'}">${value.value_level?.toUpperCase() || '-'}</span>
                        </div>
                        <div class="metric-row">
                            <span class="metric-label">Final Priority</span>
                            <span class="metric-value purple">${formatValue(value.final_priority)}</span>
                        </div>
                        ${renderProgressBar(value.final_priority || 0, 'purple')}
                        <div class="metric-row">
                            <span class="metric-label">Harm Detected</span>
                            <span class="metric-value ${value.harm_detected ? 'red' : 'green'}">${value.harm_detected ? '⚠️ YES' : '✓ NO'}</span>
                        </div>
                        ${value.harm_signals?.length > 0 ? renderTags(value.harm_signals, () => true) : ''}
                    </div>
                </div>
                
                <div class="layer-card meta">
                    <div class="layer-header">
                        <span class="layer-icon">🚀</span>
                        <div>
                            <div class="layer-title">Motivational Dynamics</div>
                            <div class="layer-subtitle">Mål, preferanser, retning</div>
                        </div>
                    </div>
                    <div class="layer-content">
                        <div class="metric-row">
                            <span class="metric-label">Motivation Strength</span>
                            <span class="metric-value pink">${formatValue(motivation.motivation_strength)}</span>
                        </div>
                        ${renderProgressBar(motivation.motivation_strength || 0, 'pink')}
                        
                        <div style="margin-top: 15px;">
                            <strong style="color: var(--accent-purple);">Active Goals:</strong>
                            ${(motivation.active_goals || []).slice(0, 3).map(goal => `
                                <div class="goal-item">
                                    <span class="goal-name">${goal.goal_type?.replace(/_/g, ' ') || '-'}</span>
                                    <span style="float: right; color: var(--accent-cyan);">Priority: ${formatValue(goal.priority)}</span>
                                </div>
                            `).join('')}
                        </div>
                        
                        <div style="margin-top: 15px;">
                            <strong style="color: var(--accent-orange);">Directional Bias:</strong>
                            ${Object.entries(motivation.directional_bias || {}).slice(0, 4).map(([key, value]) => `
                                <div class="preference-bar">
                                    <span class="preference-name">${key}</span>
                                    <div class="preference-strength">${renderProgressBar(value, 'orange')}</div>
                                    <span style="width: 50px; text-align: right; color: var(--accent-cyan)">${formatValue(value)}</span>
                                </div>
                            `).join('')}
                        </div>
                    </div>
                </div>
                
                <div class="layer-card meta">
                    <div class="layer-header">
                        <span class="layer-icon">⚖️</span>
                        <div>
                            <div class="layer-title">Balance Controller</div>
                            <div class="layer-subtitle">Top-down vs bottom-up</div>
                        </div>
                    </div>
                    <div class="layer-content">
                        <div class="metric-row">
                            <span class="metric-label">State</span>
                            <span class="metric-value cyan">${balance.state?.replace(/_/g, ' ').toUpperCase() || '-'}</span>
                        </div>
                        <div class="metric-row">
                            <span class="metric-label">Top-Down Weight</span>
                            <span class="metric-value orange">${formatValue(balance.top_down_weight)}</span>
                        </div>
                        ${renderProgressBar(balance.top_down_weight || 0, 'orange')}
                        <div class="metric-row">
                            <span class="metric-label">Bottom-Up Weight</span>
                            <span class="metric-value blue">${formatValue(balance.bottom_up_weight)}</span>
                        </div>
                        ${renderProgressBar(balance.bottom_up_weight || 0, 'blue')}
                        <div class="metric-row">
                            <span class="metric-label">Reason</span>
                            <span class="metric-value" style="font-size: 0.8em; color: var(--text-secondary)">${balance.reason || '-'}</span>
                        </div>
                    </div>
                </div>
                
                <div class="layer-card meta">
                    <div class="layer-header">
                        <span class="layer-icon">📊</span>
                        <div>
                            <div class="layer-title">Stability Monitor</div>
                            <div class="layer-subtitle">Drift detection & prevention</div>
                        </div>
                    </div>
                    <div class="layer-content">
                        <div class="metric-row">
                            <span class="metric-label">Level</span>
                            <span class="metric-value ${stability.level === 'stable' ? 'green' : stability.level === 'critical' ? 'red' : 'yellow'}">${stability.level?.toUpperCase() || '-'}</span>
                        </div>
                        <div class="metric-row">
                            <span class="metric-label">Drift Score</span>
                            <span class="metric-value ${stability.drift_score > 0.3 ? 'red' : 'green'}">${formatValue(stability.drift_score)}</span>
                        </div>
                        ${renderProgressBar(stability.drift_score || 0, stability.drift_score > 0.3 ? 'red' : 'green')}
                        <div class="metric-row">
                            <span class="metric-label">Oscillation Rate</span>
                            <span class="metric-value cyan">${formatValue(stability.oscillation_rate)}</span>
                        </div>
                        ${stability.issues?.length > 0 ? `
                            <div class="tag-list" style="margin-top: 10px;">
                                ${stability.issues.map(issue => `<span class="tag warning">${issue}</span>`).join('')}
                            </div>
                        ` : ''}
                    </div>
                </div>
                
                <div class="layer-card meta">
                    <div class="layer-header">
                        <span class="layer-icon">🔧</span>
                        <div>
                            <div class="layer-title">Routing Decision</div>
                            <div class="layer-subtitle">Parameter tuning output</div>
                        </div>
                    </div>
                    <div class="layer-content">
                        <div class="metric-row">
                            <span class="metric-label">Memory Retrieval Weight</span>
                            <span class="metric-value purple">${formatValue(routing.memory_retrieval_weight)}</span>
                        </div>
                        ${renderProgressBar((routing.memory_retrieval_weight || 0) / 2, 'purple')}
                        <div class="metric-row">
                            <span class="metric-label">Canonical Override</span>
                            <span class="metric-value cyan">${formatValue(routing.canonical_override_strength)}</span>
                        </div>
                        ${renderProgressBar(routing.canonical_override_strength || 0, 'cyan')}
                        <div class="metric-row">
                            <span class="metric-label">LLM Temperature</span>
                            <span class="metric-value orange">${formatValue(routing.llm_temperature)}</span>
                        </div>
                        ${renderProgressBar(routing.llm_temperature || 0, 'orange')}
                        <div class="metric-row">
                            <span class="metric-label">Self-Optimization</span>
                            <span class="metric-value ${routing.self_optimization_trigger ? 'green' : 'yellow'}">${routing.self_optimization_trigger ? 'ACTIVE' : 'IDLE'}</span>
                        </div>
                        <div class="metric-row">
                            <span class="metric-label">Self-Healing</span>
                            <span class="metric-value ${routing.self_healing_trigger ? 'green' : 'yellow'}">${routing.self_healing_trigger ? 'ACTIVE' : 'IDLE'}</span>
                        </div>
                        
                        ${routing.reasoning?.length > 0 ? `
                            <div class="recommendations">
                                ${routing.reasoning.map(r => `<div class="recommendation-item">→ ${r}</div>`).join('')}
                            </div>
                        ` : ''}
                    </div>
                </div>
            `;
        }
        
        function renderRecommendations(data) {
            const recommendations = data.cognitive_context?.recommendations || [];
            if (recommendations.length === 0) return '';
            
            return `
                <h2 class="section-title">💡 System Recommendations</h2>
                <div class="layer-card support" style="grid-column: 1 / -1;">
                    <div class="layer-content">
                        <div class="recommendations" style="background: rgba(63, 185, 80, 0.05);">
                            ${recommendations.map(r => `<div class="recommendation-item" style="padding: 8px 0;">→ ${r}</div>`).join('')}
                        </div>
                    </div>
                </div>
            `;
        }
        
        function renderFinalOutput(data) {
            return `
                <h2 class="section-title">📝 Latest Output</h2>
                <div class="layer-card support" style="grid-column: 1 / -1;">
                    <div class="layer-content">
                        <div class="metric-row">
                            <span class="metric-label">Override Applied</span>
                            <span class="metric-value ${data.was_overridden ? 'green' : 'yellow'}">${data.was_overridden ? '✓ YES' : '✗ NO'}</span>
                        </div>
                        <div style="margin-top: 15px; padding: 15px; background: var(--bg-tertiary); border-radius: 8px; font-family: monospace; font-size: 0.9em; line-height: 1.6; max-height: 200px; overflow-y: auto;">
                            ${data.final_answer || '-'}
                        </div>
                    </div>
                </div>
            `;
        }
        
        function updateDashboard(data) {
            const container = document.getElementById('dashboard-content');
            
            if (!data || data.error) {
                container.innerHTML = `
                    <div class="error-state" style="grid-column: 1 / -1;">
                        <h2>⚠️ Connection Error</h2>
                        <p>${data?.error || 'Unable to fetch cognitive state'}</p>
                        <p style="margin-top: 10px; font-size: 0.9em;">Retrying in ${REFRESH_INTERVAL / 1000} seconds...</p>
                    </div>
                `;
                return;
            }
            
            container.innerHTML = 
                renderMemoryLayers(data) +
                renderIntelligenceLayers(data) +
                renderAdvancedLayers(data) +
                renderMetaSupervisor(data) +
                renderRecommendations(data) +
                renderFinalOutput(data);
        }
        
        function updateStatusIndicators(data) {
            const backend = document.getElementById('backend-status');
            const memory = document.getElementById('memory-status');
            const cognitive = document.getElementById('cognitive-status');
            
            if (data && !data.error) {
                backend.className = 'status-dot green';
                memory.className = data.cognitive_context?.routing ? 'status-dot green' : 'status-dot yellow';
                // Check both 'stable' boolean and 'level' property
                const isStable = data.cognitive_context?.stability?.stable === true || 
                                data.cognitive_context?.stability?.level === 'stable';
                cognitive.className = isStable ? 'status-dot green' : 'status-dot yellow';
            } else {
                backend.className = 'status-dot red';
                memory.className = 'status-dot red';
                cognitive.className = 'status-dot red';
            }
        }
        
        async function fetchState() {
            try {
                const response = await fetch('/api/state');
                const data = await response.json();
                lastData = data;
                updateDashboard(data);
                updateStatusIndicators(data);
                document.getElementById('last-update').textContent = new Date().toLocaleTimeString();
            } catch (error) {
                console.error('Fetch error:', error);
                updateDashboard({ error: error.message });
                updateStatusIndicators(null);
            }
        }
        
        // Initial fetch and interval
        fetchState();
        setInterval(fetchState, REFRESH_INTERVAL);
    </script>
</body>
</html>
"""

@app.get("/", response_class=HTMLResponse)
async def dashboard():
    """Serve the monitoring dashboard"""
    return HTML_TEMPLATE


@app.get("/api/state")
async def get_cognitive_state():
    """
    Fetch current cognitive state from backend.
    Uses FAST /chat/cognitive/status endpoint (no LLM call).
    """
    import requests
    try:
        response = requests.get(
            f"{BACKEND_URL}/chat/cognitive/status",
            timeout=5
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            return {"error": f"Backend returned {response.status_code}: {response.text[:100]}"}
            
    except requests.exceptions.ConnectionError:
        return {"error": "Cannot connect to backend API (port 8000) - is it running?"}
    except requests.exceptions.Timeout:
        return {"error": "Backend API timeout - request took too long"}
    except Exception as e:
        return {"error": f"{type(e).__name__}: {str(e)}"}


@app.get("/api/health")
async def health():
    """Health check endpoint"""
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(f"{BACKEND_URL}/health")
            backend_ok = response.status_code == 200
    except:
        backend_ok = False
    
    return {
        "status": "ok" if backend_ok else "degraded",
        "backend": "connected" if backend_ok else "disconnected",
        "timestamp": datetime.now().isoformat()
    }


if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("🧠 EFC COGNITIVE STACK MONITOR")
    print("=" * 60)
    print("\n📊 Monitoring ALL cognitive layers:")
    print("   • Core Memory Layers (1-3): CMC, SMM, Neo4j")
    print("   • Intelligence Layers (4-6): DDE, AME, MLC")
    print("   • Advanced Layers (7-9): MIR, MCA, MCE")
    print("   • Meta-Supervisor: Intent, Value, Motivation, Balance, Stability, Routing")
    print("\n🔗 Dashboard: http://localhost:8080")
    print("🔗 API State: http://localhost:8080/api/state")
    print("🔗 Health:    http://localhost:8080/api/health")
    print("\n⏱️  Auto-refresh every 3 seconds")
    print("📖 MONITORING ONLY - No input capability")
    print("=" * 60 + "\n")
    
    uvicorn.run(app, host="0.0.0.0", port=8080)
