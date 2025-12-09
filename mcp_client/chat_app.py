
import os
import sys
import asyncio
import streamlit as st
from langchain_community.llms import LlamaCpp
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

# Configuração da página
st.set_page_config(
    page_title="Chat MCP - Transparência Gov",
    page_icon="🤖",
    layout="wide"
)

# Caminho do projeto
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LLM_PATH = os.path.join(PROJECT_ROOT, "llm_models", "qwen2.5-1.5b-instruct-q4_k_m.gguf")

# Inicializa o estado da sessão
if "messages" not in st.session_state:
    st.session_state.messages = []

if "llm" not in st.session_state:
    st.session_state.llm = None

@st.cache_resource
def load_llm():
    """Carrega o modelo Qwen (cached)."""
    if not os.path.exists(LLM_PATH):
        st.error(f"❌ Modelo LLM não encontrado em: {LLM_PATH}")
        return None

    try:
        llm = LlamaCpp(
            model_path=LLM_PATH,
            temperature=0.1,
            max_tokens=512,
            n_ctx=5000,
            n_gpu_layers=0,
            n_batch=512,
            verbose=False
        )
        return llm
    except Exception as e:
        st.error(f"❌ Erro ao carregar LLM: {e}")
        return None

# Carrega dicionário de dados
DICT_PATH = os.path.join(PROJECT_ROOT, "data", "dicionario_dados.md")
data_dictionary = ""
try:
    if os.path.exists(DICT_PATH):
        with open(DICT_PATH, "r") as f:
            data_dictionary = f.read()
except Exception as e:
    pass

# Sidebar
with st.sidebar:
    st.header("⚙️ Configuração")
    st.info("Escolha o tipo de pergunta para ajudar o assistente.")
    
    mode = st.radio(
        "Modo de Consulta:",
        ["💰 Valores de Emendas (SQL)", "📚 Teoria e Leis (Busca)"],
        captions=["Consulta tabela de dados", "Busca em documentos"]
    )
    
    st.markdown("---")
    st.header("Status")
    if st.session_state.llm is None:
        with st.spinner("Carregando Qwen..."):
            st.session_state.llm = load_llm()
            if st.session_state.llm:
                st.success("Modelo carregado!")


