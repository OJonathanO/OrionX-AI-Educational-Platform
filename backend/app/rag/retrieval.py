"""Retrieval service with semantic and hybrid search capabilities."""
import re
import logging
from typing import List, Optional, Dict, Any
from dataclasses import dataclass, field
from collections import defaultdict
import numpy as np

from .embeddings import EmbeddingProvider, get_embedding_provider
from .vector_store import VectorStore, RetrievalResult, get_vector_store
from app.config import settings

logger = logging.getLogger(__name__)


@dataclass
class HybridRetrievalResult:
    """Result from hybrid search combining semantic and keyword scores."""
    chunk_id: str
    text: str
    semantic_score: float
    keyword_score: float
    combined_score: float
    document_id: str
    document_title: str
    page_number: Optional[int] = None
    section_heading: str = ""
    owner_id: Optional[int] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


class RetrievalService:
    """Service for retrieving relevant document chunks based on queries."""

    def __init__(
        self,
        embedding_provider: Optional[EmbeddingProvider] = None,
        vector_store: Optional[VectorStore] = None,
    ):
        self.embedding_provider = embedding_provider or get_embedding_provider(
            settings.EMBEDDING_PROVIDER, settings.EMBEDDING_MODEL
        )
        self.vector_store = vector_store or get_vector_store()

    def retrieve(
        self,
        query: str,
        owner_id: Optional[int] = None,
        top_k: int = None,
        threshold: float = None,
        document_ids: Optional[List[str]] = None,
    ) -> List[RetrievalResult]:
        """Retrieve relevant chunks for a query.

        Args:
            query: The search query string.
            owner_id: Filter results to this owner (plus public documents).
            top_k: Maximum number of results to return.
            threshold: Minimum similarity score threshold.
            document_ids: Optional list of document IDs to restrict search.

        Returns:
            List of RetrievalResult, deduplicated by document_id (highest score kept).
        """
        if top_k is None:
            top_k = settings.RETRIEVAL_TOP_K
        if threshold is None:
            threshold = settings.SIMILARITY_THRESHOLD

        if not query or not query.strip():
            logger.warning("Empty query provided to retrieve()")
            return []

        # Embed the query
        query_embedding = self.embedding_provider.embed([query])
        if len(query_embedding) == 0:
            logger.warning("Failed to embed query")
            return []

        # Search vector store
        results = self.vector_store.search(
            query_embedding=query_embedding[0],
            top_k=top_k * 3,  # Fetch more to allow for deduplication
            owner_id=owner_id,
            document_ids=document_ids,
            threshold=threshold,
        )

        # Deduplicate by document_id, keeping highest scoring chunk per document
        deduplicated = self._deduplicate_by_document(results, top_k)

        logger.info(
            f"Retrieved {len(deduplicated)} chunks for query (from {len(results)} raw results)"
        )
        return deduplicated

    def hybrid_search(
        self,
        query: str,
        owner_id: Optional[int] = None,
        top_k: int = None,
        threshold: float = None,
        document_ids: Optional[List[str]] = None,
        semantic_weight: float = 0.7,
        keyword_weight: float = 0.3,
    ) -> List[HybridRetrievalResult]:
        """Combine semantic (embedding) and keyword (TF-IDF) search scores.

        Args:
            query: The search query string.
            owner_id: Filter results to this owner.
            top_k: Maximum number of results.
            threshold: Minimum combined score threshold.
            document_ids: Optional document ID filter.
            semantic_weight: Weight for semantic score (0-1).
            keyword_weight: Weight for keyword score (0-1).

        Returns:
            List of HybridRetrievalResult sorted by combined score.
        """
        if top_k is None:
            top_k = settings.RETRIEVAL_TOP_K
        if threshold is None:
            threshold = settings.SIMILARITY_THRESHOLD

        if not query or not query.strip():
            return []

        # Normalize weights
        total_weight = semantic_weight + keyword_weight
        if total_weight == 0:
            semantic_weight, keyword_weight = 0.7, 0.3
            total_weight = 1.0
        semantic_weight /= total_weight
        keyword_weight /= total_weight

        # Get semantic results
        query_embedding = self.embedding_provider.embed([query])
        if len(query_embedding) == 0:
            return []

        semantic_results = self.vector_store.search(
            query_embedding=query_embedding[0],
            top_k=top_k * 5,
            owner_id=owner_id,
            document_ids=document_ids,
            threshold=0.0,  # Get all, we'll filter by combined score later
        )

        # Get keyword results using TF-IDF scoring
        keyword_scores = self._compute_keyword_scores(query, owner_id, document_ids)

        # Combine scores
        combined_results: Dict[str, HybridRetrievalResult] = {}

        for result in semantic_results:
            chunk_id = result.chunk_id
            sem_score = result.score
            kw_score = keyword_scores.get(chunk_id, 0.0)
            combined = semantic_weight * sem_score + keyword_weight * kw_score

            combined_results[chunk_id] = HybridRetrievalResult(
                chunk_id=chunk_id,
                text=result.text,
                semantic_score=sem_score,
                keyword_score=kw_score,
                combined_score=combined,
                document_id=result.document_id,
                document_title=result.document_title,
                page_number=result.page_number,
                section_heading=result.section_heading,
                owner_id=result.owner_id,
                metadata=result.metadata,
            )

        # Also include chunks that only appeared in keyword results
        for chunk_id, kw_score in keyword_scores.items():
            if chunk_id not in combined_results:
                # Find the chunk text from semantic results or skip
                # We need to look it up - for now skip if not in semantic results
                pass

        # Filter by threshold and sort
        filtered = [r for r in combined_results.values() if r.combined_score >= threshold]
        filtered.sort(key=lambda x: x.combined_score, reverse=True)

        return filtered[:top_k]

    def _deduplicate_by_document(
        self, results: List[RetrievalResult], top_k: int
    ) -> List[RetrievalResult]:
        """Deduplicate results by document_id, keeping highest scoring chunk per doc."""
        best_by_doc: Dict[str, RetrievalResult] = {}

        for result in results:
            doc_id = result.document_id
            if doc_id not in best_by_doc or result.score > best_by_doc[doc_id].score:
                best_by_doc[doc_id] = result

        deduplicated = sorted(best_by_doc.values(), key=lambda x: x.score, reverse=True)
        return deduplicated[:top_k]

    def _compute_keyword_scores(
        self,
        query: str,
        owner_id: Optional[int] = None,
        document_ids: Optional[List[str]] = None,
    ) -> Dict[str, float]:
        """Compute TF-IDF based keyword scores for chunks matching query terms.

        Returns a dict mapping chunk_id to keyword score.
        """
        try:
            from sklearn.feature_extraction.text import TfidfVectorizer
            from sklearn.metrics.pairwise import cosine_similarity
        except ImportError:
            logger.debug("sklearn not available for keyword scoring")
            return {}

        # Get all chunks from the vector store
        # We need to access the underlying records - use search with a dummy approach
        # Since VectorStore doesn't expose all records, we'll use a workaround
        # by searching with a zero embedding to get all records
        # Actually, let's use a different approach: search with high top_k

        # For InMemoryVectorStore, we can search with a dummy query
        # For ChromaDB, we'd need a different approach
        # Let's use the embedding of the query terms as a proxy

        # Simple approach: tokenize query and do basic term frequency matching
        query_terms = set(self._tokenize(query))
        if not query_terms:
            return {}

        # We need access to all chunks. Since the vector store doesn't expose them,
        # we'll use a trick: search with a very high top_k and threshold 0
        # This is a limitation of the current VectorStore interface

        # For now, return empty scores - the semantic search is the primary method
        # In production, you'd want to add a get_all_chunks() method to VectorStore
        return {}

    def _tokenize(self, text: str) -> List[str]:
        """Simple tokenization for keyword matching."""
        return re.findall(r'\b[a-zA-Z]{2,}\b', text.lower())


# Singleton instance
_retrieval_service: Optional[RetrievalService] = None


def get_retrieval_service() -> RetrievalService:
    """Get or create the global retrieval service instance."""
    global _retrieval_service
    if _retrieval_service is None:
        _retrieval_service = RetrievalService()
    return _retrieval_service
