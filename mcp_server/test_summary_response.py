#!/usr/bin/env python3
"""
Teste de resposta sintética com trechos de referência
"""

import os
import sys
from retrieval.hybrid_search import HybridSearch

# Paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(BASE_DIR)
index_path = os.path.join(BASE_DIR, 'retrieval', 'bm25_index.pkl')

def test_search_output():
    """Testa o formato da saída da busca"""

    print("="*80)
    print("TESTE DE FORMATO DE SAÍDA")
    print("="*80)
    print()

    # Initialize hybrid search
    searcher = HybridSearch(index_path)

    # Test query
    query = "O que é emenda PIX?"
    print(f"🔍 Query: {query}")
    print()

    # Perform search (10 trechos, como configurado)
    results = searcher.search(query, top_k=10, bm25_candidates=30)

    print(f"✅ Encontrados {len(results)} trechos")
    print()

    # Simula o que o server.py faz
    formatted = []
    for i, doc in enumerate(results, 1):
        snippet = doc[:1000] + "..." if len(doc) > 1000 else doc
        formatted.append(f"[Trecho {i}]\n{snippet}")

    server_response = "\n\n".join(formatted)

    print("="*80)
    print("SAÍDA DO SERVER (primeiros 2000 chars):")
    print("="*80)
    print(server_response[:2000])
    print()

    print("="*80)
    print("SIMULAÇÃO DO CLIENT (como seria exibido ao usuário):")
    print("="*80)

    # Simula o que chat_app.py faria
    summary_placeholder = "[AQUI O LLM GERARIA UM RESUMO SINTÉTICO EM 2-4 FRASES]"

    print("📚 **Resposta:**\n")
    print(summary_placeholder)
    print()
    print("---\n")
    print("📖 **Trechos de Referência (fontes):**\n")

    # Mostra top 5
    doc_lines = server_response.split("\n\n")
    for i, trecho in enumerate(doc_lines[:5], 1):
        if trecho.strip():
            clean = trecho.replace(f"[Trecho {i}]", "").strip()
            if len(clean) > 600:
                clean = clean[:600] + "..."
            print(f"**[{i}]** {clean}\n")

if __name__ == "__main__":
    test_search_output()
