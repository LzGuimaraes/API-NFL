# Projeto NFL Data

Este projeto tem como objetivo coletar dados de times e jogadores da NFL utilizando a API da ESPN e armazenar essas informações em um banco de dados PostgreSQL.

## Estrutura do Projeto

- `db.py`: Configuração da conexão com o banco de dados PostgreSQL usando SQLAlchemy.
- `models.py`: Definição dos modelos de dados (Times e Jogadores) para o banco.
- `fetch_espn.py`: Script principal que busca os dados da API da ESPN e os armazena no banco.
- `requirements.txt`: Lista de dependências necessárias para o projeto.
- `main.py`: (Se existir) Ponto de entrada para executar o projeto.

## Requisitos

- Python 3.8 ou superior
- PostgreSQL instalado e em execução

## Configuração

1. Clone este repositório.
2. Crie um ambiente virtual Python (recomendado):

```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate    # Windows
```

3. Instale as dependências:

```bash
pip install -r requirements.txt
```

4. Configure a conexão com o banco de dados no arquivo `db.py`. Altere a variável `DATABASE_URL` para refletir seu usuário, senha, host, porta e nome do banco PostgreSQL.

Exemplo:

```python
DATABASE_URL = "postgresql+psycopg2://usuario:senha@localhost:5432/nome_do_banco"
```

5. Certifique-se que o banco de dados existe ou será criado automaticamente ao rodar o projeto.

## Uso

Para buscar os dados da NFL e armazenar no banco, execute o script `fetch_espn.py`:

```bash
python fetch_espn.py
```

Este script irá:
- Buscar os times da NFL da API da ESPN
- Para cada time, buscar os 5 principais jogadores
- Armazenar ou atualizar essas informações no banco de dados

## Observações

- O projeto utiliza SQLAlchemy ORM para manipulação do banco.
- A API da ESPN pode alterar seus endpoints, o que pode exigir ajustes futuros no script.

## Contato

Para dúvidas ou contribuições, entre em contato.