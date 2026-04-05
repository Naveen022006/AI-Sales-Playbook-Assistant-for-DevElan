"""
Playbook Routes.
Endpoints for managing playbook content — upload, stats, and re-seed.
"""

import os
from fastapi import APIRouter, HTTPException, UploadFile, File
from pydantic import BaseModel
from pathlib import Path
from rag.chunker import parse_playbook, chunk_text
from rag.embeddings import generate_embedding, generate_embeddings_batch
from database import insert_chunk, get_chunk_count, get_categories, delete_all_chunks, get_all_chunks

router = APIRouter(prefix="/api/playbook", tags=["playbook"])


class PlaybookStats(BaseModel):
    """Playbook statistics."""
    total_chunks: int
    categories: list[str]
    status: str


class SeedRequest(BaseModel):
    """Request to seed the playbook from the default file."""
    force: bool = False  # If true, delete existing chunks first


class SeedResponse(BaseModel):
    """Response from seeding operation."""
    chunks_created: int
    categories: list[str]
    message: str


@router.get("/stats", response_model=PlaybookStats)
async def get_playbook_stats():
    """Get statistics about the loaded playbook content."""
    try:
        count = get_chunk_count()
        categories = get_categories() if count > 0 else []

        return PlaybookStats(
            total_chunks=count,
            categories=categories,
            status="loaded" if count > 0 else "empty"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/chunks")
async def get_playbook_chunks():
    """Get all playbook chunks (without embeddings)."""
    try:
        chunks = get_all_chunks()
        return {"chunks": chunks, "count": len(chunks)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/seed", response_model=SeedResponse)
async def seed_playbook(request: SeedRequest):
    """
    Seed the playbook from the default sample file.
    Parses the markdown, generates embeddings, and stores in Supabase.
    """
    try:
        # Find the playbook file
        playbook_path = Path(__file__).parent.parent.parent / "data" / "sales_playbook.md"
        if not playbook_path.exists():
            raise HTTPException(
                status_code=404,
                detail=f"Playbook file not found at {playbook_path}"
            )

        # Delete existing chunks if force is True
        if request.force:
            delete_all_chunks()

        # Check if chunks already exist
        existing_count = get_chunk_count()
        if existing_count > 0 and not request.force:
            return SeedResponse(
                chunks_created=0,
                categories=get_categories(),
                message=f"Playbook already has {existing_count} chunks. Use force=true to re-seed."
            )

        # Parse the playbook into chunks
        chunks = parse_playbook(str(playbook_path))
        if not chunks:
            raise HTTPException(
                status_code=400,
                detail="No chunks could be parsed from the playbook"
            )

        # Generate embeddings for all chunks (batch)
        texts = [chunk["content"] for chunk in chunks]
        embeddings = generate_embeddings_batch(texts)

        # Insert chunks into Supabase
        created_count = 0
        for chunk, embedding in zip(chunks, embeddings):
            insert_chunk(
                category=chunk["category"],
                objection_type=chunk["objection_type"],
                strategy=chunk["strategy"],
                content=chunk["content"],
                embedding=embedding,
                metadata=chunk["metadata"]
            )
            created_count += 1

        categories = get_categories()

        return SeedResponse(
            chunks_created=created_count,
            categories=categories,
            message=f"Successfully seeded {created_count} playbook chunks across {len(categories)} categories."
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Seeding failed: {str(e)}")


@router.post("/upload")
async def upload_playbook(file: UploadFile = File(...)):
    """
    Upload a new playbook markdown file, parse it, and add to the database.
    """
    try:
        if not file.filename.endswith((".md", ".txt")):
            raise HTTPException(
                status_code=400,
                detail="Only .md and .txt files are supported"
            )

        content = await file.read()
        text = content.decode("utf-8")

        # Save temp file and parse
        temp_path = Path(__file__).parent.parent / "temp_playbook.md"
        with open(temp_path, "w", encoding="utf-8") as f:
            f.write(text)

        try:
            chunks = parse_playbook(str(temp_path))
        finally:
            if temp_path.exists():
                os.remove(temp_path)

        if not chunks:
            # Fall back to simple text chunking
            text_chunks = chunk_text(text)
            chunks = [
                {
                    "category": "Uploaded",
                    "objection_type": "General",
                    "strategy": "Custom",
                    "content": c,
                    "metadata": {"source": file.filename}
                }
                for c in text_chunks
            ]

        # Generate embeddings
        texts = [chunk["content"] for chunk in chunks]
        embeddings = generate_embeddings_batch(texts)

        # Insert chunks
        created_count = 0
        for chunk, embedding in zip(chunks, embeddings):
            insert_chunk(
                category=chunk["category"],
                objection_type=chunk["objection_type"],
                strategy=chunk["strategy"],
                content=chunk["content"],
                embedding=embedding,
                metadata=chunk.get("metadata", {})
            )
            created_count += 1

        return {
            "message": f"Successfully uploaded and processed {file.filename}",
            "chunks_created": created_count
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")


@router.delete("/clear")
async def clear_playbook():
    """Delete all playbook chunks from the database."""
    try:
        delete_all_chunks()
        return {"message": "All playbook chunks deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
