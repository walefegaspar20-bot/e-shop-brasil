
import os
from collections import Counter
from datetime import datetime
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

client = None
avisos = []


def verificar_duplicados(documentos, campo, colecao):
    valores = [
        doc.get(campo)
        for doc in documentos
        if doc.get(campo) is not None
    ]

    contagem = Counter(valores)

    for valor, quantidade in contagem.items():
        if quantidade > 1:
            avisos.append(
                f"{colecao}: valor duplicado em {campo}: {valor}"
            )


try:
    client = MongoClient(URI, serverSelectionTimeoutMS=5000)

    client.admin.command("ping")
    db = client["eshop_brasil"]

    # Carregar as seis coleções
    clientes = list(db.clientes.find())
    produtos = list(db.produtos.find())
    pedidos = list(db.pedidos.find())
    estoques = list(db.estoques.find())
    eventos = list(db.eventos_navegacao.find())
    entregas = list(db.entregas.find())

    print("\n===== AUDITORIA DO BANCO E-SHOP BRASIL =====\n")

    # 1. Quantidade de documentos
    colecoes = {
        "clientes": clientes,
        "produtos": produtos,
        "pedidos": pedidos,
        "estoques": estoques,
        "eventos_navegacao": eventos,
        "entregas": entregas
    }

    print("1. Quantidade de documentos")

    for nome, documentos in colecoes.items():
        print(f"{nome}: {len(documentos)} documentos")

    # Identificadores para verificar relacionamentos
    ids_clientes = {doc["_id"] for doc in clientes}
    ids_produtos = {doc["_id"] for doc in produtos}
    ids_pedidos = {doc["_id"] for doc in pedidos}

    # 2. Verificar duplicidades
    print("\n2. Verificação de duplicidades")

    verificar_duplicados(clientes, "email", "clientes")
    verificar_duplicados(produtos, "sku", "produtos")
    verificar_duplicados(pedidos, "numero_pedido", "pedidos")

    # 3. Verificar preços dos produtos
    print("\n3. Verificação dos preços")

    for produto in produtos:
        preco = produto.get("preco")

        if not isinstance(preco, Decimal128):
            avisos.append(
                f"Produto {produto.get('sku')}: preço não é Decimal128"
            )

        elif preco.to_decimal() < 0:
            avisos.append(
                f"Produto {produto.get('sku')}: preço negativo"
            )

    # 4. Verificar relacionamentos dos pedidos
    print("\n4. Relacionamentos dos pedidos")

    for pedido in pedidos:
        numero = pedido.get("numero_pedido", "Sem número")

        if pedido.get("cliente_id") not in ids_clientes:
            avisos.append(
                f"Pedido {numero}: cliente não encontrado"
            )

        itens = pedido.get("itens", [])

        if not isinstance(itens, list) or not itens:
            avisos.append(
                f"Pedido {numero}: nenhum item cadastrado ou lista inválida"
            )
            continue

        for item in itens:
            if not isinstance(item, dict):
                avisos.append(
                    f"Pedido {numero}: item com estrutura inválida"
                )
                continue

            if item.get("produto_id") not in ids_produtos:
                avisos.append(
                    f"Pedido {numero}: produto não encontrado"
                )

            preco_item = item.get("preco_unitario")

            if not isinstance(preco_item, Decimal128):
                avisos.append(
                    f"Pedido {numero}: preço do item não é Decimal128"
                )

    # 5. Verificar estoque
    print("\n5. Relacionamentos do estoque")

    for estoque in estoques:
        if estoque.get("produto_id") not in ids_produtos:
            avisos.append(
                "Estoque: produto relacionado não encontrado"
            )

        quantidade = estoque.get("quantidade")

        if (
            type(quantidade) not in (int, float)
            or quantidade < 0
        ):
            avisos.append(
                f"Estoque {estoque.get('localidade')}: quantidade inválida"
            )

    # 6. Verificar eventos de navegação
    print("\n6. Relacionamentos dos eventos")

    for evento in eventos:
        if evento.get("cliente_id") not in ids_clientes:
            avisos.append(
                "Evento de navegação: cliente não encontrado"
            )

        produto_id = evento.get("produto_id")

        if produto_id is not None and produto_id not in ids_produtos:
            avisos.append(
                "Evento de navegação: produto não encontrado"
            )

    # 7. Verificar entregas e relacionamentos
    print("\n7. Relacionamentos das entregas")

    verificar_duplicados(entregas, "pedido_id", "entregas")

    pedidos_com_entrega = set()

    for entrega in entregas:
        pedido_id = entrega.get("pedido_id")

        if pedido_id not in ids_pedidos:
            avisos.append(
                "Entrega: pedido relacionado não encontrado"
            )
        else:
            pedidos_com_entrega.add(pedido_id)

            pedido_relacionado = next(
                pedido for pedido in pedidos
                if pedido["_id"] == pedido_id
            )

            if entrega.get("status") != pedido_relacionado.get("status"):
                avisos.append(
                    f"Entrega do pedido "
                    f"{pedido_relacionado.get('numero_pedido')}: "
                    "status diferente do pedido"
                )

    for pedido in pedidos:
        if pedido["_id"] not in pedidos_com_entrega:
            avisos.append(
                f"Pedido {pedido.get('numero_pedido')}: "
                "entrega não encontrada"
            )

    # 8. Conferir cálculos e valores dos pedidos
    print("\n8. Consistência dos valores dos pedidos")

    status_validos = {"Aprovado", "Enviado", "Entregue"}

    for pedido in pedidos:
        numero = pedido.get("numero_pedido", "Sem número")
        soma_itens = Decimal128("0").to_decimal()
        calculo_completo = True

        if pedido.get("status") not in status_validos:
            avisos.append(
                f"Pedido {numero}: status inválido"
            )

        for item in pedido.get("itens", []):
            if not isinstance(item, dict):
                calculo_completo = False
                continue

            quantidade = item.get("quantidade")
            preco_unitario = item.get("preco_unitario")
            valor_item = item.get("valor_total")

            if type(quantidade) is not int or quantidade <= 0:
                avisos.append(
                    f"Pedido {numero}: quantidade inválida em um item"
                )
                calculo_completo = False
                continue

            if not isinstance(preco_unitario, Decimal128):
                calculo_completo = False
                continue

            preco_decimal = preco_unitario.to_decimal()

            if preco_decimal < 0:
                avisos.append(
                    f"Pedido {numero}: preço unitário negativo"
                )
                calculo_completo = False
                continue

            valor_calculado = preco_decimal * quantidade
            soma_itens += valor_calculado

            if not isinstance(valor_item, Decimal128):
                avisos.append(
                    f"Pedido {numero}: valor total do item "
                    "não é Decimal128"
                )

            elif valor_item.to_decimal() != valor_calculado:
                avisos.append(
                    f"Pedido {numero}: total de um item está incorreto"
                )

        total_pedido = pedido.get("valor_total")

        if not isinstance(total_pedido, Decimal128):
            avisos.append(
                f"Pedido {numero}: total do pedido não é Decimal128"
            )

        elif (
            calculo_completo
            and total_pedido.to_decimal() != soma_itens
        ):
            avisos.append(
                f"Pedido {numero}: total diferente da soma dos itens"
            )

    # 9. Verificar duplicidade e consistência do estoque
    print("\n9. Consistência dos registros de estoque")

    chaves_estoque = []

    for estoque in estoques:
        produto_id = estoque.get("produto_id")
        localidade = estoque.get("localidade")
        estado = estoque.get("estado")
        quantidade = estoque.get("quantidade")

        if not localidade or not estado:
            avisos.append(
                "Estoque: localidade ou estado não informado"
            )

        if (
            type(quantidade) is not int
            or quantidade < 0
        ):
            avisos.append(
                f"Estoque {localidade}: quantidade inválida"
            )

        if produto_id is not None and localidade and estado:
            chaves_estoque.append(
                (
                    produto_id,
                    localidade.strip().casefold(),
                    estado.strip().casefold()
                )
            )

    contagem_estoque = Counter(chaves_estoque)

    for chave, quantidade in contagem_estoque.items():
        if quantidade > 1:
            avisos.append(
                f"Estoque duplicado para produto e localidade: {chave}"
            )

    # 10. Conferir regras de negócio das entregas
    print("\n10. Consistência das entregas")

    for entrega in entregas:
        status = entrega.get("status")
        rastreamento = entrega.get("codigo_rastreio")
        data_envio = entrega.get("data_envio")
        previsao = entrega.get("previsao_entrega")
        data_entrega = entrega.get("data_entrega")

        if status not in status_validos:
            avisos.append(
                "Entrega: status inválido"
            )

        elif status == "Aprovado":
            if any([
                rastreamento is not None,
                data_envio is not None,
                previsao is not None,
                data_entrega is not None
            ]):
                avisos.append(
                    "Entrega aprovada: possui dados de envio indevidos"
                )

        elif status == "Enviado":
            if (
                not rastreamento
                or not isinstance(data_envio, datetime)
                or not isinstance(previsao, datetime)
            ):
                avisos.append(
                    "Entrega enviada: faltam dados de envio válidos"
                )

            if data_entrega is not None:
                avisos.append(
                    "Entrega enviada: possui data de entrega"
                )

            if (
                isinstance(data_envio, datetime)
                and isinstance(previsao, datetime)
                and previsao < data_envio
            ):
                avisos.append(
                    "Entrega enviada: previsão anterior à data de envio"
                )

        elif status == "Entregue":
            if (
                not rastreamento
                or not isinstance(data_envio, datetime)
                or not isinstance(previsao, datetime)
                or not isinstance(data_entrega, datetime)
            ):
                avisos.append(
                    "Entrega concluída: faltam dados de entrega válidos"
                )

            elif data_entrega < data_envio:
                avisos.append(
                    "Entrega concluída: data de entrega anterior ao envio"
                )

    # 11. Verificar situação dos produtos
    print("\n11. Consistência dos produtos")

    for produto in produtos:
        if not produto.get("sku"):
            avisos.append(
                "Produto: SKU não informado"
            )

        if not isinstance(produto.get("ativo"), bool):
            avisos.append(
                f"Produto {produto.get('sku')}: situação inválida"
            )

    # RESULTADO FINAL - DEVE SER A ÚLTIMA VERIFICAÇÃO
    print("\n===== RESULTADO FINAL DA AUDITORIA =====")

    if avisos:
        print(
            f"\nForam encontradas {len(avisos)} inconsistências:"
        )

        for aviso in avisos:
            print(f"- {aviso}")

    else:
        print("\nNenhuma inconsistência encontrada!")
        print("Todas as 11 verificações foram aprovadas.")

finally:
    if client is not None:
        client.close()