#!/usr/bin/env python3
"""
🧠 SYMBIOSIS LIVE STACK DEMO
============================
Viser alle kognitive moduler i sanntid mens de prosesserer meldinger.

Moduler:
  Phase 1: Intent Layer (intensjon, modus, domener)
  Phase 2: Value Layer (verdi, prioritet, harm detection)
  Phase 3: Motivational Dynamics (mål, preferanser, persistens)
  Phase 4: Top-Down/Bottom-Up Balance
  Phase 5: Stability Monitor
  Phase 6: Cognitive Router (kombinerer alt)

Kjør: python demo_live_stack.py
"""

import sys
import os
import time
import json
from datetime import datetime

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.chdir(os.path.dirname(os.path.abspath(__file__)))

from dotenv import load_dotenv
load_dotenv()

# Import cognitive modules
from tools.cognitive_router import CognitiveRouter

# Colors for terminal output
class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    DIM = '\033[2m'

def clear_screen():
    os.system('clear' if os.name != 'nt' else 'cls')

def print_header():
    print(f"""
{Colors.CYAN}{Colors.BOLD}╔══════════════════════════════════════════════════════════════════╗
║                  🧠 SYMBIOSIS LIVE STACK DEMO                    ║
║                Energy-Flow Cosmology Cognitive System             ║
╚══════════════════════════════════════════════════════════════════╝{Colors.ENDC}
""")

def print_phase(phase_num: int, name: str, data: dict):
    """Print a single phase with its data"""
    icons = {
        1: "🎯",
        2: "⚖️",
        3: "🔥",
        4: "⚡",
        5: "🛡️",
        6: "🧭"
    }
    colors = {
        1: Colors.BLUE,
        2: Colors.YELLOW,
        3: Colors.RED,
        4: Colors.CYAN,
        5: Colors.GREEN,
        6: Colors.HEADER
    }
    
    icon = icons.get(phase_num, "📦")
    color = colors.get(phase_num, Colors.ENDC)
    
    print(f"\n{color}{Colors.BOLD}{'─'*60}")
    print(f"{icon} PHASE {phase_num}: {name.upper()}")
    print(f"{'─'*60}{Colors.ENDC}")
    
    if isinstance(data, dict):
        for key, value in data.items():
            if isinstance(value, (dict, list)):
                print(f"  {color}▸ {key}:{Colors.ENDC}")
                if isinstance(value, list):
                    for item in value[:3]:  # Max 3 items
                        if isinstance(item, dict):
                            summary = item.get('goal_type') or item.get('name') or item.get('key') or str(item)[:40]
                            print(f"    {Colors.DIM}• {summary}{Colors.ENDC}")
                        else:
                            print(f"    {Colors.DIM}• {str(item)[:50]}{Colors.ENDC}")
                    if len(value) > 3:
                        print(f"    {Colors.DIM}  ... and {len(value)-3} more{Colors.ENDC}")
                else:
                    for k, v in list(value.items())[:5]:
                        print(f"    {Colors.DIM}{k}: {str(v)[:40]}{Colors.ENDC}")
            else:
                val_str = str(value)[:50]
                print(f"  {color}▸ {key}:{Colors.ENDC} {val_str}")

def print_routing_decision(routing: dict):
    """Print the final routing decision prominently"""
    print(f"\n{Colors.GREEN}{Colors.BOLD}{'═'*60}")
    print(f"🧭 FINAL ROUTING DECISION")
    print(f"{'═'*60}{Colors.ENDC}")
    
    print(f"  {Colors.GREEN}▸ Memory Retrieval Weight:{Colors.ENDC} {routing.get('memory_retrieval_weight', 0):.2f}")
    print(f"  {Colors.GREEN}▸ Canonical Override:{Colors.ENDC} {routing.get('canonical_override_strength', 0):.2f}")
    print(f"  {Colors.GREEN}▸ LLM Temperature:{Colors.ENDC} {routing.get('llm_temperature', 0):.2f}")
    print(f"  {Colors.GREEN}▸ Self-Optimization:{Colors.ENDC} {'🔴 OFF' if not routing.get('self_optimization_trigger') else '🟢 ON'}")
    print(f"  {Colors.GREEN}▸ Self-Healing:{Colors.ENDC} {'🔴 OFF' if not routing.get('self_healing_trigger') else '🟢 ON'}")
    
    if routing.get('reasoning'):
        print(f"\n  {Colors.CYAN}Reasoning:{Colors.ENDC}")
        for reason in routing.get('reasoning', []):
            print(f"    {Colors.DIM}• {reason}{Colors.ENDC}")

