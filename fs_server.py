# from mcp.server.fastmcp import FastMCP
# import os

# mcp = FastMCP("fs_server")

# @mcp.tool()
# def list_downloads() -> str:
#     """
#     Lista todos os arquivos dentro de C:/Users/gusta/Downloads em formato Markdown.
#     """
#     path = "C:/Users/gusta/Downloads"
#     if not os.path.exists(path):
#         return f"### ❌ Diretório '{path}' não encontrado."

#     files = os.listdir(path)
#     if not files:
#         return "### 📂 Downloads\n\n*(Nenhum arquivo encontrado)*"

#     markdown = "### 📂 Arquivos na pasta Downloads\n\n"
#     markdown += "\n".join([f"- {f}" for f in files])
#     return markdown

# @mcp.tool()
# def find_in_downloads(filename: str) -> str:
#     """
#     Procura recursivamente por um arquivo dentro de C:/Users/gusta/Downloads e retorna em Markdown.
#     """
#     path = "C:/Users/gusta/Downloads"
#     if not os.path.exists(path):
#         return f"### ❌ Diretório '{path}' não encontrado."

#     for root, dirs, files in os.walk(path):
#         for file in files:
#             if filename.lower() in file.lower():
#                 return f"### ✅ Arquivo encontrado\n\n`{os.path.join(root, file)}`"
#     return f"### ⚠️ Arquivo '{filename}' não encontrado em `{path}`."

# if __name__ == "__main__":
#     mcp.run()
from mcp.server.fastmcp import FastMCP
import os

mcp = FastMCP("fs_server")

DOWNLOAD_PATH = "C:/Users/gusta/Downloads"

@mcp.tool()
def list_downloads() -> str:
    """
    Lista todos os arquivos dentro de C:/Users/gusta/Downloads em formato Markdown.
    """
    if not os.path.exists(DOWNLOAD_PATH):
        return f"### ❌ Diretório '{DOWNLOAD_PATH}' não encontrado."

    files = os.listdir(DOWNLOAD_PATH)
    if not files:
        return "### 📂 Downloads\n\n*(Nenhum arquivo encontrado)*"

    markdown = "### 📂 Arquivos na pasta Downloads\n\n"
    markdown += "\n".join([f"- {f}" for f in files])
    return markdown

@mcp.tool()
def find_in_downloads(filename: str) -> str:
    """
    Procura recursivamente por um arquivo dentro de C:/Users/gusta/Downloads,
    mostra o conteúdo em Markdown e adiciona link de download.
    """
    if not os.path.exists(DOWNLOAD_PATH):
        return f"### ❌ Diretório '{DOWNLOAD_PATH}' não encontrado."

    for root, dirs, files in os.walk(DOWNLOAD_PATH):
        for file in files:
            if filename.lower() in file.lower():
                filepath = os.path.join(root, file)
                try:
                    # tenta abrir como texto
                    with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
                        content = f.read()
                except Exception:
                    content = "(Arquivo binário ou não pôde ser lido como texto)"

                # limita tamanho para não travar
                preview = content[:2000]

                md = f"### ✅ Arquivo encontrado: `{file}`\n\n"
                md += f"**Caminho:** `{filepath}`\n\n"
                md += "#### Conteúdo (prévia)\n\n"
                md += "```\n" + preview + "\n```\n\n"
                md += f"[⬇️ Download {file}](./Downloads/{file})"
                return md

    return f"### ⚠️ Arquivo '{filename}' não encontrado em `{DOWNLOAD_PATH}`."

if __name__ == "__main__":
    mcp.run()
