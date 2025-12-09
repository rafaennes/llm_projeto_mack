"""
BM25 Index - Fast keyword-based ranking
"""

from rank_bm25 import BM25Okapi
import pickle
import os
from typing import List, Tuple


class BM25Index:
    """BM25-based document index for fast keyword retrieval"""

    def __init__(self, documents: List[str]):
        """
        Initialize BM25 index with documents

        Args:
            documents: List of text documents (paragraphs)
        """
        self.documents = documents

        # Tokenize documents (simples lowercase split)
        tokenized = [doc.lower().split() for doc in documents]

        # Create BM25 index
        self.bm25 = BM25Okapi(tokenized)

        print(f"✅ BM25 Index criado com {len(documents)} documentos")

    def search(self, query: str, top_k: int = 20) -> List[Tuple[str, float]]:
        """
        Search for most relevant documents

        Args:
            query: Search query
            top_k: Number of results to return

        Returns:
            List of (document, score) tuples sorted by relevance
        """
        # Tokenize query
        query_tokens = query.lower().split()

        # Get BM25 scores
        scores = self.bm25.get_scores(query_tokens)

        # Get top k indices
        top_indices = sorted(
            range(len(scores)),
            key=lambda i: scores[i],
            reverse=True
        )[:top_k]

        # Return documents with scores
        return [(self.documents[i], scores[i]) for i in top_indices]

    def save(self, path: str):
        """Save index to disk"""
        with open(path, 'wb') as f:
            pickle.dump((self.documents, self.bm25), f)
        print(f"✅ Índice salvo em: {path}")

    @classmethod
    def load(cls, path: str):
        """Load index from disk"""
        with open(path, 'rb') as f:
            documents, bm25 = pickle.load(f)

        # Create object without calling __init__
        obj = cls.__new__(cls)
        obj.documents = documents
        obj.bm25 = bm25

        print(f"✅ Índice carregado: {len(documents)} documentos")
        return obj
