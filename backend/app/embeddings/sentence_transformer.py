"""Sentence Transformers local embedding model wrapper."""

from typing import List, Optional
import torch
from sentence_transformers import SentenceTransformer
from backend.app.core.exceptions import EmbeddingError
from backend.app.core.logging import get_logger
from backend.app.embeddings.base import BaseEmbeddings

logger = get_logger(__name__)


class SentenceTransformerEmbeddings(BaseEmbeddings):
    """Local embedding generator using Sentence Transformers with M-series Apple Silicon MPS acceleration."""

    def __init__(
        self,
        model_name: str = "sentence-transformers/all-MiniLM-L6-v2",
        device: Optional[str] = None,
        batch_size: int = 32,
    ):
        self.model_name = model_name
        self.batch_size = batch_size

        if device is None or device == "auto":
            if torch.backends.mps.is_available():
                self.device = "mps"
            elif torch.cuda.is_available():
                self.device = "cuda"
            else:
                self.device = "cpu"
        else:
            self.device = device

        logger.info(f"Loading embedding model '{self.model_name}' on device '{self.device}'...")
        try:
            try:
                # Attempt fast load from local cache first (ideal for offline sandboxes & edge devices)
                self.model = SentenceTransformer(
                    self.model_name,
                    device=self.device,
                    local_files_only=True,
                )
            except Exception:
                self.model = SentenceTransformer(
                    self.model_name,
                    device=self.device,
                    local_files_only=False,
                )

            if hasattr(self.model, "get_embedding_dimension"):
                self._dimension = self.model.get_embedding_dimension()
            else:
                self._dimension = self.model.get_sentence_embedding_dimension()
            logger.info(f"Embedding model loaded successfully. Dimension: {self._dimension}")
        except Exception as e:
            logger.error(f"Failed to load embedding model '{self.model_name}': {e}")
            raise EmbeddingError(f"Could not initialize embedding model {self.model_name}: {str(e)}")

    @property
    def dimension(self) -> int:
        return self._dimension

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        if not texts:
            return []

        # Replace empty strings with a single space to avoid tokenizer errors
        cleaned_texts = [t if t.strip() else " " for t in texts]

        try:
            embeddings = self.model.encode(
                cleaned_texts,
                batch_size=self.batch_size,
                show_progress_bar=False,
                normalize_embeddings=True,
                convert_to_numpy=True,
            )
            return embeddings.tolist()
        except Exception as e:
            logger.error(f"Error embedding {len(texts)} document chunks: {e}")
            raise EmbeddingError(f"Document embedding failed: {str(e)}")

    def embed_query(self, text: str) -> List[float]:
        cleaned_text = text if text.strip() else " "
        try:
            embedding = self.model.encode(
                cleaned_text,
                show_progress_bar=False,
                normalize_embeddings=True,
                convert_to_numpy=True,
            )
            return embedding.tolist()
        except Exception as e:
            logger.error(f"Error embedding query '{text[:50]}...': {e}")
            raise EmbeddingError(f"Query embedding failed: {str(e)}")
