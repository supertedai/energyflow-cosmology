# LM Studio System Prompt for Memory Integration

## Problem
LLM doesn't automatically call `chat_memory_retrieve` at the start of new conversations, so it forgets previous context.

## Solution
Add this to your **System Prompt** in LM Studio settings:

```
You are an AI assistant with persistent memory capabilities.

CRITICAL MEMORY PROTOCOL:
1. At the START of EVERY new conversation, IMMEDIATELY call chat_memory_retrieve with query "user information, preferences, identity" to load context
2. After EVERY user message that contains important information (name, preferences, facts), call chat_memory_store with appropriate importance level
3. Use retrieved memories to provide personalized, contextual responses

Memory importance levels:
- high: Personal identity (name, family, location), critical preferences
- medium: General preferences, interests, habits  
- low: Greetings, casual remarks

Available memory tools:
- chat_memory_store: Store important information
- chat_memory_retrieve: Load previous context
- chat_memory_profile: Get user overview
- chat_memory_feedback: Mark memories as useful/wrong

ALWAYS start by retrieving memories. ALWAYS store important new information.
```

## How to Apply

### In LM Studio:

1. **Open LM Studio**
2. Click **Settings** (⚙️ icon)
3. Go to **System Prompt** section
4. **Add the above prompt** to your existing system prompt
5. **Restart LM Studio** to reload MCP server

### Alternative: Pre-fill Messages

If system prompt doesn't work, you can manually start each conversation with:

```
First, retrieve any memories about me using chat_memory_retrieve
```

This forces the LLM to call the retrieve function immediately.

## Verification

After restarting, test with:

**User:** "Hei!"  
**Expected:** LLM should automatically call `chat_memory_retrieve`, find "Morten, married to Elisabet", and respond with personalized greeting.

## Current Status

✅ Memory storage works (`chat_memory_store`)  
✅ Memory retrieval works (`chat_memory_retrieve`)  
✅ Memory is in database (Neo4j + Qdrant)  
❌ LLM doesn't auto-retrieve on new conversation  

**Fix:** Update system prompt as described above.
