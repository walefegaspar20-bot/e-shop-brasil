# E-Shop Brasil — Aplicação de Banco de Dados e Big Data

## 1. Sobre o projeto

Este projeto apresenta uma aplicação prática de tecnologias de banco de dados e análise de dados para a empresa fictícia **E-Shop Brasil**, uma plataforma de comércio eletrônico que atende milhões de clientes e processa um grande volume de pedidos.

A proposta é demonstrar como tecnologias relacionais, NoSQL e conceitos de Big Data podem apoiar a gestão de produtos, clientes, pedidos, estoques e entregas, contribuindo para decisões de negócio mais eficientes.

O protótipo foi desenvolvido com MongoDB, Python e Streamlit, utilizando dados fictícios para simular operações de um ambiente de comércio eletrônico.

## 2. Objetivos

- Implementar uma estrutura de banco de dados NoSQL utilizando MongoDB.
- Modelar dados de clientes, produtos, pedidos, estoques, navegação e entregas.
- Realizar operações de consulta, inserção, atualização e desativação de produtos.
- Desenvolver consultas e agregações para análise de vendas e estoque.
- Criar um dashboard interativo para visualização de indicadores.
- Demonstrar conceitos de integração, flexibilidade e análise de dados aplicados ao comércio eletrônico.

## 3. Arquitetura da solução

A aplicação utiliza uma arquitetura simples, dividida em três camadas:

1. **Banco de dados:** MongoDB armazena os documentos e relacionamentos da aplicação.
2. **Camada de aplicação:** Python, por meio da biblioteca PyMongo, realiza a comunicação com o banco, executa consultas e processa os resultados.
3. **Interface e visualização:** Streamlit apresenta os indicadores, gráficos, tabelas e formulários para interação com os dados.

### Tecnologias utilizadas

| Tecnologia | Aplicação no projeto |
|---|---|
| MongoDB 8.0 | Banco de dados NoSQL orientado a documentos |
| Docker Desktop | Ambiente de execução do MongoDB |
| Docker Compose | Configuração e inicialização do container |
| Python | Linguagem utilizada na aplicação e nas consultas |
| PyMongo | Integração entre Python e MongoDB |
| python-dotenv | Carregamento das variáveis de ambiente |
| Streamlit | Construção da interface web e dashboard |
| Plotly | Criação dos gráficos interativos |
| Visual Studio Code | Ambiente de desenvolvimento |

## 4. Modelagem do banco de dados

O banco de dados utilizado é `eshop_brasil`, composto por seis coleções:

| Coleção | Finalidade |
|---|---|
| `clientes` | Armazena os dados cadastrais dos clientes |
| `produtos` | Armazena catálogo, categorias, marcas e preços |
| `pedidos` | Registra pedidos e seus respectivos itens |
| `estoques` | Controla quantidades disponíveis por localidade |
| `eventos_navegacao` | Registra interações dos clientes com a plataforma |
| `entregas` | Armazena informações de transporte e rastreamento |

Os relacionamentos entre coleções são realizados por referências utilizando identificadores do tipo `ObjectId`. Os itens dos pedidos são armazenados em documentos incorporados, permitindo consultar os produtos de cada pedido em conjunto.

Campos monetários são armazenados com `Decimal128`, evitando a utilização direta de números de ponto flutuante para representar valores financeiros no banco.

## 5. Funcionalidades implementadas

### Dashboard e indicadores

- Filtro de pedidos por status.
- Faturamento por categoria de produto.
- Quantidade de unidades vendidas.
- Quantidade de pedidos analisados.
- Cálculo do ticket médio.
- Distribuição de pedidos por status.
- Distribuição de estoque por localidade.
- Identificação de produtos com baixo estoque.

### Gerenciamento de produtos

- Cadastro de novos produtos.
- Consulta por SKU, nome ou marca.
- Edição de informações cadastrais.
- Atualização de preço e situação do produto.
- Exclusão lógica por meio da desativação do produto.
- Validação para evitar o cadastro de SKUs duplicados.

