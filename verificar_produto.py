
import os
from urllib.parse import quote_plus

from bson.decimal128 import Decimal128
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

# Codificar as credenciais para uso na URI
usuario = quote_plus(MONGO_USERNAME)
senha = quote_plus(MONGO_PASSWORD)

URI = (
    f"mongodb://{usuario}:{senha}"
    "@localhost:27017/?authSource=admin"
)

client = MongoClient(URI, serverSelectionTimeoutMS=5000)

try:
    client.admin.command("ping")

    db = client["eshop_brasil"]

    produto = db.produtos.find_one(
        {"sku": "P013"},
        {"_id": 0}
    )

    if produto is None:
        print("Produto não encontrado.")

    else:
        print("Produto encontrado!")
        print(f"SKU: {produto['sku']}")
        print(f"Nome: {produto['nome']}")
        print(f"Categoria: {produto['categoria']}")
        print(f"Marca: {produto['marca']}")
        print(f"Descrição: {produto['descricao']}")
        print(f"Preço: R$ {produto['preco'].to_decimal():.2f}")
        print(f"Ativo: {produto['ativo']}")

        print(
            "Preço armazenado como Decimal128:",
            isinstance(produto["preco"], Decimal128)
        )

finally:
    client.close()