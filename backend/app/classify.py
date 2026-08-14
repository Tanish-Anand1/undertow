from __future__ import annotations

import json
import re
from typing import Any

from app.humanize import humanize_text
from app.llm import chat_complete

VALID_TAGS = {"pain", "question", "complaint", "praise", "irrelevant"}

SYSTEM_PROMPT = """You classify social posts for founder research.
Given a keyword/niche and a post (title + body), return ONLY strict JSON:
{"tag":"pain"|"question"|"complaint"|"praise"|"irrelevant","relevance_score":0-100}

Definitions:
- pain: someone describing a problem or unmet need related to the keyword
- question: asking how to do something / looking for recommendations related to the keyword
- complaint: negative experience with a product/service in the niche
- praise: positive experience or recommendation
- irrelevant: not useful for a founder researching that niche

relevance_score: how useful this post is for a founder listening to that keyword (0-100).
No markdown, no commentary — JSON only."""

DRAFT_SYSTEM = (
    "You draft a short reply the founder could actually post. "
    "Stay under 120 words. No hashtags, no CTA spam, no 'I came across your post'. "
    "Quote or paraphrase one concrete detail from the source post so it is obvious you read it. "
    "Match the room: HN is terse and technical; GitHub issues are practical; X is brief. "
    "If the tag is pain or complaint, acknowledge the specific problem before mentioning the product. "
    "If the tag is question, answer the question first. "
    "If the tag is praise, keep it short and human, not salesy."
)


def _heuristic_classify(title: str, body: str, keyword: str) -> dict[str, Any]:
    text = f"{title}\n{body}".lower()
    kw = keyword.lower()
    score = 40
    if kw and kw in text:
        score += 25

    tag = "irrelevant"
    if any(w in text for w in ("how do i", "how to", "anyone recommend", "looking for", "?")):
        tag = "question"
        score += 10
    elif any(w in text for w in ("hate", "awful", "broken", "terrible", "worst", "frustrated")):
        tag = "complaint"
        score += 15
    elif any(w in text for w in ("love", "amazing", "best", "recommend", "game changer")):
        tag = "praise"
        score += 10
    elif any(w in text for w in ("struggle", "pain", "wish there", "problem with", "need a")):
        tag = "pain"
        score += 15
    elif kw and kw in text:
        tag = "question"
        score += 5

    return {"tag": tag, "relevance_score": max(0, min(100, score))}


def _parse_classify(raw: str) -> dict[str, Any] | None:
    text = raw.strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*", "", text)
        text = re.sub(r"\s*```$", "", text)
    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", text, re.S)
        if not match:
            return None
        try:
            data = json.loads(match.group(0))
        except json.JSONDecodeError:
            return None
    tag = str(data.get("tag", "irrelevant")).lower()
    if tag not in VALID_TAGS:
        tag = "irrelevant"
    score = float(data.get("relevance_score", 0))
    return {"tag": tag, "relevance_score": max(0.0, min(100.0, score))}


def classify_post_fast(title: str, body: str, keyword: str) -> dict[str, Any]:
    """Deterministic ingest path — no network, so Scan now always finishes."""
    return _heuristic_classify(title, body, keyword)


def classify_post(title: str, body: str, keyword: str) -> dict[str, Any]:
    """Classify a post via NVIDIA / OpenRouter / Fireworks, then heuristic."""
    raw = chat_complete(
        SYSTEM_PROMPT,
        f"Keyword: {keyword}\n\nTitle: {title}\n\nBody: {body[:3000]}",
        max_tokens=200,
    )
    if raw:
        parsed = _parse_classify(raw)
        if parsed:
            return parsed
        print("[classify] LLM returned unparseable JSON, using heuristic")
    return _heuristic_classify(title, body, keyword)


def draft_reply(
    title: str,
    body: str,
    product_description: str,
    tag: str | None = None,
    source: str | None = None,
) -> str:
    fallback = (
        f"Hey, saw your post about \"{title[:80]}\". "
        f"We built something that might help: {product_description} "
        "Happy to share more if useful."
    )
    raw = chat_complete(
        DRAFT_SYSTEM,
        (
            f"Product: {product_description}\n"
            f"Tag: {tag or 'unknown'}\n"
            f"Source: {source or 'unknown'}\n\n"
            f"Post title: {title}\n\n"
            f"Post body: {body[:2500]}\n\n"
            "Draft a reply the founder could post."
        ),
        max_tokens=400,
        temperature=0.55,
    )
    draft = raw or fallback
    return humanize_text(
        draft,
        context=f"Reply to a public post titled: {title[:120]}",
    )
