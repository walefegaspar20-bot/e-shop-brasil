
import os
from urllib.parse import quote_plus

from dotenv import load_dotenv
from pymongo import MongoClient

# Carregar as variáveis do arquivo .env
load_dotenv()

MONGO_USERNAME = os.getenv("MONGO_INITDB_ROOT_USERNAME")
MONGO_PASSWORD = os.getenv("MONGO_INITDB_ROOT_PASSWORD")

if not MONGO_USERNAME or not MONGO_PASSWORD:
    raise ValueError(
        "Credenciais do MongoDB não encontradas no arquivo .env."
    )

# Codificar as credenciais para uso seguro na URI
usuario = quote_plus(MONGO_USERNAME)
senha = quote_plus(MONGO_PASSWORD)

URI = (
    f"mongodb://{usuario}:{senha}"
    "@localhost:27017/?authSource=admin"
)

client = None

try:
    client = MongoClient(
        URI,
        serverSelectionTimeoutMS=5000
    )

    client.admin.command("ping")

    print("Conexão com MongoDB realizada com sucesso!")
    print("Bancos disponíveis:", client.list_database_names())

except Exception as erro:
    print("Erro ao conectar ao MongoDB:")
    print(erro)

finally:
    if client is not None:
        client.close()