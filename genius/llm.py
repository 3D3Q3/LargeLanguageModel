"""Language model integrations for Genius."""
from __future__ import annotations

import json
import os
from typing import Any, Dict

import requests

from .config import LLMConfig


class LLMClient:
    """Talk to local Ollama models or hosted APIs."""

    def __init__(self, config: LLMConfig):
        self.config = config

    def query(self, provider: str, prompt: str, **kwargs: Any) -> str:
        provider = provider.lower()
        if provider == "ollama":
            if not self.config.enable_ollama:
                raise RuntimeError("Ollama support is disabled in configuration")
            return self._query_ollama(prompt, **kwargs)
        if provider == "openai":
            if not self.config.enable_openai:
                raise RuntimeError("OpenAI support is disabled in configuration")
            return self._query_openai(prompt, **kwargs)
        raise ValueError(f"Unknown LLM provider: {provider}")

    # ------------------------------------------------------------------
    # Providers
    # ------------------------------------------------------------------
    def _query_ollama(self, prompt: str, **kwargs: Any) -> str:
        model = kwargs.get("model", "llama3")
        url = self.config.ollama_url.rstrip("/") + "/api/generate"
        payload = {"model": model, "prompt": prompt, "stream": False}
        payload.update(kwargs)
        response = requests.post(url, json=payload, timeout=60)
        response.raise_for_status()
        data = response.json()
        if isinstance(data, dict) and "response" in data:
            return data["response"].strip()
        return json.dumps(data)

    def _query_openai(self, prompt: str, **kwargs: Any) -> str:
        api_key = os.environ.get(self.config.openai_api_key_env)
        if not api_key:
            raise RuntimeError(
                f"Environment variable {self.config.openai_api_key_env} is not set"
            )
        model = kwargs.get("model", self.config.openai_model)
        url = "https://api.openai.com/v1/chat/completions"
        headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
        payload: Dict[str, Any] = {
            "model": model,
            "messages": [
                {"role": "system", "content": kwargs.get("system", "You are Genius assistant.")},
                {"role": "user", "content": prompt},
            ],
        }
        response = requests.post(url, headers=headers, json=payload, timeout=60)
        response.raise_for_status()
        data = response.json()
        try:
            return data["choices"][0]["message"]["content"].strip()
        except Exception:  # pragma: no cover - defensive
            return json.dumps(data)
