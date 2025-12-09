# Chat SQL com Mistral - Transparência Governamental

Cliente Streamlit inteligente que converte perguntas em linguagem natural para queries SQL usando Mistral 7B.

**Baseado no padrão NSC (Natural SQL Chatbot)**

## 🎯 Como Funciona

```
Pergunta em Linguagem Natural
         ↓
   Mistral 7B analisa + Knowledge Base
         ↓
     Gera SQL automaticamente
         ↓
  Executa no banco SQLite
         ↓
 Exibe resultados em tabela
         ↓
 Gera resposta em linguagem natural
```

## ✨ Funcionalidades

### 1. **Conversão NL → SQL com IA**
- Usa Mistral 7B local para entender perguntas complexas
- Knowledge base integrada com schema completo
- Regras de negócio e exemplos de queries

### 2. **Exibição Completa**
- ✅ **SQL Gerado**: Mostra a query construída
- ✅ **Tabela de Resultados**: Dados formatados
- ✅ **Resposta Natural**: Análise em português
- ✅ **Valores Formatados**: R$ 1.500.000,00

### 3. **Histórico de Conversa**
- Todas perguntas e respostas salvas na sessão
- SQL de cada consulta disponível para conferência
- Botão para limpar histórico

## 🚀 Início Rápido

### 1. Inicie o chat

```bash
cd /home/ennes/mestrado/llm_projeto
./mcp_client/start_chat.sh
```

### 2. Aguarde o carregamento

⏳ **Primeira execução**: ~30-60 segundos (Mistral carregando)
⚡ **Próximas**: Instantâneo (modelo fica em cache)

### 3. Acesse e pergunte!

Abra http://localhost:8504 e faça perguntas como:

```
Quais os 10 parlamentares que mais receberam recursos?
```

```
Mostre emendas para São Paulo acima de 1 milhão
```

```
Compare o total de emendas entre as regiões
```

## 💬 Exemplos de Perguntas

### Análises Gerais
- "Quais os 10 parlamentares que mais receberam recursos?"
- "Mostre a distribuição de emendas por região"
- "Qual o total de valores pagos por ano?"
- "Compare gastos entre Sudeste e Nordeste"

### Buscas Específicas
- "Busque emendas para São Paulo"
- "Emendas do deputado Silva em 2023"
- "Emendas de saúde acima de 1 milhão"
- "Mostre emendas para educação no Rio de Janeiro"

### Agregações e Estatísticas
- "Qual a média de valor por emenda?"
- "Total investido em educação por estado"
- "Quantas emendas foram pagas em 2022?"
- "Qual o maior valor pago em uma única emenda?"

## 📊 O Que Você Verá

Para cada pergunta, o sistema mostra:

### 1. **SQL Gerado** (expansível)
```sql
SELECT nome_autor, SUM(valor_pago) as total_pago
FROM emendas_parlamentares
GROUP BY nome_autor
ORDER BY total_pago DESC
LIMIT 10
```

### 2. **Tabela de Resultados**
| nome_autor | total_pago |
|------------|------------|
| João Silva | R$ 5.000.000,00 |
| Maria Santos | R$ 4.500.000,00 |
| ... | ... |

### 3. **Análise em Linguagem Natural**
> **Análise:** Foram encontrados 10 parlamentares. João Silva lidera com R$ 5 milhões em emendas pagas, seguido por Maria Santos com R$ 4,5 milhões. Os 10 parlamentares somam R$ 35 milhões em recursos.

## 🧠 Knowledge Base

O sistema usa uma base de conhecimento integrada que contém:

### Schema Completo
- 19 colunas da tabela `emendas_parlamentares`
- Tipos de dados de cada coluna
- Descrições e exemplos

### Regras de Negócio
- Hierarquia de valores (empenhado → liquidado → pago)
- Geografia (regiões, UFs, municípios)
- Classificação orçamentária
- Vocabulário comum (traduções)

### Exemplos de Queries
- Top N parlamentares
- Buscas por município
- Distribuição por região
- Filtros por função orçamentária

**Arquivo**: [knowledge_base.py](knowledge_base.py)

## 🔧 Arquitetura

### Componentes

```python
# 1. Knowledge Base (knowledge_base.py)
- Schema da tabela
- Regras de negócio
- Exemplos de queries
- Prompts para o LLM

# 2. Chat App (chat_app.py)
- Interface Streamlit
- Carregamento do Mistral
- Conversão NL → SQL
- Execução de queries
- Geração de respostas
```

### Fluxo de Dados

```
Usuário: "Top 10 autores"
    ↓
[Knowledge Base] + [Pergunta]
    ↓
[Mistral LLM] → Gera SQL
    ↓
"SELECT nome_autor, SUM(valor_pago)..."
    ↓
[SQLite] → Executa query
    ↓
DataFrame com resultados
    ↓
[Mistral LLM] → Gera resposta natural
    ↓
"Foram encontrados 10 parlamentares..."
```

## 🆚 Comparação com Versão Anterior

