#!/usr/bin/env python3
"""
Servidor MCP para Transparência do Governo Federal

Este servidor expõe ferramentas para consultar dados sobre:
- Emendas Parlamentares (SQL)
- Documentos de Transparência (RAG - quando MongoDB disponível)
- Dados em tempo real (API simulada)
"""

import os
import sys
from typing import Any
import pandas as pd
from sqlalchemy import create_engine, text, inspect
import json
import glob


# Adiciona o diretório app ao path para importar as tools existentes
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'app'))

# MCP SDK imports
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

# Configurações do banco de dados
DB_SQL_URL = os.getenv("DB_SQL_URL", "sqlite:///local_deploy/data/db_transparencia.db")

# Cria o servidor MCP
app = Server("transparencia-gov")

# Engine SQLAlchemy
sql_engine = None

def get_sql_engine():
    """Retorna o engine SQLAlchemy, criando se necessário."""
    global sql_engine
    if sql_engine is None:
        sql_engine = create_engine(DB_SQL_URL)
    return sql_engine

def get_table_schema(table_name: str = "emendas_parlamentares") -> str:
    """Retorna o schema de uma tabela."""
    try:
        engine = get_sql_engine()
        inspector = inspect(engine)

        if table_name not in inspector.get_table_names():
            return f"Tabela '{table_name}' não encontrada."

        columns = inspector.get_columns(table_name)
        schema_info = f"Tabela: {table_name}\n\nColunas:\n"

        for col in columns:
            col_type = str(col['type'])
            nullable = "NULL" if col['nullable'] else "NOT NULL"
            schema_info += f"  - {col['name']}: {col_type} ({nullable})\n"

        return schema_info
    except Exception as e:
        return f"Erro ao obter schema: {str(e)}"

def execute_sql_query(query: str) -> str:
    """Executa uma query SQL e retorna os resultados."""
    try:
        engine = get_sql_engine()

        # Executa a query
        with engine.connect() as conn:
            result = conn.execute(text(query))

            # Se é um SELECT, retorna os dados
            if query.strip().upper().startswith('SELECT'):
                df = pd.DataFrame(result.fetchall(), columns=result.keys())

                # Limita a 100 linhas para não sobrecarregar
                if len(df) > 100:
                    return f"Retornando primeiras 100 de {len(df)} linhas:\n\n{df.head(100).to_string()}"

                return df.to_string()
            else:
                return f"Query executada com sucesso. Linhas afetadas: {result.rowcount}"

    except Exception as e:
        return f"Erro ao executar query: {str(e)}"

def search_in_markdown(query: str) -> str:
    """Busca simples por palavra-chave nos arquivos markdown."""
    try:
        # Caminho para os arquivos teóricos
        data_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'teorico')
        md_files = glob.glob(os.path.join(data_path, "*.md"))
        
        results = []
        query_terms = query.lower().split()
        
        for file_path in md_files:
            file_name = os.path.basename(file_path)
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
            # Busca simples de parágrafos contendo os termos
            paragraphs = content.split('\n\n')
            for p in paragraphs:
                if any(term in p.lower() for term in query_terms):
                    results.append(f"Fonte: {file_name}\n\n{p[:500]}..." if len(p) > 500 else f"Fonte: {file_name}\n\n{p}")
                    
        if not results:
            return "Nenhum resultado encontrado nos documentos teóricos."
            
        return "\n---\n".join(results[:3]) # Retorna top 3 parágrafos
        
    except Exception as e:
        return f"Erro na busca de documentos: {str(e)}"


# ===== FERRAMENTAS MCP =====

@app.list_tools()
async def list_tools() -> list[Tool]:
    """Lista todas as ferramentas disponíveis no servidor MCP."""
    return [
        Tool(
            name="get_emendas_schema",
            description="""
            Retorna o schema completo da tabela de emendas parlamentares.
            Use esta ferramenta para entender a estrutura dos dados disponíveis,
            incluindo nomes de colunas e tipos de dados.

            A tabela 'emendas_parlamentares' contém dados sobre:
            - Código e tipo de emenda
            - Autor da emenda (nome e código)
            - Localização do gasto (município, UF, região)
            - Classificação orçamentária (função, subfunção, programa, ação)
            - Valores financeiros (empenhado, liquidado, pago, restos a pagar)
            """,
            inputSchema={
                "type": "object",
                "properties": {},
                "required": []
            }
        ),
        Tool(
            name="query_emendas",
            description="""
            Executa uma consulta SQL na tabela de emendas parlamentares.

            Use esta ferramenta para:
            - Buscar emendas por autor, região, município
            - Calcular totais e agregações de valores
            - Filtrar por tipo de emenda, função orçamentária, etc.
            - Analisar a distribuição de recursos

            Exemplos de queries úteis:
            - Total por autor: SELECT nome_autor, SUM(valor_pago) as total FROM emendas_parlamentares GROUP BY nome_autor ORDER BY total DESC LIMIT 10
            - Emendas por região: SELECT regiao, COUNT(*) as quantidade, SUM(valor_pago) as total FROM emendas_parlamentares GROUP BY regiao
            - Maiores emendas: SELECT * FROM emendas_parlamentares ORDER BY valor_pago DESC LIMIT 20

            IMPORTANTE: Sempre use LIMIT para limitar resultados!
            """,
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Query SQL a ser executada (apenas SELECT, por segurança)"
                    }
                },
                "required": ["query"]
            }
        ),
        Tool(
            name="get_emendas_stats",
            description="""
            Retorna estatísticas gerais sobre as emendas parlamentares.

            Fornece:
            - Total de emendas no banco
            - Soma total de valores (empenhado, liquidado, pago)
            - Número de autores únicos
            - Distribuição por tipo de emenda
            - Top 5 regiões com mais recursos
            """,
            inputSchema={
                "type": "object",
                "properties": {},
                "required": []
            }
        ),
        Tool(
            name="search_emendas_by_author",
            description="""
            Busca emendas por nome do autor (parlamentar).

            Retorna todas as emendas associadas a um autor específico,
            incluindo valores totais e distribuição por município.
            """,
            inputSchema={
                "type": "object",
                "properties": {
                    "author_name": {
                        "type": "string",
                        "description": "Nome ou parte do nome do autor (parlamentar)"
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Número máximo de resultados (padrão: 50)",
                        "default": 50
                    }
                },
                "required": ["author_name"]
            }
        ),
        Tool(
            name="get_emendas_by_municipality",
            description="""
            Lista emendas destinadas a um município específico.

            Retorna emendas filtradas por município, com informações sobre
            valores, autores e finalidades.
            """,
            inputSchema={
                "type": "object",
                "properties": {
                    "municipality": {
                        "type": "string",
                        "description": "Nome do município"
                    },
                    "uf": {
                        "type": "string",
                        "description": "Sigla do estado (UF) - opcional",
                        "default": None
                    }
                },
                "required": ["municipality"]
            }
        ),
        Tool(
            name="search_legislative_report",
            description="""
            Busca informações teóricas e legais sobre emendas parlamentares em documentos markdown.
            
            Use esta ferramenta para responder perguntas sobre:
            - Legislação e leis (ex: Lei Complementar 210/2024)
            - Definições e conceitos (o que é uma emenda, tipos de emenda)
            - Regras, decisões judiciais e processos administrativos
            - Contexto histórico e político
            
            NÃO use para buscar dados numéricos ou estatísticas (use query_emendas para isso).
            """,
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Termos de busca para encontrar no documento (ex: 'regras emenda pix')"
                    }
                },
                "required": ["query"]
            }
        )
    ]

