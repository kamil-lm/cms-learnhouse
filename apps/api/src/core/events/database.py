import logging
from config.config import get_learnhouse_config
from fastapi import FastAPI
from sqlmodel import SQLModel, Session, create_engine

learnhouse_config = get_learnhouse_config()
engine = create_engine(
    learnhouse_config.database_config.sql_connection_string, echo=False  # type: ignore
)
SQLModel.metadata.create_all(engine)


async def connect_to_db(app: FastAPI):
    app.db_engine = engine  # type: ignore
    logging.info("LearnHouse database has been started.")
    SQLModel.metadata.create_all(engine)




def get_db_session():
    with Session(engine) as session:
        yield session


async def close_database(app: FastAPI):
    logging.info("LearnHouse has been shut down.")
    return app
