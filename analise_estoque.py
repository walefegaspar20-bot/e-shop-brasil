
import os
from urllib.parse import quote_plus

from dotenv import load_dotenv
from pymongo import MongoClient, ASCENDING

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
db = client["eshop_brasil"]

pipeline = [
    {
        "$match": {
            "quantidade": {"$lte": 30}
        }
    },
    {
        "$lookup": {
            "from": "produtos",
            "localField": "produto_id",
            "foreignField": "_id",
            "as": "produto"
        }
    },
    {
        "$unwind": "$produto"
    },
    {
        "$project": {
            "_id": 0,
            "sku": "$produto.sku",
            "produto": "$produto.nome",
            "categoria": "$produto.categoria",
            "localidade": 1,
            "estado": 1,
            "quantidade": 1
        }
    },
    {
        "$sort": {
            "quantidade": ASCENDING
        }
    }
]

try:
    resultados = list(db.estoques.aggregate(pipeline))

    print("\nPRODUTOS COM BAIXO ESTOQUE")
    print("=" * 45)

    if not resultados:
        print("Nenhum produto com baixo estoque encontrado.")

    for item in resultados:
        print(f"\nProduto: {item['produto']}")
        print(f"SKU: {item['sku']}")
        print(f"Categoria: {item['categoria']}")
        print(f"Localidade: {item['localidade']} - {item['estado']}")
        print(f"Quantidade disponível: {item['quantidade']}")

finally:
    client.close()