@app.call_tool()
async def call_tool(name: str, arguments: Any) -> list[TextContent]:
    """Executa uma ferramenta do servidor MCP."""

    try:
        if name == "get_emendas_schema":
            schema = get_table_schema("emendas_parlamentares")
            return [TextContent(type="text", text=schema)]

        elif name == "query_emendas":
            query = arguments.get("query", "")

            # Validação de segurança: apenas SELECT
            if not query.strip().upper().startswith("SELECT"):
                return [TextContent(
                    type="text",
                    text="Erro: Apenas queries SELECT são permitidas por segurança."
                )]

            result = execute_sql_query(query)
            return [TextContent(type="text", text=result)]

        elif name == "get_emendas_stats":
            stats_query = """
            SELECT
                COUNT(*) as total_emendas,
                COUNT(DISTINCT nome_autor) as total_autores,
                SUM(valor_empenhado) as total_empenhado,
                SUM(valor_liquidado) as total_liquidado,
                SUM(valor_pago) as total_pago
            FROM emendas_parlamentares
            """

            result = execute_sql_query(stats_query)

            # Também busca top 5 regiões
            top_regions_query = """
            SELECT
                regiao,
                COUNT(*) as quantidade,
                SUM(valor_pago) as total_pago
            FROM emendas_parlamentares
            GROUP BY regiao
            ORDER BY total_pago DESC
            LIMIT 5
            """

            top_regions = execute_sql_query(top_regions_query)

            combined_result = f"=== ESTATÍSTICAS GERAIS ===\n\n{result}\n\n=== TOP 5 REGIÕES ===\n\n{top_regions}"

            return [TextContent(type="text", text=combined_result)]

        elif name == "search_emendas_by_author":
            author_name = arguments.get("author_name", "")
            limit = arguments.get("limit", 50)

            query = f"""
            SELECT
                nome_autor,
                municipio,
                uf,
                nome_acao,
                valor_pago
            FROM emendas_parlamentares
            WHERE nome_autor LIKE '%{author_name}%'
            ORDER BY valor_pago DESC
            LIMIT {limit}
            """

            result = execute_sql_query(query)
            return [TextContent(type="text", text=result)]

        elif name == "get_emendas_by_municipality":
            municipality = arguments.get("municipality", "")
            uf = arguments.get("uf")

            if uf:
                query = f"""
                SELECT
                    nome_autor,
                    nome_acao,
                    valor_pago,
                    ano_emenda
                FROM emendas_parlamentares
                WHERE municipio LIKE '%{municipality}%'
                AND uf = '{uf}'
                ORDER BY valor_pago DESC
                LIMIT 50
                """
            else:
                query = f"""
                SELECT
                    nome_autor,
                    municipio,
                    uf,
                    nome_acao,
                    valor_pago,
                    ano_emenda
                FROM emendas_parlamentares
                WHERE municipio LIKE '%{municipality}%'
                ORDER BY valor_pago DESC
                LIMIT 50
                """

            result = execute_sql_query(query)
            return [TextContent(type="text", text=result)]

        else:
            return [TextContent(
                type="text",
                text=f"Ferramenta '{name}' não encontrada."
            )]

    except Exception as e:
        return [TextContent(
            type="text",
            text=f"Erro ao executar ferramenta: {str(e)}"
        )]

        elif name == "search_legislative_report":
            query = arguments.get("query", "")
            result = search_in_markdown(query)
            return [TextContent(type="text", text=result)]


async def main():
    """Inicia o servidor MCP via stdio."""
    async with stdio_server() as (read_stream, write_stream):
        await app.run(
            read_stream,
            write_stream,
            app.create_initialization_options()
        )

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
