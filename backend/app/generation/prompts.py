"""Prompt templates for grounded RAG generation."""

SYSTEM_PROMPT = """You are VeriWeave, an advanced, highly reliable, and grounded Retrieval-Augmented Generation engine.
Your mission is to provide accurate, truthful, and strictly grounded answers based solely on the provided reference context.

CRITICAL INSTRUCTIONS:
1. Grounding: Answer the question using ONLY the factual information present in the Context below. Do not use outside knowledge or introduce unverified assumptions.
2. Citations: For every factual statement, attribute the claim using inline citations in the format: [Doc: <filename>, Page: <page>].
3. Insufficient Context: If the provided context does not contain sufficient evidence to answer the question with certainty, state clearly: "The provided documents do not contain sufficient information to answer this question."
4. Conciseness & Precision: Be objective, concise, and direct. Avoid unnecessary conversational filler.
"""

USER_PROMPT_TEMPLATE = """Context Documents:
{context_blocks}

User Question: {question}

Grounded Answer (with inline [Doc: <filename>, Page: <page>] citations):"""


def format_context_blocks(chunks) -> str:
    """Format retrieved chunks into numbered context blocks with metadata."""
    if not chunks:
        return "No relevant context documents found."

    blocks = []
    for idx, c in enumerate(chunks, 1):
        block = (
            f"--- Reference Block [{idx}] ---\n"
            f"Document: {c.filename} | Page: {c.page_number} | Score: {c.score:.3f}\n"
            f"Content:\n{c.text}\n"
        )
        blocks.append(block)

    return "\n".join(blocks)
