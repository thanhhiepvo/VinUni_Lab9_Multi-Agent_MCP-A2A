"""Thin LLM client for Lab_Assignment agents (OpenAI-compatible)."""

from __future__ import annotations

import os

from dotenv import load_dotenv

load_dotenv()


def chat_completion(
    system_prompt: str,
    user_prompt: str,
    *,
    temperature: float = 0.3,
    max_tokens: int = 800,
) -> str:
    """Call chat completion API. Supports OpenAI or OpenRouter via env."""
    from openai import OpenAI

    api_key = os.getenv("OPENAI_API_KEY") or os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        raise ValueError(
            "Set OPENAI_API_KEY or OPENROUTER_API_KEY in Lab_Assignment/.env"
        )

    base_url = os.getenv("OPENAI_BASE_URL")
    if not base_url and os.getenv("OPENROUTER_API_KEY"):
        base_url = "https://openrouter.ai/api/v1"

    model = os.getenv("LLM_MODEL", "gpt-4o-mini")
    if os.getenv("OPENROUTER_API_KEY") and not os.getenv("LLM_MODEL"):
        model = os.getenv("OPENROUTER_MODEL", "openai/gpt-3.5-turbo")

    client = OpenAI(api_key=api_key, base_url=base_url)
    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        temperature=temperature,
        max_tokens=max_tokens,
    )
    return response.choices[0].message.content or ""
