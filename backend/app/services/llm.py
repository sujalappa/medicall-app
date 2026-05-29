from __future__ import annotations

import logging

from openai import OpenAI, APIConnectionError, APITimeoutError

from app.config import settings

logger = logging.getLogger("saleslens.llm")


def get_client() -> OpenAI:
    return OpenAI(
        base_url=settings.hf_router_base_url,
        api_key=settings.hf_token,
    )


def chat_with_fallback(
    messages: list[dict[str, str]],
    primary_model: str,
    secondary_model: str | None = None,
) -> tuple[str, str]:
    client = get_client()
    candidates = [primary_model]
    if secondary_model and secondary_model != primary_model:
        candidates.append(secondary_model)

    last_error: Exception | None = None
    for model_name in candidates:
        for attempt in range(2):
            try:
                out = client.chat.completions.create(
                    model=model_name,
                    messages=messages,
                    timeout=120,
                )
                text = out.choices[0].message.content
                if not text:
                    text = "No answer generated."
                return text, model_name
            except (APIConnectionError, APITimeoutError) as exc:
                last_error = exc
                logger.warning(
                    "LLM attempt %d failed for %s: %s", attempt + 1, model_name, exc
                )
                continue
            except Exception as exc:
                last_error = exc
                logger.warning("LLM unexpected error for %s: %s", model_name, exc)
                break

    raise RuntimeError(f"LLM request failed across all models: {last_error}")
