# coding=utf-8
import sys
sys.path.append('..')
from flask import Flask,request,jsonify,make_response
from flask import Blueprint
from database.session import getSession,Article

import random
import time
from tools import string_to_md5
from tools import timestamp_to_yymmdd

from api.verification import cross
from api.user import login_require


# 注册蓝图
bp_api_article = Blueprint('api_article',__name__)


# 今天
@bp_api_article.route('/today',methods=['POST','OPTIONS'])
@cross
@login_require
def today():
    req = request.json
    user_id = req['auth'].split('->')[0]

    db = getSession()

    # 提取用户最新记录
    latest = db.query(Article).filter(Article.user_id == user_id).order_by(Article.timestamp.desc()).first()
    
    if not latest:
        return jsonify({
            'ok':False
        })
    
    # 最新一条记录是否今天，如果不是今天就返回空内容。
    if timestamp_to_yymmdd(latest.timestamp) != timestamp_to_yymmdd():
        return jsonify({
            'ok':False
        })

    # 最新一条记录以存在，且记录时间是今天时，返回该记录内容
    return jsonify({
        'ok':True,
        'data':{
            'content':latest.content,
            'timestamp':latest.timestamp
        }
    })

# 保存
@bp_api_article.route('/save',methods=['POST','OPTIONS'])
@cross
@login_require
def save():
    req = request.json
    user_id = req['auth'].split('->')[0]
    content = req['content']
    if len(content) > 200:
        return jsonify({
            'ok':False,
            'message':'字数超过限定。'
        })

    db = getSession()

    # 新建
    def new():
        _id = string_to_md5(user_id,mix=True)
        arti = Article(id=_id,user_id=user_id,timestamp=int(str(time.time()).replace('.','')[0:13]),content=content)
        db.add(arti)
        db.commit()
        return jsonify({
            'ok':True,
            'data':{
                'id':_id
            }
        })

    # 提取用户最新记录
    latest = db.query(Article).filter(Article.user_id == user_id).order_by(Article.timestamp.desc()).first()
    if not latest:
        return new()
    
    # 最新一条记录是否今天，如果不是今天就新建。
    if timestamp_to_yymmdd(latest.timestamp) != timestamp_to_yymmdd():
        return new()

    # 如果是同一天就更新
    else:
        latest.content = content
        db.commit()
        return jsonify({
            'ok':True,
            'data':{
                'id':latest.id
            }
        })


# 历史纪录
@bp_api_article.route('/history',methods=['POST','OPTIONS'])
@cross
@login_require
def history():
    req = request.json
    user_id = req['auth'].split('->')[0]

    db = getSession()

    # 提取用户记录
    history = db.query(Article.id,Article.timestamp,Article.content).filter(Article.user_id == user_id).order_by(Article.timestamp.desc()).all()
    
    if not history:
        return jsonify({
            'ok':False
        })

    return jsonify({
        'ok':True,
        'data':{
            'history':history
        }
    })