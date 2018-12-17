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


# resiger a bluepoint 
bp_api_verification = Blueprint('api_verification',__name__)

# 生成验证码
@bp_api_verification.route('/get')
@cross
def get():
    number_list = ['0','1','2','3','4','5','6','7','8','9']
    num1 = random.choice(number_list)
    num2 = random.choice(number_list)

    operators = ['+','-','*']
    opt = random.choice(operators)

    question = num1+opt+num2
    answer = eval(num1+opt+num2)
    timestamp = int(str(time.time()).replace('.','')[0:13])
    _id = string_to_md5(timestamp,mix=True)
       
    # 写入数据库
    db = getSession()
    veri = Verification(id=_id,timestamp=timestamp,question=question,answer=answer)
    db.add(veri)
    db.commit()

    return jsonify({
        'ok':True,
        'data':{
            'id':_id
        }
    })

# 获取验证图片
@bp_api_verification.route('/img/<_id>')
@cross
def getImg(*args,**kwargs):
    print (args,kwargs)
    if '_id' in kwargs:
        _id = kwargs['_id']
        db = getSession()
        veri = db.query(Verification).filter(Verification.id == _id).first()
        if not veri:
            return jsonify({
                'ok':False,
                'message':'該驗證碼不存在。'
            })

        return send_file(text_to_png(veri.question+'='), mimetype='image/png')
    else:
        return jsonify({
                'ok':False,
                'message':'意料之外的错误。'
            })


# 测试验证码
@bp_api_verification.route('/test',methods=['POST','OPTIONS'])
@cross
def use():

    req = request.json
    # print(req)
    # 檢查參數是否齊全
    if not(('id' in req) and ('answer' in req)):
        return jsonify({
            'ok':False,
            'message':'不要非法侵入本站喔。'
        })

    # 查找驗證碼記錄
    _id = req['id']
    db = getSession()
    veri = db.query(Verification).filter(Verification.id == _id).first()
    if not veri:
        return jsonify({
            'ok':False,
            'message':'該驗證碼不存在。'
        })

    # 檢查驗證碼是否過期
    timestamp = veri.timestamp
    passed_time = int(str(time.time()).replace('.','')[0:13]) - int(timestamp)
    passed_time = int(passed_time/1000/60)
    # print (passed_time)
    if passed_time > 5:
        return jsonify({
            'ok':False,
            'message':'{0}分鍾過去了，你需要重新請求驗證碼。'.format(passed_time)
        })

    # 檢查驗證碼是否正確
    # print(veri.answer,req['answer'])
    if str(veri.answer) != str(req['answer']):
        return jsonify({
            'ok':False,
            'message':'驗證失敗，請檢查輸入。'
        })

    # 通過驗證
    return jsonify({
        'ok':True,
        'message':'驗證通過。'
    })


# 提供对外接口
def check(req=None,delete=False):
    
    if not req:
        return False
    # 檢查參數是否齊全
    if not(('id' in req) and ('answer' in req)):
        return False

    # 查找驗證碼記錄
    _id = req['id']
    db = getSession()
    veri = db.query(Verification).filter(Verification.id == _id).first()
    if not veri:
        return False

    # 檢查驗證碼是否過期
    timestamp = veri.timestamp
    passed_time = int(str(time.time()).replace('.','')[0:13]) - int(timestamp)
    passed_time = int(passed_time/1000/60)
    if passed_time > 5:
        return False

    # 檢查驗證碼是否正確
    if str(veri.answer) != str(req['answer']):
        return False

    if delete:
        # 刪除數據
        db.delete(veri)
        db.commit()

    # 通過驗證
    return True