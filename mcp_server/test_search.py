#!/usr/bin/env python3
"""
Cliente de teste para o servidor MCP de Transparência
"""

import asyncio
import os
import sys
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

# Caminho absoluto do projeto
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

async def test_mcp_server():
    """Testa o servidor MCP."""

    print("=" * 60)
    print("  Testando Servidor MCP - Transparência Gov")
    print("=" * 60)
    print()

    # Parâmetros do servidor
    server_script = os.path.join(PROJECT_ROOT, "mcp_server", "start_mcp_server.sh")

    server_params = StdioServerParameters(
        command=server_script,
        args=[],
        env={
            "DB_SQL_URL": f"sqlite:///{PROJECT_ROOT}/local_deploy/data/db_transparencia.db"
        }
    )

    print(f"🚀 Iniciando servidor: {server_script}")
    print()

    try:
        async with stdio_client(server_params) as (read, write):
            async with ClientSession(read, write) as session:
                # Initialize the connection
                await session.initialize()
                print("✅ Servidor conectado e inicializado!")
                # Teste 1: Get Schema
                print("=" * 60)
                print("TESTE 1: Obtendo schema da tabela")
                print("=" * 60)

                result1 = await session.call_tool("get_emendas_schema", {})
                print(result1.content[0].text[:500] + "...")
                print()

                # Teste 2: Estatísticas
                print("=" * 60)
                print("TESTE 2: Estatísticas gerais")
                print("=" * 60)

                result2 = await session.call_tool("get_emendas_stats", {})
                print(result2.content[0].text)
                print()

                # Teste 3: Query customizada
                print("=" * 60)
                print("TESTE 3: Top 10 autores por valor pago")
                print("=" * 60)

                result3 = await session.call_tool(
                    "query_emendas",
                    {
                        "query": """
                        SELECT
                            nome_autor,
                            COUNT(*) as total_emendas,
                            SUM(valor_pago) as total_pago
                        FROM emendas_parlamentares
                        GROUP BY nome_autor
                        ORDER BY total_pago DESC
                        LIMIT 10
                        """
                    }
                )
                print(result3.content[0].text)
                print()

                # Teste 4: Busca por município
                print("=" * 60)
                print("TESTE 4: Emendas para São Paulo")
                print("=" * 60)

                result4 = await session.call_tool(
                    "get_emendas_by_municipality",
                    {
                        "municipality": "São Paulo",
                        "uf": "SP"
                    }
                )
                print(result4.content[0].text[:1000] + "...")
                print()

                print("=" * 60)
                print("✅ Todos os testes concluídos com sucesso!")
                print("=" * 60)

    except Exception as e:
        print(f"❌ Erro ao testar servidor: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(test_mcp_server())
