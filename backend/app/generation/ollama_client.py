"""Ollama client with robust connection handling and fallback grounded generation."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Dict, List, Optional, Tuple
import httpx
from backend.app.core.exceptions import GenerationError
from backend.app.core.logging import get_logger

if TYPE_CHECKING:
    from backend.app.schemas.chat import RetrievedChunk

logger = get_logger(__name__)


class OllamaClient:
    """Client for local Ollama LLM inference with health checks and graceful fallback."""

    def __init__(
        self,
        base_url: str = "http://localhost:11434",
        model: str = "llama3.2:1b",
        timeout_seconds: float = 60.0,
        temperature: float = 0.1,
        enable_fallback: bool = True,
    ):
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.timeout_seconds = timeout_seconds
        self.temperature = temperature
        self.enable_fallback = enable_fallback

    def check_health(self) -> Tuple[bool, Dict[str, Any]]:
        """Check if Ollama server is reachable and return available models."""
        try:
            with httpx.Client(timeout=2.0) as client:
                res = client.get(f"{self.base_url}/api/tags")
                if res.status_code == 200:
                    data = res.json()
                    models = [m.get("name") for m in data.get("models", [])]
                    model_loaded = self.model in models or any(self.model in m for m in models)
                    return True, {
                        "reachable": True,
                        "available_models": models,
                        "configured_model": self.model,
                        "model_ready": model_loaded,
                    }
                return False, {"reachable": False, "status_code": res.status_code}
        except Exception as e:
            logger.debug(f"Ollama server check at {self.base_url} failed: {e}")
            return False, {
                "reachable": False,
                "error": str(e),
                "configured_model": self.model,
                "fallback_active": self.enable_fallback,
            }

    def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        retrieved_chunks: Optional[List[RetrievedChunk]] = None,
    ) -> Tuple[str, str, bool]:
        """Generate response via Ollama, or use fallback generator if server is offline.

        Returns: (answer_text, model_name, is_fallback)
        """
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": self.temperature,
            },
        }
        if system_prompt:
            payload["system"] = system_prompt

        try:
            with httpx.Client(timeout=self.timeout_seconds) as client:
                res = client.post(f"{self.base_url}/api/generate", json=payload)
                if res.status_code == 200:
                    data = res.json()
                    response_text = data.get("response", "").strip()
                    return response_text, self.model, False
                else:
                    logger.warning(
                        f"Ollama request returned status {res.status_code}: {res.text}"
                    )
        except (httpx.ConnectError, httpx.TimeoutException, httpx.HTTPError) as net_err:
            logger.warning(f"Ollama server unreachable at {self.base_url} ({net_err})")

        if self.enable_fallback:
            logger.info("Using grounded extractive fallback generator (Ollama server offline)")
            fallback_answer = self._synthesize_fallback(prompt, retrieved_chunks)
            return fallback_answer, f"{self.model} (offline-fallback)", True

        raise GenerationError(
            f"Ollama server at {self.base_url} is unreachable and fallback generator is disabled."
        )

    def _synthesize_fallback(
        self,
        prompt: str,
        chunks: Optional[List[RetrievedChunk]],
    ) -> str:
        """Synthesize a strictly grounded extractive answer when Ollama is offline."""
        if not chunks:
            return "The provided documents do not contain sufficient information to answer this question."

        lines = [
            "Based on the retrieved source documents, here is the verified information:",
            "",
        ]

        # Present the top relevant chunk findings with exact citations
        for idx, chunk in enumerate(chunks[:3], 1):
            excerpt = chunk.text.strip().replace("\n", " ")
            if len(excerpt) > 280:
                excerpt = excerpt[:280] + "..."
            lines.append(f"- {excerpt} [Doc: {chunk.filename}, Page: {chunk.page_number}]")

        lines.append("")
        lines.append(
            "*(Generated via VeriWeave Fallback Grounded Engine. "
            "Start Ollama with `ollama run llama3.2:1b` for generative synthesis)*"
        )
        return "\n".join(lines)
