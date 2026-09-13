"""Wrapper around the LLM call (provider from config.settings.llm_provider).

Two providers are supported: "anthropic" (paid) and "gemini" (has a free
tier, useful for local dev without spending API credits).
"""

import anthropic
from google import genai

from app.config import settings

MAX_TOKENS = 1024


def complete(prompt: str) -> str:
    """Send `prompt` to the configured LLM and return its raw text reply."""
    if settings.llm_provider == "anthropic":
        return _complete_anthropic(prompt)
    if settings.llm_provider == "gemini":
        return _complete_gemini(prompt)
    raise ValueError(f"Unsupported LLM provider: {settings.llm_provider!r}")


def _complete_anthropic(prompt: str) -> str:
    client = anthropic.Anthropic(api_key=settings.llm_api_key)
    response = client.messages.create(
        model=settings.llm_model,
        max_tokens=MAX_TOKENS,
        messages=[{"role": "user", "content": prompt}],
    )
    return next((block.text for block in response.content if block.type == "text"), "")


def _complete_gemini(prompt: str) -> str:
    client = genai.Client(api_key=settings.llm_api_key)
    response = client.models.generate_content(model=settings.llm_model, contents=prompt)
    return response.text or ""
