#!/bin/bash
# Inicia o cliente de chat Streamlit para MCP

set -e

# Diretório do projeto
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

# Ativa o virtual environment
source "${PROJECT_ROOT}/venv/bin/activate"

# Exporta variáveis de ambiente
export DB_SQL_URL="sqlite:///${PROJECT_ROOT}/local_deploy/data/db_transparencia.db"

# Inicia o Streamlit
cd "${PROJECT_ROOT}/mcp_client"
streamlit run chat_app.py --server.port 8504 --server.headless true
