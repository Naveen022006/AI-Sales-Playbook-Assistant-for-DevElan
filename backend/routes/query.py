"""
Query Routes.
Main endpoint for processing sales objection queries through the RAG pipeline.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from rag.generator import generate_sales_suggestion
from database import save_conversation

router = APIRouter(prefix="/api", tags=["query"])


class QueryRequest(BaseModel):
    """Request model for objection queries."""
    query: str = Field(
        ...,
        min_length=1,
        max_length=1000,
        description="The customer objection or sales scenario to get help with"
    )
    top_k: int = Field(
        default=5,
        ge=1,
        le=10,
        description="Number of playbook entries to retrieve"
    )


class ChunkInfo(BaseModel):
    """Information about a retrieved playbook chunk."""
    category: str
    objection_type: str
    strategy: str
    similarity: float


class QueryResponse(BaseModel):
    """Response model for objection queries."""
    query: str
    response: str
    retrieved_chunks: list[ChunkInfo]
    similarity_scores: list[float]
    metadata: dict


@router.post("/query", response_model=QueryResponse)
async def query_objection(request: QueryRequest):
    """
    Process a sales objection query through the RAG pipeline.
    
    1. Embeds the query
    2. Retrieves relevant playbook chunks from Supabase
    3. Augments the prompt with retrieved context
    4. Generates structured sales suggestions via Groq
    5. Saves the conversation to the database
    """
    try:
        # Run RAG pipeline
        result = generate_sales_suggestion(request.query)

        # Save conversation to database
        try:
            save_conversation(
                query=request.query,
                response=result["response"],
                retrieved_chunks=result["retrieved_chunks"],
                similarity_scores=result["similarity_scores"]
            )
        except Exception as e:
            print(f"Warning: Failed to save conversation: {e}")

        return QueryResponse(
            query=request.query,
            response=result["response"],
            retrieved_chunks=[
                ChunkInfo(**chunk) for chunk in result["retrieved_chunks"]
            ],
            similarity_scores=result["similarity_scores"],
            metadata=result["metadata"]
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error processing query: {str(e)}"
        )
