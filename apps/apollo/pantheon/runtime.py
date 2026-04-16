import requests

from config import OLLAMA_BASE_URL, PANTHEON_MODEL
from core.audit import log


class LocalModelRuntime:
    """Thin wrapper around a local Ollama runtime."""

    def __init__(self, base_url: str = OLLAMA_BASE_URL, model: str = PANTHEON_MODEL):
        self.base_url = base_url.rstrip("/")
        self.model = model

    def available(self) -> bool:
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=2)
            return response.ok
        except requests.RequestException:
            return False

    def generate(self, system_prompt: str, user_prompt: str) -> str | None:
        payload = {
            "model": self.model,
            "stream": False,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
        }
        try:
            response = requests.post(
                f"{self.base_url}/api/chat",
                json=payload,
                timeout=90,
            )
            response.raise_for_status()
            data = response.json()
            message = data.get("message", {})
            content = message.get("content", "").strip()
            if content:
                return content
        except requests.RequestException as exc:
            log(f"Local model unavailable: {exc}", system="PANTHEON")
        return None
