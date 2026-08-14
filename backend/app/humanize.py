from __future__ import annotations

from app.llm import chat_complete

HUMANIZE_SYSTEM = """You rewrite text so it sounds like a real person wrote it, not a model.

Rules:
- Keep the same meaning, facts, and intent. Do not add claims, links, or product features.
- Cut marketing voice: no "excited to share", "game-changer", "leverage", "I'd love to hop on a call".
- Sound like a founder typing a Reddit/HN comment: specific, a bit casual, slightly imperfect.
- Short sentences. Contractions. No hashtags, no emoji, no bullet lists unless the original needed them.
- Under 120 words. Output ONLY the rewritten text."""


def humanize_text(text: str, *, context: str = "") -> str:
    """Second pass over any outgoing LLM text. Falls back to the original."""
    source = (text or "").strip()
    if not source:
        return source

    user = source
    if context:
        user = f"Context: {context}\n\nRewrite this:\n{source}"

    rewritten = chat_complete(
        HUMANIZE_SYSTEM,
        user,
        max_tokens=280,
        temperature=0.75,
    )
    out = (rewritten or "").strip()
    if not out or out.startswith("{") or out.startswith("```"):
        return source
    return out
