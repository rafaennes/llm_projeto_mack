"""
Knowledge Base - Schema e Regras de Negócio
Base de conhecimento para conversão de linguagem natural para SQL
"""

import os

# Caminho do relatório teórico
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REPORT_PATH = os.path.join(PROJECT_ROOT, "data", "teorico", "Relatorio_Emendas_Parlamentares.md")

DATABASE_SCHEMA = """
# SCHEMA DO BANCO DE DADOS - EMENDAS PARLAMENTARES

## Tabela Principal: emendas_parlamentares

Esta tabela contém informações sobre emendas parlamentares do Governo Federal Brasileiro.

### Colunas Disponíveis:

| Coluna | Tipo | Descrição | Exemplo |
|--------|------|-----------|---------|
| codigo_emenda | TEXT | Código único identificador da emenda | "202012345" |
| ano_emenda | INTEGER | Ano de execução da emenda | 2020, 2021, 2022, 2023 |
| tipo_emenda | TEXT | Tipo/classificação da emenda | "Individual", "Bancada" |
| codigo_autor | TEXT | Código do autor | "12345" |
| nome_autor | TEXT | Nome completo do parlamentar autor | "João da Silva" |
| numero_emenda | TEXT | Número da emenda | "1234/2020" |
| localidade_gasto | TEXT | Localidade do gasto | Texto descritivo |
| codigo_municipio_ibge | TEXT | Código IBGE do município | "3550308" |
| municipio | TEXT | Município beneficiado pela emenda | "SÃO PAULO", "RIO DE JANEIRO" |
| codigo_uf_ibge | INTEGER | Código IBGE do estado | 35 |
| uf | TEXT | Nome completo do estado (maiúsculo) | "SÃO PAULO", "RIO DE JANEIRO", "PARANÁ" |
| regiao | TEXT | Região geográfica do Brasil | "Sudeste", "Nordeste", "Sul", "Norte", "Centro-Oeste" |
| codigo_funcao | TEXT | Código da função orçamentária | "10" |
| nome_funcao | TEXT | Função orçamentária | "Saúde", "Educação", "Infraestrutura" |
| codigo_subfuncao | TEXT | Código da subfunção | "301" |
| nome_subfuncao | TEXT | Subfunção orçamentária | Detalhamento da função |
| codigo_programa | TEXT | Código do programa | "2015" |
| nome_programa | TEXT | Programa orçamentário | Nome do programa |
| codigo_acao | TEXT | Código da ação | "21C0" |
| nome_acao | TEXT | Descrição da ação/finalidade | "Construção de escola", "Pavimentação" |
| codigo_plano_orcamentario | TEXT | Código do plano orçamentário | "0001" |
| nome_plano_orcamentario | TEXT | Nome do plano orçamentário | Descrição do plano |
| valor_empenhado | REAL | Valor empenhado em Reais (R$) | 1000000.00 |
| valor_liquidado | REAL | Valor liquidado em Reais (R$) | 950000.00 |
| valor_pago | REAL | Valor efetivamente pago em Reais (R$) | 900000.00 |
| valor_restos_pagar_inscritos | REAL | Restos a pagar inscritos em Reais (R$) | 100000.00 |
| valor_restos_pagar_cancelados | REAL | Restos a pagar cancelados em Reais (R$) | 50000.00 |
| valor_restos_pagar_pagos | REAL | Restos a pagar pagos em Reais (R$) | 50000.00 |

### Total de Registros: 87.912 emendas parlamentares

---

## REGRAS DE NEGÓCIO

### 1. Hierarquia de Valores
- valor_pago <= valor_liquidado <= valor_empenhado
- Nem todo valor empenhado é pago
- Valores em Reais (R$)

### 2. Geografia
- **UF**: Nomes completos dos estados em MAIÚSCULO (SÃO PAULO, RIO DE JANEIRO, MINAS GERAIS, BAHIA, etc)
- **Regiões**: Norte, Nordeste, Centro-Oeste, Sudeste, Sul
- **Municípios**: Nomes em MAIÚSCULO. Use LIKE para busca parcial (ex: WHERE municipio LIKE '%SÃO PAULO%')

### 3. Autores
- Deputados Federais e Senadores
- Use LIKE para busca por nome parcial
- Agrupe por nome_autor para somar valores por parlamentar

### 4. Classificação Orçamentária
- **Função**: Área de atuação (Saúde, Educação, etc)
- **Subfunção**: Detalhamento da função
- **Programa**: Programa específico do governo
- **Ação**: Descrição da finalidade específica (nome_acao)

---

## EXEMPLOS DE QUERIES COMUNS

### Exemplo 1: Top 10 parlamentares por valor pago
```sql
SELECT
    nome_autor,
    COUNT(*) as total_emendas,
    SUM(valor_empenhado) as total_empenhado,
    SUM(valor_pago) as total_pago
FROM emendas_parlamentares
GROUP BY nome_autor
ORDER BY total_pago DESC
LIMIT 10
```

### Exemplo 2: Emendas por município
```sql
SELECT
    nome_autor,
    nome_acao,
    valor_pago,
    ano_emenda
FROM emendas_parlamentares
WHERE municipio LIKE '%SÃO PAULO%'
  AND uf = 'SÃO PAULO'
ORDER BY valor_pago DESC
LIMIT 50
```

### Exemplo 3: Distribuição por região
```sql
SELECT
    regiao,
    COUNT(*) as quantidade_emendas,
    SUM(valor_pago) as total_pago,
    AVG(valor_pago) as media_por_emenda
FROM emendas_parlamentares
GROUP BY regiao
ORDER BY total_pago DESC
```

### Exemplo 4: Emendas de saúde
```sql
SELECT
    municipio,
    uf,
    nome_autor,
    nome_acao,
    valor_pago
FROM emendas_parlamentares
WHERE funcao LIKE '%Saúde%'
ORDER BY valor_pago DESC
LIMIT 20
```

### Exemplo 5: Buscar emendas de um autor específico
```sql
SELECT
    municipio,
    uf,
    nome_acao,
    valor_pago,
    ano_emenda
FROM emendas_parlamentares
WHERE nome_autor LIKE '%Silva%'
ORDER BY valor_pago DESC
LIMIT 30
```

---

## INSTRUÇÕES PARA GERAÇÃO DE SQL

1. **SEMPRE use LIMIT** para limitar resultados (máximo 100)
2. **Use LIKE com %** para buscas de texto: `WHERE nome LIKE '%texto%'`
3. **Agregações comuns**:
   - COUNT(*) para contar
   - SUM(valor_pago) para somar valores
   - AVG(valor_pago) para média
   - MAX/MIN para valores extremos
4. **ORDER BY** sempre que houver agregação ou top N
5. **GROUP BY** quando usar funções agregadas
6. **Para nomes de colunas com espaços ou acentos**: Use aspas simples nos valores, não nas colunas

---

## VOCABULÁRIO COMUM - TRADUÇÕES

Quando o usuário falar... → Use a coluna:
- "autor", "parlamentar", "deputado", "senador" → nome_autor
- "cidade", "município" → municipio
- "estado" → uf
- "região" → regiao
- "quanto foi pago", "valor pago" → valor_pago
- "quanto foi empenhado" → valor_empenhado
- "finalidade", "para que serve", "objetivo" → nome_acao
- "ano" → ano_emenda
- "área", "setor" → funcao

---

## FORMATAÇÃO DE VALORES

- Valores monetários estão em número decimal (ex: 1500000.50)
- Para exibir formatado: 1.500.000,50 (formato brasileiro)
- Anos são inteiros: 2020, 2021, 2022, 2023
"""


