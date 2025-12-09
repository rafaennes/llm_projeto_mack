#!/bin/bash

# Cores para output
GREEN='\033[0;32m'
NC='\033[0m' # No Color

echo -e "${GREEN}🔄 Iniciando setup do ambiente de desenvolvimento...${NC}"

# 1. Cria ambiente virtual se não existir
if [ ! -d "venv" ]; then
    echo "📦 Criando virtual environment (venv)..."
    python3 -m venv venv
else
    echo "✅ Virtual environment já existe"
fi

# 2. Ativa ambiente
source venv/bin/activate

# 3. Instala dependências
echo "📥 Instalando dependências..."
pip install --upgrade pip
pip install -r requirements.txt

# 4. Cria arquivo .env se não existir
if [ ! -f .env ]; then
    echo "⚙️  Criando arquivo .env padrão..."
    echo "DB_SQL_URL=sqlite:///local_deploy/data/db_transparencia.db" > .env
    echo "LLM_PATH=llm_models/qwen2.5-1.5b-instruct-q4_k_m.gguf" >> .env
fi

echo -e "${GREEN}✅ Setup concluído!${NC}"
echo "Para ativar o ambiente manualmente: source venv/bin/activate"
