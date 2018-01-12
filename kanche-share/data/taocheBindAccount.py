#!python-env/bin/python
# -*- coding: UTF-8 -*-

__author__ = 'jesse'

import sys
import time
import urllib2

reload(sys)
if sys.stdout.encoding is None:
    import codecs

    writer = codecs.getwriter("utf-8")
    sys.stdout = writer(sys.stdout)

#看车帮api账号
ApiAccount = {
    'userName': 'kanchePlatForm',
    'secretkey': '5987E9595699774F338A'
}

def md5(str):
    import hashlib
    import types
    if type(str) is types.StringType:
        m = hashlib.md5()
        m.update(str)
        return m.hexdigest()
    else:
        return ''

#TODO:要改的参数
vendorcode = '100084566'


loginUrl = 'http://svc.taoche.cn/third/page/login.aspx'
authcode = ApiAccount['userName']
timestamp = str(int(time.time()))
secretkey  = ApiAccount['secretkey']
sign = md5(authcode + vendorcode + timestamp + secretkey)

loginUrl += '?authcode=' + authcode
loginUrl += '&timestamp=' + timestamp
loginUrl += '&sign=' + sign
loginUrl += '&vendorcode=' + vendorcode

print('**************')
print(loginUrl)

'''
try:
    req = urllib2.Request(loginUrl)
    res_data = urllib2.urlopen(req)
    print('res_data:' + str(res_data))
except :
    print('login error!')
'''
