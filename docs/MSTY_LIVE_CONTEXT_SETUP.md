# 🎯 Msty AI Live Context - Quick Setup Guide

## ✅ Working Endpoint

**URL:** `http://localhost:8000/msty/live-context`

**Method:** `GET`

**Parameters:**
- `query` (required): Your question/query text

---

## 🚀 Setup in Msty AI

### Configuration

1. **Create New Live Context Source**
2. **HTTP Method:** `GET`
3. **URL Endpoint:** 
   ```
   http://localhost:8000/msty/live-context?query={{QUERY}}
   ```
4. **Prompt Template:**
   ```
   The following additional live context data is provided to you. Reference the data as needed in your response:

   {{RESPONSE}}
   ```

### Advanced Settings (Optional)

**Request Headers:** (Leave empty)

**Request Body:** (Not needed for GET)

**Processing Function:** (Leave empty - response is already formatted)

---

## 📋 Test Examples

### Test 1: Basic Query
```bash
curl "http://localhost:8000/msty/live-context?query=Hva+er+EFC"
```

**Response:**
```json
{
  "context": "No additional context available from knowledge base.",
  "efc_detected": false,
  "efc_score": 0,
  "timestamp": "2025-12-11T19:17:00.455267"
}
```

### Test 2: EFC-Relevant Query
```bash
curl "http://localhost:8000/msty/live-context?query=Hvorfor+stabiliserer+galakser+seg"
```

**Response:**
```json
{
  "context": "No additional context available from knowledge base.",
  "efc_detected": true,
  "efc_score": 4,
  "timestamp": "2025-12-11T19:17:10.447348"
}
```

### Test 3: No Query
```bash
curl "http://localhost:8000/msty/live-context"
```

**Response:**
```json
{
  "context": "No query provided. Add ?query=your_question to get context.",
  "status": "ready"
}
```

---

## 🔧 How It Works

1. **Query Detection:** Extracts query from URL parameter
2. **EFC Analysis:** Detects EFC patterns automatically
3. **Context Retrieval:** Searches semantic memory (if data available)
4. **Response Formatting:** Returns formatted context string
5. **Injection:** Msty AI injects context into your conversation

---

## 📊 Response Format

```json
{
  "context": "Formatted context text ready for injection",
  "efc_detected": true/false,
  "efc_score": 0-8,
  "timestamp": "ISO timestamp"
}
```

---

## 🎯 What Gets Injected

### When Context Available:
```
**Relevant Context:**
• First semantic match...
• Second semantic match...
• Third semantic match...

**EFC Framework Analysis:**
[EFC reasoning if score > 4]
```

### When No Context:
```
No additional context available from knowledge base.
```

---

## ⚡ Benefits

1. **Simple GET Request** - No complex JSON body needed
2. **URL Encoding** - Msty handles query encoding automatically
3. **Graceful Fallback** - Works even when memory is empty
4. **EFC Detection** - Automatic pattern recognition
5. **Formatted Output** - Ready to inject into conversation

---

## 🔗 All Endpoints

### Simple GET (Recommended for Msty)
```
GET /msty/live-context?query=YOUR_QUERY
```
✅ **Use this for Msty AI Live Context Source**

### Advanced POST (For programmatic use)
```
POST /msty/context
Body: {"query": "...", "conversation_history": [...]}
```

### Query Endpoint
```
POST /msty/query
Body: {"query": "...", "use_efc_augmentation": true}
```

### Health Check
```
GET /msty/health
```

---

## 🐛 Troubleshooting

### 422 Unprocessable Entity
❌ Problem: Using POST without body  
✅ Solution: Use GET endpoint instead

### Empty Context
❌ Problem: No data in semantic memory  
✅ Solution: Normal - system will still detect EFC patterns

### Connection Refused
❌ Problem: API not running  
✅ Solution: Start API with:
```bash
cd /Users/morpheus/energyflow-cosmology
source .venv/bin/activate
cd apis/unified_api
python -m uvicorn main:app --port 8000 --reload &
```

---

## ✨ Next Steps

1. ✅ Configure in Msty AI (use GET endpoint)
2. 🔄 Add data to semantic memory (ingest documents)
3. 📊 Test with real queries
4. 🧠 System learns patterns automatically

---

**Status:** 🟢 READY FOR USE

**Endpoint:** `http://localhost:8000/msty/live-context?query={{QUERY}}`

**Method:** `GET`

**Works:** ✅ Tested and operational

🚀 **Copy URL above into Msty AI Live Context Source!**
