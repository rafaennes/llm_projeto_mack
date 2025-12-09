#!/bin/bash
# Inicia o servidor MCP

set -e

# Diretório do projeto
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

# Ativa o virtual environment
source "${PROJECT_ROOT}/venv/bin/activate"

# Exporta variáveis de ambiente
export DB_SQL_URL="sqlite:///${PROJECT_ROOT}/local_deploy/data/db_transparencia.db"
export DB_MONGO_URL="mongodb://localhost:27017/db_rag"

# Inicia o servidor MCP via stdio
exec python3 "${PROJECT_ROOT}/mcp_server/server.py"