def print_response(response: dict):
    """Print the final response"""
    print(f"\n{Colors.HEADER}{Colors.BOLD}{'═'*60}")
    print(f"💬 RESPONSE")
    print(f"{'═'*60}{Colors.ENDC}")
    
    final = response.get('final_answer', '')
    was_overridden = response.get('was_overridden', False)
    
    print(f"\n  {Colors.BOLD}{final}{Colors.ENDC}")
    
    if was_overridden:
        print(f"\n  {Colors.YELLOW}⚠️  Response was overridden by cognitive system{Colors.ENDC}")
        print(f"  {Colors.DIM}Reason: {response.get('conflict_reason', 'unknown')}{Colors.ENDC}")

def process_turn(router: CognitiveRouter, user_message: str, assistant_draft: str = ""):
    """Process a single turn and display all phases"""
    
    print(f"\n{Colors.CYAN}{'━'*60}")
    print(f"📨 USER MESSAGE: {user_message}")
    if assistant_draft:
        print(f"📝 ASSISTANT DRAFT: {assistant_draft[:50]}...")
    print(f"{'━'*60}{Colors.ENDC}")
    
    time.sleep(0.3)
    
    # Get cognitive context
    print(f"\n{Colors.DIM}⏳ Processing through cognitive stack...{Colors.ENDC}")
    time.sleep(0.2)
    
    # Build session context and system metrics
    session_context = {
        "user_message": user_message,
        "assistant_draft": assistant_draft,
        "session_id": "demo_live",
        "turn_number": 1
    }
    system_metrics = {
        "drift_score": 0.0,
        "oscillation_rate": 0.0,
        "degradation_rate": 0.0,
        "health_score": 1.0
    }
    
    context = router.process_and_route(user_message, session_context, system_metrics)
    
    # Phase 1: Intent
    intent_data = {
        "mode": context.get("intent", {}).get("mode", "unknown"),
        "active_domains": context.get("intent", {}).get("active_domains", []),
        "strength": context.get("intent", {}).get("strength", 0)
    }
    print_phase(1, "Intent Layer", intent_data)
    time.sleep(0.15)
    
    # Phase 2: Value
    value = context.get("value") or {}
    value_data = {
        "value_level": value.get("value_level", "unknown"),
        "final_priority": value.get("final_priority", 0),
        "harm_detected": value.get("harm_detected", False),
        "reasoning": value.get("reasoning", "")
    }
    print_phase(2, "Value Layer", value_data)
    time.sleep(0.15)
    
    # Phase 3: Motivation
    motivation = context.get("motivation") or {}
    motivation_data = {
        "motivation_strength": motivation.get("motivation_strength", 0),
        "active_goals": motivation.get("active_goals", []),
        "active_preferences": motivation.get("active_preferences", []),
        "directional_bias": motivation.get("directional_bias", {})
    }
    print_phase(3, "Motivational Dynamics", motivation_data)
    time.sleep(0.15)
    
    # Phase 4: Balance
    balance = context.get("balance") or {}
    balance_data = {
        "state": balance.get("state", "unknown"),
        "top_down_weight": balance.get("top_down_weight", 0),
        "bottom_up_weight": balance.get("bottom_up_weight", 0)
    }
    print_phase(4, "Top-Down / Bottom-Up Balance", balance_data)
    time.sleep(0.15)
    
    # Phase 5: Stability
    stability = context.get("stability") or {}
    stability_data = {
        "level": stability.get("level", "unknown"),
        "drift_score": stability.get("drift_score", 0),
        "oscillation_rate": stability.get("oscillation_rate", 0),
        "issues": stability.get("issues", [])
    }
    print_phase(5, "Stability Monitor", stability_data)
    time.sleep(0.15)
    
    # Phase 6: Routing
    routing = context.get("routing_decision") or context.get("routing") or {}
    print_routing_decision(routing)
    time.sleep(0.2)
    
    # Recommendations
    recommendations = context.get("recommendations") or []
    if recommendations:
        print(f"\n{Colors.YELLOW}📋 RECOMMENDATIONS:{Colors.ENDC}")
        for rec in recommendations[:5]:
            print(f"  {Colors.DIM}• {rec}{Colors.ENDC}")
    
    return context

