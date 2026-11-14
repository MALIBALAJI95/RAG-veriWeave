"""Cloudflare Workers AI client for hosted LLM generation."""

from __future__ import annotations

import re
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Tuple
import httpx
from backend.app.core.exceptions import GenerationError
from backend.app.core.logging import get_logger

if TYPE_CHECKING:
    from backend.app.schemas.chat import RetrievedChunk

logger = get_logger(__name__)


class CloudflareWorkersAIClient:
    """Hosted LLM inference using Cloudflare Workers AI free tier with graceful fallback."""

    def __init__(
        self,
        account_id: Optional[str] = None,
        api_token: Optional[str] = None,
        model: str = "@cf/meta/llama-3.2-1b-instruct",
        timeout_seconds: float = 30.0,
        temperature: float = 0.1,
        enable_fallback: bool = True,
    ):
        self.account_id = account_id
        self.api_token = api_token
        self.model = model
        self.timeout_seconds = timeout_seconds
        self.temperature = temperature
        self.enable_fallback = enable_fallback
        self.endpoint = (
            f"https://api.cloudflare.com/client/v4/accounts/{self.account_id}/ai/run/{self.model}"
            if self.account_id
            else ""
        )

    def check_health(self) -> Tuple[bool, Dict[str, Any]]:
        """Verify Cloudflare Workers AI credentials and configuration."""
        if not self.account_id or not self.api_token:
            return False, {
                "reachable": False,
                "provider": "cloudflare",
                "configured_model": self.model,
                "error": "Missing CLOUDFLARE_ACCOUNT_ID or CLOUDFLARE_API_TOKEN",
                "fallback_active": self.enable_fallback,
            }

        headers = {
            "Authorization": f"Bearer {self.api_token}",
            "Content-Type": "application/json",
        }
        # Run lightweight test ping with a minimal token query
        try:
            with httpx.Client(timeout=4.0) as client:
                res = client.post(
                    self.endpoint,
                    headers=headers,
                    json={"prompt": "ping", "max_tokens": 1},
                )
                if res.status_code == 200:
                    return True, {
                        "reachable": True,
                        "provider": "cloudflare",
                        "configured_model": self.model,
                        "account_id_masked": f"{self.account_id[:4]}...{self.account_id[-4:]}" if len(self.account_id) > 8 else "***",
                    }
                return False, {
                    "reachable": False,
                    "provider": "cloudflare",
                    "status_code": res.status_code,
                    "error": res.text,
                    "fallback_active": self.enable_fallback,
                }
        except Exception as e:
            logger.debug(f"Cloudflare health check failed: {e}")
            return False, {
                "reachable": False,
                "provider": "cloudflare",
                "error": str(e),
                "fallback_active": self.enable_fallback,
            }

    def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        retrieved_chunks: Optional[List[RetrievedChunk]] = None,
    ) -> Tuple[str, str, bool]:
        """Generate response via Cloudflare Workers AI, or use fallback generator on failure.

        Returns: (answer_text, model_name, is_fallback)
        """
        if self.account_id and self.api_token:
            headers = {
                "Authorization": f"Bearer {self.api_token}",
                "Content-Type": "application/json",
            }
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})

            payload = {
                "messages": messages,
                "temperature": self.temperature,
                "max_tokens": 1024,
            }

            try:
                with httpx.Client(timeout=self.timeout_seconds) as client:
                    res = client.post(self.endpoint, headers=headers, json=payload)
                    if res.status_code == 200:
                        data = res.json()
                        result = data.get("result", {})
                        # Cloudflare returns 'response' field or 'text'
                        response_text = result.get("response") or result.get("text") or ""
                        if response_text.strip():
                            return response_text.strip(), f"cloudflare:{self.model}", False
                    else:
                        logger.warning(
                            f"Cloudflare Workers AI returned HTTP {res.status_code}: {res.text}"
                        )
            except Exception as e:
                logger.warning(f"Cloudflare Workers AI generation call failed: {e}")

        if self.enable_fallback:
            logger.info("Using grounded extractive fallback generator (Cloudflare offline/unconfigured)")
            fallback_answer = self._synthesize_fallback(prompt, retrieved_chunks)
            return fallback_answer, f"{self.model} (cloudflare-fallback)", True

        raise GenerationError(
            "Cloudflare Workers AI is unreachable or unconfigured and fallback generator is disabled."
        )

    def _synthesize_fallback(
        self,
        prompt: str,
        retrieved_chunks: Optional[List[RetrievedChunk]] = None,
    ) -> str:
        """Deterministic extractive grounded generation when hosted LLM is unavailable."""
        if not retrieved_chunks:
            return (
                "No relevant document context was found to ground an answer for your query. "
                "Please verify that documents have been indexed or try rephrasing your question."
            )

        # Extract search terms from prompt
        words = re.findall(r"\b\w{3,}\b", prompt.lower())
        keywords = {w for w in words if w not in {
            "what", "when", "where", "which", "who", "whom", "whose",
            "why", "how", "does", "explain", "describe", "detail", "about",
            "tell", "provide", "based", "context", "document", "question",
        }}

        scored_sentences = []
        for chunk in retrieved_chunks:
            sentences = re.split(r"(?<=[.!?])\s+", chunk.text.strip())
            for sent in sentences:
                sent_clean = sent.strip()
                if len(sent_clean) < 20:
                    continue
                overlap = sum(1 for kw in keywords if kw in sent_clean.lower())
                scored_sentences.append((overlap, sent_clean, chunk.filename))

        scored_sentences.sort(key=lambda x: x[0], reverse=True)
        top_sentences = [s[1] for s in scored_sentences[:4] if s[0] > 0]

        if top_sentences:
            body = " ".join(top_sentences)
            return f"Based on the retrieved source documents:\n\n{body}"
        else:
            primary_text = retrieved_chunks[0].text.strip()
            excerpt = primary_text[:400] + ("..." if len(primary_text) > 400 else "")
            return f"Based on the retrieved context from {retrieved_chunks[0].filename}:\n\n{excerpt}"
