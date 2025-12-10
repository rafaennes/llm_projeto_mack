
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


def parse_simple_query(user_message):
    """
    Parser baseado em regras para queries simples.
    Retorna SQL se conseguir interpretar, None caso contrário.
    """
    msg_lower = user_message.lower()

    # Detecta entidade (GROUP BY)
    group_by = None
    if any(word in msg_lower for word in ["parlamentar", "autor", "deputado", "senador"]):
        group_by = "nome_autor"
    elif any(word in msg_lower for word in ["uf", "estado", "unidade federativa"]):
        group_by = "uf"
    elif any(word in msg_lower for word in ["município", "municipio", "cidade"]):
        group_by = "municipio"
    elif any(word in msg_lower for word in ["região", "regiao"]):
        group_by = "regiao"
    elif any(word in msg_lower for word in ["função", "funcao", "área", "area"]):
        group_by = "nome_funcao"
    else:
        return None  # Não conseguiu detectar entidade

    # Detecta agregações (SELECT)
    select_fields = [group_by]
    order_by = None

    has_count = any(word in msg_lower for word in ["quantas", "quantidade", "número", "numero", "count"])
    has_sum = any(word in msg_lower for word in ["quanto", "soma", "total", "valor"])

    if has_count:
        select_fields.append("COUNT(*) as quantidade")
        if not has_sum:
            order_by = "quantidade"

    if has_sum:
        # Detecta qual valor (pago, empenhado, liquidado)
        if "empenhado" in msg_lower:
            select_fields.append("SUM(valor_empenhado) as total")
        elif "liquidado" in msg_lower:
            select_fields.append("SUM(valor_liquidado) as total")
        else:
            select_fields.append("SUM(valor_pago) as total")
        order_by = "total"

    # Se não tem agregação, não é query simples
    if len(select_fields) == 1:
        return None

    # Detecta filtros (WHERE)
    where_clauses = []

    # Filtro por função
    if "saúde" in msg_lower or "saude" in msg_lower:
        where_clauses.append("nome_funcao LIKE '%Saúde%'")
    elif "educação" in msg_lower or "educacao" in msg_lower:
        where_clauses.append("nome_funcao LIKE '%Educação%'")

    # Filtro por região
    if "sul" in msg_lower:
        where_clauses.append("regiao = 'Sul'")
    elif "sudeste" in msg_lower:
        where_clauses.append("regiao = 'Sudeste'")
    elif "nordeste" in msg_lower:
        where_clauses.append("regiao = 'Nordeste'")
    elif "norte" in msg_lower and "nordeste" not in msg_lower:
        where_clauses.append("regiao = 'Norte'")
    elif "centro-oeste" in msg_lower or "centro oeste" in msg_lower:
        where_clauses.append("regiao = 'Centro-Oeste'")

    # Detecta LIMIT
    import re
    limit_match = re.search(r'\b(\d+)\b', msg_lower)
    limit = limit_match.group(1) if limit_match else "50"

    # Monta SQL
    sql = f"SELECT {', '.join(select_fields)}\n"
    sql += f"FROM emendas_parlamentares"

    if where_clauses:
        sql += f"\nWHERE {' AND '.join(where_clauses)}"

    sql += f"\nGROUP BY {group_by}"

    if order_by:
        sql += f"\nORDER BY {order_by} DESC"

    sql += f"\nLIMIT {limit};"

    return sql

async def run_sql_agent(user_message, llm, status_container):
    """Agente Especialista em SQL com parser híbrido (regras + LLM)"""

    # TENTATIVA 1: Parser baseado em regras para queries simples
    status_container.status("🔍 Analisando pergunta...", expanded=True)
    simple_sql = parse_simple_query(user_message)

    if simple_sql:
        status_container.success("✅ Query interpretada por regras (rápido)")
        sql_response = simple_sql
    else:
        status_container.info("🤖 Query complexa - usando LLM")

        # SCHEMA PARA LLM
        db_schema = """emendas_parlamentares (nome_autor, uf, municipio, regiao, nome_funcao, valor_pago, valor_empenhado)"""

        # Prompt few-shot
        system_prompt = f"""Gere SQL SQLite para: "{user_message}"

Tabela: {db_schema}

Exemplos:
P: "top 20 parlamentares" → SELECT nome_autor, COUNT(*) as total FROM emendas_parlamentares GROUP BY nome_autor ORDER BY total DESC LIMIT 20;
P: "soma por estado" → SELECT uf, SUM(valor_pago) as total FROM emendas_parlamentares GROUP BY uf ORDER BY total DESC LIMIT 50;

SQL:
```sql"""

        status_container.status("🤖 Gerando SQL com LLM...", expanded=True)

        # Gera SQL com LLM
        try:
            response_text = llm.invoke(system_prompt, stop=["User:", "```\n"], max_tokens=150)

            # Estratégia 1: Tenta pegar bloco Markdown fechado
            import re
            match = re.search(r"```sql\s*([\s\S]*?)\s*```", response_text, re.IGNORECASE)

            if match:
                sql_response = match.group(1).strip()
            else:
                # Estratégia 2: Pega do primeiro SELECT até ;
                match_fallback = re.search(r"(SELECT\s+[\s\S]+?;)", response_text, re.IGNORECASE)
                if match_fallback:
                    sql_response = match_fallback.group(1).strip()
                else:
                    # Estratégia 3: Pega linha única
                    match_line = re.search(r"(SELECT\s+.*)", response_text, re.IGNORECASE)
                    if match_line:
                        sql_response = match_line.group(1).strip()
                    else:
                        return "❌ LLM não conseguiu gerar SQL válido. Tente reformular a pergunta.", None

            # Remove caracteres extras
            sql_response = sql_response.replace("```", "").split(';')[0].strip() + ";"

            status_container.info(f"✅ SQL gerado pelo LLM")

        except Exception as e:
            return f"❌ Erro ao gerar SQL com LLM: {e}", None

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
