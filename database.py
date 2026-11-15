
import os
from urllib.parse import quote_plus

from dotenv import load_dotenv
from pymongo import MongoClient, ASCENDING, DESCENDING

# Carregar as variáveis do arquivo .env
load_dotenv()

MONGO_USERNAME = os.getenv("MONGO_INITDB_ROOT_USERNAME")
MONGO_PASSWORD = os.getenv("MONGO_INITDB_ROOT_PASSWORD")

if not MONGO_USERNAME or not MONGO_PASSWORD:
    raise ValueError(
        "Credenciais do MongoDB não encontradas no arquivo .env."
    )

# Codificar as credenciais para uso na URI
usuario = quote_plus(MONGO_USERNAME)
senha = quote_plus(MONGO_PASSWORD)

URI = (
    f"mongodb://{usuario}:{senha}"
    "@localhost:27017/?authSource=admin"
)

client = MongoClient(URI)

try:
    db = client["eshop_brasil"]

    # Criar coleções
    colecoes = [
        "clientes",
        "produtos",
        "pedidos",
        "estoques",
        "eventos_navegacao",
        "entregas"
    ]

    for nome in colecoes:
        if nome not in db.list_collection_names():
            db.create_collection(nome)
            print(f"Coleção criada: {nome}")
        else:
            print(f"Coleção já existente: {nome}")

    # Criar índices
    db.pedidos.create_index([("cliente_id", ASCENDING)])
    db.pedidos.create_index([("data_pedido", DESCENDING)])

    db.estoques.create_index([("produto_id", ASCENDING)])

    db.eventos_navegacao.create_index([("cliente_id", ASCENDING)])
    db.eventos_navegacao.create_index([("data_evento", DESCENDING)])

    db.entregas.create_index([("pedido_id", ASCENDING)])

    print("\nEstrutura do banco criada com sucesso!")

finally:
    client.close()