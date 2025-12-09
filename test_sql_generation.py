#!/usr/bin/env python3
"""
Script de teste para validar geração de SQL e exibição tabular
"""

import sys
import os

# Adiciona o path do projeto
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, PROJECT_ROOT)

from langchain_community.llms import LlamaCpp
from sqlalchemy import create_engine, text
import pandas as pd

# Configurações
LLM_PATH = os.path.join(PROJECT_ROOT, "llm_models", "qwen2.5-1.5b-instruct-q4_k_m.gguf")
DB_PATH = os.path.join(PROJECT_ROOT, "local_deploy", "data", "db_transparencia.db")
DB_URL = f"sqlite:///{DB_PATH}"

# Schema do banco
db_schema = """
CREATE TABLE emendas_parlamentares (
    codigo_emenda TEXT,
    ano_emenda INTEGER,
    tipo_emenda TEXT,
    codigo_autor TEXT,
    nome_autor TEXT, -- Nome do Deputado/Senador
    numero_emenda TEXT,
    localidade_gasto TEXT,
    codigo_municipio_ibge TEXT,
    municipio TEXT, -- Nome da Cidade
    codigo_uf_ibge INTEGER,
    uf TEXT, -- Sigla/Nome do Estado (SP, SÃO PAULO, RJ, etc)
    regiao TEXT, -- Região (Sudeste, Sul, etc)
    codigo_funcao TEXT,
    nome_funcao TEXT, -- Área (Saúde, Educação)
    codigo_subfuncao TEXT,
    nome_subfuncao TEXT,
    codigo_programa TEXT,
    nome_programa TEXT,
    codigo_acao TEXT,
    nome_acao TEXT, -- Descrição da ação
    codigo_plano_orcamentario TEXT,
    nome_plano_orcamentario TEXT,
    valor_empenhado REAL, -- Valor empenhado
    valor_liquidado REAL, -- Valor liquidado
    valor_pago REAL, -- Valor efetivamente pago
    valor_restos_pagar_inscritos REAL,
    valor_restos_pagar_cancelados REAL,
    valor_restos_pagar_pagos REAL
);
"""

def test_sql_generation(user_question):
    """Testa a geração de SQL para uma pergunta"""

    print(f"\n{'='*80}")
    print(f"PERGUNTA: {user_question}")
    print(f"{'='*80}\n")

    # Carrega LLM
    print("⏳ Carregando modelo Qwen...")
    llm = LlamaCpp(
        model_path=LLM_PATH,
        temperature=0.1,
        max_tokens=512,
        n_ctx=20000,
        n_gpu_layers=0,
        verbose=False
    )
    print("✅ Modelo carregado!\n")

    # Gera SQL
    system_prompt = f"""Você é um especialista em gerar SQL SQLite preciso.

SCHEMA DA TABELA:
{db_schema}

PERGUNTA DO USUÁRIO: "{user_question}"

REGRAS IMPORTANTES:
1. Apenas queries SELECT são permitidas
2. Campo UF contém nomes completos em maiúsculo: 'SÃO PAULO', 'PARANÁ', 'BAHIA', etc
3. Para agrupar por estado use: GROUP BY uf
4. Para somar valores use: SUM(valor_empenhado) ou SUM(valor_pago)
5. SEMPRE adicione ORDER BY quando usar agregações
6. SEMPRE adicione LIMIT 50 ao final
7. Retorne APENAS o SQL dentro de um bloco markdown

EXEMPLOS:
Pergunta: "Soma do valor empenhado por estado"
```sql
SELECT uf, SUM(valor_empenhado) as total FROM emendas_parlamentares GROUP BY uf ORDER BY total DESC LIMIT 50;
```

Pergunta: "Quantas emendas por região"
```sql
SELECT regiao, COUNT(*) as quantidade FROM emendas_parlamentares GROUP BY regiao ORDER BY quantidade DESC;
```

AGORA GERE O SQL:
```sql"""

    print("🔍 Gerando SQL...")
    response = llm.invoke(system_prompt, stop=["User:", "```\n"])

    # Extrai SQL
    import re
    match = re.search(r"```sql\s*([\s\S]*?)\s*```", response, re.IGNORECASE)

    if match:
        sql_query = match.group(1).strip()
    else:
        match_fallback = re.search(r"(SELECT\s+[\s\S]+?;)", response, re.IGNORECASE)
        if match_fallback:
            sql_query = match_fallback.group(1).strip()
        else:
            match_line = re.search(r"(SELECT\s+.*)", response, re.IGNORECASE)
            if match_line:
                sql_query = match_line.group(1).strip()
            else:
                sql_query = "SELECT * FROM emendas_parlamentares LIMIT 10"

    sql_query = sql_query.replace("```", "").split(';')[0].strip()

    print(f"✅ SQL Gerado:\n{sql_query}\n")

    # Executa SQL
    print("🛠️ Executando query...")
    engine = create_engine(DB_URL)

    try:
        with engine.connect() as conn:
            result = conn.execute(text(sql_query))
            df = pd.DataFrame(result.fetchall(), columns=result.keys())

            # Exibe como markdown (como o MCP server faz)
            markdown_result = df.to_markdown(index=False)

            print("✅ Resultado (formato markdown):\n")
            print(markdown_result)
            print(f"\n📊 Total de linhas: {len(df)}")

            return sql_query, markdown_result, True

    except Exception as e:
        print(f"❌ Erro ao executar SQL: {e}")
        return sql_query, str(e), False


if __name__ == "__main__":
    # Testes
    test_cases = [
        "Qual a soma do valor empenhado por estado?",
        "Quantas emendas por região?",
        "Top 10 autores com maior valor pago",
    ]

    results = []
    for question in test_cases:
        sql, result, success = test_sql_generation(question)
        results.append({
            "question": question,
            "sql": sql,
            "success": success
        })

    # Sumário
    print(f"\n\n{'='*80}")
    print("SUMÁRIO DOS TESTES")
    print(f"{'='*80}\n")

    for i, r in enumerate(results, 1):
        status = "✅" if r["success"] else "❌"
        print(f"{i}. {status} {r['question']}")
        print(f"   SQL: {r['sql'][:100]}...")
        print()
