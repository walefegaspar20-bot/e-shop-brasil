
import os
from urllib.parse import quote_plus
from pymongo import MongoClient
from bson.decimal128 import Decimal128
from datetime import datetime, timezone, timedelta
from decimal import Decimal
from dotenv import load_dotenv

# --------------------------------------------------
# 1. CONFIGURAÇÃO DA CONEXÃO
# --------------------------------------------------

load_dotenv()

MONGO_USERNAME = os.getenv("MONGO_INITDB_ROOT_USERNAME")
MONGO_PASSWORD = os.getenv("MONGO_INITDB_ROOT_PASSWORD")

if not MONGO_USERNAME or not MONGO_PASSWORD:
    raise ValueError(
        "Credenciais do MongoDB não encontradas no arquivo .env."
    )

usuario = quote_plus(MONGO_USERNAME)
senha = quote_plus(MONGO_PASSWORD)

URI = (
    f"mongodb://{usuario}:{senha}"
    "@localhost:27017/?authSource=admin"
)


def executar_carga():
    with MongoClient(URI) as client:
        db = client["eshop_brasil"]

        agora = datetime.now(timezone.utc)

        # --------------------------------------------------
        # 2. CLIENTES
        # --------------------------------------------------

        clientes = [
            {"nome": "Ana Silva", "email": "ana@email.com", "estado": "SP"},
            {"nome": "Bruno Costa", "email": "bruno@email.com", "estado": "RJ"},
            {"nome": "Carla Mendes", "email": "carla@email.com", "estado": "MG"},
            {"nome": "Daniel Souza", "email": "daniel@email.com", "estado": "BA"},
            {"nome": "Elisa Oliveira", "email": "elisa@email.com", "estado": "PR"},
        ]

        for cliente in clientes:
            db.clientes.update_one(
                {"email": cliente["email"]},
                {"$setOnInsert": {
                    **cliente,
                    "data_cadastro": agora,
                    "ativo": True,
                    "preferencias": ["ofertas", "novidades"],
                    "endereco": {"estado": cliente["estado"]}
                }},
                upsert=True
            )

        # --------------------------------------------------
        # 3. PRODUTOS
        # --------------------------------------------------

        produtos = [
            ("P001", "Notebook Lenovo", "Eletrônicos", "3500.00"),
            ("P002", "Smartphone Samsung", "Eletrônicos", "2200.00"),
            ("P003", "Mouse Logitech", "Acessórios", "120.00"),
            ("P004", "Teclado Mecânico", "Acessórios", "280.00"),
            ("P005", "Monitor LG 27", "Eletrônicos", "1100.00"),
            ("P006", "Headset Gamer", "Acessórios", "350.00"),
            ("P007", "Smart TV 50", "Eletrônicos", "2600.00"),
            ("P008", "Cadeira Gamer", "Móveis", "950.00"),
            ("P009", "Impressora HP", "Informática", "780.00"),
            ("P010", "Webcam Full HD", "Acessórios", "190.00"),
        ]

        for sku, nome, categoria, preco in produtos:
            db.produtos.update_one(
                {"sku": sku},
                {"$setOnInsert": {
                    "sku": sku,
                    "nome": nome,
                    "categoria": categoria,
                    "preco": Decimal128(Decimal(preco)),
                    "marca": "Marca fictícia",
                    "ativo": True
                }},
                upsert=True
            )

        # Recuperar IDs dos clientes e produtos
        clientes_db = {
            c["email"]: c["_id"]
            for c in db.clientes.find()
        }

        produtos_db = {
            p["sku"]: p["_id"]
            for p in db.produtos.find()
        }

        # --------------------------------------------------
        # 4. PEDIDOS
        # --------------------------------------------------

        pedidos = [
            ("PED001", "ana@email.com", "P001", 1, "Aprovado"),
            ("PED002", "bruno@email.com", "P002", 1, "Enviado"),
            ("PED003", "carla@email.com", "P003", 2, "Entregue"),
            ("PED004", "daniel@email.com", "P004", 1, "Aprovado"),
            ("PED005", "elisa@email.com", "P005", 1, "Enviado"),
            ("PED006", "ana@email.com", "P006", 2, "Entregue"),
            ("PED007", "bruno@email.com", "P007", 1, "Aprovado"),
            ("PED008", "carla@email.com", "P008", 1, "Enviado"),
            ("PED009", "daniel@email.com", "P009", 1, "Entregue"),
            ("PED010", "elisa@email.com", "P010", 2, "Aprovado"),
        ]

        for numero, email, sku, quantidade, status in pedidos:
            produto = db.produtos.find_one({"sku": sku})
            preco = produto["preco"].to_decimal()

            item = {
                "produto_id": produtos_db[sku],
                "nome": produto["nome"],
                "quantidade": quantidade,
                "preco_unitario": produto["preco"],
                "valor_total": Decimal128(preco * quantidade)
            }

            db.pedidos.update_one(
                {"numero_pedido": numero},
                {"$setOnInsert": {
                    "numero_pedido": numero,
                    "cliente_id": clientes_db[email],
                    "data_pedido": agora - timedelta(
                        days=int(numero[-3:])
                    ),
                    "itens": [item],
                    "valor_total": item["valor_total"],
                    "status": status,
                    "forma_pagamento": "Cartão de crédito"
                }},
                upsert=True
            )

        # --------------------------------------------------
        # 5. ESTOQUES
        # --------------------------------------------------

        localidades = [
            "São Paulo",
            "Rio de Janeiro",
            "Belo Horizonte",
            "Salvador",
            "Curitiba"
        ]

        for i, (sku, nome, categoria, preco) in enumerate(produtos):
            db.estoques.update_one(
                {
                    "produto_id": produtos_db[sku],
                    "localidade": localidades[i % len(localidades)]
                },
                {"$setOnInsert": {
                    "produto_id": produtos_db[sku],
                    "localidade": localidades[i % len(localidades)],
                    "estado": ["SP", "RJ", "MG", "BA", "PR"][i % 5],
                    "quantidade": 20 + i * 5,
                    "ultima_atualizacao": agora
                }},
                upsert=True
            )

        # --------------------------------------------------
        # 6. EVENTOS DE NAVEGAÇÃO
        # --------------------------------------------------

        eventos = [
            ("EV001", "ana@email.com", "P001", "visualizacao"),
            ("EV002", "ana@email.com", "P003", "adicao_carrinho"),
            ("EV003", "ana@email.com", "P006", "visualizacao"),
            ("EV004", "bruno@email.com", "P002", "visualizacao"),
            ("EV005", "bruno@email.com", "P007", "adicao_carrinho"),
            ("EV006", "bruno@email.com", "P004", "visualizacao"),
            ("EV007", "carla@email.com", "P003", "compra"),
            ("EV008", "carla@email.com", "P008", "visualizacao"),
            ("EV009", "carla@email.com", "P005", "visualizacao"),
            ("EV010", "daniel@email.com", "P004", "compra"),
            ("EV011", "daniel@email.com", "P009", "visualizacao"),
            ("EV012", "daniel@email.com", "P001", "visualizacao"),
            ("EV013", "elisa@email.com", "P005", "compra"),
            ("EV014", "elisa@email.com", "P010", "adicao_carrinho"),
            ("EV015", "elisa@email.com", "P007", "visualizacao"),
        ]

        for ref, email, sku, tipo in eventos:
            db.eventos_navegacao.update_one(
                {"evento_ref": ref},
                {"$setOnInsert": {
                    "evento_ref": ref,
                    "cliente_id": clientes_db[email],
                    "produto_id": produtos_db[sku],
                    "tipo_evento": tipo,
                    "categoria": db.produtos.find_one(
                        {"sku": sku}
                    )["categoria"],
                    "data_evento": agora,
                    "origem": "Aplicativo"
                }},
                upsert=True
            )

        # --------------------------------------------------
        # 7. ENTREGAS
        # --------------------------------------------------

        for numero, email, sku, quantidade, status in pedidos:
            pedido = db.pedidos.find_one(
                {"numero_pedido": numero}
            )

            if status == "Entregue":
                data_envio = agora - timedelta(days=5)
                previsao = agora - timedelta(days=2)
                data_entrega = agora - timedelta(days=2)

            elif status == "Enviado":
                data_envio = agora - timedelta(days=1)
                previsao = agora + timedelta(days=4)
                data_entrega = None

            else:
                data_envio = None
                previsao = None
                data_entrega = None

            db.entregas.update_one(
                {"pedido_id": pedido["_id"]},
                {"$set": {
                    "pedido_id": pedido["_id"],
                    "transportadora": "Transportadora Express",
                    "codigo_rastreio": (
                        f"BR{numero}2026"
                        if status != "Aprovado" else None
                    ),
                    "status": status,
                    "data_envio": data_envio,
                    "previsao_entrega": previsao,
                    "data_entrega": data_entrega
                }},
                upsert=True
            )

        # --------------------------------------------------
        # 8. RESULTADO
        # --------------------------------------------------

        print("\nCarga de dados concluída!")

        for nome in [
            "clientes",
            "produtos",
            "pedidos",
            "estoques",
            "eventos_navegacao",
            "entregas"
        ]:
            print(
                f"{nome}: {db[nome].count_documents({})} documentos"
            )


if __name__ == "__main__":
    executar_carga()