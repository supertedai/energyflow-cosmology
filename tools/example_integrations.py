#!/usr/bin/env python3
"""
Example: Update existing APIs to use ingestion_hook
===================================================

This shows how to migrate existing API endpoints to use
the new unified ingestion pipeline.

BEFORE (old way - NO SYNC):
    qdrant.upsert(collection_name="efc", points=[...])
    session.run("CREATE (n:Document {id: $id})", ...)

AFTER (new way - PERFECT SYNC):
    from tools.ingestion_hook import ingest_text
    result = ingest_text(text=text, source=source)
"""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional, Dict, Any
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from tools.ingestion_hook import ingest_text

# -------------------------------------------------------------
# Example: Figshare Integration
# -------------------------------------------------------------

class FigshareWebhook(BaseModel):
    """Webhook payload from Figshare"""
    article_id: int
    title: str
    description: str
    doi: str
    authors: list
    url: str

def handle_figshare_webhook(payload: FigshareWebhook):
    """
    Handle Figshare webhook and ingest new article
    
    OLD WAY (deprecated):
        # Manual Qdrant insert
        # Manual Neo4j write
        # NO concept extraction
        # NO sync guarantee
    
    NEW WAY (required):
    """
    # Combine metadata into text
    text = f"""
    Title: {payload.title}
    
    Description: {payload.description}
    
    DOI: {payload.doi}
    Authors: {', '.join(payload.authors)}
    URL: {payload.url}
    """
    
    # Ingest through pipeline
    result = ingest_text(
        text=text,
        source=f"figshare_{payload.article_id}",
        input_type="document",
        metadata={
            "figshare_id": payload.article_id,
            "doi": payload.doi,
            "url": payload.url,
            "authors": payload.authors
        }
    )
    
    return result

# -------------------------------------------------------------
# Example: WordPress Integration
# -------------------------------------------------------------

class WordPressPost(BaseModel):
    """WordPress post data"""
    post_id: int
    title: str
    content: str
    excerpt: str
    author: str
    categories: list
    url: str

def handle_wordpress_post(post: WordPressPost):
    """
    Handle WordPress post and ingest content
    
    NEW WAY (required):
    """
    # Combine post data
    text = f"""
    # {post.title}
    
    {post.content}
    
    Excerpt: {post.excerpt}
    Categories: {', '.join(post.categories)}
    """
    
    # Ingest through pipeline
    result = ingest_text(
        text=text,
        source=f"wp_post_{post.post_id}",
        input_type="document",
        metadata={
            "wordpress_id": post.post_id,
            "url": post.url,
            "author": post.author,
            "categories": post.categories
        }
    )
    
    return result

# -------------------------------------------------------------
# Example: Chat/Conversation Integration
# -------------------------------------------------------------

class ChatMessage(BaseModel):
    """Chat message"""
    session_id: str
    user_id: str
    message: str
    timestamp: str

def handle_chat_message(msg: ChatMessage):
    """
    Handle chat message and ingest conversation
    
    NEW WAY (required):
    """
    # Format as conversation
    text = f"[{msg.timestamp}] User {msg.user_id}: {msg.message}"
    
    # Ingest through pipeline
    result = ingest_text(
        text=text,
        source=f"chat_{msg.session_id}",
        input_type="chat",
        metadata={
            "session_id": msg.session_id,
            "user_id": msg.user_id,
            "timestamp": msg.timestamp
        }
    )
    
    return result

# -------------------------------------------------------------
# Example: FastAPI Router
# -------------------------------------------------------------

app = FastAPI(title="Example Integration API")

@app.post("/webhook/figshare")
async def figshare_webhook(payload: FigshareWebhook):
    """Figshare webhook endpoint"""
    try:
        result = handle_figshare_webhook(payload)
        return {
            "status": "ingested",
            "document_id": result["document_id"],
            "chunks": len(result["chunk_ids"]),
            "concepts": result["concepts"]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/webhook/wordpress")
async def wordpress_webhook(post: WordPressPost):
    """WordPress webhook endpoint"""
    try:
        result = handle_wordpress_post(post)
        return {
            "status": "ingested",
            "document_id": result["document_id"],
            "chunks": len(result["chunk_ids"]),
            "concepts": result["concepts"]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/webhook/chat")
async def chat_webhook(msg: ChatMessage):
    """Chat message endpoint"""
    try:
        result = handle_chat_message(msg)
        return {
            "status": "ingested",
            "document_id": result["document_id"],
            "chunks": len(result["chunk_ids"]),
            "concepts": result["concepts"]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# -------------------------------------------------------------
# Usage Examples
# -------------------------------------------------------------

if __name__ == "__main__":
    print("Example integrations:")
    print()
    print("1. Figshare webhook:")
    print("   curl -X POST http://localhost:8000/webhook/figshare \\")
    print("        -H 'Content-Type: application/json' \\")
    print("        -d '{...}'")
    print()
    print("2. WordPress webhook:")
    print("   curl -X POST http://localhost:8000/webhook/wordpress \\")
    print("        -H 'Content-Type: application/json' \\")
    print("        -d '{...}'")
    print()
    print("3. Chat message:")
    print("   curl -X POST http://localhost:8000/webhook/chat \\")
    print("        -H 'Content-Type: application/json' \\")
    print("        -d '{...}'")
