# 🧠 SERVER-MCP-AGILITY

## 📖 Descrição

Este projeto implementa um servidor MCP (Modular Command Processor) com integração OpenAI, autenticação PKCE via Keycloak, consultas automáticas ao PostgreSQL e consumo de APIs Swagger protegidas. O orquestrador principal está em `host.py`.

## 🏗️ Estrutura do Projeto

```
SERVER-MCP-AGILITY/
├── host.py         # Orquestrador MCP principal
├── client.py       # Cliente OpenAI
├── requirements.in # Dependências
├── README.md       # Documentação
└── __pycache__/    # Cache Python
```

## 🚀 Tecnologias Utilizadas

- Python 3.11+
- FastMCP
- OpenAI API
- PostgreSQL (psycopg2)
- Flask
- python-dotenv
- requests

## ⚙️ Instalação

```bash
git clone https://github.com/seuusuario/SERVER-MCP-AGILITY.git
cd SERVER-MCP-AGILITY
python -m venv .venv
.venv\Scripts\activate  # Windows
pip install -r requirements.in
```

## 🔑 Configuração

Crie um arquivo `.env` com as variáveis:

```
OPENAI_API_KEY=your_openai_key
POSTGRES_PASSWORD=your_postgres_password
KEYCLOAK_CLIENT_ID=front-manager
```

## 🛠️ Funcionalidades do host.py

- **Autenticação PKCE**: Login OAuth2 automatizado via Keycloak.
- **Consulta PostgreSQL**: Interpreta linguagem natural e converte para SQL seguro (apenas SELECT).
- **Swagger API**: Lista e consome endpoints protegidos via Bearer Token.
- **Integração OpenAI**: Geração automática de SQL usando GPT-4o.

### Exemplos de Uso

#### 1. Rodar o servidor MCP

```bash
python host.py
```

#### 2. Consultar SQL por linguagem natural

Via ferramenta MCP:

```
route_request("Quantos usuários ativos?")
```

#### 3. Listar endpoints Swagger

```
swagger_api("list")
```

#### 4. Chamar endpoint Swagger

```
swagger_api("call", path="v2/usuarios", method="GET")
```

## 📚 Referências

- [FastMCP](https://github.com/gustavoguanabara/fastmcp)
- [OpenAI API](https://platform.openai.com/docs/api-reference)
- [Keycloak PKCE](https://www.keycloak.org/docs/latest/securing_apps/#_pkce)
- [psycopg2](https://www.psycopg.org/)


## CRIAR O .ENV
OPENAI_API_KEY=sk-
POSTGRES_PASSWORD=your_postgres_password
KEYCLOAK_CLIENT_ID=front-manager
POSTGRES_DB=prod_phg_m18aK1
POSTGRES_USER=postgres
POSTGRES_HOST=10.20.1.64
POSTGRES_PORT=5432
OAUTH2_AUTH_URL = "https://auth-dev.centralit.com.br/realms/central-prd/protocol/openid-connect/auth"
OAUTH2_TOKEN_URL = "https://auth-dev.centralit.com.br/realms/central-prd/protocol/openid-connect/token"
REDIRECT_URI = "http://localhost:5005/callback"
SWAGGER_JSON_URL = "https://itsmx-dev.centralit.com.br/lowcode/v2/api-docs"
