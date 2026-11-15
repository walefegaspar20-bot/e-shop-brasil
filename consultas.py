
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
    {
        "$lookup": {
            "from": "clientes",
            "localField": "cliente_id",
            "foreignField": "_id",
            "as": "cliente"
        }
    },
    {
        "$lookup": {
            "from": "entregas",
            "localField": "_id",
            "foreignField": "pedido_id",
            "as": "entrega"
        }
    },
    {
        "$unwind": "$cliente"
    },
    {
        "$unwind": {
            "path": "$entrega",
            "preserveNullAndEmptyArrays": True
        }
    },
    {
        "$project": {
            "_id": 0,
            "numero_pedido": 1,
            "cliente": "$cliente.nome",
            "status_pedido": "$status",
            "status_entrega": "$entrega.status",
            "codigo_rastreio": "$entrega.codigo_rastreio",
            "previsao_entrega": "$entrega.previsao_entrega"
        }
    },
    {
        "$sort": {
            "numero_pedido": DESCENDING
        }
    }
]

try:
    resultados = list(db.pedidos.aggregate(pipeline))

    print("\nRELATÓRIO DE PEDIDOS E ENTREGAS")
    print("=" * 55)

    for pedido in resultados:
        print(f"\nPedido: {pedido['numero_pedido']}")
        print(f"Cliente: {pedido['cliente']}")
        print(f"Status do pedido: {pedido['status_pedido']}")
        print(
            f"Status da entrega: "
            f"{pedido.get('status_entrega', 'Não disponível')}"
        )
        print(
            f"Rastreamento: "
            f"{pedido.get('codigo_rastreio') or 'Não disponível'}"
        )

        previsao = pedido.get("previsao_entrega")

        if previsao:
            print(f"Previsão: {previsao.strftime('%d/%m/%Y')}")
        else:
            print("Previsão: Não definida")

finally:
    client.close()