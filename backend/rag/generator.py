"""
Generator Module.
Handles prompt augmentation and LLM response generation using Groq API.
Produces structured sales suggestions from retrieved playbook content.
"""

from groq import Groq
from config import config
from rag.retriever import retrieve_relevant_chunks, format_context_for_prompt

# Initialize Groq client
_client: Groq = None


def get_groq_client() -> Groq:
    """Get or create the Groq client."""
    global _client
    if _client is None:
        _client = Groq(api_key=config.GROQ_API_KEY)
    return _client


# System prompt template
SYSTEM_PROMPT = """You are an expert AI Sales Coach and Playbook Assistant. Your role is to help salespeople handle customer objections effectively using the company's proven playbook strategies.

IMPORTANT RULES:
1. Base your responses ONLY on the provided playbook content. Do not make up strategies.
2. If the playbook content doesn't directly address the objection, adapt the closest strategies and clearly note you're adapting.
3. Always provide actionable, ready-to-use response scripts.
4. Be encouraging and supportive — you're coaching the salesperson to succeed.
5. You MUST output your response in valid JSON format ONLY.

OUTPUT FORMAT:
Always output exactly with the following JSON schema:
{
  "objection_identified": "[Summary of the objection in one sentence]",
  "category": "[Objection category from playbook]",
  "strategy": "[The recommended strategy name]",
  "recommended_responses": [
    "[First ready-to-use script the salesperson can say]",
    "[Second alternative ready-to-use script]"
  ],
  "pro_tips": [
    "[Actionable tip 1]",
    "[Actionable tip 2]"
  ],
  "avoid_mistakes": [
    "[Common mistake to avoid]"
  ],
  "follow_up_strategy": "[Brief advice on what to do after delivering the response]",
  "confidence_score": 0.95
}
"""


def generate_sales_suggestion(query: str) -> dict:
    """
    Main RAG pipeline: retrieve context, augment prompt, generate response.
    
    Args:
        query: The salesperson's description of the customer objection
        
    Returns:
        Dictionary with the generated response, retrieved chunks, and metadata
    """
    # Step 1: Retrieve relevant playbook chunks
    retrieved_chunks = retrieve_relevant_chunks(query)

    # Step 2: Format context for prompt augmentation
    context = format_context_for_prompt(retrieved_chunks)

    # Step 3: Build the augmented prompt
    user_prompt = f"""A salesperson needs help with the following customer objection:

CUSTOMER OBJECTION: "{query}"

Here are the most relevant entries from our company sales playbook:

{context}

Based on the playbook entries above, provide a structured sales coaching response. Include ready-to-use scripts the salesperson can adapt for their conversation."""

    # Step 4: Call Groq API for generation
    client = get_groq_client()

    try:
        chat_completion = client.chat.completions.create(
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt}
            ],
            model=config.GROQ_MODEL,
            temperature=0.7,
            max_tokens=2000,
            top_p=0.9,
            response_format={"type": "json_object"},
        )

        response_json_str = chat_completion.choices[0].message.content
        
        import json
        structured_data = json.loads(response_json_str)

        # Format back into the expected Markdown for existing frontend compatibility
        response_text = f"📌 **Objection Identified:** {structured_data.get('objection_identified', 'Unknown')}\n"
        response_text += f"📂 **Category:** {structured_data.get('category', 'Unknown')}\n"
        response_text += f"🎯 **Strategy:** {structured_data.get('strategy', 'Unknown')}\n"
        response_text += f"📊 **Confidence:** {int(structured_data.get('confidence_score', 0) * 100)}%\n\n---\n\n"
        
        response_text += "### 🗣️ Recommended Responses:\n\n"
        for i, resp in enumerate(structured_data.get('recommended_responses', [])):
            response_text += f"**Response {i+1}:**\n> \"{resp}\"\n\n"
            
        response_text += "---\n\n### 💡 Pro Tips:\n"
        for tip in structured_data.get('pro_tips', []):
            response_text += f"- {tip}\n"
            
        response_text += "\n---\n\n### ⚠️ What NOT to Do:\n"
        for mistake in structured_data.get('avoid_mistakes', []):
            response_text += f"- {mistake}\n"

        response_text += f"\n---\n\n### 🔄 Follow-Up Strategy:\n{structured_data.get('follow_up_strategy', '')}"

        # Extract metadata
        usage = chat_completion.usage
        metadata = {
            "model": config.GROQ_MODEL,
            "prompt_tokens": usage.prompt_tokens if usage else 0,
            "completion_tokens": usage.completion_tokens if usage else 0,
            "total_tokens": usage.total_tokens if usage else 0,
            "chunks_retrieved": len(retrieved_chunks),
        }

    except Exception as e:
        response_text = f"Error generating response: {str(e)}"
        metadata = {"error": str(e)}

    return {
        "response": response_text,
        "retrieved_chunks": [
            {
                "category": c["category"],
                "objection_type": c["objection_type"],
                "strategy": c["strategy"],
                "similarity": c["similarity"]
            }
            for c in retrieved_chunks
        ],
        "similarity_scores": [c["similarity"] for c in retrieved_chunks],
        "metadata": metadata
    }
