# coding=utf-8
import sys
sys.path.append('..')
from flask import Flask,request,jsonify,make_response
from flask import Blueprint
from database.session import getSession,User

import functools
import random
import time
from tools import string_to_md5

from api.verification import cross
from api.verification import check
from api.mail import send_fpassword_reset_mail

from threading import Thread

# resiger a bluepoint 
bp_api_user = Blueprint('api_user',__name__)

def login_require(F):
    @functools.wraps(F)
    def dec():
        req = request.json
        if not('auth' in req):
            resp = make_response(jsonify({
                'ok':False,
                'message':'auth 缺失。'
            }))
        else:
            try:
                # 校验密钥
                db = getSession()
                _id = req['auth'].split('->')[0]
                # 检查用户是否存在
                is_user = db.query(User.id).filter(User.id == _id).first()
                if not is_user:
                    resp = make_response(jsonify({
                        'ok':False,
                        'message':'失效的密钥。'
                    }))
                else:
                    resp = make_response(F())
            except:
                resp = make_response(jsonify({
                        'ok':False,
                        'message':'意料之外的错误。'
                    }))
        return resp
    return dec

# build apis base on this bluepoint
@bp_api_user.route('/login',methods=['POST','OPTIONS'])
@cross
def login():
    req = request.json
    # 檢查參數是否齊全
    if not(('id' in req) and ('answer' in req) and ('mail' in req) and ('password' in req) and ('timestamp' in req)):
        return jsonify({
            'ok':False,
            'message':'不要非法侵入本站喔。'
        })

    result = check(req=req,delete=True)
    if not result:
        return jsonify({
            'ok':False,
            'message':'验证码错误，你是机器人吗？'
        })

    # 登录逻辑
    db = getSession()
    _id = string_to_md5(req['mail'],mix=False)
    # 检查用户是否存在
    is_user = db.query(User).filter(User.id == _id).first()
    if not is_user:
        return jsonify({
            'ok':False,
            'message':'你还没注册过喔。'
        })

    # 检查密码是否正确
    password = string_to_md5(req['password'])
    if (password != is_user.password):
        return jsonify({
            'ok':False,
            'message':'你应该是记错密码了。'
        })

    return jsonify({
        'ok':True,
        'data':{
            'auth':is_user.id + '->' + is_user.password
        }
    })


# build apis base on this bluepoint
@bp_api_user.route('/signup',methods=['POST','OPTIONS'])
@cross
def signup():
    req = request.json
    # 檢查參數是否齊全
    if not(('id' in req) and ('answer' in req) and ('mail' in req) and ('password' in req) and ('timestamp' in req)):
        return jsonify({
            'ok':False,
            'message':'不要非法侵入本站喔。'
        })

    result = check(req=req,delete=True)
    if not result:
        return jsonify({
            'ok':False,
            'message':'验证码错误/失效，你是机器人吗？'
        })

    # 注册逻辑
    db = getSession()
    _id = string_to_md5(req['mail'],mix=False)
    is_user = db.query(User.mail).filter(User.id == _id).first()
    if is_user:
        return jsonify({
            'ok':False,
            'message':'你已经注册过了。'
        })

    try:
        mail = req['mail']
        password = string_to_md5(req['password'])
        name = req['mail'].split('@')[0]
        user = User(id=_id,mail=mail,password=password,name=name,config='')
        db.add(user)
        db.commit()
        
        return jsonify({
            'ok':True
        })
    except:
        return jsonify({
            'ok':False,
            'message':'产生了一些预料之外的错误，我们会尽快修复。'
        })

@bp_api_user.route('/get_password_reset_code',methods=['POST','OPTIONS'])
@cross
def get_password_reset_code():
    req = request.json
    # 檢查參數是否齊全
    if not(('id' in req) and ('answer' in req) and ('mail' in req)):
        return jsonify({
            'ok':False,
            'message':'不要非法侵入本站喔。'
        })

    result = check(req=req,delete=True)
    if not result:
        return jsonify({
            'ok':False,
            'message':'验证码错误，你是机器人吗？'
        })

    db = getSession()
    _id = string_to_md5(req['mail'],mix=False)
    is_user = db.query(User).filter(User.id == _id).first()
    if not is_user:
        return jsonify({
            'ok':False,
            'message':'你还没注册过喔。'
        })

    url = 'https://app.d-c.bid/gengai/#/forget?mail={0}&code={1}'.format(is_user.mail,is_user.password)
    t = Thread(target=send_fpassword_reset_mail,args=(is_user.mail,is_user.name,url))
    t.start()
    return jsonify({
        'ok':True,
    })


@bp_api_user.route('/reset_password',methods=['POST','OPTIONS'])
@cross
def reset_password():
    req = request.json
    # 檢查參數是否齊全
    if not(('id' in req) and ('answer' in req) and ('mail' in req) and ('password' in req) and ('code' in req)):
        return jsonify({
            'ok':False,
            'message':'不要非法侵入本站喔。'
        })

    result = check(req=req,delete=True)
    if not result:
        return jsonify({
            'ok':False,
            'message':'验证码错误/失效，你是机器人吗？'
        })

    db = getSession()
    _id = string_to_md5(req['mail'],mix=False)
    is_user = db.query(User).filter(User.id == _id).first()
    if not is_user:
        return jsonify({
            'ok':False,
            'message':'你还没注册过。'
        })

    if is_user.password == req['code']:
        password = string_to_md5(req['password'])
        is_user.password = password
        db.commit()
        
        return jsonify({
            'ok':True
        })
    else:
        return jsonify({
            'ok':False,
            'message':'校验码已失效'
        })
