#coding=utf-8
from flask import Flask,request,jsonify,make_response
from api.verification import bp_api_verification
from api.user import bp_api_user
from api.article import bp_api_article

# 创建 Flask 实例
app = Flask(__name__)
# 掛載藍圖
app.register_blueprint(bp_api_verification, url_prefix='/verification')
app.register_blueprint(bp_api_user, url_prefix='/user')
app.register_blueprint(bp_api_article, url_prefix='/article')

@app.route('/')
def page_index():
    return jsonify({
        'ok':True,
        'message':'API serve.'
    })

if __name__ == '__main__':
    app.run(threaded=True,debug=True,host='0.0.0.0',port=8080)