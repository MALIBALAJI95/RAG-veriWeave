"""Prompt templates for grounded RAG generation across multi-source evidence."""

SYSTEM_PROMPT = """You are VeriWeave, an advanced, highly reliable, and grounded multi-source retrieval engine.
Your mission is to provide accurate, truthful, and strictly grounded answers based solely on the provided reference context.

CRITICAL INSTRUCTIONS:
1. Grounding: Answer the question using ONLY the factual information present in the Context blocks below. Do not use outside knowledge or introduce unverified assumptions.
2. Accurate Source Citation:
   - For uploaded documents, use: [Doc: <filename>, Page: <page>].
   - For structured database facts, use: [Database: SQLite Catalog].
   - For external web sources, use: [Web: <title or URL>].
   Never represent external web information or database records as coming from an uploaded document.
3. Insufficient Context: If the provided context does not contain sufficient evidence to answer the question with certainty, state clearly: "The provided context does not contain sufficient information to answer this question."
4. Conciseness & Precision: Be objective, concise, and direct. Avoid conversational filler.
"""

USER_PROMPT_TEMPLATE = """Reference Context Blocks:
{context_blocks}

User Question: {question}

Grounded Answer (with accurate inline source citations):"""


def format_context_blocks(items) -> str:
    """Format retrieved document chunks or unified evidence items into structured blocks with origin provenance."""
    if not items:
        return "No relevant context documents found."

    blocks = []
    for idx, item in enumerate(items, 1):
        # Support both EvidenceItem and RetrievedChunk
        source_type = getattr(item, "source_type", "vector_document")

        if source_type == "structured_sql":
            header = f"--- Reference Block [{idx}] (Structured Database Source) ---\nOrigin: SQLite Catalog | Query: {item.source_id}"
            body = getattr(item, "content_excerpt", getattr(item, "text", ""))
        elif source_type == "web_search":
            url_str = getattr(item, "url", "https://external-search")
            title_str = getattr(item, "title", "Web Article")
            header = f"--- Reference Block [{idx}] (External Web Source) ---\nOrigin: Web | Title: {title_str} | URL: {url_str}"
            body = getattr(item, "content_excerpt", getattr(item, "text", ""))
        else:
            filename = getattr(item, "filename", "unknown")
            page_num = getattr(item, "page_number", 1)
            score_val = getattr(item, "score", 1.0)
            header = f"--- Reference Block [{idx}] (Document Source) ---\nOrigin: Uploaded Document | File: {filename} | Page: {page_num} | Score: {score_val:.3f}"
            body = getattr(item, "text", getattr(item, "content_excerpt", ""))

        block = f"{header}\nContent:\n{body}\n"
        blocks.append(block)

    return "\n".join(blocks)
