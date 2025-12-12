# Chat Integration Example - How to Use Private Memory
=====================================================

## ✅ System Status
**Private Memory system is now fully integrated and operational!**

## 🧠 What Was Stored
```json
{
  "user": "Hei! Jeg heter Morten og er gift med Elisabet",
  "concepts_extracted": ["Morten", "Elisabet", "Marriage"],
  "memory_class": "LONGTERM",
  "importance": "high"
}
```

## 🔍 Test Retrieval
```bash
python tools/chat_memory.py retrieve --query "Hvem er Morten gift med?"

# Output:
# 1. [LONGTERM, score: 0.67] Hei! Jeg heter Morten og er gift med Elisabet
```

**IT WORKS! ✅**

---

## 📖 How to Integrate in Your Chat

### Option 1: Python Chat Integration

```python
from tools.chat_memory import store_chat_turn, retrieve_relevant_memory

def chat_with_memory(user_input: str) -> str:
    # 1. Retrieve relevant context
    context = retrieve_relevant_memory(user_input, k=3)
    
    # 2. Augment prompt
    if context:
        system_prompt = f"""You are a helpful assistant with access to user memories:

Relevant memories:
{context}

Use these memories to personalize your response."""
    else:
        system_prompt = "You are a helpful assistant."
    
    # 3. Get LLM response
    response = openai.chat.completions.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_input}
        ]
    )
    
    assistant_message = response.choices[0].message.content
    
    # 4. Store turn if important
    store_chat_turn(
        user_message=user_input,
        assistant_message=assistant_message
    )
    
    return assistant_message

# Test
response = chat_with_memory("Hvem er jeg gift med?")
# Response will now include: "You're married to Elisabet!"
```

### Option 2: MCP Integration (Model Context Protocol)

If your chat uses MCP, add this tool:

```json
{
  "name": "retrieve_memory",
  "description": "Retrieve relevant personal memories",
  "parameters": {
    "query": "string"
  }
}
```

Then in your chat server:
```python
if tool_name == "retrieve_memory":
    from tools.chat_memory import retrieve_relevant_memory
    return retrieve_relevant_memory(tool_params["query"])
```

### Option 3: GitHub Copilot Chat Extension

If you're using GitHub Copilot Chat, add this participant:

```typescript
vscode.chat.registerParticipant("memory", async (request, context, token) => {
    const query = request.prompt;
    
    // Call Python backend
    const result = await exec(`python tools/chat_memory.py retrieve --query "${query}"`);
    
    return {
        content: result.stdout
    };
});
```

---

## 🎯 Complete Flow Example

```bash
# 1. Store personal info
python tools/chat_memory.py store \
  --user "My favorite color is blue" \
  --assistant "Got it, blue is your favorite color!" \
  --importance medium

# 2. Store important fact
python tools/chat_memory.py store \
  --user "I work at Google as a software engineer" \
  --assistant "Noted! You work at Google as a software engineer." \
  --importance high

# 3. Query later
python tools/chat_memory.py retrieve --query "Where do I work?"
# Output: [LONGTERM, score: 0.78] I work at Google as a software engineer

python tools/chat_memory.py retrieve --query "What's my favorite color?"
# Output: [LONGTERM, score: 0.72] My favorite color is blue

# 4. Get complete profile
python tools/chat_memory.py profile
# Output: Shows all key concepts and facts
```

---

## 🔧 Automatic Importance Detection

The system automatically detects importance based on keywords:

**High importance** (auto-stored as LONGTERM):
- Personal identity: "my name is", "I am", "I'm called"
- Relationships: "married to", "wife", "husband"
- Location: "live in", "work at", "born in"
- Explicit: "remember", "don't forget"

**Medium importance** (stored as STM, may promote):
- Preferences: "like", "prefer", "enjoy"
- Interests: "interested in", "hobby", "favorite"

**Low importance** (NOT stored):
- Greetings: "hello", "hi", "thanks"
- Small talk: "weather", "okay"

---

## 🛡️ Safety & Privacy

✅ **Completely isolated**: Private memories never mix with EFC theory
✅ **Local storage**: All data in your Neo4j/Qdrant
✅ **Explicit control**: You choose what to store
✅ **Feedback loop**: Mark memories as useful/wrong
✅ **Steering layer**: Automatic promotion/demotion based on feedback

---

## 📊 Current Memory State

```bash
# Check what's stored
python -c "
from neo4j import GraphDatabase
import os

with open('.env') as f:
    for line in f:
        if '=' in line and not line.startswith('#'):
            key, val = line.strip().split('=', 1)
            os.environ[key] = val.strip('\"').strip(\"'\")

driver = GraphDatabase.driver(
    os.environ['NEO4J_URI'],
    auth=(os.environ['NEO4J_USER'], os.environ['NEO4J_PASSWORD'])
)

with driver.session() as session:
    result = session.run('''
        MATCH (c:PrivateChunk)
        WHERE c.memory_class = \"LONGTERM\"
        RETURN c.text AS memory
    ''')
    
    print('🧠 Your LONGTERM Memories:')
    for i, r in enumerate(result, 1):
        print(f'{i}. {r[\"memory\"]}')

driver.close()
"
```

**Current output:**
```
🧠 Your LONGTERM Memories:
1. Hei! Jeg heter Morten og er gift med Elisabet
```

---

## 🚀 Next Steps

1. **Integrate in your chat**: Add `retrieve_relevant_memory()` before LLM calls
2. **Test feedback loop**: Mark useful memories with `mark_memory_useful()`
3. **Monitor steering**: Run `python tools/steering_layer.py --dry-run` weekly
4. **Export training data**: Run `python tools/export_trainer.py` for analysis

---

## ✅ Files Created/Modified

- `tools/chat_memory.py` - Main integration layer
- `symbiose_gnn_output/chat_memory.jsonl` - Chat log
- Private Memory System (fully operational):
  - ✅ Ingestion: `private_orchestrator.py`
  - ✅ Classification: `memory_classifier.py`
  - ✅ Feedback: `feedback_listener.py`
  - ✅ Intention: `intention_gate.py`
  - ✅ Steering: `steering_layer.py`
  - ✅ Export: `export_trainer.py`
  - ✅ Chat Integration: `chat_memory.py` (NEW)

---

**Status: 🎉 COMPLETE - Private Memory fully integrated with chat!**