async def run_sql_agent(user_message, llm, status_container):
    """Agente Especialista em SQL"""
    
    # SCHEMA EXPLÍCITO (atualizado com campos reais)
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
    # Prompt com Chain-of-Thought para evitar memorização de exemplos
    system_prompt = f"""Você é um gerador de SQL SQLite. Analise a pergunta e gere o SQL apropriado.

SCHEMA:
{db_schema}

PERGUNTA: "{user_message}"

PASSO 1 - Identifique o que perguntar:
- Parlamentares/Autores/Deputados → campo: nome_autor
- Estados/UF → campo: uf (contém "SÃO PAULO", não "SP")
- Municípios/Cidades → campo: municipio
- Regiões → campo: regiao
- Funções/Áreas → campo: nome_funcao

PASSO 2 - Identifique a operação:
- "quantos", "listar", "top" → COUNT(*)
- "soma", "total de valores" → SUM(valor_pago) ou SUM(valor_empenhado)
- "média" → AVG(valor_pago)
- Sem agregação → SELECT direto

PASSO 3 - Identifique filtros:
- "para saúde", "na área de educação" → WHERE nome_funcao LIKE '%palavra%'
- "na região sul" → WHERE regiao = 'Sul'
- "no estado X" → WHERE uf = 'NOME COMPLETO'

PASSO 4 - Monte o SQL:
SELECT [campos]
FROM emendas_parlamentares
WHERE [filtros se houver]
GROUP BY [campo se usar agregação]
ORDER BY [resultado] DESC
LIMIT [número mencionado ou 20]

AGORA GERE O SQL:
```sql"""
    
    status_container.status("🔍 Gerando Query SQL...", expanded=True)
    
    # 1. Gera SQL
    try:
        # Stop token forçado para evitar alucinações
        response_text = llm.invoke(system_prompt, stop=["User:", "```\n"])
        
        # Estratégia 1: Tenta pegar bloco Markdown fechado (Mais seguro)
        import re
        match = re.search(r"```sql\s*([\s\S]*?)\s*```", response_text, re.IGNORECASE)
        
        if match:
            sql_response = match.group(1).strip()
        else:
            # Estratégia 2: Fallback - Pega do primeiro SELECT até o primeiro ponto e vírgula
            match_fallback = re.search(r"(SELECT\s+[\s\S]+?;)", response_text, re.IGNORECASE)
            if match_fallback:
                sql_response = match_fallback.group(1).strip()
            else:
                 # Estratégia 3: Fallback final - tenta pegar linha única se não tiver ;
                 match_line = re.search(r"(SELECT\s+.*)", response_text, re.IGNORECASE)
                 if match_line:
                    sql_response = match_line.group(1).strip()
                 else:
                    sql_response = f"SELECT * FROM emendas_parlamentares WHERE uf LIKE '%{user_message[-2:].upper()}%' LIMIT 10"
        
        # Remove caracteres perigosos que sobram
        sql_response = sql_response.replace("```", "").split(';')[0].strip()
        
        status_container.info(f"Query Gerada: {sql_response}")
        
    except Exception as e:
        return f"Erro ao gerar SQL: {e}", None

    # 2. Executa
    status_container.status("🛠️ Executando no Banco...", expanded=True)
    server_script = os.path.join(PROJECT_ROOT, "mcp_server", "start_mcp_server.sh")
    server_params = StdioServerParameters(command=server_script, args=[], env=None)

    try:
        async with stdio_client(server_params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                result = await session.call_tool("query_emendas", {"query": sql_response})
                data_str = result.content[0].text

                status_container.info("✅ Query executada com sucesso")

                # 3. Verificar se tem erro
                if "Erro" in data_str:
                    return f"❌ Erro ao consultar dados:\n\n{data_str}\n\n**Query gerada:**\n```sql\n{sql_response}\n```", sql_response

                # 4. O MCP server já retorna markdown formatado! Vamos usar direto
                # Verifica se é uma tabela markdown (contém | e -)
                if "|" in data_str and "---" in data_str:
                    # É uma tabela! Retorna direto com formatação bonita
                    final_ans = f"📊 **Resultado da consulta:**\n\n{data_str}\n\n**Query SQL utilizada:**\n```sql\n{sql_response}\n```"
                    return final_ans, data_str

                # 5. Se não é tabela, pode ser mensagem de sucesso ou resultado simples
                # Vamos gerar uma explicação em linguagem natural
                explain_prompt = f"""Você é um assistente que explica resultados de queries SQL.

PERGUNTA ORIGINAL: {user_message}

RESULTADO DA QUERY:
{data_str[:1000]}

Gere uma resposta em linguagem natural clara e objetiva em 2-3 frases, explicando o resultado.
Não invente informações. Use os dados fornecidos.

Resposta:"""

                final_ans = llm.invoke(explain_prompt, stop=["User:", "Pergunta:", "PERGUNTA:", "\n\n\n"])
                final_ans += f"\n\n**Query SQL utilizada:**\n```sql\n{sql_response}\n```"

                return final_ans, data_str

    except Exception as e:
        return f"❌ Erro na execução da tool: {e}\n\n**Query gerada:**\n```sql\n{sql_response}\n```", None

async def run_theory_agent(user_message, llm, status_container):
    """Agente Especialista em Teoria"""
    
    status_container.status("📚 Pesquisando documentos...", expanded=True)
    
    # Chama direto a busca
    server_script = os.path.join(PROJECT_ROOT, "mcp_server", "start_mcp_server.sh")
    server_params = StdioServerParameters(command=server_script, args=[], env=None)
    
    try:
        async with stdio_client(server_params) as (read, write):
             async with ClientSession(read, write) as session:
                await session.initialize()
                # Usa a pergunta do usuario como termo de busca
                result = await session.call_tool("search_legislative_report", {"query": user_message})
                doc_content = result.content[0].text
                
                status_container.info("✅ Documentos encontrados")

                # Gera resposta sintética e concisa
                status_container.status("🤖 Gerando resumo com LLM...", expanded=True)

                # Limita contexto para evitar travamento
                context_limit = 2000
                limited_context = doc_content[:context_limit]

                explain_prompt = (
                    "Baseado nos trechos abaixo, responda de forma CONCISA (2-3 frases):\n\n"
                    f"CONTEXTO:\n{limited_context}\n\n"
                    f"PERGUNTA: {user_message}\n\n"
                    "RESPOSTA:"
                )

                try:
                    summary = llm.invoke(explain_prompt, max_tokens=200)
                    status_container.success("✅ Resumo gerado")
                except Exception as e:
                    status_container.error(f"❌ Erro ao gerar resumo: {e}")
                    import traceback
                    traceback.print_exc()
                    summary = "Não foi possível gerar resumo automático. Veja os trechos abaixo."

                # Monta resposta final: Resumo + Trechos de referência
                final_response = f"📚 **Resposta:**\n\n{summary}\n\n"
                final_response += "---\n\n📖 **Trechos de Referência (fontes):**\n\n"

                # Pega apenas os primeiros 5 trechos para exibir como referência
                doc_lines = doc_content.split("\n\n")
                references = []
                for i, trecho in enumerate(doc_lines[:5], 1):
                    if trecho.strip():
                        # Remove o label [Trecho X] se existir
                        clean_trecho = trecho.replace(f"[Trecho {i}]", "").strip()
                        # Limita tamanho
                        if len(clean_trecho) > 600:
                            clean_trecho = clean_trecho[:600] + "..."
                        references.append(f"**[{i}]** {clean_trecho}")

                final_response += "\n\n".join(references)

                return final_response, doc_content
    except Exception as e:
        return f"Erro na busca: {e}", None


# Chat Interface
st.title("🤖 Agente de Transparência")

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

if prompt := st.chat_input("Digite sua pergunta..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)
        
    with st.chat_message("assistant"):
        if st.session_state.llm:
            status = st.empty()
            
            # Decide qual agente chamar baseado no RadioButton
            if "SQL" in mode:
                # Hack async

                
                response, details = asyncio.run(run_sql_agent(prompt, st.session_state.llm, status))
            else:
                 response, details = asyncio.run(run_theory_agent(prompt, st.session_state.llm, status))
            
            st.markdown(response)
            st.session_state.messages.append({"role": "assistant", "content": response})
            status.empty()
        else:
            st.error("Carregando modelo...")
