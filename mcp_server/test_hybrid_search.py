#!/usr/bin/env python3
"""
Test script para comparar busca híbrida BM25 + Reranker
vs busca simples por keywords
"""

import os
import sys
from retrieval.hybrid_search import HybridSearch

# Paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(BASE_DIR)
index_path = os.path.join(BASE_DIR, 'retrieval', 'bm25_index.pkl')
md_file = os.path.join(PROJECT_ROOT, 'data', 'teorico', 'Relatorio_Emendas_Parlamentares.md')

# Test queries
test_queries = [
    "O que é emenda PIX?",
    "Quais são as regras de rastreabilidade?",
    "Lei Complementar 210/2024",
    "Tipos de emendas parlamentares",
    "Como funciona a execução orçamentária?"
]

def main():
    print("="*80)
    print("TESTE DE BUSCA HÍBRIDA (BM25 + Reranker)")
    print("="*80)
    print()

    # Initialize hybrid search
    print(f"📂 Carregando documentos de: {md_file}")
    print(f"📂 Índice BM25 será salvo em: {index_path}")
    print()

    searcher = HybridSearch(index_path)

    # Create or load index
    if not os.path.exists(index_path):
        print("🔧 Criando índice BM25 pela primeira vez...")
        searcher.index_documents(md_file, index_path)
        print()
    else:
        print("✅ Índice BM25 já existe, carregado com sucesso!")
        print()

    # Test each query
    for i, query in enumerate(test_queries, 1):
        print(f"\n{'='*80}")
        print(f"TESTE {i}/{len(test_queries)}: {query}")
        print(f"{'='*80}\n")

        # Perform hybrid search
        results = searcher.search(query, top_k=3, bm25_candidates=20)

        if not results:
            print("❌ Nenhum resultado encontrado")
            continue

        # Display results
        for j, doc in enumerate(results, 1):
            # Truncate long paragraphs
            snippet = doc[:500] + "..." if len(doc) > 500 else doc

            print(f"**[Resultado {j}]**")
            print(snippet)
            print()

    print("\n" + "="*80)
    print("✅ TESTE CONCLUÍDO")
    print("="*80)
    print()
    print("📊 Estatísticas:")
    print(f"   - Total de documentos indexados: {len(searcher.bm25.documents)}")
    print(f"   - Modelo de reranking: cross-encoder/ms-marco-MiniLM-L-6-v2")
    print(f"   - Pipeline: BM25 (20 candidatos) → Reranker (top 3)")
    print()

if __name__ == "__main__":
    main()
