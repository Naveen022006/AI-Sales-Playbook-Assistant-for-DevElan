"""
Playbook Chunker Module.
Parses markdown sales playbook files into structured chunks
suitable for embedding and vector search.
"""

import re
from pathlib import Path


def parse_playbook(file_path: str) -> list[dict]:
    """
    Parse a markdown sales playbook into structured chunks.
    
    Each chunk contains:
    - category: e.g., "Price and Budget Objections"
    - objection_type: e.g., "Your product is too expensive"
    - strategy: e.g., "Reframe the Value"
    - content: The full text content of the objection handler
    - metadata: Additional metadata
    """
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()

    chunks = []
    current_category = ""
    current_objection = ""
    current_strategy = ""
    current_content_lines = []

    lines = content.split("\n")
    i = 0

    while i < len(lines):
        line = lines[i]

        # Detect category headers: ## Category: ...
        category_match = re.match(r'^## Category:\s*(.+)', line)
        if category_match:
            # Save previous chunk if exists
            if current_objection and current_content_lines:
                chunks.append(_create_chunk(
                    current_category, current_objection,
                    current_strategy, current_content_lines
                ))
                current_content_lines = []

            current_category = category_match.group(1).strip()
            i += 1
            continue

        # Detect objection headers: ### Objection: ...
        objection_match = re.match(r'^### Objection:\s*(.+)', line)
        if objection_match:
            # Save previous chunk if exists
            if current_objection and current_content_lines:
                chunks.append(_create_chunk(
                    current_category, current_objection,
                    current_strategy, current_content_lines
                ))
                current_content_lines = []

            current_objection = objection_match.group(1).strip().strip('"')
            current_strategy = ""
            i += 1
            continue

        # Detect strategy headers: **Strategy: ...**
        strategy_match = re.match(r'^\*\*Strategy:\s*(.+?)\*\*', line)
        if strategy_match:
            current_strategy = strategy_match.group(1).strip()
            i += 1
            continue

        # Skip top-level headers and horizontal rules
        if line.startswith("# ") or line.strip() == "---" or line.startswith("> "):
            i += 1
            continue

        # Accumulate content lines
        if current_objection and line.strip():
            current_content_lines.append(line)

        i += 1

    # Save the last chunk
    if current_objection and current_content_lines:
        chunks.append(_create_chunk(
            current_category, current_objection,
            current_strategy, current_content_lines
        ))

    return chunks


def _create_chunk(category: str, objection: str,
                  strategy: str, content_lines: list[str]) -> dict:
    """Create a structured chunk dictionary."""
    content = "\n".join(content_lines).strip()

    # Clean up markdown formatting for better embedding
    clean_content = (
        f"Category: {category}\n"
        f"Objection: \"{objection}\"\n"
        f"Strategy: {strategy}\n\n"
        f"{content}"
    )

    return {
        "category": category,
        "objection_type": objection,
        "strategy": strategy,
        "content": clean_content,
        "metadata": {
            "raw_length": len(content),
            "word_count": len(content.split()),
        }
    }


def chunk_text(text: str, chunk_size: int = 500, overlap: int = 50) -> list[str]:
    """
    Split a long text into overlapping chunks.
    Used for processing uploaded playbook content that isn't pre-structured.
    """
    words = text.split()
    chunks = []

    for i in range(0, len(words), chunk_size - overlap):
        chunk = " ".join(words[i:i + chunk_size])
        if chunk.strip():
            chunks.append(chunk)

    return chunks


if __name__ == "__main__":
    # Test the chunker
    playbook_path = Path(__file__).parent.parent.parent / "data" / "sales_playbook.md"
    if playbook_path.exists():
        chunks = parse_playbook(str(playbook_path))
        print(f"Parsed {len(chunks)} chunks from playbook:")
        for i, chunk in enumerate(chunks):
            print(f"\n--- Chunk {i+1} ---")
            print(f"Category: {chunk['category']}")
            print(f"Objection: {chunk['objection_type']}")
            print(f"Strategy: {chunk['strategy']}")
            print(f"Content length: {chunk['metadata']['word_count']} words")
    else:
        print(f"Playbook not found at {playbook_path}")
