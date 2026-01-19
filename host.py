# from fastmcp import FastMCP
# import json

# # =====================================================
# # IMPORTS DOS MCPs ESPECIALIZADOS
# # =====================================================
# from fs_server import list_downloads, find_in_downloads
# from db_server import query_postgres   # precisa existir em db_server.py
# from client import client, send_message_to_client  # usa o client pronto com API key

# # =====================================================
# # MCP PRINCIPAL (ORQUESTRADOR)
# # =====================================================
# mcp = FastMCP("mcp-host")

# # =====================================================
# # TOOLS DIRETAS (EXPOSTAS NO INSPECTOR)
# # =====================================================
# @mcp.tool()
# def list_downloads_proxy() -> str:
#     """Lista arquivos do diretório em Markdown"""
#     return list_downloads()

# @mcp.tool()
# def find_in_downloads_proxy(filename: str) -> str:
#     """Busca um arquivo específico em Markdown"""
#     return find_in_downloads(filename)

# @mcp.tool()
# def query_postgres_proxy(query: str) -> str:
#     """Executa SELECT no Postgres e retorna Markdown"""
#     return query_postgres(query)

# @mcp.tool()
# def send_message_proxy(message: str) -> str:
#     """Envia mensagem ao client"""
#     return send_message_to_client(message)

# # =====================================================
# # ROUTER NLU (OPENAI → ORQUESTRAÇÃO MCP)
# # =====================================================
# @mcp.tool()
# def route_request(message: str) -> str:
#     """
#     Interpreta linguagem natural e decide qual MCP usar.
#     Retorna SEMPRE Markdown.
#     """

#     prompt = f"""
# Você é um roteador MCP.

# A partir da mensagem do usuário, escolha UMA ação
# e responda SOMENTE um JSON válido no formato:

# {{
#   "intent": "<nome_da_tool>",
#   "content": "<parametro>"
# }}

# Ferramentas disponíveis:

# 1. list_downloads_proxy
# 2. find_in_downloads_proxy
# 3. query_postgres_proxy
# 4. send_message_proxy

# ⚠️ IMPORTANTE:
# - Se a intenção for "query_postgres_proxy", o campo "content" deve conter
#   uma query SQL **válida para PostgreSQL** (NUNCA usar sintaxe MySQL).
# - Para listar tabelas, use:
#   SELECT table_name FROM information_schema.tables WHERE table_schema='public';

# Usuário: "{message}"
# """

#     try:
#         completion = client.chat.completions.create(
#             model="gpt-4o-mini",  # ou "gpt-4" se disponível
#             messages=[{"role": "user", "content": prompt}],
#             temperature=0
#         )

#         parsed = json.loads(completion.choices[0].message.content.strip())
#         intent = parsed.get("intent")
#         content = parsed.get("content", "")

#     except Exception as e:
#         return f"## Erro de NLU: {str(e)}"

#     # =================================================
#     # ORQUESTRAÇÃO MCP
#     # =================================================
#     if intent == "list_downloads_proxy":
#         return list_downloads()

#     if intent == "find_in_downloads_proxy":
#         return find_in_downloads(content)

#     if intent == "query_postgres_proxy":
#         return query_postgres(content)

#     if intent == "send_message_proxy":
#         return send_message_to_client(content)

#     return f"## Intenção não reconhecida: {intent}"

# # =====================================================
# # START (STDIO LIMPO — NÃO USAR PRINT)
# # =====================================================
# if __name__ == "__main__":
#     mcp.run()
# from fastmcp import FastMCP
# import json

# # =====================================================
# # IMPORTS DOS MCPs ESPECIALIZADOS
# # =====================================================
# from fs_server import list_downloads, find_in_downloads
# from db_server import query_postgres   # precisa existir em db_server.py
# from client import client, send_message_to_client  # usa o client pronto com API key

# # =====================================================
# # MCP PRINCIPAL (ORQUESTRADOR)
# # =====================================================
# mcp = FastMCP("mcp-host")

# # =====================================================
# # TOOLS DIRETAS (EXPOSTAS NO INSPECTOR)
# # =====================================================
# @mcp.tool()
# def list_downloads_proxy() -> str:
#     """Lista arquivos do diretório em Markdown"""
#     return list_downloads()

# @mcp.tool()
# def find_in_downloads_proxy(filename: str) -> str:
#     """Busca um arquivo específico em Markdown"""
#     return find_in_downloads(filename)

# @mcp.tool()
# def query_postgres_proxy(query: str) -> str:
#     """Executa SELECT no Postgres e retorna Markdown"""
#     return query_postgres(query)

# @mcp.tool()
# def send_message_proxy(message: str) -> str:
#     """Envia mensagem ao client"""
#     return send_message_to_client(message)

# # =====================================================
# # ROUTER NLU (OPENAI → ORQUESTRAÇÃO MCP)
# # =====================================================
# @mcp.tool()
# def route_request(message: str) -> str:
#     """
#     Interpreta linguagem natural e decide qual MCP usar.
#     Retorna SEMPRE Markdown.
#     """

