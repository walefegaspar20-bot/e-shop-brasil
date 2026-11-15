
import os
import re
from urllib.parse import quote_plus

import plotly.express as px
import streamlit as st
from bson.decimal128 import Decimal128
from dotenv import load_dotenv
from pymongo import MongoClient, ASCENDING, DESCENDING
from pymongo.errors import PyMongoError

st.set_page_config(
    page_title="E-Shop Brasil | Dashboard",
    page_icon="🛒",
    layout="wide"
)


# Carregar as variáveis do arquivo .env
load_dotenv()

MONGO_USERNAME = os.getenv("MONGO_INITDB_ROOT_USERNAME")
MONGO_PASSWORD = os.getenv("MONGO_INITDB_ROOT_PASSWORD")

if not MONGO_USERNAME or not MONGO_PASSWORD:
    st.error(
        "Credenciais do MongoDB não encontradas no arquivo .env."
    )
    st.stop()

# Codificar as credenciais para uso na URI
usuario = quote_plus(MONGO_USERNAME)
senha = quote_plus(MONGO_PASSWORD)

URI = (
    f"mongodb://{usuario}:{senha}"
    "@localhost:27017/?authSource=admin"
)

st.title("🛒 E-Shop Brasil")
st.subheader("Painel de indicadores do comércio eletrônico")
st.caption("Análise de faturamento e disponibilidade de estoque")

client = None

