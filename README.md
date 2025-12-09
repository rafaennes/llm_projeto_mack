# LLM Projeto - Transparência Governamental (MCP Agent)

Uma aplicação de **Agente Inteligente** para transparência governamental. O sistema utiliza a arquitetura **MCP (Model Context Protocol)** onde um Agente (Streamlit + Qwen) orquestra o uso de ferramentas para responder perguntas tanto técnicas quanto teóricas sobre emendas parlamentares.

## 🏗️ Arquitetura

O projeto segue estritamente o protocolo MCP, separando a inteligência (Cliente/Agente) das ferramentas (Servidor).

```mermaid
graph TD
    User([👤 Usuário]) <--> Client[🖥️ MCP Client (Streamlit + Agente Qwen)]
    Client <-->|Stdio / Pipe| Server[⚙️ MCP Server (Python)]
    
    subgraph "Agente de Decisão"
        Client -- "Analisa Pergunta" --> Intent{Raciocínio}
        Intent -- "Dados?" --> ToolSql[🛠️ query_emendas]
        Intent -- "Teoria?" --> ToolDocs[🛠️ search_legislative_report]
    end

    subgraph "MCP Tools"
        ToolSql --> SQLite[(💾 Banco de Dados)]
        ToolDocs --> Markdown[(📄 Relatórios/Leis)]
    end
```

## ✨ Funcionalidades

### 🤖 Agente Qwen Integrado
O cliente de chat não é apenas uma interface, mas um **Agente Autônomo** rodando o modelo `Qwen-2.5-1.5B`. Ele:
1.  **Entende** a pergunta do usuário.
2.  **Decide** qual ferramenta usar:
    *   *Dados quantitativos* -> Gera SQL e consulta o banco.
    *   *Dúvidas teóricas* -> Pesquisa na base de conhecimento (Markdown).
3.  **Responde** de forma natural com base no retorno das ferramentas.

### 🛠️ Ferramentas MCP Disponíveis
O servidor expõe as seguintes capabilities:

| Ferramenta | Descrição | Exemplo de Uso |
|------------|-----------|----------------|
| `query_emendas` | Executa consultas SQL seguras na base de dados. | "Quanto foi pago para SP?" |
| `search_legislative_report` | Busca semântica/keyword em documentos teóricos. | "O que é uma emenda pix?" |
| `get_emendas_schema` | Retorna a estrutura da tabela. | "Quais campos existem?" |
| `get_emendas_stats` | Estatísticas gerais do banco. | "Resumo dos dados" |

## 🚀 Como Rodar (Deploy)

### Pré-requisitos
- Python 3.10+
- 4GB+ RAM (para rodar o modelo LLM local)

### 1. Setup Inicial
Prepare o ambiente e o banco de dados:

```bash
# 1. Instalar dependências
./local_deploy/setup_env.sh

# 2. Popular o banco SQLite (se ainda não fez)
source venv/bin/activate
python local_deploy/init_sqlite.py
```

### 2. Rodar a Aplicação
Basta iniciar o cliente. Ele cuidará de subir o servidor MCP automaticamente via Stdio.

```bash
./mcp_client/start_chat.sh
```

Acesse em: `http://localhost:8501`

![Interface do Agente](https://raw.githubusercontent.com/modelcontextprotocol/assets/main/demo.png) *(Imagem ilustrativa)*

## 📂 Estrutura de Pastas

*   `mcp_client/`: **Agente Inteligente**. Contém a lógica do Chat e integração com LLM.
    *   `chat_app.py`: Código principal do Agente.
*   `mcp_server/`: **Provedor de Ferramentas**. Não tem IA, apenas executa funções.
    *   `server.py`: Definição das ferramentas MCP.
*   `data/`:
    *   `db_transparencia.db`: Banco SQLite.
    *   `dicionario_dados.md`: Dicionário de dados para contexto do Agente.
    *   `teorico/`: Documentos para busca textual.

## 📚 Stack Tecnológica
- **Protocolo**: Model Context Protocol (MCP)
- **Frontend**: Streamlit
- **LLM**: Qwen-2.5-1.5B (GGUF via `llama-cpp-python`)
- **Database**: SQLite3
- **Search**: Busca textual simples em Markdown
# llm_projeto_mack