def get_database_knowledge() -> str:
    """Retorna a base de conhecimento completa."""
    return DATABASE_SCHEMA


def get_sql_generation_prompt(user_question: str) -> str:
    """
    Gera o prompt completo para o LLM converter linguagem natural em SQL.

    Args:
        user_question: Pergunta do usuário em linguagem natural

    Returns:
        Prompt formatado para o LLM
    """

    # Prompt simplificado para performance
    prompt = f"""Converta para SQL.

TABELA: emendas_parlamentares
COLUNAS PRINCIPAIS: nome_autor, municipio, uf (nome completo do estado em maiúsculo), regiao, nome_funcao, nome_acao, valor_empenhado, valor_liquidado, valor_pago, ano_emenda

REGRAS:
- Campo UF contém nomes completos em MAIÚSCULO: 'SÃO PAULO', 'RIO DE JANEIRO', etc
- Use LIKE com % para texto
- Sempre use LIMIT (max 100)
- ORDER BY quando fizer sentido
- Valores monetários: valor_pago, valor_empenhado, valor_liquidado

PERGUNTA: {user_question}

Responda APENAS com o SQL (sem ```sql, sem explicações):
"""

    return prompt


def get_response_generation_prompt(user_question: str, sql_query: str, sql_results: str) -> str:
    """
    Gera prompt para o LLM criar uma resposta em linguagem natural.

    Args:
        user_question: Pergunta original do usuário
        sql_query: Query SQL gerada
        sql_results: Resultados da query em formato de tabela

    Returns:
        Prompt para geração de resposta natural
    """

    # Prompt ultra simplificado - apenas 1 frase
    prompt = f"""Responda em 1 frase curta:

PERGUNTA: {user_question}
DADOS: {sql_results[:500]}

Resposta:"""

    return prompt


