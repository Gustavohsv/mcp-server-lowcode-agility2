# 🧠 SERVER-MCP

## 📖 Descrição

Este projeto implementa um sistema de orquestração modular baseado em MCPs (Modular Command Processors), permitindo a execução de tarefas específicas como manipulação de arquivos locais, consultas em banco de dados PostgreSQL e comunicação com clientes via API da OpenAI. A arquitetura é orientada por linguagem natural, com roteamento inteligente de comandos através de um MCP principal.

## 🏗️ Estrutura do Projeto


SERVER-MCP/ ├── client.py              # Cliente OpenAI com chave de API ├── db_server.py           # MCP especializado em consultas PostgreSQL ├── fs_server.py           # MCP especializado em manipulação de arquivos locais ├── host.py                # MCP principal (orquestrador) ├── .env                   # Variáveis de ambiente ├── requirements.txt       # Dependências do projeto ├── README.md              # Documentação └── venv/                  # Ambiente virtual



## 🚀 Tecnologias Utilizadas

- Python 3.11+
- [FastMCP](https://github.com/gustavoguanabara/fastmcp) (orquestrador MCP)
- OpenAI API (via `openai` ou `OpenAI`)
- PostgreSQL (via `psycopg2`)
- Markdown para retorno estruturado

## ⚙️ Instalação

```bash
git clone https://github.com/seuusuario/SERVER-MCP.git
cd SERVER-MCP
python -m venv .venv
source .venv/bin/activate  # ou .venv\Scripts\activate no Windows
pip install -r requirements.txt

