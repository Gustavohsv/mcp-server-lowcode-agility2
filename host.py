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

OAUTH2_AUTH_URL = "https://auth-dev.centralit.com.br/realms/central-prd/protocol/openid-connect/auth"
OAUTH2_TOKEN_URL = "https://auth-dev.centralit.com.br/realms/central-prd/protocol/openid-connect/token"
REDIRECT_URI = "http://localhost:5005/callback"
SWAGGER_JSON_URL = "https://itsmx-dev.centralit.com.br/lowcode/v2/api-docs"


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
            dbname="prod_phg_m18aK1",
            user="postgres",
            password="vPTkT/agjwOYMp1grS3NSA",
            host="10.20.1.64",
            port="5432",
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
    Interpreta linguagem natural e gera SQL automaticamente.
    """

    prompt = f"""
Você é um especialista em PostgreSQL.

Converta a frase abaixo em um comando SQL válido.
Retorne APENAS o SQL puro.
Nunca use markdown.
Nunca use ```sql.
Nunca explique nada.

Frase:
{message}
"""

    completion = openai_client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "Você gera SQL puro para PostgreSQL."},
            {"role": "user", "content": prompt}
        ]
    )

    sql = completion.choices[0].message.content.strip()

    # 🔥 Remove markdown se vier
    sql = sql.replace("```sql", "").replace("```", "").strip()

    # 🔐 Segurança: permitir apenas SELECT
    if not sql.lower().startswith("select"):
        return f"Consulta bloqueada por segurança. SQL gerado: {sql}"

    return execute_query(sql)




# ======================================================
# TOOL 2 - SWAGGER API
# ======================================================

@mcp.tool()
def swagger_api(action: str, path: str = "", method: str = "GET"):
    """
    action:
        - "list" → lista endpoints do Swagger
        - "call" → chama endpoint específico

    path:
        obrigatório quando action="call"

    method:
        GET, POST, PUT, DELETE...
    """

    swagger = get_swagger_json()

    if "error" in swagger:
        return swagger

    # LISTAR ENDPOINTS
    if action == "list":
        endpoints = []

        for route, methods in swagger.get("paths", {}).items():
            for m in methods.keys():
                endpoints.append({
                    "path": route,
                    "method": m.upper()
                })

        return {"endpoints": endpoints}

    # CHAMAR ENDPOINT
    if action == "call":

        if not path:
            return {"error": "Path é obrigatório quando action='call'"}

        BASE_URL = "https://itsmx-dev.centralit.com.br/lowcode"

        token = get_bearer_token_pkce()
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }

        full_url = f"{BASE_URL}/{path.lstrip('/')}"

        response = requests.request(
            method.upper(),
            full_url,
            headers=headers
        )

        try:
            data = response.json()
        except Exception:
            data = response.text

        return {
            "status": response.status_code,
            "url": full_url,
            "data": data
        }

    return {"error": "Ação inválida. Use 'list' ou 'call'."}



# ======================================================
# START SERVER
# ======================================================

if __name__ == "__main__":
    mcp.run()