### Consultas e análises

- Consulta de pedidos relacionados a clientes.
- Consulta integrada de pedidos e entregas.
- Agregações para análise de faturamento por categoria.
- Identificação de produtos com estoque igual ou inferior a 30 unidades.
- Auditoria da estrutura e dos dados armazenados.

## 6. Estrutura dos arquivos

A estrutura principal do projeto está organizada da seguinte forma:

```text
e-shop-brasil/
│
├── app.py
├── database.py
├── seed.py
├── test_connection.py
├── consultas.py
├── analises.py
├── analise_estoque.py
├── verificar_produto.py
├── auditoria_banco.py
│
├── docker-compose.yml
├── requirements.txt
├── README.md
├── .env.example
├── .gitignore
│
└── .venv/  (ambiente virtual local, não publicado)
```

### Descrição dos arquivos

| Arquivo | Responsabilidade |
|---|---|
| `app.py` | Aplicação Streamlit, dashboard e gerenciamento de produtos |
| `database.py` | Criação do banco, coleções e índices |
| `seed.py` | Inserção dos dados fictícios iniciais |
| `test_connection.py` | Teste de conexão com o MongoDB |
| `consultas.py` | Consultas integrando informações de diferentes coleções |
| `analises.py` | Análise de faturamento por categoria |
| `analise_estoque.py` | Consulta de produtos com baixo estoque |
| `verificar_produto.py` | Consulta um produto pelo SKU e verifica os dados após cadastro, edição ou desativação pela interface |
| `auditoria_banco.py` | Verificação da estrutura e consistência dos dados |
| `docker-compose.yml` | Configuração do container MongoDB |
| `requirements.txt` | Dependências Python do projeto |
| `.env.example` | Modelo das variáveis de ambiente necessárias |
| `.gitignore` | Define arquivos e pastas que não devem ser enviados ao Git |

O arquivo `.env` contém as credenciais locais e não deve ser publicado. A pasta `.venv` contém o ambiente virtual Python e também não deve ser enviada ao GitHub.

## 7. Como executar o projeto

### Pré-requisitos

- Windows 10 ou superior.
- Python instalado.
- Docker Desktop instalado e em execução.
- Visual Studio Code (recomendado).

### 7.1. Obter os arquivos do projeto

Após baixar ou clonar o repositório, abra o terminal na pasta `e-shop-brasil`.

### 7.2. Criar o arquivo de configuração

O projeto utiliza variáveis de ambiente para armazenar as credenciais do MongoDB.

Crie seu arquivo `.env` a partir do modelo disponibilizado:

```powershell
Copy-Item .env.example .env
```

Abra o arquivo `.env` e substitua os valores fictícios por um usuário e uma senha próprios:

```text
MONGO_INITDB_ROOT_USERNAME=seu_usuario
MONGO_INITDB_ROOT_PASSWORD=sua_senha_forte
```

Não compartilhe nem publique esse arquivo.

### 7.3. Iniciar o MongoDB

Com o arquivo `.env` configurado, execute:

```powershell
docker compose up -d
```

Para verificar se o container está em execução:

```powershell
docker ps
```

O container utilizado pelo projeto é `eshop-mongodb`, com a porta `27017` disponibilizada localmente.

O Docker Compose utiliza um volume persistente chamado `mongodb_data` para armazenar os dados do banco.

**Observação:** as variáveis de usuário e senha do Docker Compose são utilizadas na inicialização de um banco novo. Se o volume já tiver sido inicializado, alterar essas variáveis no `.env` não modifica automaticamente as credenciais existentes no MongoDB.

### 7.4. Criar e ativar o ambiente virtual

Caso o ambiente virtual ainda não exista:

```powershell
python -m venv .venv
```

Ative o ambiente:

```powershell
.\.venv\Scripts\Activate.ps1
```

