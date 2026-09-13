from unittest.mock import MagicMock

import pytest

from app.llm import client as client_module


def test_complete_dispatches_to_anthropic(monkeypatch):
    monkeypatch.setattr(client_module.settings, "llm_provider", "anthropic")

    fake_block = MagicMock(type="text", text="anthropic reply")
    fake_response = MagicMock(content=[fake_block])
    fake_client = MagicMock()
    fake_client.messages.create.return_value = fake_response
    monkeypatch.setattr(client_module.anthropic, "Anthropic", lambda **kwargs: fake_client)

    assert client_module.complete("hi") == "anthropic reply"


def test_complete_dispatches_to_gemini(monkeypatch):
    monkeypatch.setattr(client_module.settings, "llm_provider", "gemini")

    fake_response = MagicMock(text="gemini reply")
    fake_client = MagicMock()
    fake_client.models.generate_content.return_value = fake_response
    monkeypatch.setattr(client_module.genai, "Client", lambda **kwargs: fake_client)

    assert client_module.complete("hi") == "gemini reply"


def test_complete_raises_on_unsupported_provider(monkeypatch):
    monkeypatch.setattr(client_module.settings, "llm_provider", "openai")

    with pytest.raises(ValueError):
        client_module.complete("hi")
