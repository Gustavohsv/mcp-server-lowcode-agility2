from fastmcp import FastMCP
from openai import OpenAI
import psycopg2
import json
import os
import base64
import hashlib
import secrets
import threading
import webbrowser
import requests
import time
from flask import Flask, request as flask_request
from urllib.parse import urlencode
from dotenv import load_dotenv



# ======================================================
# LOAD ENV
# ======================================================

load_dotenv()

CLIENT_ID = os.getenv("KEYCLOAK_CLIENT_ID", "front-manager")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

OAUTH2_AUTH_URL = os.getenv("OAUTH2_AUTH_URL")
OAUTH2_TOKEN_URL = os.getenv("OAUTH2_TOKEN_URL")
REDIRECT_URI = os.getenv("REDIRECT_URI")
SWAGGER_JSON_URL = os.getenv("SWAGGER_JSON_URL")

# ======================================================
# INICIALIZAÇÕES
# ======================================================

mcp = FastMCP("mcp-host")
openai_client = OpenAI(api_key=OPENAI_API_KEY) 
TOKEN_DATA = {}


# ======================================================
# POSTGRES
# ======================================================

def execute_query(query: str) -> str:
    try:
        conn = psycopg2.connect(
            dbname=os.getenv("POSTGRES_DB"),
            user=os.getenv("POSTGRES_USER"),
            password=os.getenv("POSTGRES_PASSWORD"),
            host=os.getenv("POSTGRES_HOST"),
            port=os.getenv("POSTGRES_PORT", "5432"),
            options='-c client_encoding=UTF8'
        )

        cur = conn.cursor()
        cur.execute(query)

        if cur.description:
            rows = cur.fetchall()
            result = json.dumps(rows, ensure_ascii=False, default=str)
        else:
            conn.commit()
            result = "Comando executado com sucesso."

        cur.close()
        conn.close()

        return result

    except Exception as e:
        return f"Erro ao executar consulta: {str(e)}"


# ======================================================
# PKCE AUTH
# ======================================================

def _generate_pkce_pair():
    code_verifier = base64.urlsafe_b64encode(secrets.token_bytes(32)).rstrip(b'=').decode()
    code_challenge = base64.urlsafe_b64encode(
        hashlib.sha256(code_verifier.encode()).digest()
    ).rstrip(b'=').decode()
    return code_verifier, code_challenge


def get_bearer_token_pkce():
    global TOKEN_DATA

    if TOKEN_DATA.get("access_token") and time.time() < TOKEN_DATA.get("expires_at", 0):
        return TOKEN_DATA["access_token"]

    code_verifier, code_challenge = _generate_pkce_pair()
    state = secrets.token_urlsafe(16)

    params = {
        "client_id": CLIENT_ID,
        "redirect_uri": REDIRECT_URI,
        "response_type": "code",
        "scope": "openid offline_access",
        "state": state,
        "code_challenge": code_challenge,
        "code_challenge_method": "S256"
    }

    url = f"{OAUTH2_AUTH_URL}?{urlencode(params)}"

    app = Flask(__name__)
    auth_code_holder = {}

    @app.route("/callback")
    def callback():
        auth_code_holder["code"] = flask_request.args.get("code")
        return "Login realizado! Pode fechar."

    def run_flask():
        app.run(port=5005, debug=False, use_reloader=False)

    threading.Thread(target=run_flask, daemon=True).start()

    webbrowser.open(url)

    for _ in range(120):
        if "code" in auth_code_holder:
            break
        time.sleep(1)
    else:
        raise Exception("Timeout esperando código.")

    data = {
        "grant_type": "authorization_code",
        "client_id": CLIENT_ID,
        "code": auth_code_holder["code"],
        "redirect_uri": REDIRECT_URI,
        "code_verifier": code_verifier
    }

    resp = requests.post(OAUTH2_TOKEN_URL, data=data)

    if resp.status_code != 200:
        raise Exception(resp.text)

    token_data = resp.json()

    TOKEN_DATA["access_token"] = token_data["access_token"]
    TOKEN_DATA["expires_at"] = time.time() + token_data["expires_in"]

    return TOKEN_DATA["access_token"]


# ======================================================
# SWAGGER
# ======================================================

def get_swagger_json():
    token = get_bearer_token_pkce()
    headers = {"Authorization": f"Bearer {token}"}

    resp = requests.get(SWAGGER_JSON_URL, headers=headers)

    if resp.status_code != 200:
        return {"error": f"Erro ao acessar Swagger: {resp.status_code}", "detail": resp.text}

    return resp.json()


# ======================================================
# TOOL 1 - POSTGRES
# ======================================================


