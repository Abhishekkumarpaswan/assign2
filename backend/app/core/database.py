import logging
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from backend.app.core.config import settings

logger = logging.getLogger("kinetic_app")

db_url = settings.DATABASE_URL
connect_args = {}
if db_url.startswith("sqlite"):
    connect_args = {"check_same_thread": False}

try:
    engine = create_engine(
        db_url,
        connect_args=connect_args,
        echo=False,
        future=True
    )
    # Quick probe if not sqlite
    if not db_url.startswith("sqlite"):
        with engine.connect() as test_conn:
            pass
except Exception as e:
    logger.warning(
        f"Unable to connect to configured DATABASE_URL ({db_url}): {e}. "
        "Falling back to local SQLite database 'kinetic_support.db'."
    )
    db_url = "sqlite:///./kinetic_support.db"
    connect_args = {"check_same_thread": False}
    engine = create_engine(
        db_url,
        connect_args=connect_args,
        echo=False,
        future=True
    )

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
