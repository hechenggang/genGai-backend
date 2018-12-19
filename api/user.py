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
                        'message':'失效的密钥'
                    }))
                else:
                    resp = make_response(F())
            except:
                resp = make_response(jsonify({
                        'ok':False,
                        'message':'意料之外的错误'
                    }))
        return resp
    return dec

# build apis base on this bluepoint
@bp_api_user.route('/login',methods=['POST','OPTIONS'])
@cross
@need_verification
def login():
    
    # 校验输入
    req = request.json
    if not(('id' in req) and ('answer' in req) and ('mail' in req) and ('password' in req) and ('timestamp' in req)):
        return jsonify({
            'ok':False,
            'message':'不要非法侵入本站喔。'
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
    # 输入校验
    req = request.json
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
    req = request.json
    # 檢查參數是否齊全
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
    req = request.json
    # 檢查參數是否齊全
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
