# coding: utf-8

import datetime

from sqlalchemy import Column, Enum, ForeignKey, func, Boolean, \
        Integer, String, Table, text, DateTime, TIMESTAMP
from sqlalchemy.orm import relationship, column_property
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import create_engine 
from sqlalchemy.orm.properties import ColumnProperty


Base = declarative_base()
metadata = Base.metadata
engine = create_engine("mysql://root:eisoo.com@localhost:3306/mealer")


class Food(Base):
    __tablename__ = 'food'

    food_id = Column(Integer, primary_key=True)
    food_name = Column(String(64), nullable=False)
    comment = Column(String(256))


class Order(Base):
    __tablename__ = 'order'

    order_id = Column(Integer, primary_key=True)
    user_id = Column(ForeignKey(u'user.user_id'), nullable=False, index=True)
    food_id = Column(ForeignKey(u'food.food_id'), nullable=False, index=True)
    created_at = Column(TIMESTAMP, default=func.now())
    updated_at = Column(TIMESTAMP, default=func.now(), onupdate=func.now())

    food = relationship(u'Food')
    user = relationship(u'User')


class Switch(Base):
    __tablename__ = 'switch'

    switch_id = Column(Integer, primary_key=True)
    stop = Column(Boolean, default=False)


class User(Base):
    __tablename__ = 'user'

    user_id = Column(Integer, primary_key=True)
    username = Column(String(64), nullable=False)
    password = Column(String(256), nullable=False)
    email = Column(String(64))
    role = Column(Enum(u'admin', u'normal', u'audit'), nullable=False, server_default=text("'normal'"))

if __name__ == "__main__":
    Base.metadata.bind = engine
    Base.metadata.create_all()

