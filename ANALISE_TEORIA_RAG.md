# 📚 Análise: Perguntas Teóricas - Busca Simples vs RAG

## 🔍 Problema Atual

### Fluxo Atual (Busca Keyword Simples)

```
Usuário: "O que é emenda PIX?"
    ↓
1. MCP Server: search_in_markdown("O que é emenda PIX?")
    ↓
2. Busca: query_terms = ["o", "que", "é", "emenda", "pix"]
    ↓
3. Retorna: Top 5 parágrafos que contêm QUALQUER termo
    ↓
4. LLM Qwen: Recebe ~5000 chars de texto + prompt
    ↓
5. Problema: Contexto pode ser irrelevante! ❌
```

### Problemas Identificados

1. **Busca muito superficial**
   - Apenas keyword matching (`"pix" in texto.lower()`)
   - Retorna parágrafos com ANY palavra, não ALL
   - Sem ranking de relevância

2. **Sem compreensão semântica**
   - "emenda PIX" vs "emenda de relator" são tratados igual
   - Não entende sinônimos ou contexto

3. **LLM pequeno (Qwen 1.5B) sem contexto suficiente**
   - Modelo pequeno tem dificuldade de interpretar texto longo
   - Tende a "alucinação" quando contexto é confuso

4. **Qualidade do contexto recuperado**
   - Top 5 parágrafos podem não ser os mais relevantes
   - Pode faltar informação chave

---

## 🎯 Soluções Propostas

### Opção 1: **Busca BM25 (Mais Rápida)** ⚡

**O que é:** Algoritmo de ranking estatístico (TF-IDF melhorado)

**Vantagens:**
- ✅ Muito mais rápido que embeddings (~50ms)
- ✅ Não precisa de GPU
- ✅ Rank melhor que keyword simples
- ✅ Biblioteca Python simples (`rank-bm25`)

**Desvantagens:**
- ⚠️ Ainda não é semântico (não entende sinônimos)
- ⚠️ Precisa de palavras exatas

**Implementação:**
```python
from rank_bm25 import BM25Okapi

# Pré-processa uma vez
paragraphs = [p for p in doc.split('\n\n')]
tokenized_corpus = [p.lower().split() for p in paragraphs]
bm25 = BM25Okapi(tokenized_corpus)

# Busca
query_tokens = user_question.lower().split()
scores = bm25.get_scores(query_tokens)
top_indices = np.argsort(scores)[-5:]  # Top 5
```

**Resultado esperado:**
- Velocidade: ~50ms (vs ~30ms atual)
- Qualidade: +30-40% melhor ranking

---

### Opção 2: **RAG com Embeddings (Melhor Qualidade)** 🎯

**O que é:** Vetorização semântica + busca por similaridade

**Vantagens:**
- ✅ Busca semântica real (entende sinônimos, contexto)
- ✅ "emenda PIX" encontra "transferência especial"
- ✅ Qualidade muito superior
- ✅ Pode usar modelo pequeno de embedding (~100MB)

**Desvantagens:**
- ❌ Mais lento: ~200-500ms para embedding + busca
- ❌ Precisa vetorizar documentos (setup inicial)
- ❌ Mais complexo

**Stack Sugerida:**
```python
# Modelo de embedding leve
from sentence_transformers import SentenceTransformer

# Opção 1: all-MiniLM-L6-v2 (80MB, rápido)
model = SentenceTransformer('all-MiniLM-L6-v2')

# Opção 2: Modelo em português
model = SentenceTransformer('neuralmind/bert-base-portuguese-cased')

# Vector store simples
import faiss
index = faiss.IndexFlatL2(384)  # Dimensão do embedding
```

**Resultado esperado:**
- Velocidade: +200-300ms (ainda aceitável)
- Qualidade: +60-80% melhor relevância

---

### Opção 3: **Híbrido BM25 + Reranking** ⚡🎯 **(RECOMENDADO)**

**Como funciona:**
1. BM25 recupera top 20 candidatos (~50ms)
2. Reranker classifica os 20 (~100ms)
3. Retorna top 5 realmente relevantes

**Vantagens:**
- ✅ Velocidade boa (~150ms total)
- ✅ Qualidade próxima de RAG puro
- ✅ Melhor custo-benefício