#     prompt = f"""
# Você é um roteador MCP.

# A partir da mensagem do usuário, escolha UMA ação
# e responda SOMENTE um JSON válido no formato:

# {{
#   "intent": "<nome_da_tool>",
#   "content": "<parametro>"
# }}

# Ferramentas disponíveis:

# 1. list_downloads_proxy
# 2. find_in_downloads_proxy
# 3. query_postgres_proxy
# 4. send_message_proxy

# ⚠️ IMPORTANTE:
# - Se a intenção for "query_postgres_proxy", o campo "content" deve conter
#   uma query SQL **válida para PostgreSQL** (NUNCA usar sintaxe MySQL).
# - Para listar tabelas, use:
#   SELECT table_name FROM information_schema.tables WHERE table_schema='public';

# Usuário: "{message}"
# """

#     try:
#         completion = client.chat.completions.create(
#             model="gpt-4o-mini",  # ou "gpt-4" se disponível
#             messages=[{"role": "user", "content": prompt}],
#             temperature=0
#         )

#         parsed = json.loads(completion.choices[0].message.content.strip())
#         intent = parsed.get("intent")
#         content = parsed.get("content", "")

#     except Exception as e:
#         return f"## Erro de NLU: {str(e)}"

#     # =================================================
#     # ORQUESTRAÇÃO MCP
#     # =================================================
#     if intent == "list_downloads_proxy":
#         return list_downloads()

#     if intent == "find_in_downloads_proxy":
#         return find_in_downloads(content)

#     if intent == "query_postgres_proxy":
#         return query_postgres(content)

#     if intent == "send_message_proxy":
#         return send_message_to_client(content)

#     return f"## Intenção não reconhecida: {intent}"

# # =====================================================
# # START (STDIO LIMPO — NÃO USAR PRINT)
# # =====================================================
# if __name__ == "__main__":
#     mcp.run()
from fastmcp import FastMCP
import json

# =====================================================
# IMPORTS DOS MCPs ESPECIALIZADOS
# =====================================================
from fs_server import list_downloads, find_in_downloads
from db_server import query_postgres   # precisa existir em db_server.py e retornar Markdown
from client import client, send_message_to_client  # usa o client pronto com API key

# =====================================================
# MCP PRINCIPAL (ORQUESTRADOR)
# =====================================================
mcp = FastMCP("mcp-host")

# =====================================================
# TOOLS DIRETAS (EXPOSTAS NO INSPECTOR)
# =====================================================
@mcp.tool()
def list_downloads_proxy() -> str:
    """Lista arquivos do diretório em Markdown"""
    return list_downloads()

@mcp.tool()
def find_in_downloads_proxy(filename: str) -> str:
    """Busca um arquivo específico em Markdown"""
    return find_in_downloads(filename)

@mcp.tool()
def query_postgres_proxy(query: str) -> str:
    """Executa SELECT no Postgres e retorna Markdown"""
    return query_postgres(query)

@mcp.tool()
def send_message_proxy(message: str) -> str:
    """Envia mensagem ao client"""
    return send_message_to_client(message)

# =====================================================
# ROUTER NLU (OPENAI → ORQUESTRAÇÃO MCP)
# =====================================================
@mcp.tool()
def route_request(message: str) -> str:
    """
    Interpreta linguagem natural e decide qual MCP usar.
    Retorna SEMPRE Markdown.
    """

    prompt = f"""
Você é um roteador MCP.

A partir da mensagem do usuário, escolha UMA ação
e responda SOMENTE um JSON válido no formato:

{{
  "intent": "<nome_da_tool>",
  "content": "<parametro>"
}}

Ferramentas disponíveis:

1. list_downloads_proxy
2. find_in_downloads_proxy
3. query_postgres_proxy
4. send_message_proxy

⚠️ IMPORTANTE:
- Se a intenção for "query_postgres_proxy", o campo "content" deve conter
  uma query SQL **válida para PostgreSQL** (NUNCA usar sintaxe MySQL).
- Para listar tabelas, use:
  SELECT table_name FROM information_schema.tables WHERE table_schema='public';

Usuário: "{message}"
"""

    try:
        completion = client.chat.completions.create(
            model="gpt-4o-mini",  # ou "gpt-4" se disponível
            messages=[{"role": "user", "content": prompt}],
            temperature=0
        )

        parsed = json.loads(completion.choices[0].message.content.strip())
        intent = parsed.get("intent")
        content = parsed.get("content", "")

    except Exception as e:
        return f"## Erro de NLU: {str(e)}"

    # =================================================
    # ORQUESTRAÇÃO MCP
    # =================================================
    if intent == "list_downloads_proxy":
        return list_downloads()

    if intent == "find_in_downloads_proxy":
        return find_in_downloads(content)

    if intent == "query_postgres_proxy":
        return query_postgres(content)

    if intent == "send_message_proxy":
        return send_message_to_client(content)

    return f"## Intenção não reconhecida: {intent}"

# =====================================================
# START (STDIO LIMPO — NÃO USAR PRINT)
# =====================================================
if __name__ == "__main__":
    mcp.run()
