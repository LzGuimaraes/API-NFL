from fetch_espn import fetch_and_store_data
from stats import update_stats_in_db
from db import Base, engine

# Cria tabelas se não existirem
Base.metadata.create_all(bind=engine)

# Busca times e 5 melhores jogadores
fetch_and_store_data()

# Atualiza pontos dos times e top players
update_stats_in_db()
