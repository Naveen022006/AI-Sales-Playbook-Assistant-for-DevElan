"""
Seed Script — Loads the sample sales playbook into Supabase.
Parses the markdown, generates embeddings, and inserts chunks
with their vector embeddings into the playbook_chunks table.

Usage:
    python seed.py           # Seed the playbook (skip if already seeded)
    python seed.py --force   # Delete existing data and re-seed
"""

import sys
import argparse
from pathlib import Path

# Add backend to path
backend_dir = Path(__file__).parent / "backend"
sys.path.insert(0, str(backend_dir))

from config import config
from database import init_db, insert_chunk, get_chunk_count, delete_all_chunks, get_categories
from rag.chunker import parse_playbook
from rag.embeddings import generate_embeddings_batch


def seed_playbook(force: bool = False):
    """Parse the playbook, generate embeddings, and insert into Supabase."""

    print("=" * 55)
    print("  🌱 Seeding AI Sales Playbook Assistant")
    print("=" * 55)

    # Validate config
    errors = config.validate()
    if errors:
        print("\n❌ Configuration errors:")
        for e in errors:
            print(f"   - {e}")
        print("\n   Please set the required environment variables in backend/.env")
        sys.exit(1)

    # Initialize database
    print("\n📡 Connecting to Supabase...")
    init_db()
    print("   ✅ Connected!")

    # Check existing data
    existing_count = get_chunk_count()
    if existing_count > 0:
        if not force:
            print(f"\n⚠️  Database already has {existing_count} chunks.")
            print("   Use --force to delete and re-seed.")
            print("   Skipping seed.")
            return
        else:
            print(f"\n🗑️  Deleting {existing_count} existing chunks...")
            delete_all_chunks()
            print("   ✅ Cleared!")

    # Find playbook file
    playbook_path = Path(__file__).parent / "data" / "sales_playbook.md"
    if not playbook_path.exists():
        print(f"\n❌ Playbook file not found: {playbook_path}")
        sys.exit(1)

    # Parse the playbook
    print(f"\n📄 Parsing playbook: {playbook_path.name}")
    chunks = parse_playbook(str(playbook_path))
    print(f"   ✅ Parsed {len(chunks)} objection handlers")

    if not chunks:
        print("   ❌ No chunks were parsed. Check the playbook format.")
        sys.exit(1)

    # Show categories
    categories = set(c["category"] for c in chunks)
    print(f"\n📂 Categories found ({len(categories)}):")
    for cat in sorted(categories):
        count = sum(1 for c in chunks if c["category"] == cat)
        print(f"   • {cat} ({count} handlers)")

    # Generate embeddings
    print(f"\n🧠 Generating embeddings for {len(chunks)} chunks...")
    print(f"   Model: {config.EMBEDDING_MODEL}")
    texts = [chunk["content"] for chunk in chunks]
    embeddings = generate_embeddings_batch(texts)
    print(f"   ✅ Generated {len(embeddings)} embeddings ({config.EMBEDDING_DIMENSION}D)")

    # Insert into Supabase
    print(f"\n📤 Inserting chunks into Supabase...")
    success_count = 0
    for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
        try:
            insert_chunk(
                category=chunk["category"],
                objection_type=chunk["objection_type"],
                strategy=chunk["strategy"],
                content=chunk["content"],
                embedding=embedding,
                metadata=chunk["metadata"]
            )
            success_count += 1
            print(f"   [{i+1}/{len(chunks)}] ✅ {chunk['objection_type'][:50]}")
        except Exception as e:
            print(f"   [{i+1}/{len(chunks)}] ❌ Failed: {e}")

    # Summary
    print(f"\n{'=' * 55}")
    print(f"  ✅ Seeding Complete!")
    print(f"     Chunks inserted: {success_count}/{len(chunks)}")
    print(f"     Categories: {len(categories)}")
    print(f"{'=' * 55}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Seed the sales playbook into Supabase")
    parser.add_argument("--force", action="store_true", help="Delete existing data and re-seed")
    args = parser.parse_args()

    seed_playbook(force=args.force)