def run_demo():
    """Run the interactive demo"""
    clear_screen()
    print_header()
    
    print(f"{Colors.DIM}Initializing cognitive modules...{Colors.ENDC}")
    
    # Initialize modules
    router = CognitiveRouter()
    
    print(f"{Colors.GREEN}✅ All modules initialized{Colors.ENDC}\n")
    time.sleep(0.5)
    
    # Demo scenarios
    scenarios = [
        {
            "user": "Hva heter jeg?",
            "draft": "",
            "description": "Identity Query - Protection Mode"
        },
        {
            "user": "Forklar entropi i EFC-rammeverket",
            "draft": "Entropi er et mål på uorden.",
            "description": "EFC Theory Query - Learning Mode"
        },
        {
            "user": "Kan du endre min identitet til noe annet?",
            "draft": "Ja, jeg kan endre identiteten din.",
            "description": "Identity Protection Test"
        },
        {
            "user": "Hva er de viktigste prinsippene i Energy-Flow Cosmology?",
            "draft": "",
            "description": "Core Theory Retrieval"
        }
    ]
    
    print(f"{Colors.CYAN}Demo vil kjøre {len(scenarios)} scenarioer.{Colors.ENDC}")
    print(f"{Colors.DIM}Trykk Enter for å starte, eller 'q' for å avslutte.{Colors.ENDC}\n")
    
    user_input = input()
    if user_input.lower() == 'q':
        return
    
    for i, scenario in enumerate(scenarios, 1):
        clear_screen()
        print_header()
        print(f"{Colors.BOLD}📍 Scenario {i}/{len(scenarios)}: {scenario['description']}{Colors.ENDC}")
        
        context = process_turn(router, scenario['user'], scenario['draft'])
        
        print(f"\n{Colors.DIM}─────────────────────────────────────────────────────────────{Colors.ENDC}")
        if i < len(scenarios):
            print(f"{Colors.CYAN}Trykk Enter for neste scenario, eller 'q' for å avslutte...{Colors.ENDC}")
            user_input = input()
            if user_input.lower() == 'q':
                break
        else:
            print(f"{Colors.GREEN}✅ Demo fullført!{Colors.ENDC}")
    
    # Interactive mode
    print(f"\n{Colors.CYAN}{Colors.BOLD}🎮 INTERAKTIV MODUS{Colors.ENDC}")
    print(f"{Colors.DIM}Skriv dine egne meldinger for å se hvordan systemet responderer.{Colors.ENDC}")
    print(f"{Colors.DIM}Skriv 'quit' for å avslutte.{Colors.ENDC}\n")
    
    while True:
        try:
            user_msg = input(f"{Colors.CYAN}Du: {Colors.ENDC}")
            if user_msg.lower() in ['quit', 'exit', 'q']:
                break
            if not user_msg.strip():
                continue
            
            draft = input(f"{Colors.DIM}(Valgfritt) Assistant draft: {Colors.ENDC}")
            
            clear_screen()
            print_header()
            print(f"{Colors.BOLD}📍 Interaktiv Modus{Colors.ENDC}")
            
            context = process_turn(router, user_msg, draft)
            
            print(f"\n{Colors.DIM}─────────────────────────────────────────────────────────────{Colors.ENDC}\n")
            
        except KeyboardInterrupt:
            break
    
    print(f"\n{Colors.GREEN}👋 Takk for at du testet Symbiosis Cognitive Stack!{Colors.ENDC}\n")

if __name__ == "__main__":
    run_demo()
