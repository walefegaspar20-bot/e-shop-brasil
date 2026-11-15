
import os
from urllib.parse import quote_plus

from dotenv import load_dotenv
from pymongo import MongoClient, DESCENDING

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
    # Considerar somente pedidos enviados ou entregues
    {
        "$match": {
            "status": {"$in": ["Enviado", "Entregue"]}
        }
    },

    # Separar os itens de cada pedido
    {
        "$unwind": "$itens"
    },

    # Relacionar os itens com os produtos
    {
        "$lookup": {
            "from": "produtos",
            "localField": "itens.produto_id",
            "foreignField": "_id",
            "as": "produto"
        }
    },

    {
        "$unwind": "$produto"
    },

    # Agrupar por categoria e calcular os indicadores
    {
        "$group": {
            "_id": "$produto.categoria",
            "quantidade_vendida": {
                "$sum": "$itens.quantidade"
            },
            "faturamento": {
                "$sum": {
                    "$multiply": [
                        "$itens.preco_unitario",
                        "$itens.quantidade"
                    ]
                }
            }
        }
    },

    # Ordenar pelo maior faturamento
    {
        "$sort": {
            "faturamento": DESCENDING
        }
    }
]

try:
    resultados = list(db.pedidos.aggregate(pipeline))

    print("\nFATURAMENTO POR CATEGORIA")
    print("=" * 45)

    if not resultados:
        print("Nenhum pedido encontrado para análise.")

    for resultado in resultados:
        faturamento = resultado["faturamento"].to_decimal()

        print(f"\nCategoria: {resultado['_id']}")
        print(
            f"Quantidade vendida: "
            f"{resultado['quantidade_vendida']}"
        )
        print(f"Faturamento: R$ {faturamento:.2f}")

finally:
    client.close()