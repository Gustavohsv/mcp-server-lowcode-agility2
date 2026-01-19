from mcp.server.fastmcp import FastMCP
import psycopg2

mcp = FastMCP("db_server")

@mcp.tool()
def query_postgres(query: str) -> str:
    """
    Executa uma consulta SQL no banco Postgres configurado.
    """
    try:
        conn = psycopg2.connect(
            dbname="phg_dev_Mj180",
            user="postgres",
            password="vPTkT/agjwOYMp1grS3NSA",
            host="10.20.1.64",
            port="5432"
        )
        cur = conn.cursor()
        cur.execute(query)
        rows = cur.fetchall()
        cur.close()
        conn.close()
        return str(rows)
    except Exception as e:
        return f"Erro ao executar consulta: {str(e)}"

if __name__ == "__main__":
    mcp.run()

