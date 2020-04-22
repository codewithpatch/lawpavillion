from datetime import datetime
import uuid

from sqlalchemy import (
    Column,
    BigInteger, create_engine, Date, DateTime, Float,
    ForeignKey, Integer, String, Boolean, JSON
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.engine.url import URL
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

from scrapy.utils.project import get_project_settings
from sqlalchemy.sql.ddl import CreateSchema

Base = declarative_base()


def connect_db():
    s = get_project_settings()
    return create_engine(URL(**s['DATABASE']))


def create_tables(engine, drop_tables=False):
    if drop_tables:
        Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)


def create_schema(engine, schema_name):
    if not engine.dialect.has_schema(engine, schema_name):
        engine.execute(CreateSchema(schema_name))


class Case(Base):
    __tablename__ = 'case'
    __table_args__ = {'schema': 'law_pavillion'}

    id = Column(
            UUID(as_uuid=True),
            primary_key=True,
            unique=True,
            default=uuid.uuid4
        )

    url = Column(String)
    name = Column(String)
    name_abbreviation = Column(String)
    slug = Column(String)
    suit_no = Column(String)
    decision_date = Column(JSON)
    jurisdiction_id = Column(UUID(as_uuid=True), ForeignKey('law_pavillion.jurisdiction.id'))
    court_id = Column(UUID(as_uuid=True), ForeignKey('law_pavillion.court.id'))
    frontend = Column(JSON)
    citations = Column(JSON)
    casebody_id = Column(UUID(as_uuid=True), ForeignKey('law_pavillion.casebody.id'))


class Jurisdiction(Base):
    __tablename__ = 'jurisdiction'
    __table_args__ = {'schema': 'law_pavillion'}

    id = Column(UUID(as_uuid=True), unique=True)
    slug = Column(String)
    whitelisted = Column(Boolean)
    name_long = Column(String)
    name = Column(String)


class Court(Base):
    __tablename__ = 'court'
    __table_args__ = {'schema': 'law_pavillion'}

    name = Column(String)
    name_abbreviation = Column(String)
    slug = Column(String)
    id = Column(UUID(as_uuid=True), unique=True)


class Casebody(Base):
    __tablename__ = 'casebody'
    __table_args__ = {'schema': 'law_pavillion'}

    opinion_id = Column(UUID(as_uuid=True), ForeignKey('law_pavillion.opinion.id'))
    ratio_decidendi_id = Column(UUID(as_uuid=True), ForeignKey('law_pavillion.ratio_decidendi.id'))
    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        unique=True,
        default=uuid.uuid4
    )
    judge_id = Column(UUID(as_uuid=True), ForeignKey('law_pavillion.judge.id'))
    summary = Column(String)
    respondents = Column(JSON)
    attorney_id = Column(UUID(as_uuid=True), ForeignKey('law_pavillion.attorney.id'))


class Attorney(Base):
    __tablename__ = 'attorney'
    __table_args__ = {'schema': 'law_pavillion'}

    id = Column(UUID(as_uuid=True), unique=True)
    name = Column(String)
    title = Column(String)


class Opinion(Base):
    __tablename__ = 'opinion'
    __table_args__ = {'schema': 'law_pavillion'}

    author = Column(String)
    text = Column(String)
    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        unique=True,
        default=uuid.uuid4
    )
    judge_id = Column(UUID(as_uuid=True), ForeignKey('law_pavillion.judge.id'))


class Ratio_decidendi(Base):
    __tablename__ = 'ratio_decidendi'
    __table_args__ = {'schema': 'law_pavillion'}

    id = Column(UUID(as_uuid=True), unique=True)
    matter = Column(String)
    topic = Column(String)
    text = Column(String)


class Judge(Base):
    __tablename__ = 'judge'
    __table_args__ = {'schema': 'law_pavillion'}

    id = Column(UUID(as_uuid=True), unique=True)
    name = Column(String)
    title = Column(String)
