"""
File declares all SQL alchemy / db related objects and models
"""

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, scoped_session
from sqlalchemy import Column, String, Integer, Float, Binary, DateTime


"""
    SQL alchemy configuration and engine creation
"""
db_conn_str = 'postgresql+psycopg2://test:testpass@localhost:5432/heyjobs'
engine = create_engine(db_conn_str)


def session_factory():
    """
    session factory returns a threadsafe scopped session object to access db through sql alchemy
    :return:
    """
    return scoped_session(sessionmaker(autocommit=False,
                                       autoflush=False,
                                       bind=engine))

"""
    necessary objects to define models using declariative base
"""
Session = session_factory()
Base = declarative_base()


class JobAdd(Base):

    """
        simple model used to hold job title and id
    """

    __tablename__ = 'job_adds'

    id = Column(Integer, primary_key=True)
    uid = Column(String(500), nullable=False)
    title = Column(String(500), nullable=False)

    def __init__(self, uid, title):
        self.uid = uid
        self.title = title


def init_db():
    """
    method simply drops and rebuilds the tables each time it's called.
    :return:
    """
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)