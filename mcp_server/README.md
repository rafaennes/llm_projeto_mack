# Servidor MCP - Transparência do Governo Federal

Servidor MCP (Model Context Protocol) real que expõe ferramentas para consultar dados sobre emendas parlamentares do governo federal brasileiro.

## 🎯 O que é este servidor?

Este é um **servidor MCP oficial** que pode ser conectado por:
- **Claude Desktop** (aplicativo oficial da Anthropic)
- **Qualquer cliente MCP** que siga o protocolo
- **Sua própria aplicação** usando o MCP SDK

## 🛠️ Ferramentas Disponíveis

### 1. **get_emendas_schema**
Retorna o schema da tabela de emendas parlamentares (colunas e tipos).

### 2. **query_emendas**
Executa queries SQL customizadas na base de dados de emendas.
- Apenas queries SELECT (por segurança)
- Limite automático de 100 resultados

### 3. **get_emendas_stats**
Estatísticas gerais sobre as emendas:
- Total de emendas
- Número de autores
- Valores totais (empenhado, liquidado, pago)
- Top 5 regiões

### 4. **search_emendas_by_author**
Busca emendas por nome do parlamentar.

### 5. **get_emendas_by_municipality**
Lista emendas de um município específico.

## 🚀 Como usar

### Opção 1: Com Claude Desktop

1. **Copie a configuração**:
```bash
cp mcp_server/claude_desktop_config.json ~/.config/Claude/claude_desktop_config.json
```

2. **Ajuste o caminho** no arquivo (se necessário):
   - Edite `~/.config/Claude/claude_desktop_config.json`
   - Verifique se o caminho do script está correto

3. **Reinicie o Claude Desktop**

4. **Verifique a conexão**:
   - Abra o Claude Desktop
   - Procure pelo ícone 🔌 ou ferramentas do MCP
   - Você deverá ver "transparencia-gov" listado

5. **Use as ferramentas**:
```
Me mostre o schema da tabela de emendas

Quais são os parlamentares que mais receberam emendas?

Busque emendas para o município de São Paulo
```

### Opção 2: Testar o servidor diretamente

```bash
# Teste via linha de comando
cd /home/ennes/mestrado/llm_projeto
./mcp_server/start_mcp_server.sh
```

O servidor ficará aguardando comandos via stdin/stdout (protocolo MCP stdio).

### Opção 3: Integrar em sua aplicação Python

```python
import asyncio
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

async def main():
    server_params = StdioServerParameters(
        command="/home/ennes/mestrado/llm_projeto/mcp_server/start_mcp_server.sh",
        args=[],
        env={}
    )

    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()

            # Lista ferramentas disponíveis
            tools = await session.list_tools()
            print("Ferramentas disponíveis:")
            for tool in tools.tools:
                print(f"  - {tool.name}: {tool.description[:100]}...")

            # Chama uma ferramenta
            result = await session.call_tool("get_emendas_stats", {})
            print("\nEstatísticas:")
            print(result.content[0].text)

asyncio.run(main())
```

## 📊 Dados

O servidor usa o banco SQLite criado em:
```
/home/ennes/mestrado/llm_projeto/local_deploy/data/db_transparencia.db
```

**87,912 registros** de emendas parlamentares brasileiras.

## 🔧 Desenvolvimento

### Adicionar novas ferramentas

Edite `mcp_server/server.py`:

1. Adicione a ferramenta em `@app.list_tools()`:
```python
Tool(
    name="minha_ferramenta",
    description="O que ela faz",
    inputSchema={
        "type": "object",
        "properties": {
            "param1": {"type": "string", "description": "..."}
        },
        "required": ["param1"]
    }
)
```

2. Implemente em `@app.call_tool()`:
```python
elif name == "minha_ferramenta":
    param1 = arguments.get("param1")
    # Lógica da ferramenta
    result = fazer_algo(param1)
    return [TextContent(type="text", text=result)]
```

### Adicionar RAG/MongoDB

Para adicionar suporte a busca semântica em documentos:

1. Instale dependências:
```bash
source venv/bin/activate
pip install pymongo sentence-transformers
```

2. Adicione ferramentas no `server.py` para:
   - Buscar documentos por similaridade
   - Adicionar novos documentos
   - Listar documentos disponíveis

## 🧪 Testando

### Teste manual via stdio

```bash
# Terminal 1: Inicie o servidor
./mcp_server/start_mcp_server.sh

# O servidor aguarda entrada JSON via stdin
# Envie comandos MCP no formato JSON
```

### Teste com script Python

Veja `mcp_server/test_client.py` para exemplos de como conectar ao servidor.

## 📝 Arquivos

```
mcp_server/
├── server.py                      # Servidor MCP principal
├── start_mcp_server.sh            # Script de inicialização
├── claude_desktop_config.json      # Configuração para Claude Desktop
├── README.md                       # Esta documentação
└── test_client.py                 # Cliente de teste (opcional)
```

## 🔒 Segurança

- ✅ Apenas queries SELECT são permitidas
- ✅ Limite de 100 resultados por query
- ✅ Validação de inputs
- ⚠️ Para produção, adicione autenticação e rate limiting

## 🐛 Troubleshooting

### Servidor não inicia
```bash
# Verifique se o banco existe
ls -lh local_deploy/data/db_transparencia.db

# Teste o Python diretamente
source venv/bin/activate
python mcp_server/server.py
```

### Claude Desktop não encontra o servidor
1. Verifique o caminho em `~/.config/Claude/claude_desktop_config.json`
2. Certifique-se de que o script é executável: `chmod +x mcp_server/start_mcp_server.sh`
3. Reinicie completamente o Claude Desktop

### Ferramentas não aparecem
1. Verifique os logs do Claude Desktop
2. Teste o servidor manualmente primeiro
3. Verifique se o virtualenv está ativado no script

## 📚 Referências

- [MCP Documentation](https://modelcontextprotocol.io/)
- [MCP Python SDK](https://github.com/modelcontextprotocol/python-sdk)
- [Claude Desktop Setup](https://docs.anthropic.com/claude/docs/model-context-protocol)

## 🎉 Próximos Passos

1. ✅ Servidor MCP funcionando com SQL
2. 🔄 Adicionar ferramentas RAG (MongoDB)
3. 🔄 Adicionar APIs em tempo real
4. 🔄 Criar cliente Streamlit que usa MCP
5. 🔄 Deploy em produção com autenticação
