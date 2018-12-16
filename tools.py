#coding=utf-8
import time
import hashlib

# 将字符串进行 md5 编码,或者返回时间戳的 md5 编码
def string_to_md5(string=None,mix=False):
    if not string:
        string=time.time()
    string = str(string)
    if mix:
        string = str(time.time()) + string
    return hashlib.md5(string.encode(encoding='UTF-8')).hexdigest()

def timestamp_to_yymmdd(timestamp=None):
    if timestamp:
        if len(str(timestamp)) == 13:
            timestamp = str(timestamp)[0:10]+'.000'
        return time.strftime('%Y-%m-%d',time.localtime(float(timestamp)))
    return time.strftime('%Y-%m-%d',time.localtime())

# print (timestamp_to_yymmdd())
# print(string_to_md5('123456789',mix=True))
