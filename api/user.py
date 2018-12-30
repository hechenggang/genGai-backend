# coding=utf-8
from flask import Flask, request, jsonify, make_response, render_template, abort
from database.session import getSession, User, Article
from api.verification import cross, need_verification
from tools import string_to_md5, check_item_in_dict
from threading import Thread
from api import mail
from api.verification import check
import time
import random
import functools
from flask import Blueprint
import config
import sys
sys.path.append('..')


# 注册蓝图
bp_api_user = Blueprint('api_user', __name__)

# 鉴权装饰器


def login_require(F):
    @functools.wraps(F)
    def dec():
        # GET请求
        if request.method == 'GET':
            auth = request.args.get('auth')
            if check_auth(auth):
                return F()
            else:
                abort(401)
        # POST
        elif request.method == 'POST':
            if(request.is_json):
                if check_auth(request.json['auth']):
                    return F()
                else:
                    abort(401)
            else:
                abort(400)
        else:
            abort(401)
    return dec


def check_auth(auth):
    _id = None
    _hash = None
    try:
        _id = auth.split('->')[0]
        _hash = auth.split('->')[1]
    except:
        return False

    if _id and _hash:
        db = getSession()
        is_user = db.query(User).filter(User.id == _id).first()
        if not is_user:
            return False
        elif not (is_user.password == _hash):
            return False
        else:
            return True
    else:
        return False

# 登录


@bp_api_user.route('/login', methods=['POST', 'OPTIONS'])
@cross
@need_verification
def login():
    # 校验输入
    data = None
    try:
        data = request.json
        if not check_item_in_dict(['id', 'answer', 'mail', 'password', 'timestamp'], data):
            return jsonify({
                'ok': False,
                'message': '参数错误'
            }), 500
    except:
        return jsonify({
            'ok': False,
            'message': '非法请求'
        }), 400

    # 查询记录
    db = getSession()
    _id = string_to_md5(data['mail'], mix=False)
    # 检查用户是否存在
    is_user = db.query(User).filter(User.id == _id).first()
    if not is_user:
        return jsonify({
            'ok': False,
            'message': '该邮箱尚未注册'
        })

    # 检查密码是否正确
    password = string_to_md5(data['password'])
    if (password != is_user.password):
        return jsonify({
            'ok': False,
            'message': '密码错误'
        })

    return jsonify({
        'ok': True,
        'data': {
            'auth': is_user.id + '->' + is_user.password
        }
    })


# 注册
@bp_api_user.route('/signup', methods=['POST', 'OPTIONS'])
@cross
@need_verification
def signup():
    # 校验输入
    data = None
    try:
        data = request.json
        if not check_item_in_dict(['id', 'answer', 'mail', 'password', 'timestamp'], data):
            return jsonify({
                'ok': False,
                'message': '参数错误'
            }), 500
    except:
        return jsonify({
            'ok': False,
            'message': '非法请求'
        }), 400

    db = getSession()
    _id = string_to_md5(data['mail'], mix=False)
    is_user = db.query(User.mail).filter(User.id == _id).first()
    if is_user:
        return jsonify({
            'ok': False,
            'message': '该邮箱已注册'
        })

    # 新建记录
    try:
        mail = data['mail']
        password = string_to_md5(data['password'])
        name = data['mail'].split('@')[0]
        user = User(id=_id, mail=mail, password=password, name=name, config='')
        db.add(user)
        db.commit()
        return jsonify({
            'ok': True
        })
    except:
        return jsonify({
            'ok': False,
            'message': '预料之外的错误'
        })


@bp_api_user.route('/get_password_reset_code', methods=['POST', 'OPTIONS'])
@cross
@need_verification
def get_password_reset_code():
    # 校验输入
    data = None
    try:
        data = request.json
        if not check_item_in_dict(['id', 'answer', 'mail'], data):
            return jsonify({
                'ok': False,
                'message': '参数错误'
            }), 500
    except:
        return jsonify({
            'ok': False,
            'message': '非法请求'
        }), 400

    db = getSession()
    _id = string_to_md5(data['mail'], mix=False)
    is_user = db.query(User).filter(User.id == _id).first()
    if not is_user:
        return jsonify({
            'ok': False,
            'message': '该邮箱尚未注册'
        })

    # 准备数据
    reset_link = '{}#/forget?mail={}&code={}'.format(
        config.app['web_addr'], is_user.mail, is_user.password)
    content = render_template('reset_password.html',
                              link=reset_link, name=is_user.name)
    subject = '重置梗概轻日记的密码'
    # 启动新线程来发送邮件
    Thread(target=mail.send, args=(
        {'name': is_user.name, 'mail': is_user.mail}, content, subject)).start()
    return jsonify({
        'ok': True
    })


@bp_api_user.route('/reset_password', methods=['POST', 'OPTIONS'])
@cross
@need_verification
def reset_password():
    # 校验输入
    data = None
    try:
        data = request.json
        if not check_item_in_dict(['id', 'answer', 'mail', 'password', 'timestamp', 'code'], data):
            return jsonify({
                'ok': False,
                'message': '参数错误'
            }), 500
    except:
        return jsonify({
            'ok': False,
            'message': '非法请求'
        }), 400

    db = getSession()
    _id = string_to_md5(data['mail'], mix=False)
    is_user = db.query(User).filter(User.id == _id).first()
    if not is_user:
        return jsonify({
            'ok': False,
            'message': '该邮箱尚未注册'
        })

    # 更新密码记录
    if is_user.password == data['code']:
        password = string_to_md5(data['password'])
        is_user.password = password
        db.commit()

        return jsonify({
            'ok': True
        })

    else:
        return jsonify({
            'ok': False,
            'message': '校验码已失效'
        })


@bp_api_user.route('/clean', methods=['GET'])
@cross
@login_require
def history_json():
    auth = request.args.get('auth')
    user_id = auth.split('->')[0]
    password = auth.split('->')[1]

    db = getSession()
    user = db.query(User).filter(User.id == user_id).first()
    print(user)
    if not(user.password == password):
        abort(401)
    db.delete(user)
    db.commit()

    history = db.query(Article).filter(Article.user_id == user_id).all()
    print(history)
    print('删除历史')
    if not history:
        pass
    else:
        print('删除日记')
        for i in history:
            db.delete(i)
        db.commit()

    return jsonify({
        'ok': True,
        'message': '再会'
    })
