"""
Database module for Supabase operations.
Handles all database interactions for playbook chunks and conversations.
"""

import json
from supabase import create_client, Client
from config import config


def get_supabase_client() -> Client:
    """Create and return a Supabase client."""
    return create_client(config.SUPABASE_URL, config.SUPABASE_ANON_KEY)


# Global client instance
supabase: Client = None


def init_db():
    """Initialize the database connection."""
    global supabase
    supabase = get_supabase_client()
    return supabase


def get_db() -> Client:
    """Get the database client, initializing if necessary."""
    global supabase
    if supabase is None:
        supabase = get_supabase_client()
    return supabase


# ─── Playbook Chunks Operations ───

def insert_chunk(category: str, objection_type: str, strategy: str,
                 content: str, embedding: list[float], metadata: dict = None) -> dict:
    """Insert a playbook chunk with its embedding into the database."""
    db = get_db()
    data = {
        "category": category,
        "objection_type": objection_type,
        "strategy": strategy,
        "content": content,
        "embedding": embedding,
        "metadata": metadata or {}
    }
    result = db.table("playbook_chunks").insert(data).execute()
    return result.data[0] if result.data else None


def get_all_chunks() -> list[dict]:
    """Get all playbook chunks (without embeddings for efficiency)."""
    db = get_db()
    result = db.table("playbook_chunks").select(
        "id, category, objection_type, strategy, content, metadata, created_at"
    ).execute()
    return result.data


def get_chunk_count() -> int:
    """Get the total number of playbook chunks."""
    db = get_db()
    result = db.table("playbook_chunks").select("id", count="exact").execute()
    return result.count or 0


def get_categories() -> list[str]:
    """Get unique categories from playbook chunks."""
    db = get_db()
    result = db.table("playbook_chunks").select("category").execute()
    categories = list(set(chunk["category"] for chunk in result.data))
    return sorted(categories)


def search_similar_chunks(query_embedding: list[float],
                          match_threshold: float = None,
                          match_count: int = None) -> list[dict]:
    """Search for similar playbook chunks using vector similarity."""
    db = get_db()
    threshold = match_threshold or config.SIMILARITY_THRESHOLD
    count = match_count or config.TOP_K_RESULTS

    result = db.rpc("match_chunks", {
        "query_embedding": query_embedding,
        "match_threshold": threshold,
        "match_count": count
    }).execute()

    return result.data


def delete_all_chunks() -> bool:
    """Delete all playbook chunks (for re-seeding)."""
    db = get_db()
    db.table("playbook_chunks").delete().neq("id", 0).execute()
    return True


# ─── Conversations Operations ───

def save_conversation(query: str, response: str,
                      retrieved_chunks: list = None,
                      similarity_scores: list = None) -> dict:
    """Save a conversation to the database."""
    db = get_db()
    data = {
        "query": query,
        "response": response,
        "retrieved_chunks": retrieved_chunks or [],
        "similarity_scores": similarity_scores or []
    }
    result = db.table("conversations").insert(data).execute()
    return result.data[0] if result.data else None


def get_conversations(limit: int = 50) -> list[dict]:
    """Get recent conversations ordered by creation time."""
    db = get_db()
    result = db.table("conversations").select("*").order(
        "created_at", desc=True
    ).limit(limit).execute()
    return result.data


def delete_conversation(conversation_id: int) -> bool:
    """Delete a specific conversation."""
    db = get_db()
    db.table("conversations").delete().eq("id", conversation_id).execute()
    return True


def clear_conversations() -> bool:
    """Delete all conversations."""
    db = get_db()
    db.table("conversations").delete().neq("id", 0).execute()
    return True