**Implementação:**
```python
from rank_bm25 import BM25Okapi
from sentence_transformers import CrossEncoder

# Stage 1: BM25 (rápido, recupera 20)
bm25_results = bm25.get_top_n(query, paragraphs, n=20)

# Stage 2: Reranker (preciso, classifica 20)
reranker = CrossEncoder('cross-encoder/ms-marco-MiniLM-L-6-v2')
scores = reranker.predict([(query, doc) for doc in bm25_results])
top_5 = [bm25_results[i] for i in np.argsort(scores)[-5:]]
```

---

## 📊 Comparação das Opções

| Critério | Keyword Atual | BM25 | RAG Embeddings | Híbrido BM25+Rerank |
|----------|--------------|------|----------------|---------------------|
| **Velocidade** | ~30ms | ~50ms | ~300ms | ~150ms |
| **Qualidade** | ⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ |
| **Complexidade** | Baixa | Baixa | Alta | Média |
| **Uso RAM** | ~5MB | ~10MB | ~200MB | ~150MB |
| **GPU necessária?** | Não | Não | Não* | Não* |
| **Setup inicial** | 0s | ~1s | ~30s | ~5s |

*Modelos pequenos rodam bem em CPU

---

## 🎯 Minha Recomendação

### Para SEU caso específico: **Opção 3 (Híbrido BM25 + Reranker)**

**Justificativa:**

1. **Documento pequeno (42KB)**
   - RAG puro seria "overkill"
   - Híbrido é suficiente

2. **Qwen 1.5B já está no limite**
   - Precisa de contexto BEM selecionado
   - Qualidade do retrieval é CRÍTICA

3. **Usuário quer velocidade**
   - 150ms adicional é aceitável
   - Muito melhor que 300ms do RAG puro

4. **Não precisa de GPU**
   - Reranker roda bem em CPU
   - Não adiciona dependência de hardware

---

## 🛠️ Implementação Sugerida

### Estrutura Proposta

```
mcp_server/
├── server.py
└── retrieval/
    ├── __init__.py
    ├── bm25_index.py      # BM25 indexing
    ├── reranker.py        # Cross-encoder reranker
    └── hybrid_search.py   # Orquestração
```

### Código Base

#### 1. `retrieval/bm25_index.py`

```python
from rank_bm25 import BM25Okapi
import pickle
import os

class BM25Index:
    def __init__(self, documents):
        """documents: lista de strings (parágrafos)"""
        self.documents = documents
        tokenized = [doc.lower().split() for doc in documents]
        self.bm25 = BM25Okapi(tokenized)

    def search(self, query, top_k=20):
        """Retorna top_k documentos mais relevantes"""
        query_tokens = query.lower().split()
        scores = self.bm25.get_scores(query_tokens)
        top_indices = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)[:top_k]
        return [(self.documents[i], scores[i]) for i in top_indices]

    def save(self, path):
        with open(path, 'wb') as f:
            pickle.dump((self.documents, self.bm25), f)

    @classmethod
    def load(cls, path):
        with open(path, 'rb') as f:
            documents, bm25 = pickle.load(f)
        obj = cls.__new__(cls)
        obj.documents = documents
        obj.bm25 = bm25
        return obj
```

#### 2. `retrieval/reranker.py`

```python
from sentence_transformers import CrossEncoder
import numpy as np

class Reranker:
    def __init__(self, model_name='cross-encoder/ms-marco-MiniLM-L-6-v2'):
        """Reranker usando cross-encoder"""
        self.model = CrossEncoder(model_name)

    def rerank(self, query, documents, top_k=5):
        """Reordena documentos por relevância"""
        if len(documents) == 0:
            return []

        # Cria pares (query, doc)
        pairs = [(query, doc) for doc in documents]

        # Calcula scores
        scores = self.model.predict(pairs)

        # Retorna top_k
        top_indices = np.argsort(scores)[-top_k:][::-1]
        return [(documents[i], scores[i]) for i in top_indices]
```

#### 3. `retrieval/hybrid_search.py`

```python
from .bm25_index import BM25Index
from .reranker import Reranker
import os

class HybridSearch:
    def __init__(self, index_path=None):
        self.bm25 = None
        self.reranker = Reranker()

        if index_path and os.path.exists(index_path):
            self.bm25 = BM25Index.load(index_path)

    def index_documents(self, markdown_file, index_path):
        """Indexa um arquivo markdown"""
        with open(markdown_file, 'r', encoding='utf-8') as f:
            content = f.read()

        # Divide em parágrafos
        paragraphs = [p.strip() for p in content.split('\n\n') if len(p.strip()) > 50]

        # Cria índice BM25
        self.bm25 = BM25Index(paragraphs)
        self.bm25.save(index_path)

        print(f"✅ Indexed {len(paragraphs)} paragraphs")

    def search(self, query, top_k=5):
        """Busca híbrida: BM25 + Reranking"""
        if not self.bm25:
            return []

        # Stage 1: BM25 recupera 20 candidatos
        candidates = self.bm25.search(query, top_k=20)
        docs_only = [doc for doc, score in candidates]

        # Stage 2: Reranker seleciona top 5
        reranked = self.reranker.rerank(query, docs_only, top_k=top_k)

        return [doc for doc, score in reranked]
```

