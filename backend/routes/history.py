"""
History Routes.
Endpoints for managing conversation history.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from database import get_conversations, delete_conversation, clear_conversations

router = APIRouter(prefix="/api/history", tags=["history"])


class ConversationItem(BaseModel):
    """A single conversation record."""
    id: int
    query: str
    response: str
    retrieved_chunks: list
    similarity_scores: list
    created_at: str


@router.get("")
async def list_conversations(limit: int = 50):
    """Get recent conversation history."""
    try:
        conversations = get_conversations(limit=limit)
        return {"conversations": conversations, "count": len(conversations)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{conversation_id}")
async def remove_conversation(conversation_id: int):
    """Delete a specific conversation."""
    try:
        delete_conversation(conversation_id)
        return {"message": f"Conversation {conversation_id} deleted"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("")
async def clear_all_conversations():
    """Delete all conversation history."""
    try:
        clear_conversations()
        return {"message": "All conversations cleared"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
