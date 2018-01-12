__author__ = 'qinying'

import top.api
import top
import requests


url = 'https://gw.api.tbsandbox.com/router/rest'
appkey = '23255590'
appsecret = '6a962c9b9606ee0e47c2b866fd1d68f2'

req = top.api.ItemAddRequest(url)
req.set_app_info(top.appinfo(appkey,appsecret))


try:
    resp= req.getResponse('23255590')
    print(resp)
except Exception,e:
    print(e)



def login():
	redirect_uri = 'http://www.kanche.cn'
	login_url = 'https://oauth.taobao.com/authorize?response_type=code&client_id=%s&redirect_uri=%s=1212&view=web' % (appkey, redirect_uri)
	# login_url = 'https://oauth.tbsandbox.com/authorize'
	# client_id = appkey
	# client_secret = appsecret
	h = requests.get(login_url)
	print(h.text)

if __name__ == '__main__':
    login()