try:
    client = MongoClient(URI, serverSelectionTimeoutMS=5000)
    client.admin.command("ping")

    db = client["eshop_brasil"]

    # Filtro de pedidos por status
    status_selecionados = st.multiselect(
        "Filtrar pedidos por status",
        options=["Aprovado", "Enviado", "Entregue"],
        default=["Enviado", "Entregue"]
    )

    # Faturamento por categoria
    pipeline_faturamento = [
        {"$match": {"status": {"$in": status_selecionados}}},
        {"$unwind": "$itens"},
        {
            "$lookup": {
                "from": "produtos",
                "localField": "itens.produto_id",
                "foreignField": "_id",
                "as": "produto"
            }
        },
        {"$unwind": "$produto"},
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
        {"$sort": {"faturamento": DESCENDING}}
    ]

    resultados_faturamento = list(
        db.pedidos.aggregate(pipeline_faturamento)
    )

    dados_faturamento = []

    for item in resultados_faturamento:
        dados_faturamento.append({
            "Categoria": item["_id"],
            "Quantidade vendida": item["quantidade_vendida"],
            "Faturamento (R$)": float(
                item["faturamento"].to_decimal()
            )
        })

    faturamento_total = sum(
        item["Faturamento (R$)"] for item in dados_faturamento
    )

    quantidade_total = sum(
        item["Quantidade vendida"] for item in dados_faturamento
    )

    # Pedidos analisados e ticket médio
    pedidos_analisados = db.pedidos.count_documents({
        "status": {"$in": status_selecionados}
    })

    ticket_medio = (
        faturamento_total / pedidos_analisados
        if pedidos_analisados > 0
        else 0
    )

    # Pedidos por status
    pipeline_pedidos_status = [
        {
            "$match": {
                "status": {"$in": status_selecionados}
            }
        },
        {
            "$group": {
                "_id": "$status",
                "quantidade": {"$sum": 1}
            }
        },
        {"$sort": {"quantidade": -1}}
    ]

    dados_pedidos_status = list(
        db.pedidos.aggregate(pipeline_pedidos_status)
    )

    # Produtos com baixo estoque
    pipeline_estoque = [
        {"$match": {"quantidade": {"$lte": 30}}},
        {
            "$lookup": {
                "from": "produtos",
                "localField": "produto_id",
                "foreignField": "_id",
                "as": "produto"
            }
        },
        {"$unwind": "$produto"},
        {"$sort": {"quantidade": ASCENDING}},
        {
            "$project": {
                "_id": 0,
                "Produto": "$produto.nome",
                "SKU": "$produto.sku",
                "Categoria": "$produto.categoria",
                "Localidade": "$localidade",
                "Estado": "$estado",
                "Quantidade disponível": "$quantidade"
            }
        }
    ]

    dados_estoque = list(
        db.estoques.aggregate(pipeline_estoque)
    )

    # Quantidade total de estoque por localidade
    pipeline_estoque_localidade = [
        {
            "$group": {
                "_id": {
                    "localidade": "$localidade",
                    "estado": "$estado"
                },
                "total_unidades": {
                    "$sum": "$quantidade"
                }
            }
        },
        {
            "$sort": {
                "total_unidades": DESCENDING
            }
        }
    ]

    resultados_localidade = list(
        db.estoques.aggregate(pipeline_estoque_localidade)
    )

    dados_estoque_localidade = []

    for item in resultados_localidade:
        dados_estoque_localidade.append({
            "Localidade": (
                f"{item['_id']['localidade']} - "
                f"{item['_id']['estado']}"
            ),
            "Unidades disponíveis": item["total_unidades"]
        })

    # Indicadores
    st.divider()
    st.subheader("Visão geral")

    coluna1, coluna2, coluna3, coluna4, coluna5 = st.columns(5)

    coluna1.metric(
        "Faturamento analisado",
        f"R$ {faturamento_total:,.2f}"
    )

    coluna2.metric(
        "Unidades vendidas",
        quantidade_total
    )

    coluna3.metric(
        "Produtos com baixo estoque",
        len(dados_estoque)
    )

    coluna4.metric(
        "Pedidos analisados",
        pedidos_analisados
    )

    coluna5.metric(
        "Ticket médio",
        f"R$ {ticket_medio:,.2f}"
    )

    # Gráfico de faturamento por categoria
    st.subheader("Distribuição do faturamento")

    if dados_faturamento:
        grafico_faturamento = px.bar(
            dados_faturamento,
            x="Categoria",
            y="Faturamento (R$)",
            text="Faturamento (R$)",
            labels={
                "Categoria": "Categoria",
                "Faturamento (R$)": "Faturamento (R$)"
            },
            title="Faturamento por categoria"
        )

        grafico_faturamento.update_traces(
            texttemplate="R$ %{y:,.2f}",
            textposition="outside"
        )

        grafico_faturamento.update_layout(
            yaxis_title="Faturamento (R$)",
            xaxis_title="Categoria",
            showlegend=False
        )

        st.plotly_chart(
            grafico_faturamento,
            width="stretch"
        )
    else:
        st.info("Não há dados para gerar o gráfico.")

    # Tabela de faturamento
    st.divider()
    st.subheader("Faturamento por categoria")

    if dados_faturamento:
        st.dataframe(
            dados_faturamento,
            width="stretch",
            hide_index=True
        )
    else:
        st.info("Nenhum faturamento encontrado.")

    # Gráfico de pedidos por status
    st.divider()
    st.subheader("Distribuição de pedidos por status")

    if dados_pedidos_status:
        grafico_pedidos = px.bar(
            dados_pedidos_status,
            x="_id",
            y="quantidade",
            text="quantidade",
            labels={
                "_id": "Status do pedido",
                "quantidade": "Quantidade de pedidos"
            },
            title="Quantidade de pedidos por status"
        )

        grafico_pedidos.update_traces(
            texttemplate="%{y}",
            textposition="outside"
        )

        grafico_pedidos.update_layout(
            xaxis_title="Status",
            yaxis_title="Quantidade de pedidos",
            showlegend=False
        )

        st.plotly_chart(
            grafico_pedidos,
            width="stretch"
        )
    else:
        st.info("Não há pedidos para os filtros selecionados.")

    # Gráfico de estoque por localidade
    st.divider()
    st.subheader("Distribuição de estoque por localidade")

    if dados_estoque_localidade:
        grafico_estoque = px.bar(
            dados_estoque_localidade,
            x="Localidade",
            y="Unidades disponíveis",
            text="Unidades disponíveis",
            title="Total de unidades disponíveis por cidade"
        )

        grafico_estoque.update_traces(
            texttemplate="%{y} unidades",
            textposition="outside"
        )

        grafico_estoque.update_layout(
            xaxis_title="Localidade",
            yaxis_title="Unidades disponíveis",
            showlegend=False
        )

        st.plotly_chart(
            grafico_estoque,
            width="stretch"
        )
    else:
        st.info("Não há dados de estoque para gerar o gráfico.")

    # Tabela de estoque
    st.divider()
    st.subheader("Produtos com baixo estoque")

    st.caption(
        "Critério utilizado: estoque igual ou inferior a 30 unidades."
    )

    if dados_estoque:
        st.dataframe(
            dados_estoque,
            width="stretch",
            hide_index=True
        )
    else:
        st.success("Nenhum produto com baixo estoque.")

    # Cadastro de produtos
    st.divider()
    st.subheader("Cadastro de produtos")

    with st.form("form_cadastro_produto"):

        sku = st.text_input("SKU")
        nome = st.text_input("Nome do produto")

        categoria = st.selectbox(
            "Categoria",
            [
                "Eletrônicos",
                "Acessórios",
                "Móveis",
                "Informática"
            ]
        )

        marca = st.text_input("Marca")
        descricao = st.text_area("Descrição")

        preco = st.number_input(
            "Preço (R$)",
            min_value=0.01,
            value=100.00,
            step=10.00,
            format="%.2f"
        )

        ativo = st.checkbox(
            "Produto ativo",
            value=True
        )

        cadastrar = st.form_submit_button("Cadastrar produto")

        if cadastrar:

            sku = sku.strip().upper()
            nome = nome.strip()
            marca = marca.strip()
            descricao = descricao.strip()

            if not sku or not nome or not marca:
                st.error(
                    "Preencha o SKU, o nome e a marca do produto."
                )

            elif db.produtos.find_one({"sku": sku}):
                st.error(
                    "Já existe um produto cadastrado com esse SKU."
                )

            else:
                novo_produto = {
                    "sku": sku,
                    "nome": nome,
                    "categoria": categoria,
                    "marca": marca,
                    "descricao": descricao,
                    "preco": Decimal128(str(preco)),
                    "ativo": ativo
                }

                db.produtos.insert_one(novo_produto)

                st.success(
                    f"Produto {nome} cadastrado com sucesso!"
                )

    # Consulta de produtos
    st.divider()
    st.subheader("Consulta de produtos")

    termo_busca = st.text_input(
        "Pesquisar por SKU, nome ou marca",
        placeholder="Ex.: P013 ou Chinela Alpargatas"
    )

    filtro_produtos = {}

    if termo_busca.strip():
        expressao = re.escape(termo_busca.strip())

        filtro_produtos = {
            "$or": [
                {"sku": {"$regex": expressao, "$options": "i"}},
                {"nome": {"$regex": expressao, "$options": "i"}},
                {"marca": {"$regex": expressao, "$options": "i"}}
            ]
        }

    produtos = list(
        db.produtos.find(
            filtro_produtos,
            {"_id": 0}
        ).sort("sku", ASCENDING)
    )

    dados_produtos = []

    for produto in produtos:
        dados_produtos.append({
            "SKU": produto.get("sku", ""),
            "Nome": produto.get("nome", ""),
            "Categoria": produto.get("categoria", ""),
            "Marca": produto.get("marca", ""),
            "Preço (R$)": float(
                produto["preco"].to_decimal()
            ),
            "Ativo": "Sim" if produto.get("ativo") else "Não"
        })

    if dados_produtos:
        st.dataframe(
            dados_produtos,
            width="stretch",
            hide_index=True
        )

        st.caption(
            f"Total de produtos encontrados: {len(dados_produtos)}"
        )

    else:
        st.info("Nenhum produto encontrado.")

    # Edição de produtos
    st.divider()
    st.subheader("Edição de produtos")

    produtos_para_edicao = list(
        db.produtos.find(
            {},
            {"_id": 0, "sku": 1, "nome": 1}
        ).sort("sku", ASCENDING)
    )

    if produtos_para_edicao:

        opcoes_produtos = {
            f"{produto['sku']} - {produto['nome']}": produto["sku"]
            for produto in produtos_para_edicao
        }

        produto_selecionado = st.selectbox(
            "Selecione o produto que deseja editar",
            options=list(opcoes_produtos.keys())
        )

        sku_selecionado = opcoes_produtos[produto_selecionado]

        produto_atual = db.produtos.find_one(
            {"sku": sku_selecionado}
        )

        with st.form("form_edicao_produto"):

            nome_editado = st.text_input(
                "Nome do produto",
                value=produto_atual.get("nome", "")
            )

            categorias = [
                "Eletrônicos",
                "Acessórios",
                "Móveis",
                "Informática"
            ]

            categoria_atual = produto_atual.get("categoria", "")

            if categoria_atual not in categorias:
                categorias.append(categoria_atual)

            categoria_editada = st.selectbox(
                "Categoria",
                options=categorias,
                index=categorias.index(categoria_atual)
            )

            marca_editada = st.text_input(
                "Marca",
                value=produto_atual.get("marca", "")
            )

            descricao_editada = st.text_area(
                "Descrição",
                value=produto_atual.get("descricao", "")
            )

            preco_editado = st.number_input(
                "Preço (R$)",
                min_value=0.01,
                value=float(
                    produto_atual["preco"].to_decimal()
                ),
                step=10.00,
                format="%.2f"
            )

            ativo_editado = st.checkbox(
                "Produto ativo",
                value=produto_atual.get("ativo", True)
            )

            atualizar = st.form_submit_button(
                "Salvar alterações"
            )

            if atualizar:

                nome_editado = nome_editado.strip()
                marca_editada = marca_editada.strip()
                descricao_editada = descricao_editada.strip()

                if not nome_editado or not marca_editada:
                    st.error(
                        "O nome e a marca são obrigatórios."
                    )

                else:
                    resultado = db.produtos.update_one(
                        {"sku": sku_selecionado},
                        {
                            "$set": {
                                "nome": nome_editado,
                                "categoria": categoria_editada,
                                "marca": marca_editada,
                                "descricao": descricao_editada,
                                "preco": Decimal128(
                                    str(preco_editado)
                                ),
                                "ativo": ativo_editado
                            }
                        }
                    )

                    if resultado.modified_count > 0:
                        st.success(
                            "Produto atualizado com sucesso!"
                        )

                    else:
                        st.info(
                            "Nenhuma alteração foi realizada."
                        )

    else:
        st.info("Não existem produtos cadastrados para edição.")


    # Exclusão lógica de produtos
    st.divider()
    st.subheader("Exclusão de produtos")

    produtos_para_exclusao = list(
        db.produtos.find(
            {},
            {"_id": 0, "sku": 1, "nome": 1, "ativo": 1}
        ).sort("sku", ASCENDING)
    )

    if produtos_para_exclusao:

        opcoes_exclusao = {
            f"{produto['sku']} - {produto['nome']}": produto["sku"]
            for produto in produtos_para_exclusao
        }

        produto_exclusao = st.selectbox(
            "Selecione o produto",
            options=list(opcoes_exclusao.keys()),
            key="produto_para_excluir"
        )

        sku_exclusao = opcoes_exclusao[produto_exclusao]

        with st.form("form_exclusao_produto"):

            confirmar_exclusao = st.checkbox(
                "Confirmo a desativação deste produto."
            )

            excluir = st.form_submit_button(
                "Desativar produto"
            )

            if excluir:

                if not confirmar_exclusao:
                    st.warning(
                        "Confirme a desativação antes de continuar."
                    )

                else:
                    resultado = db.produtos.update_one(
                        {
                            "sku": sku_exclusao,
                            "ativo": True
                        },
                        {
                            "$set": {
                                "ativo": False
                            }
                        }
                    )

                    if resultado.modified_count > 0:
                        st.success(
                            f"Produto {sku_exclusao} desativado com sucesso!"
                        )

                    else:
                        st.info(
                            "Este produto já está desativado."
                        )

    else:
        st.info("Não existem produtos cadastrados.")


except PyMongoError as erro:
    st.error(f"Não foi possível acessar o MongoDB: {erro}")

finally:
    if client is not None:
        client.close()
