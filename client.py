from openai import OpenAI
import os
from dotenv import load_dotenv

# Carrega variáveis do arquivo .env
load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# 🔑 Instancia o cliente OpenAI com sua chave (inicialização lazy)
_client = None

def get_client():
    """Retorna o cliente OpenAI, inicializando-o uma única vez quando necessário."""
    global _client
    if _client is None:
        if not OPENAI_API_KEY:
            raise ValueError(
                "OPENAI_API_KEY não está configurada. "
                "Configure a variável de ambiente OPENAI_API_KEY antes de usar o cliente."
            )
        _client = OpenAI(api_key=OPENAI_API_KEY)
    return _client

# Para compatibilidade com código existente
@property
def client():
    return get_client()

def send_message_to_client(message: str) -> str:
    """
    Simula envio de mensagem para o cliente.
    Aqui você pode integrar com outro sistema real se quiser.
    """
    return f"Mensagem enviada ao cliente: {message}"

