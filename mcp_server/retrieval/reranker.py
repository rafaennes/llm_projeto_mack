"""
Cross-Encoder Reranker - Semantic reranking
"""

from sentence_transformers import CrossEncoder
import numpy as np
from typing import List, Tuple


class Reranker:
    """Cross-encoder based reranker for semantic relevance"""

    def __init__(self, model_name: str = 'cross-encoder/ms-marco-MiniLM-L-6-v2'):
        """
        Initialize reranker with cross-encoder model

        Args:
            model_name: HuggingFace model name
                       Default: cross-encoder/ms-marco-MiniLM-L-6-v2 (~80MB, fast)
        """
        print(f"⏳ Carregando reranker: {model_name}")
        self.model = CrossEncoder(model_name)
        print(f"✅ Reranker carregado!")

    def rerank(self, query: str, documents: List[str], top_k: int = 5) -> List[Tuple[str, float]]:
        """
        Rerank documents by semantic relevance

        Args:
            query: Search query
            documents: List of candidate documents
            top_k: Number of results to return

        Returns:
            List of (document, score) tuples sorted by relevance
        """
        if len(documents) == 0:
            return []

        # Create query-document pairs
        pairs = [(query, doc) for doc in documents]

        # Predict relevance scores (semantic similarity)
        scores = self.model.predict(pairs)

        # Get top k indices (highest scores first)
        top_indices = np.argsort(scores)[-top_k:][::-1]

        # Return documents with scores
        return [(documents[i], float(scores[i])) for i in top_indices]