| Característica | Versão Simples | **Versão com Mistral** |
|---------------|----------------|------------------------|
| **NL → SQL** | Regras if/else | ✅ Mistral 7B |
| **Inteligência** | Básica (keywords) | ✅ Alta (entende contexto) |
| **Respostas** | Apenas dados | ✅ Dados + análise natural |
| **SQL visível** | ❌ Não | ✅ Sim (expansível) |
| **Formatação** | Básica | ✅ Moeda brasileira |
| **Knowledge** | Nenhum | ✅ Schema + regras |
| **Carregamento** | Instantâneo | ⏳ 30-60s (primeira vez) |

## ⚙️ Configuração

### Variáveis de Ambiente

O script `start_chat.sh` configura automaticamente:

```bash
DB_SQL_URL="sqlite:///.../db_transparencia.db"
LLM_PATH=".../mistral-7b-instruct-v0.2.gguf"
```

### Parâmetros do Mistral

```python
LlamaCpp(
    model_path=LLM_PATH,
    temperature=0.1,      # Baixa = mais determinístico
    max_tokens=2048,      # Máximo de tokens na resposta
    n_ctx=4096,          # Context window
    n_gpu_layers=0,      # CPU only (0) ou GPU (>0)
    verbose=False
)
```

## 🐛 Troubleshooting

### Erro: "Modelo LLM não encontrado"
```bash
# Verifique se o modelo existe
ls -lh llm_models/mistral-7b-instruct-v0.2.gguf

# Deve ter ~4.1GB
```

### Erro: "ModuleNotFoundError: langchain_community"
```bash
source venv/bin/activate
pip install langchain==0.1.20 langchain-community==0.0.38
```

### Mistral demora muito para carregar
- Normal na primeira vez: 30-60 segundos
- Nas próximas: Cache do Streamlit reutiliza
- Se usar GPU (n_gpu_layers > 0): Mais rápido

### SQL gerado está errado
1. Verifique o prompt em [knowledge_base.py](knowledge_base.py)
2. Ajuste a temperatura (0.0 = mais determinístico)
3. Adicione mais exemplos no knowledge base

### Tabela não aparece
- Verifique se a query retornou resultados
- Veja o SQL gerado (clique no expansor)
- Teste a query direto no SQLite

## 📈 Performance

### Tempos Típicos

| Operação | Tempo |
|----------|-------|
| Carregar Mistral (primeira vez) | 30-60s |
| Carregar Mistral (cache) | <1s |
| NL → SQL | 2-5s |
| Executar SQL | <1s |
| Gerar resposta natural | 2-5s |
| **Total por pergunta** | **4-10s** |

### Otimizações

- ✅ Streamlit `@st.cache_resource` no LLM
- ✅ Temperature baixa (0.1) para respostas rápidas
- ✅ Limite de tokens (2048)
- ✅ SQL com LIMIT automático

## 🔒 Segurança

- ✅ Apenas queries SELECT permitidas
- ✅ Validação antes de executar SQL
- ✅ Limite de 100 resultados por query
- ✅ Timeout de execução
- ⚠️ Para produção: adicionar autenticação

## 🎓 Baseado em NSC

Este cliente segue o padrão **NSC (Natural SQL Chatbot)**:

1. ✅ Knowledge base com schema
2. ✅ Conversão NL → SQL com LLM
3. ✅ Execução segura de queries
4. ✅ Exibição de SQL para conferência
5. ✅ Tabela de resultados formatada
6. ✅ Resposta em linguagem natural

## 📝 Próximos Passos

### Melhorias Planejadas

- [ ] Suporte a gráficos (matplotlib/plotly)
- [ ] Exportar resultados (CSV, Excel, PDF)
- [ ] Histórico persistente (banco de dados)
- [ ] Sugestões de perguntas baseadas no contexto
- [ ] Multi-tabelas (joins automáticos)
- [ ] Cache de queries frequentes
- [ ] Logs de analytics

### Integrações Futuras

- [ ] RAG com MongoDB (documentos legais)
- [ ] APIs em tempo real
- [ ] Notificações de novas emendas
- [ ] Comparações temporais automáticas

## 📚 Arquivos

```
mcp_client/
├── chat_app.py           # Interface Streamlit principal
├── knowledge_base.py     # Schema + regras + prompts
├── start_chat.sh         # Script de inicialização
└── README.md             # Esta documentação
```

## 🤝 Contribuindo

Para adicionar novas funcionalidades:

### 1. Melhorar Knowledge Base
Edite `knowledge_base.py` → `DATABASE_SCHEMA`

### 2. Adicionar Validações
Edite `chat_app.py` → `execute_sql()`

### 3. Customizar Prompts
Edite `knowledge_base.py` → `get_sql_generation_prompt()`

## 📄 Licença

MIT License - Projeto acadêmico de mestrado

---

**Desenvolvido para:** Análise de Transparência Governamental
**Tecnologias:** Mistral 7B, Streamlit, SQLite, LangChain
**Dados:** 87.912 emendas parlamentares do Governo Federal
