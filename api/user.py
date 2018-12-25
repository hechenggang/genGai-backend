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

from api.verification import cross,need_verification
from api.verification import check
from api.mail import send_fpassword_reset_mail

from threading import Thread

# 注册蓝图
bp_api_user = Blueprint('api_user',__name__)

# 鉴权装饰器
def login_require(F):
    @functools.wraps(F)
    def dec():
        req = None
        _id = None
        _hash = None
        # 校验输入
        try:
            req = request.json
            _id = req['auth'].split('->')[0]
            _hash = req['auth'].split('->')[1]
        except:
            return jsonify({
                'ok':False,
                'message':'非法请求'
            }),400
        # 检查用户是否存在
        if _id and _hash:
            db = getSession()
            is_user = db.query(User).filter(User.id == _id).first()
            if not is_user:
                resp = make_response(jsonify({
                    'ok':False,
                    'message':'密钥无效'
                })),401

            elif not (is_user.password == _hash):
                resp = make_response(jsonify({
                    'ok':False,
                    'message':'校验失败'
                })),403

            else:
                resp = make_response(F(auth={'_id':_id,'_hash':_hash}))
        return resp
    return dec

# 登录
@bp_api_user.route('/login',methods=['POST','OPTIONS'])
@cross
@need_verification
def login():
    # 校验输入
    req = None
    try:
        req = request.json
    except:
        return jsonify({
                'ok':False,
                'message':'非法请求'
            }),400

    if not(('id' in req) and ('answer' in req) and ('mail' in req) and ('password' in req) and ('timestamp' in req)):
        return jsonify({
            'ok':False,
            'message':'参数错误'
        })

    # 查询记录
    db = getSession()
    _id = string_to_md5(req['mail'],mix=False)
    
    # 检查用户是否存在
    is_user = db.query(User).filter(User.id == _id).first()
    if not is_user:
        return jsonify({
            'ok':False,
            'message':'该邮箱尚未注册'
        })

    # 检查密码是否正确
    password = string_to_md5(req['password'])
    if (password != is_user.password):
        return jsonify({
            'ok':False,
            'message':'密码错误'
        })

    return jsonify({
        'ok':True,
        'data':{
            'auth':is_user.id + '->' + is_user.password
        }
    })


# 注册
@bp_api_user.route('/signup',methods=['POST','OPTIONS'])
@cross
@need_verification
def signup():
    # 校验输入
    req = None
    try:
        req = request.json
    except:
        pass
    if not(('id' in req) and ('answer' in req) and ('mail' in req) and ('password' in req) and ('timestamp' in req)):
        return jsonify({
            'ok':False,
            'message':'参数错误'
        })

    # 注册逻辑
    db = getSession()
    _id = string_to_md5(req['mail'],mix=False)
    is_user = db.query(User.mail).filter(User.id == _id).first()
    if is_user:
        return jsonify({
            'ok':False,
            'message':'该邮箱已注册'
        })

    # 新建记录
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
            'message':'预料之外的错误'
        })

@bp_api_user.route('/get_password_reset_code',methods=['POST','OPTIONS'])
@cross
@need_verification
def get_password_reset_code():
    # 校验输入
    req = None
    try:
        req = request.json
    except:
        pass
    if not(('id' in req) and ('answer' in req) and ('mail' in req)):
        return jsonify({
            'ok':False,
            'message':'参数错误'
        })

    db = getSession()
    _id = string_to_md5(req['mail'],mix=False)
    is_user = db.query(User).filter(User.id == _id).first()
    if not is_user:
        return jsonify({
            'ok':False,
            'message':'该邮箱尚未注册'
        })

    url = 'https://web.imhcg.cn/app/gengai/#/forget?mail={0}&code={1}'.format(is_user.mail,is_user.password)
    # 启动新线程来发送邮件
    Thread(target=send_fpassword_reset_mail,args=(is_user.mail,is_user.name,url)).start()
    return jsonify({
        'ok':True,
    })


@bp_api_user.route('/reset_password',methods=['POST','OPTIONS'])
@cross
@need_verification
def reset_password():
    # 校验输入
    req = None
    try:
        req = request.json
    except:
        pass
    if not(('id' in req) and ('answer' in req) and ('mail' in req) and ('password' in req) and ('code' in req)):
        return jsonify({
            'ok':False,
            'message':'参数错误'
        })

    db = getSession()
    _id = string_to_md5(req['mail'],mix=False)
    is_user = db.query(User).filter(User.id == _id).first()
    if not is_user:
        return jsonify({
            'ok':False,
            'message':'该邮箱尚未注册'
        })

    # 更新密码记录
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
