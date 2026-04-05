"""
Retriever Module.
Performs vector similarity search against Supabase pgvector
to find the most relevant playbook chunks for a given query.
"""

from rag.embeddings import generate_embedding
from database import search_similar_chunks
from config import config


def retrieve_relevant_chunks(query: str,
                             top_k: int = None,
                             threshold: float = None) -> list[dict]:
    """
    Retrieve the most relevant playbook chunks for a given objection query.
    
    Args:
        query: The salesperson's description of the customer objection
        top_k: Number of results to return (default: config.TOP_K_RESULTS)
        threshold: Minimum similarity score (default: config.SIMILARITY_THRESHOLD)
        
    Returns:
        List of matching chunks with similarity scores, sorted by relevance
    """
    # Generate embedding for the query
    query_embedding = generate_embedding(query)

    # Search Supabase for similar chunks
    results = search_similar_chunks(
        query_embedding=query_embedding,
        match_threshold=threshold or config.SIMILARITY_THRESHOLD,
        match_count=top_k or config.TOP_K_RESULTS
    )

    # Format results
    formatted_results = []
    for result in results:
        formatted_results.append({
            "id": result.get("id"),
            "category": result.get("category", ""),
            "objection_type": result.get("objection_type", ""),
            "strategy": result.get("strategy", ""),
            "content": result.get("content", ""),
            "similarity": round(result.get("similarity", 0), 4),
            "metadata": result.get("metadata", {})
        })

    return formatted_results


def format_context_for_prompt(chunks: list[dict]) -> str:
    """
    Format retrieved chunks into a context string for the LLM prompt.
    
    Args:
        chunks: List of retrieved chunk dictionaries
        
    Returns:
        Formatted context string
    """
    if not chunks:
        return "No relevant playbook entries found for this objection."

    context_parts = []
    for i, chunk in enumerate(chunks, 1):
        part = (
            f"--- Playbook Entry {i} (Relevance: {chunk['similarity']:.1%}) ---\n"
            f"Category: {chunk['category']}\n"
            f"Objection: \"{chunk['objection_type']}\"\n"
            f"Strategy: {chunk['strategy']}\n"
            f"Content:\n{chunk['content']}\n"
        )
        context_parts.append(part)

    return "\n".join(context_parts)
