import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, declarative_base as sa_declarative_base
from sqlalchemy.engine.url import URL

# dotenv-Handling: Automatisch die richtige .env laden
try:
    from dotenv import load_dotenv

    if os.getenv("PYTEST_CURRENT_TEST"):
        load_dotenv(".env.test")
    else:
        load_dotenv(".env")
except ImportError:
    pass  # Fallback: dotenv nicht installiert, Umgebungsvariablen müssen gesetzt sein

DATABASE_URL = os.getenv("DATABASE_URL")

# Safety-Check: Tests dürfen nie gegen Produktionsdatenbank laufen!
if os.getenv("PYTEST_CURRENT_TEST") and os.getenv("DB_HOST") in [
    "db",
    "prod-db-host",
    "production-db-host",
]:
    raise RuntimeError(
        "Tests dürfen nicht gegen die Produktionsdatenbank laufen! Bitte .env.test korrekt konfigurieren."
    )

engine = create_engine(DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = sa_declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
