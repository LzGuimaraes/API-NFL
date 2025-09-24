from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy_utils import database_exists, create_database

# Configuração da conexão
DATABASE_URL = "postgresql+psycopg2://postgres:senha@localhost:5432/nfl_db"

# Cria engine
engine = create_engine(DATABASE_URL)

# Verifica se o DB existe, se não → cria
if not database_exists(engine.url):
    create_database(engine.url)
    print("✅ Banco de dados criado:", engine.url.database)
else:
    print("✅ Banco de dados já existe:", engine.url.database)

# Session
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base
Base = declarative_base()
