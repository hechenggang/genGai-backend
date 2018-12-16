# coding=utf-8
import os
from sqlalchemy import Column, String, Integer, create_engine, func, ForeignKey
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base

# 创建 SQLAlchemy 实例
Base = declarative_base()
# 创建继承自 SQLAlchemy 数据库模型的数据表抽象层，包含数据字段和自定义的方法
class User(Base):
    __tablename__ = 'user'
    id = Column(String(32), primary_key=True)
    mail = Column(String(100))
    password = Column(String(32))
    name = Column(String(15))
    config = Column(String(1000))

class Article(Base):
    __tablename__ = 'article'
    id = Column(String(32), primary_key=True)
    user_id = Column(String(32),ForeignKey(User.id))
    timestamp = Column(Integer)
    content = Column(String(200))

class Verification(Base):
    __tablename__ = 'verification'
    id = Column(String(32), primary_key=True)
    timestamp = Column(Integer)
    question = Column(String(50))
    answer = Column(String(50))

def getSession():
    # 取得 Sqlite 数据库文件的绝对地址
    db_abspath = os.path.abspath('./database/database.db')
    # 初始化数据库连接:
    engine = create_engine('sqlite:///'+db_abspath,connect_args={
        'check_same_thread':False
        })
    # 检查并创建表
    Base.metadata.create_all(engine)
    # 创建DBSession类型:
    DBSession = sessionmaker(bind=engine)
    return DBSession()