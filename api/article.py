# coding=utf-8
from flask import Flask, request, jsonify, make_response, send_file, abort
from tools import string_to_md5, timestamp_to_yymmdd, check_item_in_dict
from api.user import login_require, check_auth
from database.session import getSession, Article
import json
from io import BytesIO
from api.verification import cross
import time
import random
from flask import Blueprint
import sys
sys.path.append('..')


# 注册蓝图
bp_api_article = Blueprint('api_article', __name__)

# 今天


@bp_api_article.route('/today', methods=['POST', 'OPTIONS'])
@cross
@login_require
def today():
    auth = request.json['auth']
    user_id = auth.split('->')[0]
    db = getSession()
    # 提取用户最新记录
    latest = db.query(Article).filter(Article.user_id == user_id).order_by(
        Article.timestamp.desc()).first()
    if not latest:
        abort(404)

    # 最新一条记录是否今天，如果不是今天就返回空内容。
    if timestamp_to_yymmdd(latest.timestamp) != timestamp_to_yymmdd():
        abort(404)

    # 最新一条记录以存在，且记录时间是今天时，返回该记录内容
    return jsonify({
        'ok': True,
        'data': {
            'content': latest.content,
            'timestamp': latest.timestamp
        }
    })

# 保存


@bp_api_article.route('/save', methods=['POST', 'OPTIONS'])
@cross
@login_require
def save():
    # 校验输入
    auth = request.json['auth']
    user_id = auth.split('->')[0]
    content = None
    try:
        content = request.json['content']
    except:
        abort(400)

    if len(content) > 200:
        return jsonify({
            'ok': False,
            'message': '字数超过限定'
        }), 500

    db = getSession()
    # 新建

    def new():
        _id = string_to_md5(user_id, mix=True)
        arti = Article(id=_id, user_id=user_id, timestamp=int(
            str(time.time()).replace('.', '')[0:13]), content=content)
        db.add(arti)
        db.commit()
        return jsonify({
            'ok': True
        })

    # 提取用户最新记录
    latest = db.query(Article).filter(Article.user_id == user_id).order_by(
        Article.timestamp.desc()).first()
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
            'ok': True
        })


# 历史纪录
@bp_api_article.route('/history', methods=['POST', 'OPTIONS'])
@cross
@login_require
def history():
    auth = request.json['auth']
    user_id = auth.split('->')[0]
    db = getSession()
    # 提取用户记录
    history = db.query(Article.id, Article.timestamp, Article.content).filter(
        Article.user_id == user_id).order_by(Article.timestamp.desc()).all()
    if not history:
        return jsonify({
            'ok': False,
        }), 404

    return jsonify({
        'ok': True,
        'data': {
            'history': history
        }
    })

# 导出历史纪录


@bp_api_article.route('/history/json/', methods=['GET'])
@cross
@login_require
def history_json():
    auth = request.args.get('auth')
    user_id = auth.split('->')[0]
    db = getSession()
    history = db.query(Article.id, Article.timestamp, Article.content).filter(
        Article.user_id == user_id).order_by(Article.timestamp.desc()).all()
    if not history:
        abort(404)
    # print (history)
    s = bytes(json.dumps(history), encoding="utf8")
    f = BytesIO()
    f.write(s)
    f.seek(0)
    return send_file(f, cache_timeout=600, mimetype='application/octet-stream', as_attachment=True, attachment_filename='history.json')

# 上传并导入


@bp_api_article.route('/history/json/upload', methods=['POST', 'OPTIONS'])
@cross
@login_require
def history_upload():
    # 校验输入
    auth = request.json['auth']
    user_id = auth.split('->')[0]
    history = None
    try:
        history = request.json['history']
    except:
        abort(400)

    db = getSession()
    # 新建

    def new(item):
        _id = item[0]
        _timestamp = item[1]
        _content = item[2]
        arti = Article(id=_id, user_id=user_id,
                       timestamp=_timestamp, content=_content)
        db.add(arti)
        db.commit()

    for i in history:
        if len(i[2]) > 200:
            return jsonify({
                'ok': False,
                'message': '字数超过限定'
            }), 400

        else:
            # 尝试提取记录
            article = db.query(Article).filter(
                Article.user_id == user_id, Article.id == i[0]).first()
            if not article:
                try:
                    new(i)
                except:
                    return jsonify({
                        'ok': False,
                        'message': '无法跨账户导入'
                    }), 500
            else:
                continue
    return jsonify({
        'ok': True
    })
