"""
Embeddings Module.
Generates vector embeddings using sentence-transformers (local, no API key needed).
Uses the all-MiniLM-L6-v2 model which produces 384-dimensional embeddings.
"""

from sentence_transformers import SentenceTransformer
from config import config

# Global model instance (loaded once)
_model: SentenceTransformer = None


def get_model() -> SentenceTransformer:
    """Load the embedding model (lazy initialization)."""
    global _model
    if _model is None:
        print(f"Loading embedding model: {config.EMBEDDING_MODEL}...")
        _model = SentenceTransformer(config.EMBEDDING_MODEL)
        print("Embedding model loaded successfully!")
    return _model


def generate_embedding(text: str) -> list[float]:
    """
    Generate a single embedding vector for the given text.
    
    Args:
        text: The text to embed
        
    Returns:
        A list of floats representing the embedding vector (384 dimensions)
    """
    model = get_model()
    embedding = model.encode(text, normalize_embeddings=True)
    return embedding.tolist()


def generate_embeddings_batch(texts: list[str]) -> list[list[float]]:
    """
    Generate embeddings for multiple texts at once (much faster than one-by-one).
    
    Args:
        texts: List of texts to embed
        
    Returns:
        List of embedding vectors
    """
    model = get_model()
    embeddings = model.encode(texts, normalize_embeddings=True, show_progress_bar=True)
    return [emb.tolist() for emb in embeddings]


if __name__ == "__main__":
    # Test embeddings
    test_texts = [
        "The product is too expensive for our budget",
        "We are already using a competitor's solution",
        "We need more time to make a decision"
    ]

    print("Generating test embeddings...")
    embeddings = generate_embeddings_batch(test_texts)

    for text, emb in zip(test_texts, embeddings):
        print(f"\nText: {text}")
        print(f"Embedding dimension: {len(emb)}")
        print(f"First 5 values: {emb[:5]}")
