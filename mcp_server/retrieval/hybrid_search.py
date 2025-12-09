"""
Hybrid Search - BM25 + Reranking pipeline
"""

import os
from typing import List
from .bm25_index import BM25Index
from .reranker import Reranker


class HybridSearch:
    """Two-stage hybrid search: BM25 recall + Reranker precision"""

    def __init__(self, index_path: str = None):
        """
        Initialize hybrid search

        Args:
            index_path: Path to BM25 index file (optional)
        """
        self.bm25 = None
        self.reranker = None

        # Load BM25 index if exists
        if index_path and os.path.exists(index_path):
            self.bm25 = BM25Index.load(index_path)

    def _lazy_load_reranker(self):
        """Lazy load reranker (only when needed)"""
        if self.reranker is None:
            self.reranker = Reranker()

    def index_documents(self, markdown_file: str, index_path: str):
        """
        Index markdown document for search

        Args:
            markdown_file: Path to markdown file
            index_path: Path to save BM25 index
        """
        print(f"📄 Indexando: {markdown_file}")

        # Read markdown content
        with open(markdown_file, 'r', encoding='utf-8') as f:
            content = f.read()

        # Split into paragraphs (filter out very short ones)
        paragraphs = [
            p.strip()
            for p in content.split('\n\n')
            if len(p.strip()) > 50  # Min 50 chars
        ]

        print(f"📝 Encontrados {len(paragraphs)} parágrafos")

        # Create BM25 index
        self.bm25 = BM25Index(paragraphs)

        # Save index
        self.bm25.save(index_path)

    def search(self, query: str, top_k: int = 5, bm25_candidates: int = 20) -> List[str]:
        """
        Two-stage hybrid search

        Stage 1: BM25 retrieves top N candidates (fast, keyword-based)
        Stage 2: Reranker selects top K from candidates (slower, semantic)

        Args:
            query: Search query
            top_k: Final number of results to return
            bm25_candidates: Number of candidates for reranking (default: 20)

        Returns:
            List of relevant document strings
        """
        if not self.bm25:
            print("⚠️  Índice BM25 não carregado!")
            return []

        # Stage 1: BM25 Recall (fast)
        print(f"🔍 Stage 1: BM25 retrieving top {bm25_candidates} candidates...")
        candidates = self.bm25.search(query, top_k=bm25_candidates)
        docs_only = [doc for doc, score in candidates]

        if len(docs_only) == 0:
            return []

        # Stage 2: Reranker Precision (semantic)
        print(f"🎯 Stage 2: Reranking to top {top_k}...")
        self._lazy_load_reranker()
        reranked = self.reranker.rerank(query, docs_only, top_k=top_k)

        # Return only documents (no scores)
        return [doc for doc, score in reranked]
