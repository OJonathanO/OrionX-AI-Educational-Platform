"""Embedding providers with pluggable backends."""
import numpy as np
from typing import List, Optional
from abc import ABC, abstractmethod
import logging

logger = logging.getLogger(__name__)


class EmbeddingProvider(ABC):
    """Abstract base for embedding providers."""

    @abstractmethod
    def embed(self, texts: List[str]) -> np.ndarray:
        """Embed a list of texts into vectors."""
        pass

    @property
    @abstractmethod
    def dimension(self) -> int:
        """Return embedding dimension."""
        pass


class TFIDFEmbeddingProvider(EmbeddingProvider):
    """TF-IDF vectorizer-based embeddings. No heavy ML dependencies needed."""

    def __init__(self, max_features: int = 10000):
        from sklearn.feature_extraction.text import TfidfVectorizer
        self.max_features = max_features
        self.vectorizer = TfidfVectorizer(
            max_features=max_features,
            stop_words="english",
            ngram_range=(1, 2),
            min_df=1,
        )
        self._dimension = max_features
        self._is_fitted = False

    def embed(self, texts: List[str]) -> np.ndarray:
        if not texts:
            return np.array([])
        if not self._is_fitted:
            vectors = self.vectorizer.fit_transform(texts).toarray()
            self._is_fitted = True
        else:
            vectors = self.vectorizer.transform(texts).toarray()
        # Pad to max_features if vocabulary is smaller
        if vectors.ndim == 2 and vectors.shape[1] < self.max_features:
            pad_width = self.max_features - vectors.shape[1]
            vectors = np.pad(vectors, ((0, 0), (0, pad_width)), mode="constant")
        return vectors

    @property
    def dimension(self) -> int:
        return self._dimension


class SentenceTransformerProvider(EmbeddingProvider):
    """Sentence Transformers embeddings. Requires sentence-transformers package."""

    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        try:
            from sentence_transformers import SentenceTransformer
        except ImportError:
            raise ImportError(
                "sentence-transformers is not installed. "
                "Install it with: pip install sentence-transformers"
            )
        self.model = SentenceTransformer(model_name)
        self._dimension = self.model.get_sentence_embedding_dimension()

    def embed(self, texts: List[str]) -> np.ndarray:
        return self.model.encode(texts, show_progress_bar=False)

    @property
    def dimension(self) -> int:
        return self._dimension


def get_embedding_provider(provider: str = "sklearn", model: str = "tfidf") -> EmbeddingProvider:
    """Factory function to get embedding provider."""
    if provider == "sklearn" or model == "tfidf":
        return TFIDFEmbeddingProvider()
    elif provider == "sentence-transformers":
        return SentenceTransformerProvider(model)
    else:
        logger.warning(f"Unknown embedding provider '{provider}', falling back to sklearn")
        return TFIDFEmbeddingProvider()