Se o PowerShell bloquear a ativação, execute:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
```

Em seguida, tente ativar novamente.

### 7.5. Instalar as dependências

Com o ambiente virtual ativado:

```powershell
pip install -r requirements.txt
```

O arquivo `requirements.txt` contém:

```text
pymongo
streamlit
plotly
python-dotenv
```

### 7.6. Testar a conexão com o banco

```powershell
python test_connection.py
```

O teste deve confirmar a conexão com o MongoDB e listar os bancos disponíveis.

### 7.7. Criar a estrutura do banco

```powershell
python database.py
```

O script cria as seis coleções e os índices necessários. Se as coleções já existirem, elas serão preservadas.

### 7.8. Inserir os dados fictícios

```powershell
python seed.py
```

O script utiliza operações de atualização com inserção condicional (`upsert`) para evitar duplicação de registros em reexecuções. Os registros de entregas existentes também podem ser atualizados durante uma nova execução.

### 7.9. Executar as consultas e análises

Os scripts podem ser executados individualmente:

```powershell
python consultas.py
python analises.py
python analise_estoque.py
python auditoria_banco.py
```

Para consultar um produto específico pelo SKU:

```powershell
python verificar_produto.py
```

### 7.10. Iniciar o dashboard

```powershell
python -m streamlit run app.py
```

O Streamlit disponibilizará a aplicação no navegador, normalmente no endereço:

```text
http://localhost:8501
```

## 8. Resultados e validações

Durante os testes do projeto, foram implementadas e verificadas as seguintes funcionalidades:

- Criação das seis coleções do banco de dados.
- Inserção de dados fictícios sem duplicação em reexecuções do script de carga.
- Consultas integrando clientes, pedidos e entregas.
- Agregação de faturamento por categoria.
- Identificação de produtos com baixo estoque.
- Visualização dos indicadores no dashboard.
- Cadastro, consulta, edição e desativação lógica de produtos.
- Auditoria complementar da estrutura e dos dados armazenados.

Na última auditoria executada, foram identificados:

| Coleção | Documentos |
|---|---:|
| `clientes` | 5 |
| `produtos` | 11 |
| `pedidos` | 10 |
| `estoques` | 10 |
| `eventos_navegacao` | 15 |
| `entregas` | 10 |
| **Total** | **61** |

O resultado da última execução da auditoria foi: **nenhuma inconsistência encontrada**, com todas as 11 verificações aprovadas.

## 9. Segurança e privacidade

O projeto utiliza dados fictícios para fins acadêmicos e de demonstração.

Em um ambiente de produção, seria necessário complementar a solução com medidas como:

- Controle de acesso e autenticação adequada.
- Proteção das credenciais e variáveis de ambiente.
- Criptografia dos dados em trânsito e em repouso.
- Políticas de backup e recuperação.
- Controle de acesso aos dados pessoais.
- Adequação aos requisitos da Lei Geral de Proteção de Dados (LGPD).

As credenciais utilizadas no ambiente local não devem ser publicadas em repositórios públicos. O arquivo `.env.example` disponibiliza apenas valores fictícios para orientar a configuração de um novo ambiente.

## 10. Considerações finais

O projeto demonstra a aplicação prática do MongoDB em um cenário de comércio eletrônico, utilizando documentos flexíveis, referências entre coleções, consultas de agregação e visualização de indicadores.

A solução permite compreender como a integração entre banco de dados NoSQL, Python e ferramentas de visualização pode apoiar a gestão operacional e a tomada de decisões.

Em uma evolução para um ambiente de grande escala, tecnologias como Apache Kafka, Apache Spark e serviços de armazenamento distribuído poderiam complementar a arquitetura, permitindo processamento de eventos e análises de grandes volumes de dados.

---

**Projeto acadêmico — Advanced Databases and Big Data**

**E-Shop Brasil | Dashboard de indicadores do comércio eletrônico**