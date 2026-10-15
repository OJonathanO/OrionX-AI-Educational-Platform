"""RAG evaluation framework for measuring retrieval and generation quality."""
import re
import logging
from typing import List, Dict, Any, Optional, Set, Tuple
from dataclasses import dataclass, field
from collections import defaultdict

logger = logging.getLogger(__name__)


@dataclass
class EvaluationResult:
    """Container for evaluation metrics."""
    metrics: Dict[str, float] = field(default_factory=dict)
    details: Dict[str, Any] = field(default_factory=dict)

    def summary(self) -> str:
        """Return a human-readable summary of metrics."""
        lines = ["=== Evaluation Results ==="]
        for key, value in self.metrics.items():
            lines.append(f"  {key}: {value:.4f}" if isinstance(value, float) else f"  {key}: {value}")
        return "\n".join(lines)


class RetrievalEvaluator:
    """Evaluate retrieval quality with standard IR metrics."""

    def evaluate_retrieval(
        self,
        test_questions: List[Dict[str, Any]],
        expected_doc_ids: Dict[str, List[str]],
        k: int = 5,
    ) -> EvaluationResult:
        """Evaluate retrieval performance.

        Args:
            test_questions: List of dicts with 'query' and 'question_id' keys.
            expected_doc_ids: Dict mapping question_id to list of relevant document IDs.
            k: The k value for Recall@k and MRR.

        Returns:
            EvaluationResult with recall_at_k, mrr, precision_at_k, and f1_at_k.
        """
        if not test_questions:
            return EvaluationResult(metrics={"error": "no test questions provided"})

        recalls = []
        mrrs = []
        precisions = []
        f1_scores = []

        for item in test_questions:
            question_id = item.get("question_id", "")
            query = item.get("query", "")

            if not query:
                continue

            # Get expected documents
            expected = set(expected_doc_ids.get(question_id, []))
            if not expected:
                continue

            # Simulate retrieval (in practice, this would call the actual retrieval service)
            # For evaluation, we assume the caller provides retrieved_doc_ids
            retrieved = item.get("retrieved_doc_ids", [])[:k]
            retrieved_set = set(retrieved)

            # Compute metrics
            hits = len(expected & retrieved_set)

            # Recall@k
            recall = hits / len(expected) if expected else 0.0
            recalls.append(recall)

            # Precision@k
            precision = hits / len(retrieved) if retrieved else 0.0
            precisions.append(precision)

            # F1@k
            if precision + recall > 0:
                f1 = 2 * precision * recall / (precision + recall)
            else:
                f1 = 0.0
            f1_scores.append(f1)

            # MRR
            mrr = 0.0
            for rank, doc_id in enumerate(retrieved, 1):
                if doc_id in expected:
                    mrr = 1.0 / rank
                    break
            mrrs.append(mrr)

        n = len(recalls)
        if n == 0:
            return EvaluationResult(metrics={"error": "no valid test cases"})

        metrics = {
            "recall_at_k": sum(recalls) / n,
            "precision_at_k": sum(precisions) / n,
            "f1_at_k": sum(f1_scores) / n,
            "mrr": sum(mrrs) / n,
            "num_questions": float(n),
            "k": float(k),
        }

        return EvaluationResult(
            metrics=metrics,
            details={
                "per_question_recall": recalls,
                "per_question_mrr": mrrs,
            },
        )

    def evaluate_citation_validity(
        self,
        sources: List[Dict[str, Any]],
        retrieved_chunks: List[Dict[str, Any]],
    ) -> EvaluationResult:
        """Check if citations point to actual retrieved chunks.

        Args:
            sources: List of citation dicts with 'source_id' or 'chunk_id'.
            retrieved_chunks: List of retrieved chunk dicts with 'chunk_id'.

        Returns:
            EvaluationResult with citation_precision, citation_recall, and citation_f1.
        """
        if not retrieved_chunks:
            return EvaluationResult(
                metrics={
                    "citation_precision": 0.0,
                    "citation_recall": 0.0,
                    "citation_f1": 0.0,
                },
                details={"error": "no retrieved chunks to validate against"},
            )

        # Build set of valid chunk IDs
        valid_chunk_ids = {chunk.get("chunk_id", "") for chunk in retrieved_chunks}
        valid_chunk_ids.discard("")

        # Extract cited chunk IDs from sources
        cited_ids = set()
        for source in sources:
            chunk_id = source.get("chunk_id", "")
            source_id = source.get("source_id", "")

            # Try to match source_id to chunk_id
            if chunk_id:
                cited_ids.add(chunk_id)
            elif source_id:
                # Source IDs are typically 1-based indices into retrieved chunks
                try:
                    idx = int(source_id) - 1
                    if 0 <= idx < len(retrieved_chunks):
                        cited_id = retrieved_chunks[idx].get("chunk_id", "")
                        if cited_id:
                            cited_ids.add(cited_id)
                except (ValueError, TypeError):
                    pass

        # Compute metrics
        valid_citations = cited_ids & valid_chunk_ids
        citation_precision = (
            len(valid_citations) / len(cited_ids) if cited_ids else 0.0
        )
        citation_recall = (
            len(valid_citations) / len(valid_chunk_ids) if valid_chunk_ids else 0.0
        )

        if citation_precision + citation_recall > 0:
            citation_f1 = (
                2 * citation_precision * citation_recall
                / (citation_precision + citation_recall)
            )
        else:
            citation_f1 = 0.0

        return EvaluationResult(
            metrics={
                "citation_precision": citation_precision,
                "citation_recall": citation_recall,
                "citation_f1": citation_f1,
                "num_citations": float(len(cited_ids)),
                "num_valid_citations": float(len(valid_citations)),
            },
            details={
                "invalid_citations": list(cited_ids - valid_chunk_ids),
                "uncited_chunks": list(valid_chunk_ids - cited_ids),
            },
        )

    def evaluate_groundedness(
        self,
        answer_text: str,
        context_passages: List[str],
    ) -> EvaluationResult:
        """Evaluate if the answer is grounded in the provided context.

        Uses keyword overlap as a basic groundedness check.

        Args:
            answer_text: The generated answer text.
            context_passages: List of context passage strings.

        Returns:
            EvaluationResult with groundedness_score and coverage_ratio.
        """
        if not answer_text or not context_passages:
            return EvaluationResult(
                metrics={
                    "groundedness_score": 0.0,
                    "coverage_ratio": 0.0,
                },
                details={"error": "empty answer or context"},
            )

        # Tokenize answer and context
        answer_tokens = set(self._tokenize(answer_text))
        if not answer_tokens:
            return EvaluationResult(
                metrics={
                    "groundedness_score": 0.0,
                    "coverage_ratio": 0.0,
                },
            )

        # Combine all context passages
        all_context = " ".join(context_passages)
        context_tokens = set(self._tokenize(all_context))

        # Compute overlap
        overlapping = answer_tokens & context_tokens
        groundedness_score = len(overlapping) / len(answer_tokens)

        # Coverage: how much of the context is used by the answer
        coverage_ratio = len(overlapping) / len(context_tokens) if context_tokens else 0.0

        # Check for hallucination indicators
        hallucination_markers = [
            "i believe",
            "i think",
            "it seems",
            "probably",
            "likely",
            "in my opinion",
            "as far as i know",
        ]
        hallucination_count = sum(
            1 for marker in hallucination_markers
            if marker in answer_text.lower()
        )

        return EvaluationResult(
            metrics={
                "groundedness_score": groundedness_score,
                "coverage_ratio": coverage_ratio,
                "hallucination_markers": float(hallucination_count),
                "answer_token_count": float(len(answer_tokens)),
                "context_token_count": float(len(context_tokens)),
            },
            details={
                "overlapping_tokens": len(overlapping),
                "answer_only_tokens": list(answer_tokens - context_tokens)[:20],
            },
        )

    def _tokenize(self, text: str) -> List[str]:
        """Simple tokenization for evaluation."""
        return re.findall(r'\b[a-zA-Z]{2,}\b', text.lower())
