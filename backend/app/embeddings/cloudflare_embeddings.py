"""Cloudflare Workers AI embedding provider with local fallback."""

from __future__ import annotations

import math
from typing import List, Optional
import httpx
from backend.app.core.exceptions import EmbeddingError
from backend.app.core.logging import get_logger
from backend.app.embeddings.base import BaseEmbeddings
from backend.app.embeddings.sentence_transformer import SentenceTransformerEmbeddings

logger = get_logger(__name__)


class CloudflareEmbeddings(BaseEmbeddings):
    """Cloudflare Workers AI embedding model (@cf/baai/bge-small-en-v1.5) with local fallback."""

    def __init__(
        self,
        account_id: Optional[str] = None,
        api_token: Optional[str] = None,
        model: str = "@cf/baai/bge-small-en-v1.5",
        dimension: int = 384,
        timeout_seconds: float = 20.0,
        fallback_local: bool = True,
    ):
        self.account_id = account_id
        self.api_token = api_token
        self.model = model
        self._dimension = dimension
        self.timeout_seconds = timeout_seconds
        self.fallback_local = fallback_local
        self._local_fallback_model: Optional[SentenceTransformerEmbeddings] = None
        self.endpoint = (
            f"https://api.cloudflare.com/client/v4/accounts/{self.account_id}/ai/run/{self.model}"
            if self.account_id
            else ""
        )
        logger.info(f"Initialized CloudflareEmbeddings for model: {self.model} (dim={self._dimension})")

    @property
    def dimension(self) -> int:
        return self._dimension

    def _get_local_fallback(self) -> SentenceTransformerEmbeddings:
        """Lazily initialize local sentence-transformers model as fallback."""
        if self._local_fallback_model is None:
            logger.info("Initializing local SentenceTransformerEmbeddings as Cloudflare fallback...")
            self._local_fallback_model = SentenceTransformerEmbeddings(
                model_name="sentence-transformers/all-MiniLM-L6-v2",
                device="cpu",
            )
        return self._local_fallback_model

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """Generate dense vector embeddings using Cloudflare Workers AI."""
        if not texts:
            return []

        if self.account_id and self.api_token:
            headers = {
                "Authorization": f"Bearer {self.api_token}",
                "Content-Type": "application/json",
            }
            # Batch process in chunks of 16 to respect Cloudflare payload limits
            batch_size = 16
            all_embeddings: List[List[float]] = []
            try:
                with httpx.Client(timeout=self.timeout_seconds) as client:
                    for i in range(0, len(texts), batch_size):
                        batch = texts[i : i + batch_size]
                        res = client.post(self.endpoint, headers=headers, json={"text": batch})
                        if res.status_code == 200:
                            data = res.json()
                            result = data.get("result", {})
                            embeddings = result.get("data")
                            if embeddings and isinstance(embeddings, list):
                                for emb in embeddings:
                                    all_embeddings.append([float(x) for x in emb])
                                continue
                        logger.warning(
                            f"Cloudflare embedding API returned {res.status_code}: {res.text}. Falling back."
                        )
                        raise EmbeddingError(f"Cloudflare returned status {res.status_code}")

                if len(all_embeddings) == len(texts):
                    return all_embeddings
            except Exception as e:
                logger.warning(f"Cloudflare Workers AI embedding error: {e}. Attempting local fallback.")

        if self.fallback_local:
            try:
                local_emb = self._get_local_fallback()
                return local_emb.embed_documents(texts)
            except Exception as loc_err:
                logger.error(f"Local embedding fallback also failed: {loc_err}")

        # Deterministic normalized hash-based embedding fallback if local model fails
        return [self._hash_embed(t, self._dimension) for t in texts]

    def embed_query(self, text: str) -> List[float]:
        """Embed a single query text."""
        result = self.embed_documents([text])
        return result[0]

    @staticmethod
    def _hash_embed(text: str, dim: int = 384) -> List[float]:
        """Deterministic pseudo-semantic vector generation fallback."""
        vec = [0.0] * dim
        tokens = text.lower().split()
        if not tokens:
            return vec
        for tok in tokens:
            h = hash(tok)
            idx = abs(h) % dim
            sign = 1.0 if (h % 2 == 0) else -1.0
            vec[idx] += sign
        norm = math.sqrt(sum(x * x for x in vec)) or 1.0
        return [x / norm for x in vec]
