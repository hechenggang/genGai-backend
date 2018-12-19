# coding=utf-8
import sys
sys.path.append('..')
from flask import Flask,request,jsonify,make_response,send_file
from flask import Blueprint
from database.session import getSession,Verification
import random
import time
from tools import string_to_md5

import functools

from PIL import Image, ImageDraw, ImageFont, ImageFilter
from io import BytesIO

from threading import Thread

# 文字转图片数据流
def text_to_png(input_text=None):
    image = Image.new('RGBA', size=(100, 40), color=(255, 255, 255, 0))
    font = ImageFont.truetype(font='./src/font/font.ttf', size=50)
    draw = ImageDraw.Draw(image)
    draw.text(xy=(7, 2), text=input_text, font=font, fill=(0,0,0))
    byte_img = BytesIO()
    image.save(byte_img,'png')
    byte_img.seek(0)
    return byte_img


# 为反馈添加跨域头部
def cross(F):
    @functools.wraps(F)
    def dec(*args,**kwargs):
        if request.method == 'OPTIONS':
            resp = make_response('')
        else:
            resp = make_response(F(*args,**kwargs))
        resp.headers['Access-Control-Allow-Headers'] = 'Content-Type'
        resp.headers['Access-Control-Allow-Origin'] = '*'
        resp.headers['Access-Control-Allow-Methods'] = '*'
        return resp
    return dec


# 验证装饰器
def need_verification(F):
    @functools.wraps(F)
    def dec(*args,**kwargs):
        if not check(req=request.json):
            resp = jsonify({
                'ok':False,
                'message':'你是机器人吗？'
            })
        else:
            resp = make_response(F(*args,**kwargs))
        return resp
    return dec


# 注册蓝图
bp_api_verification = Blueprint('api_verification',__name__)

# 生成验证码
@bp_api_verification.route('/get')
@cross
def get():
    # 准备一个随机问题
    number_list = ['0','1','2','3','4','5','6','7','8','9']
    num1 = random.choice(number_list)
    num2 = random.choice(number_list)
    operators = ['+','-','*']
    opt = random.choice(operators)

    # 准备一条验证记录
    timestamp = int(str(time.time()).replace('.','')[0:13])
    _id = string_to_md5(timestamp,mix=True)
    question = num1+opt+num2
    answer = eval(num1+opt+num2)
    
    # 写入记录到数据库
    db = getSession()
    veri = Verification(id=_id,timestamp=timestamp,question=question,answer=answer)
    db.add(veri)
    db.commit()
    db.close()

    # 启动另外一个线程来清理过期验证码
    Thread(target=clean).start()

    # 返回生成记录的唯一标识
    return jsonify({
        'ok':True,
        'data':{
            'id':_id
        }
    })


# 获取验证的图片
@bp_api_verification.route('/img/<_id>')
@cross
def getImg(*args,**kwargs):
    # 校验输入
    if '_id' in kwargs:
        _id = kwargs['_id']
        # 查询记录
        db = getSession()
        veri = db.query(Verification).filter(Verification.id == _id).first()
        db.close()
        if not veri:
            return jsonify({
                'ok':False,
                'message':'无效的查询'
            })

        # 调用字符转图片函数生成验证码的图片并返回
        return send_file(text_to_png(veri.question+'='), mimetype='image/png')
    else:
        return jsonify({
                'ok':False,
                'message':'参数错误'
            })


# # 测试验证码
# @bp_api_verification.route('/test',methods=['POST','OPTIONS'])
# @cross
# def use():
#     req = request.json
#     if not(('id' in req) and ('answer' in req)):
#         return jsonify({
#             'ok':False,
#             'message':'参数错误'
#         })

#     _id = req['id']
#     db = getSession()
#     veri = db.query(Verification).filter(Verification.id == _id).first()
#     if not veri:
#         return jsonify({
#             'ok':False,
#             'message':'验证码不存在。'
#         })

#     timestamp = veri.timestamp
#     passed_time = int(str(time.time()).replace('.','')[0:13]) - int(timestamp)
#     passed_time = int(passed_time/1000/60)
#     if passed_time > 5:
#         return jsonify({
#             'ok':False,
#             'message':'验证码过期'
#         })

#     if str(veri.answer) != str(req['answer']):
#         return jsonify({
#             'ok':False,
#             'message':'验证码错误'
#         })

#     db.close()
#     return jsonify({
#         'ok':True,
#         'message':'验证通过'
#     })


# 删除过期验证码
def clean():
    try:
        db = getSession()
        timenow = int(str(time.time()).replace('.','')[0:13])
        overdue = db.query(Verification).filter((timenow - Verification.timestamp) > 300000).all()
        for i in overdue:
            db.delete(i)
        db.commit()
        db.close()
        print('过期验证码清理完成')
        return True
    except:
        return False


# 提供对外检测接口
def check(req=None,delete=False):
    # 输入校验
    if not req:
        return False
    if not(('id' in req) and ('answer' in req)):
        return False

    # 提取记录
    _id = req['id']
    db = getSession()
    veri = db.query(Verification).filter(Verification.id == _id).first()
    if not veri:
        return False

    # 检查时效
    timestamp = veri.timestamp
    passed_time = int(str(time.time()).replace('.','')[0:13]) - int(timestamp)
    passed_time = int(passed_time/1000/60)
    if passed_time > 5:
        return False

    # 检查答案
    if str(veri.answer) != str(req['answer']):
        return False

    # 验证成功，删除验证码
    db.delete(veri)
    db.commit()
    db.close()
    return True

