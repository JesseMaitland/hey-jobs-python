from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, scoped_session
from sqlalchemy import Column, String, Integer, Float, Binary, DateTime


db_conn_str = ''

engine = create_engine(db_conn_str)


def session_factory():
    return scoped_session(sessionmaker(autocommit=False,
                                       autoflush=False,
                                       bind=engine))


Session = session_factory()
Base = declarative_base()