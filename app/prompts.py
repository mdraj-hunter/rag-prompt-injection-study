"""
Prompt templates, versioned so every experiment log can record exactly
which prompt wording was used (needed for reproducibility).
"""

PROMPT_VERSION = "v1-baseline"

BASELINE_SYSTEM_PROMPT = (
    "You are a helpful customer support assistant. Answer the user's question "
    "using the provided reference context. If the context doesn't contain the "
    "answer, say you don't have that information."
)


def build_baseline_user_prompt(query: str, retrieved_chunks: list[str]) -> str:
    context_block = "\n\n".join(retrieved_chunks)
    return (
        f"Reference context:\n{context_block}\n\n"
        f"User question: {query}"
    )