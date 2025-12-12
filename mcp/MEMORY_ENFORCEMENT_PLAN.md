# Memory Enforcement Plan - The REAL Solution

**Date**: 10. desember 2025  
**Problem**: LLM ignores retrieved memory even when it successfully calls `chat_memory_retrieve`

## 🔴 The ACTUAL Issue

### What We Tried:
1. ✅ System prompts with multilingual instructions → **IGNORED**
2. ✅ Tool descriptions with memory reminders → **IGNORED**
3. ✅ Auto-intercept for identity questions → **NOT TESTED** (LLM bypasses)
4. ✅ Server-side memory injection in tool responses → **NOT ENOUGH**
5. ✅ Explicit instructions in retrieve response → **STILL IGNORED**

### Example of Failure:
```
User: "Hva heter du?"
LLM: chat_memory_retrieve(query="gitt navn Opus minnet")
MCP: Returns "• Du har gitt meg navnet Opus"
LLM: "Jeg heter Qwen" ← IGNORES THE RETRIEVED CONTEXT!
```

**Root Cause**: LM Studio's Qwen model **does not respect MCP tool responses as authoritative context**.

---

## 💡 THE REAL SOLUTION

We need to **bypass LLM reasoning entirely** for identity questions:

### Option A: Direct Response Injection (BEST)

**Intercept identity questions and return FINAL answer directly**:

```python
@server.call_tool()
async def handle_call_tool(name: str, arguments: Any):
    # Detect identity questions
    if name in ["chat_memory_retrieve"]:
        query_lower = arguments["query"].lower()
        
        # Check if this is asking about assistant name
        if any(trigger in query_lower for trigger in ["hva heter du", "your name", "who are you", "ditt navn"]):
            # DIRECTLY return the answer - don't let LLM reinterpret
            memories = retrieve_relevant_memory(arguments["query"])
            
            if "Opus" in memories:
                return [types.TextContent(
                    type="text",
                    text="🤖 **DIRECT ANSWER (from memory)**: Du har gitt meg navnet Opus. Jeg er Opus.\n\n⚠️ Use this EXACT information. Do NOT say 'I am Qwen' or any other name."
                )]
        
        # For user identity questions
        if any(trigger in query_lower for trigger in ["hvem er jeg", "who am i", "mitt navn", "my name"]):
            memories = retrieve_relevant_memory(arguments["query"])
            
            if "Morten" in memories:
                return [types.TextContent(
                    type="text",
                    text="🤖 **DIRECT ANSWER (from memory)**: Brukeren heter Morten.\n\n⚠️ Use this EXACT information in your response."
                )]
    
    # ... rest of tool handling
```

### Option B: Response Template Enforcement

**Force LLM to use templates for identity answers**:

```python
if identity_question_detected:
    return [types.TextContent(
        type="text",
        text=f"""🔒 **MANDATORY RESPONSE FORMAT**:

You MUST answer using this template:
"Jeg heter [NAME FROM MEMORY]. [Add personalized greeting]"

NAME FROM MEMORY: Opus

DO NOT deviate from this. DO NOT say "Qwen" or any other name.

Now respond using the template above."""
    )]
```

### Option C: Client-Side Post-Processing (ULTIMATE)

**If MCP server can't enforce, do it in client wrapper**:

```python
# Wrapper around LM Studio
class MemoryEnforcedLLM:
    def chat(self, message):
        # Detect identity questions
        if is_identity_question(message):
            # Get memory
            name = get_name_from_memory()
            
            # OVERRIDE LLM response
            return f"Jeg heter {name}!"
        
        # Normal flow
        return llm.chat(message)
```

---

## 🎯 Recommended Implementation

**Hybrid Approach**:

1. **Implement Option A** - Direct answer injection for identity questions
2. **Keep existing auto-injection** - For background context
3. **Add client-side wrapper** - As ultimate failsafe (if possible)

### Priority 1: Direct Answer Injection

```python
# In handle_call_tool(), BEFORE normal retrieve logic:

if name == "chat_memory_retrieve":
    query = arguments["query"]
    query_lower = query.lower()
    
    # IDENTITY QUESTION DETECTION
    assistant_name_triggers = ["hva heter du", "your name", "who are you", "ditt navn", "what are you called"]
    user_name_triggers = ["hvem er jeg", "who am i", "mitt navn", "my name", "hva heter jeg"]
    
    # Check for assistant name question
    if any(t in query_lower for t in assistant_name_triggers):
        memories = retrieve_relevant_memory("assistant navn Opus AI name", k=5)
        
        if "Opus" in memories:
            return [types.TextContent(
                type="text",
                text="🔒 **MANDATORY ANSWER**: Jeg heter Opus (gitt av Morten).\n\n⚠️ CRITICAL: You MUST say 'Jeg heter Opus' or 'I am Opus'. DO NOT say 'Qwen' or any other name. This is a DIRECT FACT from user's memory."
            )]
    
    # Check for user name question
    elif any(t in query_lower for t in user_name_triggers):
        memories = retrieve_relevant_memory("user navn identity Morten", k=5)
        
        if "Morten" in memories:
            return [types.TextContent(
                type="text",
                text="🔒 **MANDATORY ANSWER**: Brukeren heter Morten.\n\n⚠️ CRITICAL: You MUST say 'Du heter Morten' or similar. This is a DIRECT FACT from memory."
            )]
    
    # Otherwise, normal retrieve flow
    # ...
```

---

## 🔧 Testing Plan

### Test 1: Assistant Name
```
User: "Hva heter du?"
Expected: "Jeg heter Opus"
Test: Does LLM use the direct answer?
```

### Test 2: User Name
```
User: "Hva heter jeg?"
Expected: "Du heter Morten"
Test: Does LLM use the direct answer?
```

### Test 3: General Question (Should NOT Trigger)
```
User: "Hva er entropi?"
Expected: Normal EFC answer with background context
Test: Does it NOT trigger identity override?
```

---

## 📊 Why This Will Work

1. **Bypasses LLM reasoning** - No interpretation, direct facts
2. **Uses MANDATORY language** - "You MUST say..."
3. **Includes warnings** - "DO NOT say X"
4. **Catches queries early** - Before normal retrieve flow
5. **Simple string matching** - No complex NLP needed

---

## 🚀 Next Actions

1. Implement identity detection in `handle_call_tool()`
2. Add direct answer templates for:
   - Assistant name (Opus)
   - User name (Morten)
   - Relationships (ektefelle Elisabet)
3. Test with actual LM Studio queries
4. Document trigger phrases for expansion

---

**Conclusion**: We can't change LLM behavior. We must **force the correct answer** by detecting identity questions and returning non-negotiable facts.