def load_legislative_report() -> str:
    """
    Carrega o relatório teórico sobre emendas parlamentares.

    Returns:
        Conteúdo do relatório em markdown
    """
    try:
        with open(REPORT_PATH, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        return f"Erro ao carregar relatório: {str(e)}"


def is_legislative_question(user_question: str) -> bool:
    """
    Detecta se a pergunta é sobre legislação/normas/conceitos
    ao invés de dados numéricos.

    Args:
        user_question: Pergunta do usuário

    Returns:
        True se for pergunta legislativa, False se for sobre dados
    """
    question_lower = user_question.lower()

    # Palavras-chave que indicam pergunta sobre legislação/normas
    legislative_keywords = [
        'lei', 'norma', 'regra', 'pode', 'permitido', 'proibido',
        'como funciona', 'o que é', 'define', 'definição',
        'constitucional', 'legal', 'legislação', 'regulamento',
        'resolução', 'decreto', 'portaria', 'instrução',
        'ministro', 'stf', 'supremo', 'decisão', 'judicial',
        'dino', 'transparência', 'rastreabilidade', 'orçamento secreto',
        'emenda pix', 'emenda de relator', 'emenda de bancada',
        'limite', 'teto', 'impositividade', 'obrigatoriedade',
        'tipo de emenda', 'modalidade', 'categoria',
        'processo', 'tramitação', 'aprovação', 'sanção',
        'conceito', 'explique', 'explicação', 'entenda'
    ]

    # Verifica se contém alguma palavra-chave legislativa
    for keyword in legislative_keywords:
        if keyword in question_lower:
            return True

    # Palavras que indicam claramente consulta de dados
    data_keywords = [
        'quantos', 'quanto', 'total', 'soma', 'média',
        'maior', 'menor', 'top', 'ranking', 'lista',
        'valor', 'montante', 'recurso', 'verba',
        'parlamentar específico', 'município', 'estado', 'região',
        'ano', 'período', 'comparar valores', 'crescimento'
    ]

    # Se tem palavra de dados E não tem palavra legislativa, é consulta de dados
    has_data_keyword = any(kw in question_lower for kw in data_keywords)
    if has_data_keyword:
        return False

    # Default: se não é claramente sobre dados, trata como legislativa
    return True


def get_legislative_answer_prompt(user_question: str, report_content: str) -> str:
    """
    Gera prompt para o LLM responder baseado no relatório teórico.

    Args:
        user_question: Pergunta do usuário
        report_content: Conteúdo do relatório markdown

    Returns:
        Prompt formatado
    """

    # Trunca para 12000 chars (~3000 tokens) para performance
    # Qwen 1.5B é pequeno, processar 10K tokens é muito lento
    if len(report_content) > 12000:
        report_content = report_content[:12000] + "\n\n[... mais informações disponíveis no relatório completo ...]"

    prompt = f"""Você é especialista em emendas parlamentares brasileiras.

Use o relatório abaixo para responder:

{report_content}

PERGUNTA: {user_question}

Resposta objetiva (2-4 frases):"""

    return prompt