@mcp.tool()
def route_request(message: str) -> str:
    """
    Gera SELECT apenas na view agility_etl.vw_dados_transformados
    """

    colunas_validas = [
        "workspace_id",
        "workspace",
        "board_id",
        "projeto",
        "inicio",
        "fim",
        "tarefa",
        "estimado",
        "utilizado",
        "responsável",
        "estado",
        "description",
        "planned_costs",
        "task_order",
        "task_inserted_on",
        "dt_conclusao",
        "dt_vencimento",
        "bug",
        "rework",
        "produto",
        "updated_on"
    ]

    prompt = f"""
Você é especialista em PostgreSQL.

A única fonte de dados permitida é:

agility_etl.vw_dados_transformados

Colunas disponíveis:
{", ".join(colunas_validas)}

Regras obrigatórias:
- Sempre usar SELECT
- Nunca usar JOIN
- Nunca usar subqueries
- Nunca usar outro schema ou tabela
- Nunca usar information_schema
- Nunca gerar INSERT, UPDATE, DELETE, DROP, ALTER ou TRUNCATE
- Sempre usar exatamente:
  FROM agility_etl.vw_dados_transformados
- A coluna principal do chamado é board_id
- Quando o usuário mencionar número de chamado, filtrar por board_id
- Nunca inventar colunas
- Usar apenas colunas da lista fornecida
- Se o usuário pedir "listar tudo", usar SELECT *

Retorne APENAS o SQL puro.

Frase do usuário:
{message}
"""

    completion = openai_client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "Você gera SQL seguro restrito a uma única view."},
            {"role": "user", "content": prompt}
        ],
        temperature=0
    )

    sql = completion.choices[0].message.content.strip()

    # 🔥 Limpeza
    sql = sql.replace("```sql", "").replace("```", "").strip()
    sql_lower = sql.lower()

    # 🔐 Validações de segurança

    if not sql_lower.startswith("select"):
        return "Consulta bloqueada: apenas SELECT é permitido."

    if "agility_etl.vw_dados_transformados" not in sql_lower:
        return "Consulta bloqueada: apenas a view permitida pode ser utilizada."

    if " join " in sql_lower:
        return "Consulta bloqueada: JOIN não é permitido."

    if any(keyword in sql_lower for keyword in [
        "insert", "update", "delete", "drop",
        "alter", "truncate", "information_schema", "pg_"
    ]):
        return "Consulta bloqueada: operação não permitida."

    # 🔎 Validação de colunas
    for palavra in sql_lower.replace(",", " ").split():
        if palavra in ["select", "from", "where", "and", "or", "=", "*", ">", "<", ">=", "<=", "like"]:
            continue
        if palavra in colunas_validas:
            continue
        if palavra.isnumeric():
            continue

    return execute_query(sql)


# ======================================================
# TOOL 2 - SWAGGER API
# ======================================================


# @mcp.tool()
# def swagger_api(message: str):
#     """
#     Interpreta linguagem natural, lista endpoints ou executa conforme Swagger.
#     Suporta:
#     - Query params (?name=valor)
#     - Path params (/users/{id})
#     - GET/PUT/POST/DELETE com body
#     - Validação de obrigatórios
#     """

#     import json
#     import requests

#     swagger = get_swagger_json()

#     if "error" in swagger:
#         return swagger

#     paths = swagger.get("paths", {})

#     # =====================================================
#     # 🔎 Monta resumo para o modelo
#     # =====================================================
#     resumo = []

#     for route, methods in paths.items():
#         for m, details in methods.items():
#             resumo.append({
#                 "path": route,
#                 "method": m.upper(),
#                 "summary": details.get("summary", ""),
#                 "parameters": details.get("parameters", []),
#                 "hasBody": "requestBody" in details
#             })

#     # =====================================================
#     # 1️⃣ Classificar intenção
#     # =====================================================
#     classification_prompt = f"""
# Classifique a intenção do usuário.

# Retorne APENAS:

# {{
#   "intent": "list" | "describe" | "execute"
# }}

# Mensagem:
# {message}
# """

#     classification = openai_client.chat.completions.create(
#         model="gpt-4o-mini",
#         temperature=0,
#         messages=[{"role": "user", "content": classification_prompt}]
#     )

#     intent_raw = classification.choices[0].message.content.strip()
#     intent_raw = intent_raw.replace("```json", "").replace("```", "").strip()

#     try:
#         intent = json.loads(intent_raw)["intent"]
#     except:
#         return {"error": "Erro ao classificar intenção", "raw": intent_raw}

