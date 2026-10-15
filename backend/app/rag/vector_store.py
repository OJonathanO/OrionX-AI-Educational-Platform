"""Vector store with pluggable backends (in-memory, ChromaDB)."""
import uuid
import json
import logging
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, field
from abc import ABC, abstractmethod
import numpy as np

logger = logging.getLogger(__name__)


@dataclass
class VectorRecord:
    id: str
    text: str
    embedding: np.ndarray
    metadata: Dict[str, Any] = field(default_factory=dict)
    document_id: str = ""
    owner_id: Optional[int] = None


@dataclass
class RetrievalResult:
    chunk_id: str
    text: str
    score: float
    document_id: str
    document_title: str
    page_number: Optional[int] = None
    section_heading: str = ""
    owner_id: Optional[int] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


class VectorStore(ABC):
    """Abstract vector store."""

    @abstractmethod
    def add(self, records: List[VectorRecord]) -> None:
        pass

    @abstractmethod
    def search(
        self,
        query_embedding: np.ndarray,
        top_k: int = 5,
        owner_id: Optional[int] = None,
        document_ids: Optional[List[str]] = None,
        threshold: float = 0.0,
    ) -> List[RetrievalResult]:
        pass

    @abstractmethod
    def delete_by_document(self, document_id: str) -> int:
        pass

    @abstractmethod
    def delete_by_owner(self, owner_id: int) -> int:
        pass

    @abstractmethod
    def count(self) -> int:
        pass


class InMemoryVectorStore(VectorStore):
    """In-memory vector store using numpy cosine similarity. Good for development."""

    def __init__(self):
        self._records: Dict[str, VectorRecord] = {}

    def add(self, records: List[VectorRecord]) -> None:
        for r in records:
            self._records[r.id] = r

    def search(
        self,
        query_embedding: np.ndarray,
        top_k: int = 5,
        owner_id: Optional[int] = None,
        document_ids: Optional[List[str]] = None,
        threshold: float = 0.0,
    ) -> List[RetrievalResult]:
        if not self._records:
            return []

        # Normalize query
        query_norm = np.linalg.norm(query_embedding)
        if query_norm == 0:
            return []
        query_normalized = query_embedding / query_norm

        results = []
        for record in self._records.values():
            # Filter by owner
            if owner_id is not None and record.owner_id != owner_id:
                continue
            if record.owner_id is None and owner_id is not None:
                # Public documents are accessible to all
                if record.metadata.get("is_public") != True:
                    continue

            # Filter by document IDs
            if document_ids and record.document_id not in document_ids:
                continue

            # Handle dimension mismatch by padding the shorter vector with zeros
            rec_emb = record.embedding
            if query_embedding.shape[0] != rec_emb.shape[0]:
                max_dim = max(query_embedding.shape[0], rec_emb.shape[0])
                q_padded = np.zeros(max_dim)
                r_padded = np.zeros(max_dim)
                q_padded[: query_embedding.shape[0]] = query_embedding
                r_padded[: rec_emb.shape[0]] = rec_emb
                q_padded_norm = np.linalg.norm(q_padded)
                r_padded_norm = np.linalg.norm(r_padded)
                if q_padded_norm == 0 or r_padded_norm == 0:
                    continue
                similarity = float(np.dot(q_padded / q_padded_norm, r_padded / r_padded_norm))
            else:
                # Cosine similarity
                rec_norm = np.linalg.norm(rec_emb)
                if rec_norm == 0:
                    continue
                similarity = float(np.dot(query_normalized, rec_emb / rec_norm))

            if similarity >= threshold:
                results.append(RetrievalResult(
                    chunk_id=record.id,
                    text=record.text,
                    score=similarity,
                    document_id=record.document_id,
                    document_title=record.metadata.get("title", ""),
                    page_number=record.metadata.get("page_number"),
                    section_heading=record.metadata.get("section_heading", ""),
                    owner_id=record.owner_id,
                    metadata=record.metadata,
                ))

        results.sort(key=lambda x: x.score, reverse=True)
        return results[:top_k]

    def delete_by_document(self, document_id: str) -> int:
        to_delete = [k for k, v in self._records.items() if v.document_id == document_id]
        for k in to_delete:
            del self._records[k]
        return len(to_delete)

    def delete_by_owner(self, owner_id: int) -> int:
        to_delete = [k for k, v in self._records.items() if v.owner_id == owner_id]
        for k in to_delete:
            del self._records[k]
        return len(to_delete)

    def count(self) -> int:
        return len(self._records)


class ChromaDBVectorStore(VectorStore):
    """ChromaDB-backed vector store. Requires chromadb package."""

    def __init__(self, persist_path: str, collection_name: str = "documents"):
        try:
            import chromadb
        except ImportError:
            raise ImportError("chromadb is not installed. Install with: pip install chromadb")
        self.client = chromadb.PersistentClient(path=persist_path)
        self.collection = self.client.get_or_create_collection(name=collection_name)

    def add(self, records: List[VectorRecord]) -> None:
        if not records:
            return
        ids = [r.id for r in records]
        texts = [r.text for r in records]
        embeddings = [r.embedding.tolist() for r in records]
        metadatas = [r.metadata for r in records]
        self.collection.upsert(ids=ids, documents=texts, embeddings=embeddings, metadatas=metadatas)

    def search(
        self,
        query_embedding: np.ndarray,
        top_k: int = 5,
        owner_id: Optional[int] = None,
        document_ids: Optional[List[str]] = None,
        threshold: float = 0.0,
    ) -> List[RetrievalResult]:
        where = {}
        if owner_id is not None:
            where["owner_id"] = owner_id
        if document_ids:
            where["document_id"] = {"$in": document_ids}

        results = self.collection.query(
            query_embeddings=[query_embedding.tolist()],
            n_results=top_k,
            where=where if where else None,
        )

        retrieval_results = []
        if results and results["ids"] and results["ids"][0]:
            for i, chunk_id in enumerate(results["ids"][0]):
                distance = results["distances"][0][i] if results.get("distances") else 0
                score = 1.0 - distance  # Convert distance to similarity
                if score < threshold:
                    continue
                metadata = results["metadatas"][0][i] if results.get("metadatas") else {}
                retrieval_results.append(RetrievalResult(
                    chunk_id=chunk_id,
                    text=results["documents"][0][i],
                    score=score,
                    document_id=metadata.get("document_id", ""),
                    document_title=metadata.get("title", ""),
                    page_number=metadata.get("page_number"),
                    section_heading=metadata.get("section_heading", ""),
                    owner_id=metadata.get("owner_id"),
                    metadata=metadata,
                ))
        return retrieval_results

    def delete_by_document(self, document_id: str) -> int:
        result = self.collection.get(where={"document_id": document_id})
        ids = result.get("ids", [])
        if ids:
            self.collection.delete(ids=ids)
        return len(ids)

    def delete_by_owner(self, owner_id: int) -> int:
        result = self.collection.get(where={"owner_id": owner_id})
        ids = result.get("ids", [])
        if ids:
            self.collection.delete(ids=ids)
        return len(ids)

    def count(self) -> int:
        return self.collection.count()


# Singleton instance
_vector_store: Optional[VectorStore] = None


def get_vector_store() -> VectorStore:
    """Get or create the global vector store instance."""
    global _vector_store
    if _vector_store is None:
        _vector_store = InMemoryVectorStore()
    return _vector_store


def set_vector_store(store: VectorStore) -> None:
    """Set the global vector store (useful for testing)."""
    global _vector_store
    _vector_store = store