#### 4. Integração no `server.py`

```python
# No início do arquivo
from retrieval.hybrid_search import HybridSearch
import os

# Variável global
hybrid_search = None

def get_hybrid_search():
    """Inicializa busca híbrida (lazy loading)"""
    global hybrid_search
    if hybrid_search is None:
        index_path = os.path.join(os.path.dirname(__file__), 'retrieval', 'bm25_index.pkl')
        hybrid_search = HybridSearch(index_path)

        # Se índice não existe, cria
        if not os.path.exists(index_path):
            md_file = os.path.join(os.path.dirname(__file__), '..', 'data', 'teorico', 'Relatorio_Emendas_Parlamentares.md')
            hybrid_search.index_documents(md_file, index_path)

    return hybrid_search

# Substitui search_in_markdown
def search_in_markdown(query: str) -> str:
    """Busca híbrida BM25 + Reranking"""
    try:
        searcher = get_hybrid_search()
        results = searcher.search(query, top_k=5)

        if not results:
            return "Nenhum resultado encontrado nos documentos teóricos."

        # Formata resultados
        formatted = []
        for i, doc in enumerate(results, 1):
            formatted.append(f"**Trecho {i}:**\n{doc}\n")

        return "\n---\n".join(formatted)

    except Exception as e:
        return f"Erro na busca: {str(e)}"
```

---

## 📦 Dependências Adicionais

```bash
pip install rank-bm25 sentence-transformers
```

**Tamanho adicional:**
- rank-bm25: ~50KB
- sentence-transformers: ~5MB
- Modelo reranker: ~80MB (download automático)

**Total:** ~85MB adicional

---

## ⚡ Performance Esperada

### Antes (Keyword simples):
```
Pergunta: "O que é emenda PIX?"
Tempo: 8-12s total
├─ Busca: 30ms
├─ LLM: 8-12s
└─ Qualidade: ⭐⭐ (contexto ruim)
```

### Depois (Híbrido BM25 + Rerank):
```
Pergunta: "O que é emenda PIX?"
Tempo: 8-12s total (similar!)
├─ Busca: 150ms (+120ms)
├─ LLM: 8-12s (mesmo tempo, mas contexto MELHOR)
└─ Qualidade: ⭐⭐⭐⭐ (contexto relevante)
```

**Resultado:** Mesma velocidade, MUITO mais qualidade!

---

## 🎯 Decisão Final

### Eu recomendo: **Implementar Híbrido (Opção 3)**

**Motivos:**
1. ✅ Melhor custo-benefício
2. ✅ Não aumenta tempo perceptível (~150ms é insignificante vs 8s do LLM)
3. ✅ Qualidade MUITO superior
4. ✅ Fácil de implementar (~200 linhas)
5. ✅ Não precisa de GPU

### Se não quiser complexidade: **BM25 simples (Opção 1)**

**Motivos:**
1. ✅ Muito simples (~50 linhas)
2. ✅ +20ms apenas
3. ✅ Já melhora 30-40%
4. ❌ Não é semântico

---

## 🧪 Plano de Implementação

### Fase 1: Proof of Concept (1-2h)
1. Instalar dependências
2. Criar script de teste isolado
3. Comparar resultados: keyword vs BM25 vs híbrido

### Fase 2: Integração (1-2h)
1. Criar módulo `retrieval/`
2. Modificar `server.py`
3. Testar com queries reais

### Fase 3: Validação (30min)
1. Criar benchmark de queries
2. Medir qualidade (manual)
3. Medir velocidade

---

## 📝 Próximos Passos

Quer que eu:
1. ✅ Implemente a solução híbrida completa?
2. ✅ Crie script de teste para comparar abordagens?
3. ✅ Implemente apenas BM25 simples primeiro?

**Minha recomendação:** Começar com **script de teste** para você ver a diferença de qualidade, depois decidir qual implementar.

---

**Autor:** Claude (2025-12-09)