#     # =====================================================
#     # 2️⃣ Listar endpoints
#     # =====================================================
#     if intent == "list":
#         return {"endpoints": resumo}

#     # =====================================================
#     # 3️⃣ Decidir endpoint + extrair parâmetros
#     # =====================================================
#     decision_prompt = f"""
# Escolha o endpoint correto e extraia os parâmetros do pedido.

# Retorne APENAS:

# {{
#   "path": "...",
#   "method": "...",
#   "query": {{}} ,
#   "path_params": {{}} ,
#   "body": {{}} ou null
# }}

# Endpoints disponíveis:
# {resumo}

# Pedido:
# {message}
# """

#     completion = openai_client.chat.completions.create(
#         model="gpt-4o-mini",
#         temperature=0,
#         messages=[{"role": "user", "content": decision_prompt}]
#     )

#     decision_raw = completion.choices[0].message.content.strip()
#     decision_raw = decision_raw.replace("```json", "").replace("```", "").strip()

#     try:
#         decision = json.loads(decision_raw)
#     except:
#         return {"error": "Erro ao interpretar decisão", "raw": decision_raw}

#     path = decision.get("path")
#     method = decision.get("method", "GET")
#     query = decision.get("query", {}) or {}
#     path_params = decision.get("path_params", {}) or {}
#     body = decision.get("body")

#     if not path:
#         return {"error": "Modelo não retornou path válido."}

#     endpoint_data = paths.get(path, {})
#     method_data = endpoint_data.get(method.lower(), {})

#     # =====================================================
#     # 4️⃣ Validar parâmetros obrigatórios (query/path)
#     # =====================================================
#     missing = []

#     for param in method_data.get("parameters", []):
#         name = param["name"]
#         location = param["in"]
#         required = param.get("required", False)

#         if required:
#             if location == "query" and name not in query:
#                 missing.append({"name": name, "in": "query"})

#             if location == "path" and name not in path_params:
#                 missing.append({"name": name, "in": "path"})

#     # =====================================================
#     # 5️⃣ Validar requestBody (inclusive GET ou PUT)
#     # =====================================================
#     request_body = method_data.get("requestBody")

#     if request_body:
#         body_required = request_body.get("required", False)

#         if body_required and not body:
#             missing.append({"name": "body", "in": "body"})

#         try:
#             schema = request_body["content"]["application/json"]["schema"]
#             required_fields = schema.get("required", [])

#             if body:
#                 for field in required_fields:
#                     if field not in body:
#                         missing.append({"name": field, "in": "body"})

#         except Exception:
#             pass

#     if missing:
#         return {
#             "error": "Parâmetros obrigatórios ausentes",
#             "missing": missing
#         }

#     # =====================================================
#     # 6️⃣ Substituir path params
#     # =====================================================
#     final_path = path

#     for key, value in path_params.items():
#         final_path = final_path.replace(f"{{{key}}}", str(value))

#     if "{" in final_path or "}" in final_path:
#         return {
#             "error": "Path parameter não substituído corretamente.",
#             "expected_path": path
#         }

#     # =====================================================
#     # 7️⃣ Executar requisição
#     # =====================================================
#     BASE_URL = "https://itsmx-dev.centralit.com.br/lowcode"

#     token = get_bearer_token_pkce()

#     headers = {
#         "Authorization": f"Bearer {token}",
#         "Content-Type": "application/json"
#     }

#     full_url = f"{BASE_URL}/{final_path.lstrip('/')}"

#     response = requests.request(
#         method.upper(),
#         full_url,
#         headers=headers,
#         params=query if query else None,   
#         json=body if body else None        
#     )

#     try:
#         data = response.json()
#     except Exception:
#         data = response.text

