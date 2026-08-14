from __future__ import annotations

from dataclasses import dataclass

import httpx

from app.config import get_settings


@dataclass(frozen=True)
class LLMProvider:
    name: str
    base_url: str
    model: str
    extra_headers: dict[str, str]


def _providers() -> list[tuple[LLMProvider, str]]:
    settings = get_settings()
    out: list[tuple[LLMProvider, str]] = []
    if settings.nvidia_api_key:
        out.append(
            (
                LLMProvider(
                    name="nvidia",
                    base_url="https://integrate.api.nvidia.com/v1",
                    model=settings.nvidia_model,
                    extra_headers={},
                ),
                settings.nvidia_api_key,
            )
        )
    if settings.openrouter_api_key:
        out.append(
            (
                LLMProvider(
                    name="openrouter",
                    base_url="https://openrouter.ai/api/v1",
                    model=settings.openrouter_model,
                    extra_headers={
                        "HTTP-Referer": "http://localhost:5173",
                        "X-Title": "Undertow",
                    },
                ),
                settings.openrouter_api_key,
            )
        )
    if settings.fireworks_api_key:
        out.append(
            (
                LLMProvider(
                    name="fireworks",
                    base_url="https://api.fireworks.ai/inference/v1",
                    model=settings.fireworks_model,
                    extra_headers={},
                ),
                settings.fireworks_api_key,
            )
        )
    return out


def chat_complete(
    system: str,
    user: str,
    *,
    max_tokens: int = 400,
    temperature: float = 0.2,
) -> str | None:
    """OpenAI-compatible chat. Tries NVIDIA, then OpenRouter, then Fireworks."""
    last_err = None
    for provider, key in _providers():
        try:
            headers = {
                "Authorization": f"Bearer {key}",
                "Content-Type": "application/json",
                **provider.extra_headers,
            }
            payload = {
                "model": provider.model,
                "messages": [
                    {"role": "system", "content": system},
                    {"role": "user", "content": user},
                ],
                "max_tokens": max_tokens,
                "temperature": temperature,
            }
            with httpx.Client(timeout=12.0 if provider.name == "nvidia" else 30.0) as client:
                resp = client.post(
                    f"{provider.base_url}/chat/completions",
                    headers=headers,
                    json=payload,
                )
                resp.raise_for_status()
                data = resp.json()
            text = (data.get("choices") or [{}])[0].get("message", {}).get("content")
            if text and str(text).strip():
                print(f"[llm] used {provider.name}")
                return str(text).strip()
            last_err = f"{provider.name} empty response"
        except Exception as exc:  # noqa: BLE001
            last_err = f"{provider.name}: {exc}"
            print(f"[llm] {last_err}")
            continue
    if last_err:
        print(f"[llm] all providers failed ({last_err})")
    return None
