"""
FastAPI Main Application — AI Sales Playbook Assistant
Entry point for the backend API server.
"""

import sys
from pathlib import Path

# Add backend directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from config import config
from database import init_db
from routes.query import router as query_router
from routes.playbook import router as playbook_router
from routes.history import router as history_router

# Create FastAPI app
app = FastAPI(
    title="AI Sales Playbook Assistant",
    description="RAG-powered assistant that retrieves the best objection handlers from your sales playbook",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS middleware — allow frontend to call API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register route modules
app.include_router(query_router)
app.include_router(playbook_router)
app.include_router(history_router)


@app.on_event("startup")
async def startup_event():
    """Initialize services on startup."""
    # Validate configuration
    errors = config.validate()
    if errors:
        print("⚠️  Configuration warnings:")
        for error in errors:
            print(f"   - {error}")
        print("   Set these in backend/.env file")
    else:
        print("✅ Configuration validated")

    # Initialize database
    try:
        init_db()
        print("✅ Supabase connection established")
    except Exception as e:
        print(f"⚠️  Database connection failed: {e}")

    print("\n🚀 AI Sales Playbook Assistant API is running!")
    print(f"   API Docs: http://localhost:{config.FASTAPI_PORT}/docs")


@app.get("/")
async def root():
    """Root endpoint — API info."""
    return {
        "name": "AI Sales Playbook Assistant",
        "version": "1.0.0",
        "status": "running",
        "docs": f"http://localhost:{config.FASTAPI_PORT}/docs",
        "endpoints": {
            "query": "POST /api/query",
            "playbook_stats": "GET /api/playbook/stats",
            "playbook_seed": "POST /api/playbook/seed",
            "playbook_upload": "POST /api/playbook/upload",
            "history": "GET /api/history"
        }
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=config.FASTAPI_PORT,
        reload=True
    )