#     return {
#         "chosen_path": path,
#         "method": method,
#         "url": full_url,
#         "query_params": query,
#         "path_params": path_params,
#         "body": body,
#         "status": response.status_code,
#         "data": data
#     }
@mcp.tool()
def swagger_api(message: str):
    """
    Interpreta linguagem natural, lista endpoints ou executa conforme Swagger.
    Agora também retorna exemplos de body definidos no Swagger.
    """

    import json
    import requests

    swagger = get_swagger_json()

    if "error" in swagger:
        return swagger

    paths = swagger.get("paths", {})

    # =====================================================
    # 🔎 Função para extrair exemplo de body
    # =====================================================
    def extract_body_example(details):
        request_body = details.get("requestBody")
        if not request_body:
            return None

        try:
            content = request_body["content"]["application/json"]

            # Prioriza example direto
            if "example" in content:
                return content["example"]

            # Depois examples
            if "examples" in content:
                first_example = next(iter(content["examples"].values()))
                return first_example.get("value")

            # Se não tiver exemplo, monta baseado no schema
            schema = content.get("schema", {})
            properties = schema.get("properties", {})

            example_auto = {}
            for prop, prop_data in properties.items():
                example_auto[prop] = f"<{prop_data.get('type', 'value')}>"

            return example_auto if example_auto else None

        except Exception:
            return None

    # =====================================================
    # 🔎 Monta resumo completo para o modelo e listagem
    # =====================================================
    resumo = []

    for route, methods in paths.items():
        for m, details in methods.items():

            example_body = extract_body_example(details)

            resumo.append({
                "path": route,
                "method": m.upper(),
                "summary": details.get("summary", ""),
                "parameters": details.get("parameters", []),
                "hasBody": "requestBody" in details,
                "bodyExample": example_body
            })

    # =====================================================
    # 1️⃣ Classificar intenção
    # =====================================================
    classification_prompt = f"""
Classifique a intenção do usuário.

Retorne APENAS:

{{
  "intent": "list" | "describe" | "execute"
}}

Mensagem:
{message}
"""

    classification = openai_client.chat.completions.create(
        model="gpt-4o-mini",
        temperature=0,
        messages=[{"role": "user", "content": classification_prompt}]
    )

    intent_raw = classification.choices[0].message.content.strip()
    intent_raw = intent_raw.replace("```json", "").replace("```", "").strip()

    try:
        intent = json.loads(intent_raw)["intent"]
    except:
        return {"error": "Erro ao classificar intenção", "raw": intent_raw}

    # =====================================================
    # 2️⃣ LISTAR ENDPOINTS (COM EXEMPLOS)
    # =====================================================
    if intent == "list":
        return {
            "endpoints": resumo
        }

    # =====================================================
    # 3️⃣ Decidir endpoint
    # =====================================================
    decision_prompt = f"""
Escolha o endpoint correto e extraia os parâmetros.

Retorne APENAS:

{{
  "path": "...",
  "method": "...",
  "query": {{}} ,
  "path_params": {{}} ,
  "body": {{}} ou null
}}

Endpoints:
{resumo}

Pedido:
{message}
"""

    completion = openai_client.chat.completions.create(
        model="gpt-4o-mini",
        temperature=0,
        messages=[{"role": "user", "content": decision_prompt}]
    )

    decision_raw = completion.choices[0].message.content.strip()
    decision_raw = decision_raw.replace("```json", "").replace("```", "").strip()

    try:
        decision = json.loads(decision_raw)
    except:
        return {"error": "Erro ao interpretar decisão", "raw": decision_raw}

    path = decision.get("path")
    method = decision.get("method", "GET")
    query = decision.get("query", {}) or {}
    path_params = decision.get("path_params", {}) or {}
    body = decision.get("body")

    if not path:
        return {"error": "Modelo não retornou path válido."}

    endpoint_data = paths.get(path, {})
    method_data = endpoint_data.get(method.lower(), {})

    # =====================================================
    # Validar obrigatórios
    # =====================================================
    missing = []

    for param in method_data.get("parameters", []):
        name = param["name"]
        location = param["in"]
        required = param.get("required", False)

        if required:
            if location == "query" and name not in query:
                missing.append({"name": name, "in": "query"})
            if location == "path" and name not in path_params:
                missing.append({"name": name, "in": "path"})

    request_body = method_data.get("requestBody")

    if request_body:
        body_required = request_body.get("required", False)

        if body_required and not body:
            missing.append({"name": "body", "in": "body"})

    if missing:
        return {
            "error": "Parâmetros obrigatórios ausentes",
            "missing": missing,
            "bodyExample": extract_body_example(method_data)
        }

    # =====================================================
    # Substituir path params
    # =====================================================
    final_path = path

    for key, value in path_params.items():
        final_path = final_path.replace(f"{{{key}}}", str(value))

    # =====================================================
    # Executar
    # =====================================================
    BASE_URL = "https://itsmx-dev.centralit.com.br/lowcode"

    token = get_bearer_token_pkce()

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    full_url = f"{BASE_URL}/{final_path.lstrip('/')}"

    response = requests.request(
        method.upper(),
        full_url,
        headers=headers,
        params=query if query else None,
        json=body if body else None
    )

    try:
        data = response.json()
    except Exception:
        data = response.text

    return {
        "chosen_path": path,
        "method": method,
        "url": full_url,
        "query_params": query,
        "path_params": path_params,
        "body": body,
        "status": response.status_code,
        "data": data
    }

# ======================================================
# START SERVER
# ======================================================

if __name__ == "__main__":
    mcp.run()





