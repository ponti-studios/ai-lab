from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

from src.utils.config import settings
from src.utils.logger import logger

engine = create_engine(settings.DATABASE_URL, echo=settings.ENVIRONMENT == "local")

Base = declarative_base()

# Session
Session = sessionmaker(engine)
SessionLocal = sessionmaker(bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def connect_to_db():
    try:
        connection = engine.connect()
        logger.info("Successfully connected to the database!")
        connection.close()
    except Exception as e:
        logger.error(f"An error occurred: {e}")
