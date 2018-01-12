#!/usr/bin/python
# -*- coding: UTF-8 -*-

import re
import tz
import httplib
import urllib,urllib2
import lxml.html
import copy
import json
import errorcode
import errormsg
from cityTaoche import CityTaoche
from urlparse import urlparse
import logger
from base import BaseSharer
import random, string
from datetime import datetime
from decimal import Decimal
import subprocess
import os
import time

#看车帮公共账号
publicAccount = {
    "username": u"100060074@tc",
    "password": u"ktcc1qaz2wsx1"
}

HOST = "dealer.taoche.com"
##################
###不再维护
##################

class TaocheSharer(BaseSharer):
    def __init__(self, sessionServer, specServer):
        super(TaocheSharer, self).__init__(sessionServer, specServer)
        self.cityTaoche = CityTaoche()

        # self.taocheHeaders = copy.copy(self.headers)
        # self.taocheHeaders['Host'] = "http://dealer.taoche.com"

        self.headers["Referer"] = "http://dealer.taoche.com"
        self.AppId = ''
        self.taocheASPNET_SessionId = ''
        self.easypassASPNET_SessionId = ''
        self.AppKey = ''


    def setCookies(self, headers):
        for header in headers:
            if header[0].lower() == 'set-cookie':
                logger.debug("--header--\n" + str(header))
                set_cookies = header[1].split('; path=/, ')
                for set_cookie in set_cookies:
                    set_cookie = set_cookie.split('; ')
                    cookie = set_cookie[0].split('=')
                    if len(cookie) > 1:
                        self.cookies[cookie[0]] = cookie[1]
                    elif len(cookie) > 0:
                        self.cookies[cookie[0]] = ""
        ks = self.cookies.keys()
        cookie_list = []
        for k in ks:
            cookie_list.append(k + '=' + self.cookies[k])
        self.headers['Cookie'] = string.join(cookie_list, '; ')
        logger.debug(str(self.headers))

    '''
    # ==========================================
    # login 入口
    # ==========================================
    def doLogin(self, username, password):
        #GET http://dealer.taoche.com/content/html/login.html
        AppId = '59BCDCB7-1E37-4B95-9334-4E12A582156F'
        taocheLoginPage = self.taocheLoginPage()
        if taocheLoginPage:
            loginEasypass = self.loginEasypass(username, password, AppId)
            if loginEasypass:
                (success,  AppKey, AppValue, OP_UserID, Check_Code, radomCode, ClientIP) = self.loginGotoApp(AppId)
                if success:
                    loginOS = self.loginOS(AppKey, AppValue, OP_UserID, Check_Code, radomCode, ClientIP, AppId)
                    if loginOS:
                        loginHomeIndex = self.loginHomeIndex()
                        if loginHomeIndex:
                            return True
                        else:
                            logger.debug("-- error:loginHomeIndex headers--\n" + str(self.headers))
                            return False
                    else:
                        logger.debug("-- error:loginOS headers--\n" + str(self.headers))
                        return False
                else:
                    logger.debug("-- error:loginGotoApp headers--\n" + str(self.headers))
                    return False
            else:
                logger.debug("-- error:loginEasypass headers--\n" + str(self.headers))
                return False
        else:
            logger.debug("-- error:taocheLoginPage headers--\n" + str(self.headers))
            return False

    def taocheLoginPage(self):
        conn = httplib.HTTPConnection("dealer.taoche.com", timeout=10)
        url = '/content/html/login.html'
        conn.request("GET", url, headers=self.headers)
        res = conn.getresponse()
        result = self.decodeBody(res.getheaders(), res.read())
        self.setCookies(res.getheaders())
        if result.count(u'账号登录'):
            return True
        return False

    def loginEasypass(self, username, password, AppId):
        CheckCode = ''
        r = '0.09992716462829399'
        _ = str(int(time.time()))+'000'
        host = 'dealer.easypass.cn'
        uri = '/Interface/CheckUserNameInterface.aspx?UserName=%s&CheckCode=%s&Pwd=%s&autoLogin=true&appid=%s&r=%s&_=%s&urls='%(username, CheckCode, password, AppId, r, _)

        conn = httplib.HTTPConnection(host=host, timeout=10)
        conn.request(method="GET", url=uri, headers=self.headers)
        res = conn.getresponse()
        result = self.decodeBody(res.getheaders(), res.read())
        self.setCookies(res.getheaders())
        if result.count('redirectToPage'):
            return True
        return False

    def loginGotoApp(self, AppId):
        #'http://dealer.easypass.cn/gotoapp.aspx?appid=%s&r=635715395373697201' % (AppId)
        uri = '/gotoapp.aspx?appid=%s&r=635715395373697201' % (AppId)
        host = 'dealer.easypass.cn'
        conn = httplib.HTTPConnection(host=host, timeout=10)
        conn.request(method="GET", url=uri, headers=self.headers)
        res = conn.getresponse()
        result = self.decodeBody(res.getheaders(), res.read())
        dom = lxml.html.fromstring(result)
        self.setCookies(res.getheaders())
        if result.count('AppKey'):
            AppKey = dom.xpath('.//input[@id="AppKey"]/@value')[0]
            AppValue = dom.xpath('.//input[@id="AppValue"]/@value')[0]
            OP_UserID = dom.xpath('.//input[@id="OP_UserID"]/@value')[0]
            Check_Code = dom.xpath('.//input[@id="Check_Code"]/@value')[0]
            radomCode = dom.xpath('.//input[@id="radomCode"]/@value')[0]
            ClientIP = dom.xpath('.//input[@id="ClientIP"]/@value')[0]
            return (True, AppKey, AppValue, OP_UserID, Check_Code, radomCode, ClientIP)
        return (False, '', '' ,'', '', '', '')

    def loginOS(self, AppKey, AppValue, OP_UserID, Check_Code, radomCode, ClientIP, AppId):
        #url = 'http://dealer.taoche.com/oslogin.aspx?&urls='
        now = time.time()
        now = time.localtime(now)
        cTime = time.strftime("%Y/%m/%d %p:%I:%M:%S", now)
        ClientTime = cTime.replace('PM', '下午')
        ClientTime = ClientTime.replace('AM', '上午')
        if '0' == ClientTime[5]:
            ClientTime = cTime[:5] + cTime[6:]
        if '0' == ClientTime[7]:
            ClientTime = ClientTime[:7] + ClientTime[8:]

        ImitateUserID = ''
        SuperFlag = ''
        WeakOPUserID = ''

        formdata = {
            "AppKey": AppKey,
            "AppValue": AppValue,
            "Check_Code": Check_Code,
            "ClientIP": ClientIP,
            "ClientTime": ClientTime,
            "OP_UserID": OP_UserID,
            "radomCode": radomCode,
            'ImitateUserID': ImitateUserID,
            'SuperFlag': SuperFlag,
            'WeakOPUserID': WeakOPUserID
        }
        logger.debug(str(formdata))
        host = 'dealer.taoche.com'
        url = '/oslogin.aspx?&urls='
        headers = self.headers
        r = '635715395373697201'
        headers['Referer'] = 'http://dealer.easypass.cn/gotoapp.aspx?appid=%s&r=%s&urls=' % (AppId, r)
        conn = httplib.HTTPConnection(host=host, timeout=10)
        conn.request(method="POST", body=urllib.urlencode(formdata), url=url, headers=headers)
        res = conn.getresponse()
        result = self.decodeBody(res.getheaders(), res.read())
        self.setCookies(res.getheaders())
        if result.count('/Account/Login'):
            return True
        return False

    def loginHomeIndex(self):
        #url = 'http://dealer.taoche.com/Home/index'
        host = 'dealer.taoche.com'
        url = '/Home/index'
        conn = httplib.HTTPConnection(host=host, timeout=10)
        conn.request(method="GET", url=url, headers=self.headers)
        res = conn.getresponse()
        result = self.decodeBody(res.getheaders(), res.read())
        self.setCookies(res.getheaders())
        if result.count(u'车源浏览量'):
            return True
        return False
    '''




    def doLogin(self, username, password):

        # 代码示例
        # OtherLoginInfo=100060074%24 268785 %24100060074%40tc%24
        # import urllib
        # urllib.unquote('%24')
        # '$'

        taocheDealerIndexResult = self.taocheDealerIndex()

        if taocheDealerIndexResult:
            # autologin
            easypassAutoLoginIndexResult = self.easypassAutoLoginIndex()

            taocheSaveuserResult = self.taocheSaveuser(username, password)

            if easypassAutoLoginIndexResult and taocheSaveuserResult:
                easypassCheckUserNameInterfaceResult = self.easypassCheckUserNameInterface(username,password)
                if easypassCheckUserNameInterfaceResult:
                    # 第二步结果
                    (easypassCheckUserNameResult,location_url) = self.easypassHomeIndex302(self.AppId)

                    if easypassCheckUserNameResult:
                        # 第三步结果
                        (gotoReuslt,gotoString) = self.gotoApp(location_url)

                        if gotoReuslt:
                            # 第四步结果
                            (osLoginResult, taocheAccountUrl) = self.osLogin(gotoString, location_url)
                            if osLoginResult:
                                # 第五步结果
                                taocheLoginSuccessResult = self.taocheLoginSuccess(taocheAccountUrl)
                                if taocheLoginSuccessResult:
                                    return True
                                else:
                                    logger.debug("-- taocheLoginSuccessResult header--\n" + str(self.headers))
                                    return False
                            else:
                                logger.debug("-- osLoginResult headers--\n" + str(self.headers))
                                return False
                        else:
                            logger.debug("-- gotoReuslt headers--\n" + str(self.headers))
                            return False
                    else:
                        logger.debug("-- easypassCheckUserNameResult headers--\n" + str(self.headers))
                        return False
                else:
                    logger.debug("-- easypassCheckUserNameInterfaceResult headers--\n" + str(self.headers))
                    return False
            else:
                logger.debug("-- easypassAutoLoginIndexResult headers--\n" + str(self.headers))
                return False
        else:
            logger.debug("-- taocheDealerIndexResult headers--\n" + str(self.headers))
            return False

    # 第零步 获得AppId, ASP.NET_SessionId
    def taocheDealerIndex(self):

        conn = httplib.HTTPConnection("dealer.taoche.com", timeout=10)

        url = "/"

        conn.request("GET", url, headers=self.headers)
        res = conn.getresponse()

        # set taoche ASP.NET_SessionId]
        logger.debug(str(self.cookies))
        self.setCookies(res.getheaders())
        #self.taocheASPNET_SessionId = self.cookies['ASP.NET_SessionId']
        #print 'taocheASPNET_SessionId: ' + self.taocheASPNET_SessionId


        loginResult = self.decodeBody(res.getheaders(), res.read())
        print loginResult



        conn.close()

        # 从网页中获得appid 赋值给 self.AppId
        '''
        appidRe = re.search('var\ AppID\ \=\ \"(?P<appid>.*)\"', loginResult)
        self.AppId = appidRe.group('appid')
        '''
        self.AppId = '59BCDCB7-1E37-4B95-9334-4E12A582156F'
        logger.debug("appid=" + self.AppId)
        logger.debug("taocheDealerIndex_loginResult success")
        return True
   
    # 第一步 没有set cooikie, 只是验证用户名密码
    def taocheSaveuser(self,username, password):

        host = "dealer.taoche.com"
        conn = httplib.HTTPConnection(host, timeout=10)

        username = urllib.quote(unicode(username))
        password = urllib.quote(unicode(password))

        # url = "/pages/account/ajax/saveuser.ashx?"
        url = "/content/html/login.html"
        # url = url + 'u=' + username
        # url = url + '&p=' + password

        saveuserHeader = copy.copy(self.headers)
        saveuserHeader['Cookie'] = 'ASP.NET_SessionId='+self.taocheASPNET_SessionId+'; '
        # set taoche ASP.NET_SessionId
        print '====taocheSaveuser getheaders===='
        print saveuserHeader

        conn.request("GET", url, headers = saveuserHeader)
        res = conn.getresponse()



        loginResult = self.decodeBody(res.getheaders(), res.read())
        print '=====taocheSaveuser====='
        print res.getheaders()

        conn.close()

        print loginResult
        if not loginResult.count(u"账号登录"):
            logger.debug("taocheSaveuser = " + loginResult)
            return False
        logger.debug("taocheSaveuser success")        
        return True

    # 第二步 有用 easypass.cn setcoolie newLoginName 获得 easypass 的 ASP.NET_SessionId 
    def easypassAutoLoginIndex(self):

        host = "dealer.easypass.cn"
        conn = httplib.HTTPConnection(host, timeout=10)

        url = "/LoginPage/AutoLogin.aspx?"
        url = url + 'appid=' + self.AppId
        url = url + '&urls=&_=' + str(random.random())
        self.headers['Cookie'] = ''
        self.headers['Referer'] = 'http://dealer.taoche.com/'

        conn.request("GET", url, headers=self.headers)
        res = conn.getresponse()

        # set taoche ASP.NET_SessionId
        print '====easypassAutoLoginIndex getheaders===='
        print res.getheaders()

        self.setCookies(res.getheaders())

        self.easypassASPNET_SessionId = self.cookies['ASP.NET_SessionId']
        resStatus = res.status

        conn.close()


        print 'res.status'
        print resStatus
        if resStatus == 200:
            logger.debug("easypassAutoLoginIndex success= ")
            return True
        else:
            logger.debug("easypassAutoLoginIndex = " + res.status)
            return False

    # 第三步 easypass 检查用户名密码 set
    def easypassCheckUserNameInterface(self,username,password):

        conn = httplib.HTTPConnection("dealer.easypass.cn", timeout=10)
        url = "/Interface/CheckUserNameInterface.aspx?"

        username = urllib.quote(unicode(username))
        password = urllib.quote(unicode(password))
        url = url + 'UserName=' + username
        url = url + '&Pwd=' + password
        url = url + '&autoLogin=false'
        url = url + '&r=' + str(random.random())
        url = url + '&CheckCode=undefined'
        url = url + '&appid=' + self.AppId
        url = url + '&urls=&_=' + str(random.random())

        conn.request("GET", url, headers = self.headers)
        print url
        res = conn.getresponse()

        # set EasySystem Cookie; newLoginName
        self.setCookies(res.getheaders())
        print '====Cookie========'
        print self.headers['Cookie']

        loginResult = self.decodeBody(res.getheaders(), res.read())
        conn.close()

        print '=====CheckUserNameInterface====='
        print loginResult
        if not loginResult.startswith(u"redirectToPage('/HomeIndex.aspx?"):
            logger.debug("loginResult=" + loginResult)
            return False
        logger.debug("loginResult success=")
        return True

    # 第四步 这里302 跳转
    # it can be jump through because it's header is same as gotoAoo
    # http://dealer.easypass.cn/HomeIndex.aspx?autoLogin=false&appid=59BCDCB7-1E37-4B95-9334-4E12A582156F&urls=
    def easypassHomeIndex302(self, appid):

        host = 'dealer.easypass.cn'
        conn = httplib.HTTPConnection(host, timeout=10)
        url = "/HomeIndex.aspx?"
        url = url + 'autoLogin=false'
        url = url + '&appid=' + self.AppId
        url = url + '&urls='

        print '\n'
        print '====HomeIndex before Cookie========'
        print url
        print self.cookies

        conn.request("GET", url, headers = self.headers)
        res = conn.getresponse()

        # set loginKey; loginName, isAuto
        self.setCookies(res.getheaders())
        print '\n'
        print '====HomeIndex after Cookie========'
        print self.headers['Cookie']

        if "location" in str(res.getheaders()):
            for header in res.getheaders():
                if header[0].lower() == 'location':
                    location_url = "http://" + host + header[1]
                    print '====HomeIndex jump location Cookie========'
                    print location_url

                    conn.close()
                    return True, location_url

        # 跳转失败
        conn.close()
        return False,'error'

    # 第五步 跳转完返回 全局的 AppKey
    # http://dealer.easypass.cn/gotoapp.aspx?appid=59BCDCB7-1E37-4B95-9334-4E12A582156F&r=635443862117389951&urls=
    def gotoApp(self, location_url):

        conn = httplib.HTTPConnection("dealer.easypass.cn", timeout=10)

        conn.request("GET", location_url, headers = self.headers)
        res = conn.getresponse()

        # set 268785; Api.Client.Current.UserKey; Api.Client.Current.UserSerect
        self.setCookies(res.getheaders())
        print '\n'
        print '====GotoApp after Cookie========'
        print self.headers['Cookie']

        loginResult = self.decodeBody(res.getheaders(), res.read())

        print '\n'
        print '=====gotoApp====='
        # print loginResult
        print loginResult.count('oslogin.aspx')

        conn.close()

        if not loginResult.count('oslogin.aspx'):
            logger.debug("gotoApp=" + loginResult)
            return False, 'error'

        logger.debug("gotoApp success")
        return True, loginResult

    # 第六步 构造login form post 过去
    def osLogin(self, fromString, referer):

        host = 'dealer.taoche.com'
        getDom = lxml.html.fromstring(fromString)
        mtime = datetime.now()


        AppKey = getDom.xpath('.//input[@id="AppKey"]/@value')[0]
        AppValue = getDom.xpath('.//input[@id="AppValue"]/@value')[0]
        OP_UserID = getDom.xpath('.//input[@id="OP_UserID"]/@value')[0]
        Check_Code = getDom.xpath('.//input[@id="Check_Code"]/@value')[0]
        radomCode = getDom.xpath('.//input[@id="radomCode"]/@value')[0]
        ClientIP = getDom.xpath('.//input[@id="ClientIP"]/@value')[0]
        ClientTime = mtime.ctime()

        # 从 easypass.cn 拿到的AppKey 下面会用到
        self.AppKey = AppKey

        formData = {"AppKey": AppKey, "AppValue": AppValue, "OP_UserID": OP_UserID, "Check_Code":Check_Code, "radomCode":radomCode, "ClientIP":ClientIP,"ClientTime":ClientTime}
        formStr = urllib.urlencode(formData)

        print '\n'
        print formData
        conn = httplib.HTTPConnection(host, timeout=10)
        postUrl = '/oslogin.aspx?urls='
        osLoginheaders = copy.copy(self.headers)

        osLoginheaders['Host'] = host
        osLoginheaders['Referer'] = referer
        osLoginCookie = {} #copy.copy(self.cookies)
        osLoginCookie['ASP.NET_SessionId'] = self.taocheASPNET_SessionId
        # osLoginCookie['ASP.NET_SessionId'] = 'epscads2zlp5nhkcligw1ieo'
        # osLoginCookie['lv'] = '1408782186056'
        # osLoginCookie['ss'] = '1408782186056'
        # osLoginCookie['Hm_lvt_4e3b095bc33309060d0ad48697589c51'] = '1408760965,1408762594,1408767082,1408777458'
        # osLoginCookie['Hm_lpvt_4e3b095bc33309060d0ad48697589c51'] = '1408782186'

        osLoginheaders['Cookie'] = string.join(['%s=%s;' % (key, value) for (key, value) in osLoginCookie.items()])

        # osLoginheaders['Cookie'] = 'ASP.NET_SessionId=d4yhjmgxjvpdheshjvnxkgmv; WT_FPC=id=2955eebab3cb15c482a1408782186056:lv=1408787678914:ss=1408787678914; Hm_lvt_4e3b095bc33309060d0ad48697589c51=1408762594,1408767082,1408777458,1408782211; Hm_lpvt_4e3b095bc33309060d0ad48697589c51=1408787679'

        print '\n'
        print '======osLogin post header====='
        print osLoginheaders
        print formStr

        osLoginheaders['Content-Type'] = 'application/x-www-form-urlencoded;'

        conn.request("POST", postUrl, formStr, headers = osLoginheaders)
        res = conn.getresponse()
        print '======osLogin getheaders====='
        print res.getheaders()
        self.setCookies(res.getheaders())

        loginResult = self.decodeBody(res.getheaders(), res.read())
        print '=====osLogin====='
        print loginResult

        conn.close()

        if "location" in str(res.getheaders()):
            for header in res.getheaders():
                if header[0].lower() == 'location':
                    if header[1].count('/Account/Login'):
                        location_url = header[1]
                        print '====osLogin jump location Cookie========'
                        print location_url
                        return True, location_url

        return False, 'error'

    # 第七步 判断是不是真正的login success
    def taocheLoginSuccess(self, location_url):

        conn = httplib.HTTPConnection("dealer.taoche.com", timeout=10)

        taocheLoginCookie = copy.copy(self.cookies)
        taocheLoginCookie['ASP.NET_SessionId'] = self.taocheASPNET_SessionId
        # taocheLoginCookie['.ASPXAUTH'] = self.cookies['EasySystem']
        taocheLoginCookie['OPUserID'] = 0
        UserKey = 'Api.Client.Current.UserKey_'+self.AppId
        taocheLoginCookie['UserKey'] = self.AppKey
        # request header

        taocheLoginHeader = copy.copy(self.headers)
        taocheLoginHeader['Cookie'] = string.join(['%s=%s;' % (key, value) for (key, value) in taocheLoginCookie.items()])

        print '====taocheLoginSuccess before Cookie========'
        print taocheLoginHeader['Cookie']

        conn.request("GET", location_url, headers=taocheLoginHeader)
        print location_url
        res = conn.getresponse()

        # set ASP.NET_SessionId; ASPXAUTH, Api.Client.Current.UserKey; Api.Client.Current.UserSerect
        self.setCookies(res.getheaders())
        print '\n'
        print '====taocheLoginSuccess after Cookie========'
        print self.headers['Cookie']

        loginResult = self.decodeBody(res.getheaders(), res.read())

        conn.close()

        print '\n'
        print '=====taocheLoginSuccess====='

        # 发布车源
        if not loginResult.count(u'发布车源'):
            logger.debug("taocheLogin=" + loginResult)
            return False

        print "==== dealer.taoche.com login success ===="

        location_url = '/Home/Index'
        conn = httplib.HTTPConnection("dealer.taoche.com", timeout=10)
        conn.request("GET", location_url, headers=taocheLoginHeader)
        res = conn.getresponse()
        loginResult = self.decodeBody(res.getheaders(), res.read())

        conn.close()
        logger.debug("taocheLogin success")
        return True



    # ==========================================
    # shareVehicle 入口
    # ==========================================

    def shareVehicle(self, shareJob):
        shareAccount = shareJob.get("share_account", None)
        if shareAccount is None:
            return errorcode.DATA_ERROR, errormsg.SHARE_ACCOUNT_EMPTY
        if shareAccount.get('account_type', None) == 'public':
            shareAccount['username'] = publicAccount['username']
            shareAccount['password'] = publicAccount['password']

        logger.debug("taoche shareVehicle")

        # =========================
        # get or set session

        cookies = self.sessionServer.getSession('taoche', shareAccount['username'])
        if cookies is None:
            res = self.doLogin(shareAccount['username'], shareAccount['password'])
            if not res:
                logger.debug("login error")
                return errorcode.AUTH_ERROR, errormsg.LOGIN_FAIL
            #self.sessionServer.setSession('taoche', shareAccount['username'], self.cookies)
        else:
            self.cookies = cookies
            ks = self.cookies.keys()
            cookie_list = []
            for k in ks:
                cookie_list.append(k + '=' + self.cookies[k])
            self.headers['Cookie'] = string.join(cookie_list, '; ')

        logger.debug("self.cookies" + str(self.cookies))

        # =========================
        # get vehicle

        vehicle = shareJob.get("vehicle", None)
        merchantSubstituteConfig = shareJob.get("merchant_substitute_config", None)

        externalSpec = shareJob.get("external_vehicle_spec", None)

        if vehicle is None:
            logger.error("sharejob vehicle missing")
            return errorcode.DATA_ERROR, errormsg.VEHICLE_EMPTY

        user = vehicle.get("user", None)
        if user is None:
            logger.error("sharejob user missing")
            return errorcode.DATA_ERROR, errormsg.USER_EMPTY

        (name, mobile) = self.getContact(shareJob)

        # =========================
        # get provice and city code and name
        merchant = vehicle.get('merchant', None)
        address = merchant.get('address', None)
        if address is None:
            logger.error("sharejob address missing")
            return errorcode.DATA_ERROR, errormsg.ADDRESS_EMPTY
        provinceCode = address.get('province_code', None)
        if provinceCode is None:
            logger.error("sharejob province missing")
            return errorcode.DATA_ERROR, errormsg.PROVINCE_EMPTY
        cityCode = address.get('city_code', None)
        if cityCode is None:
            logger.error("sharejob city missing")
            return errorcode.DATA_ERROR, errormsg.CITY_EMPTY

        taocheProvinceCode = self.cityTaoche.getProvinceCode(provinceCode)
        taocheProvinceName = self.cityTaoche.getProvinceName(provinceCode)
        taocheCityCode = self.cityTaoche.getCityCode(cityCode)
        taocheCityName = self.cityTaoche.getCityName(cityCode)


        if taocheProvinceCode is None:
            logger.error(str(provinceCode) + "provinceCode not match")
            return errorcode.DATA_ERROR, str(provinceCode) + "无法匹配到淘车的省级代码"
        if taocheProvinceName is None:
            logger.error(str(provinceCode) + "provinceName not match")
            return errorcode.DATA_ERROR, str(provinceCode) + "无法匹配到淘车的省级名称"
        if taocheCityCode is None:
            logger.error(str(cityCode) + "cityCode not match")
            return errorcode.DATA_ERROR, str(cityCode) + "无法匹配到淘车的城市代码"
        if taocheCityName is None:
            logger.error(str(cityCode) + "cityName not match")
            return errorcode.DATA_ERROR, str(cityCode) + "无法匹配到淘车的城市名称"

        # =========================
        # 第一联系人

        # salesid = '292397'
        salesid = self.getSaleId(name,mobile)
        if salesid is None:
            logger.error("salesid missing")
            return errorcode.LOGIC_ERROR, errormsg.SALEID_EMPTY
        logger.debug("salesid=" + salesid)

        # =========================
        # 第二联系人
        salesSecondId = ""
        if merchantSubstituteConfig is not None:
            extraContact = merchantSubstituteConfig.get("extra_contact", None)
            if extraContact is not None:
                phone = extraContact.get("phone",None)
                if phone is not None:
                    salesSecondId = self.getSaleSecondId(extraContact.get("name"), extraContact.get("phone"))
                    if salesSecondId is None:
                        logger.error("salesSecondId missing")
                    logger.debug("salesSecondId=" + salesSecondId)


        # =========================
        # get spec
        # big part
        spec = vehicle.get("spec", None)
        summary = vehicle.get("summary", None)
        desc = vehicle.get("desc", None)

        if spec is None:
            logger.error("vehicle spec missing")
            return errorcode.DATA_ERROR, errormsg.VEHICLE_SPEC_EMPTY

        if summary is None:
            logger.error("vehicle summary missing")
            return errorcode.DATA_ERROR, errormsg.VEHICLE_SUMMARY_EMPTY

        if desc is None:
            logger.error("vehicle desc missing")
            return errorcode.DATA_ERROR, errormsg.VEHICLE_SUMMARY_EMPTY

        # small part

        # spec
        levelId = spec.get("level_id", None)
        if levelId is None:
            logger.error("levelId missing")
            return errorcode.DATA_ERROR, errormsg.VEHICLE_SPEC_EMPTY
        logger.debug("levelId=" + levelId)


        # viewState
        conn = httplib.HTTPConnection(HOST, timeout=10)
        conn.request("GET", 'http://dealer.taoche.com/Pages/carsource/sellcar.aspx', headers = self.headers)
        res = conn.getresponse()
        pageResult = self.decodeBody(res.getheaders(), res.read())
        conn.close()

        getDom = lxml.html.fromstring(pageResult)
        VIEWSTATE = getDom.xpath('.//input[@id="__VIEWSTATE"]/@value')[0]

        # 从网页中获得 url 车辆显示的URL


        # =========================
        # make photoList

        # =========================
        # make form
        # ctl00$ContentPlaceHolder 可能都没用
        form = {}
        form['__VIEWSTATE'] = VIEWSTATE
        form['__SCROLLPOSITIONX'] = 0
        form['__SCROLLPOSITIONY'] = 2045
        form['__EVENTTARGET'] = 'ctl00$ContentPlaceHolder1$btnSubmit'
        form['__EVENTARGUMENT'] = ''

        #一句话标题
        form['ctl00$ContentPlaceHolder1$txtCarTitle'] = '一证在手 把车贷走'

        # 车型库匹配
        form['ctl00$ContentPlaceHolder1$hidSelfCarId'] = 0
        form['ctl00$ContentPlaceHolder1$hidMainBrandId'] = externalSpec.get("brand").get("id", None)
        form['ctl00$ContentPlaceHolder1$hidMainBrandName'] = externalSpec.get("brand").get("name", None) #'奥迪'
        form['ctl00$ContentPlaceHolder1$hidMainBrandGroup'] = externalSpec.get("brand").get("fchar", None) 
        form['ctl00$ContentPlaceHolder1$hidSerialId'] = externalSpec.get("series").get("id", None)
        form['ctl00$ContentPlaceHolder1$hidSerialName'] = externalSpec.get("series").get("name", None)
        form['ctl00$ContentPlaceHolder1$hidCarId'] = externalSpec.get("model").get("id", None)
        form['ctl00$ContentPlaceHolder1$hidCarGroup'] = externalSpec.get("model").get("year", None)
        combineCarName = externalSpec.get("model").get("year", None)[2:] + externalSpec.get("model").get("name", None)
        form['ctl00$ContentPlaceHolder1$hidCarName'] = combineCarName
        form['ctl00$ContentPlaceHolder1$hidSerialGroup'] = externalSpec.get("vendor").get("name", None)
        form['inputGearBox'] = externalSpec.get("summary").get("gear", '自动')

        form['ctl00$ContentPlaceHolder1$hidEditOrAdd'] = '1'
        form['ctl00$ContentPlaceHolder1$hidBasicSetCarId'] = ''
        form['ctl00$ContentPlaceHolder1$hidBasicSets'] = ''
        form['ctl00$ContentPlaceHolder1$selExhaustValue'] = '-1'
        form['ctl00$ContentPlaceHolder1$txtEvalue'] = ''
        # 车型配置 自定义
        # form['basicSet'] = [1,4,5,6,8,9,10,12]
        form['ctl00$ContentPlaceHolder1$hidStandardCarTypeConfig'] = 000000000000000000
        form['ctl00$ContentPlaceHolder1$txtSelfConfig'] = '最多可输入3个配置，逗号隔开'
        #color and innercolor
        form['ctl00$ContentPlaceHolder1$hidColor'] = self.getColorCode(vehicle)
        form['innerColor'] = self.getInterior(vehicle)
        form['ctl00$ContentPlaceHolder1$hidInnerColor'] = self.getInterior(vehicle)
        form['isLicensed'] = 1
        form['ctl00$ContentPlaceHolder1$hidIsLicensed'] = 1
        form['ctl00$ContentPlaceHolder1$txtDrivingMileage'] = self.getMileage(vehicle)

        # get location and dom pass

        # TODO 地区匹配
        form['ctl00$ContentPlaceHolder1$txtLicenseCity'] = taocheCityName
        form['ctl00$ContentPlaceHolder1$hidLicenseProviceId'] = taocheProvinceCode
        form['ctl00$ContentPlaceHolder1$hidLicenseCityId'] = taocheCityCode
        form['ctl00$ContentPlaceHolder1$hidLicenseProviceName'] = taocheProvinceName
        form['ctl00$ContentPlaceHolder1$hidLicenseCityName'] = taocheCityName
        form['ctl00$ContentPlaceHolder1$hidLicenseProviceIndex'] = 0.06451612903225806
        form['ctl00$ContentPlaceHolder1$hidLicenseCityIndex'] = 1
        form['ctl00$ContentPlaceHolder1$hidLicenseBakProviceId'] = taocheProvinceCode

        form['ctl00$ContentPlaceHolder1$hidLicenseCityIndex'] = 1
        form['ctl00$ContentPlaceHolder1$hidLicenseBakProviceId'] = taocheProvinceCode

        # 3个时间 上牌时间 年检有效期 商业保险有效期
        registrationDate = vehicle.get("vehicle_date").get("registration_date").astimezone(tz.HKT)
        if registrationDate is not None:
            form['ctl00$ContentPlaceHolder1$hidBuyCarDate'] = str(registrationDate.year) + '-' + str(registrationDate.month) + '-1'

        inspectionDate = vehicle.get("vehicle_date").get("inspection_date")
        if inspectionDate is not None:
            form['ctl00$ContentPlaceHolder1$hidExamineExpireDate'] = str(inspectionDate.year) + '-' + str(inspectionDate.month) + '-1'

        commercialInsuranceExpireDate = vehicle.get("vehicle_date").get("commercial_insurance_expire_date")
        if commercialInsuranceExpireDate is not None:
            form['ctl00$ContentPlaceHolder1$hidInsuranceExpireDate'] = str(commercialInsuranceExpireDate.year) + '-' + str(commercialInsuranceExpireDate.month) + '-1'
        else:
            form['ctl00$ContentPlaceHolder1$hidInsuranceExpireDate'] = str(inspectionDate.year) + '-' + str(inspectionDate.month) + '-1'

        # 图片视频
        form['isCards'] = 1
        form['ctl00$ContentPlaceHolder1$hidIsCards'] = 1
        form['ctl00$ContentPlaceHolder1$txtVinCode'] = self.getVehicleVin(vehicle)
        form['ctl00$ContentPlaceHolder1$hidDriveLicensePic'] = self.uploadDrivingLicense(vehicle.get("summary",None))
        form['ctl00$ContentPlaceHolder1$hidvideojson'] = '{"videoid":"0"}'
        form['ctl00$ContentPlaceHolder1$hiduploadedVideoid'] = 0
        form['ctl00$ContentPlaceHolder1$hiduploadingVideoid'] = ''

        # TODO NEW 特色服务
        form['hiddelysuitId'] = 46 # 特色服务 默认
        form['hidservicetd_1'] = 0 #原厂质保
        form['hidservicetd_2'] = self.getQualityAssuranceTime(merchantSubstituteConfig)#延长质保
        form['hidservicetd_3'] = self.getIncludeTransferFee(vehicle)
        form['hidservicetd_1_date'] = ''
        form['hid_WarrantTime'] = ''

        # 保障车源
        consumerGuarantee = self.getConsumerGuarantee(merchantSubstituteConfig)
        form['r_iswp'] = consumerGuarantee
        form['hid_iswp'] = consumerGuarantee
        if consumerGuarantee is 1:
            inspectionList = self.uploadInspectionReport(shareJob, merchantSubstituteConfig)
            form['ctl00$ContentPlaceHolder1$hidJcImageJson'] = json.dumps(inspectionList)


        # 一句话说明
        form['ctl00$ContentPlaceHolder1$txtSlogan'] = self.getDescBrief(vehicle.get("desc", None))

        # 运营类型
        form['carType'] = self.getUsage(vehicle)
        form['ctl00$ContentPlaceHolder1$hidCarType'] = self.getUsage(vehicle)

        # 定期保养
        form['maintainRecord'] = self.getMaintenance(vehicle)
        form['ctl00$ContentPlaceHolder1$hidMaintainRecord'] = self.getMaintenance(vehicle)

        # 3个不知道有用么
        form['ctl00$ContentPlaceHolder1$txtZBMonth'] = ''
        form['ctl00$ContentPlaceHolder1$txtZBMileage'] = ''
        form['ctl00$ContentPlaceHolder1$hidTransferAgent'] = ''

        form['ctl00$ContentPlaceHolder1$txtStateDescription'] = self.getContentVal_taoche(shareJob, Symbol='\r\n')
        form['ctl00$ContentPlaceHolder1$txtDisplayPrice'] = self.getQuotedPrice(vehicle)
        form['ctl00$ContentPlaceHolder1$txtLowestPrice'] = self.getQuotedPrice(vehicle)

        form['ctl00$ContentPlaceHolder1$ddlLinkman'] = salesid
        form['ctl00$ContentPlaceHolder1$hidDvlId'] = salesid
        form['ctl00$ContentPlaceHolder1$ddlLinkman2'] = salesSecondId
        form['ctl00$ContentPlaceHolder1$hidDvlId2'] = salesSecondId
        form['ctl00$ContentPlaceHolder1$hidHasSecondLinkman'] = 1 #0 没有 1 有
        # form['ctl00$ContentPlaceHolder1$hiddealerservice'] = self.getQuotedPriceIncludeTransferFee(vehicle)
        form['ctl00$ContentPlaceHolder1$hidDraftId'] = ''
        # form['ctl00$ContentPlaceHolder1$hidapplayservice'] = '1,2,3,4,5,6,7,'


        gallery = vehicle.get("gallery", None)
        if gallery is None:
            logger.error("gallery missing")
            return errorcode.DATA_ERROR, errormsg.PHOTO_NOT_ENOUGH
        photoList = self.uploadPics(gallery.get("photos", []))
        photoJson = json.dumps(photoList)

        form['ctl00$ContentPlaceHolder1$hidImageJson'] = photoJson

        logger.debug(photoJson)


        (success, msg, extra) = self.postVehicle(shareJob, form)
        if success:
            # self.deleteNewContact(salesid)
            return errorcode.SUCCESS, msg, extra
        return errorcode.SITE_ERROR, errormsg.SITE_OTHER_ERROR

    @staticmethod
    def makePhotos(photoList):
        photos = []
        for photo in photoList:
            photos.append(photo)
        return ",".join(photos)

    @staticmethod
    def getColorCode(vehicle):
        color = vehicle.get("summary").get('color')
        if color is None:
            logger.error("color missing")
            return errorcode.DATA_ERROR, errormsg.VEHICLE_SUMMARY_EMPTY
        logger.debug("color=" + color)

        colorCode = "黑色"
        colorTable = {"black": "黑色", "white": "白色", "red": "红色", "yellow": "黄色", "multi":"多彩色", "orange": "橙色",
                    "brown":"咖啡色", "blue": "蓝色", "green": "绿色", "purple": "紫色", "silver": "银灰色", "grey": "深灰色",
                      "champagne": "香槟色", "other": "其它"}

        colorCode = colorTable.get(color, "黑色")
        return colorCode

    def getMileage(self,vehicle):
        mileage = vehicle.get("summary").get("mileage", None)
        if mileage is None:
            logger.error("mileage missing")
            return errorcode.DATA_ERROR, errormsg.VEHICLE_SUMMARY_EMPTY
        logger.debug("mileage=" + str(mileage))
        result = Decimal(mileage) / Decimal(10000)
        if result >= 60:
            result = 60
        return result

    def getQuotedPrice(self,vehicle):
        quotedPrice = vehicle.get("price").get("quoted_price", None)
        if quotedPrice is None:
            logger.error("quotedPrice missing")
            return errorcode.DATA_ERROR, errormsg.VEHICLE_SUMMARY_EMPTY
        quotedPrice = int(round(Decimal(quotedPrice) / 100) * 100)
        logger.debug("quotedPrice=" + str(quotedPrice))
        return Decimal(quotedPrice) / Decimal(10000)

    def getInterior(self,vehicle):
        interior = vehicle.get("summary").get("interior", None)
        interiorString = '深'
        if interior is None:
            logger.error("interior missing")
            return interiorString
            # return errorcode.DATA_ERROR, ""
        else:
            if interior.count(u'浅') or interior.count(u'light'):
                interiorString = '浅'
            elif interior.count(u'深') or interior.count(u'dark'):
                interiorString = '深'
            else:
                interiorString = '深'

        logger.debug("interior=" + interiorString)
        return interiorString

    def getQuotedPriceIncludeTransferFee(self, vehicle):
        transferFee = vehicle.get("price").get("quoted_price_include_transfer_fee", None)
        transferFeeString = ''
        if transferFee is None:
            transferFeeString = '000000'
        else:
            if transferFee is True:
                transferFeeString = '0001000'
            else:
                transferFeeString = '000000'
                
        return transferFeeString

    # 4S店定期保养:2 无4S店定期保养:1
    def getMaintenance(self,vehicle):
        maintenance = vehicle.get("summary").get("maintenance", None)
        if maintenance is True:
            maintenance = 2
        else:
            maintenance = 1
        return maintenance


    def getUsage(self, vehicle):
        # 非营运 0, 营运1, 营转非2, 租赁4    
        purpose = vehicle.get("summary").get("purpose")
        if purpose is None:
            logger.error("purpose missing")
            return errorcode.DATA_ERROR, errormsg.VEHICLE_SUMMARY_EMPTY
        logger.debug("purpose=" + purpose)

        if purpose == "business":
            return 1
        if purpose == "personal":
            return 0
        if purpose == "lease":
            return 4
        return 0

    def getContentVal_taoche(self, shareJob):
        Symbol = "\r\n"
        lateral = "——"*23
        externalSpec = shareJob['external_vehicle_spec']
        share_account = shareJob.get("share_account", None)
        model = externalSpec.get('model', None)
        key = model.get('key', None)
        content = ''
        vehicle = shareJob.get('vehicle', None)
        desc = vehicle.get('desc', None)

        merchantDisable = True  #默认不填写
        vehicleDisable = False  #默认填写
        globalDisable = False   #默认填写
        merchant_substitute_config = shareJob.get('merchant_substitute_config', None)
        if merchant_substitute_config is not None:
            description_switch = merchant_substitute_config.get('description_switch', None)
            if description_switch is not None:
                merchantDisable = description_switch.get('merchant_disable', None)
                if merchantDisable is None:
                    merchantDisable = True
                vehicleDisable = description_switch.get('vehicle_disable', None)
                if vehicleDisable is None:
                    vehicleDisable = False
                globalDisable = description_switch.get('global_disable', None)
                if globalDisable is None:
                    globalDisable = False

        # 采用商家说明 追加
        if False == merchantDisable:
            description = ""
            description_list = merchant_substitute_config.get('description_list', None)
            if description_list is not None:
                for i in description_list:
                    site = i.get('site', None)
                    if site == 'taoche.com':
                        description = i.get('description', None)
                        description = string.replace(description, '\n', Symbol)
            content += description
            content += Symbol + str(vehicle['_id'])

        # 统一说明 追加
        if globalDisable == False:
            if share_account.get("account_type", None) == "substitute":
                content += Symbol*2 + '看车网，发现二手好车。提供专业的咨询和购车指导，保证车源信息真实准确。二手车质量我们保证 !' + Symbol
                content += '（更多信息请来电咨询400-895-0101）' + Symbol*2

        # 每辆车说明 追加
        if vehicleDisable == False:
            content += lateral + Symbol*2
            content += '看车网车辆编号: '+str(shareJob.get('series_number', None)) + Symbol*2

            if not (model is None) and not (key is None):
                content += "[ 车辆名称 ]" + Symbol
                if externalSpec['model']['key'] == '0':
                    vehicleSpec = shareJob['vehicle']['spec']
                    content += (externalSpec['brand']['name'] + externalSpec['series']['name'] + u' ' + vehicleSpec['sale_name'] + u'' + vehicleSpec['year_group']) + Symbol*2
                else:
                    content += (externalSpec['brand']['name'] + externalSpec['series']['name'] + u' ' + externalSpec['model']['name']) + Symbol*2

            #车况说明
            condition =  "乘坐空间宽敞，储物空间充足;"
            condition = condition + "转向清晰，指向精准;" + Symbol
            condition = condition + "提速表现优秀，动力源源不断;" + Symbol
            condition = condition +"车身有少量、轻微划痕或者局部补漆的情况，不超过3处;" + Symbol
            condition = condition + "车辆内部后备箱内干净整洁，内饰及座椅无磨损、污渍;" + Symbol
            condition = condition + "油耗低，节能环保；座椅舒适度上乘，车内无噪音;"


            #亮点配置
            vehicle = shareJob.get("vehicle", None)
            highlight_dict = {
                "sunroof": u"天窗",
                "panoramicSunroof": u"全景天窗",
                "GPS": u"GPS导航",
                "reverseImage": u"倒车影像",
                "childSafetyLock": u"儿童锁",
                "xenonHeadlights": u"氙气大灯",
                "turboCharged": u"涡轮增压",
                "fourWheelDiskBrakes": u"四轮碟刹",
                "leatherSeats": u"真皮座椅",
                "ESP": u"ESP",
                "automaticParking": u"自动泊车",
                "cruise": u"定速巡航",
                "automaticAirConditioning": u"自动空调",
                "airPurifier": u"空气净化器",
                "childSeatInterface": u"儿童座椅接口",
                "keyless": u"无钥匙启动",
                "TPMS": u"胎压监测",
                "powerSeats": u"电动座椅",
                "paddles": u"换档拨片"
            }

            desc = vehicle.get("desc", None)
            highlight_list = desc.get("highlight_list", None)
            highlight_show_name_list = []
            if highlight_list is not None:
                highlight_str = ""
                for highlight in highlight_list:
                    if highlight.get("selected", False) is False:
                        continue
                    highlight_name = highlight.get("name", None)
                    if highlight_name is None:
                        continue
                    show_name = highlight_dict.get(highlight_name, None)
                    if show_name is None:
                        continue
                    highlight_show_name_list.append(show_name)

                for name in highlight_show_name_list:
                    highlight_str += name + "、"

            if len(highlight_show_name_list):
                content += "[ 亮点配置 ] " + Symbol + highlight_str + Symbol*2 + "[ 车况说明 ] " + condition + Symbol*2
            else:
                content += "[ 车况说明 ] " + Symbol + condition + Symbol*2

            content +=  lateral
            content +=  Symbol*4

        content += str(vehicle['_id'])
        if "" == content:
            content = u"无车辆说明，请添加至10个字以上"
        return content


    # ==========================================
    # postVehicle main
    # ==========================================

    def postVehicle(self, shareJob, form):
        logger.debug(form)

        conn = httplib.HTTPConnection(HOST, timeout=10)
        headers = copy.copy(self.headers)
        headers['Content-Length'] = len(form)

        boundaryHeader = "------WebKitFormBoundary" + self.random_str(16)
        headers['Referer'] = 'http://dealer.taoche.com/Pages/carsource/sellcar.aspx'
        headers['Host'] = HOST
        headers["Content-Type"] = "multipart/form-data; boundary=" + boundaryHeader

        formString = ''
        boundary = "--" + boundaryHeader

        for (key,value) in form.items():
            formString += boundary + '\r\n' + 'Content-Disposition: form-data; name="'+key+'"\r\n\r\n'
            formString += str(value) + "\r\n"

        formString += boundary + "--"

        headers['Content-Length'] = len(formString)

        conn.request("POST", "/Pages/carsource/sellcar.aspx", formString, headers=headers)
        res = conn.getresponse()
        result = self.decodeBody(res.getheaders(), res.read())
        logger.debug(result)
        resH = res.getheaders()
        status = res.status
        conn.close()



        if "location" in str(res.getheaders()):
            for header in res.getheaders():
                if header[0].lower() == 'location':
                    if header[1].count('carsource/ok.aspx?ucarid'):
                        # 获得跳转的URL
                        conn = httplib.HTTPConnection(HOST, timeout=10)
                        conn.request("GET", header[1], headers = self.headers)
                        res = conn.getresponse()
                        pageResult = self.decodeBody(res.getheaders(), res.read())
                        conn.close()

                        # 从网页中获得 url 车辆显示的URL
                        buyer = "http://www.taoche.com/buycar/"
                        carUrlRe = re.search(buyer+'(?P<carUrl>.*)\"', pageResult)
                        carUrl = buyer + carUrlRe.group('carUrl')
                        logger.debug("taoche url = "+carUrl)

                        ucaridRe = re.search('ucarid\=(?P<ucarid>.*)\&', header[1])
                        ucarid = ucaridRe.group('ucarid')
                        result_url = "http://dealer.taoche.com/Pages/carsource/carinfo.aspx?ucarid="+ucarid
                        logger.debug("backend url=" + result_url)

                        return True, carUrl, result_url

        return False, "", ""

    # ==========================================
    # upload pic
    # ==========================================

    def uploadPicContent(self, content):
        host = '59.151.102.110'
        conn = httplib.HTTPConnection(host, timeout=10)
        headers = copy.copy(self.headers)

        boundaryHeader = "------WebKitFormBoundary" + self.random_str(16)
        headers['Referer'] = 'http://dealer.taoche.com/Pages/carsource/sellcar.aspx'
        headers['Host'] = host
        headers["Content-Type"] = "multipart/form-data; boundary=" + boundaryHeader
        del headers['Cookie']
        headers['Origin'] = 'http://dealer.taoche.com'

        formString = ''
        picname = self.random_str(16) + ".jpg"
        boundary = "--" + boundaryHeader

        formString += boundary + '\r\n' + 'Content-Disposition: form-data; name="Filename"\r\n\r\n'
        formString += picname + "\r\n"
        formString += boundary + '\r\n' + 'Content-Disposition: form-data; name="app"\r\n\r\n'
        formString += "02\r\n"
        formString += boundary + '\r\n' + 'Content-Disposition: form-data; name="callback"\r\n\r\n'
        formString += "api\r\n"
        formString += boundary + '\r\n' + 'Content-Disposition: form-data; name="pic"; filename="'+picname+'"\r\n'
        formString += "Content-Type: application/octet-stream\r\n\r\n"
        formString += content + "\r\n"
        formString += boundary + '\r\n' + 'Content-Disposition: form-data; name="Upload"\r\n\r\n'
        formString += "Submit Query\r\n"

        formString += boundary + "--"

        headers['Content-Length'] = len(formString)
        conn.request("POST", "/imgup.ashx", formString, headers=headers)
        res = conn.getresponse()
        picJson = self.decodeBody(res.getheaders(), res.read())

        conn.close()

        picItem = json.loads(picJson)
        picData = {"PictureDesc":"", "PicturePath":picItem['img'], "Md5": picItem['md5']}

        logger.debug(picData)

        if  picItem['img'] is None:
            return None
        return picData

    def uploadPics(self, photos):
        photo_list = []
        if len(photos) < 4:
            logger.error('photo is less than 4')
            return errorcode.DATA_ERROR, errormsg.PHOTO_NOT_ENOUGH
        photos = photos[:15]  # 最多15张图

        index = 0
        for photo in photos:
            url = photo.get("url", None)
            if url is None:
                continue
            o = urlparse(url)
            host = o.netloc
            uri = o.path

            upload = self.sessionServer.getUpload('taoche', uri)
            logger.debug('--upload-- ' + str(upload))
            if upload is None:
                host = 'pic.kanche.com'
                # if host == 'pic.kanche.com':
                #     host = 'kanche-pic.qiniudn.com'
                conn = httplib.HTTPConnection(host, timeout=10)
                headers = copy.copy(self.headers)
                del headers['Cookie']
                headers['Referer'] = "www.kanche.com"
                headers['Host'] = host

                conn.request("GET", uri, headers=headers)
                res = conn.getresponse()
                content = res.read()
                conn.close()
                result = self.uploadPicContent(content)


                if result is not None:
                    index += 1
                    result['UppId'] = index
                    photo_list.append(result)
                else:
                    logger.error('upload picture failed')
                    return errorcode.SITE_ERROR, errormsg.SITE_OTHER_ERROR

            else:
                logger.debug("getUpload failed")
        return photo_list

    # ==========================================
    # 上传行驶证
    # ==========================================
    def uploadDrivingLicense(self, summary):
        url = summary.get("driving_license_picture", None)
        if url is None or url == '':
            logger.error('no drivingLicensePicture')
            return ''
        o = urlparse(url)
        host = o.netloc
        uri = o.path

        upload = self.sessionServer.getUpload('taoche', uri)
        logger.debug('--upload-- ' + str(upload))
        if upload is None:
            # 下载
            host = 'pic.kanche.com'

            conn = httplib.HTTPConnection(host, timeout=10)
            headers = copy.copy(self.headers)
            del headers['Cookie']
            headers['Referer'] = "www.kanche.com"
            headers['Host'] = host

            conn.request("GET", uri, headers=headers)
            res = conn.getresponse()
            content = res.read()
            conn.close()
            # 上传
            result = self.uploadPicContent(content)

            if result is not None:
                return result.get("PicturePath")
            else:
                logger.error('upload picture failed')
                return errorcode.SITE_ERROR, errormsg.SITE_OTHER_ERROR


    #生成图片：具体生成某个图片
    def createPic(self, testportPath):
        #TODO:将生成的testport.html用phantomjs生成图片，然后上传到服务器，得到url，删除该html
        jsPath = './app/jsfunc/create_port.js'
        size = 1
        cmd = '/usr/local/bin/phantomjs "%s" "%s" %s'%(jsPath, testportPath, size)
        logger.debug(cmd)
        #生成图片的64位数据
        stdout, stderr = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE).communicate()
        logger.debug(stderr)
        logger.debug(stdout)

        #生成图片:图片路径
        picPath = './testport' + '.jpg'

        inspectReportFile = open(picPath)
        inspectReportContent = ''

        try:
            inspectReportContent = inspectReportFile.read()
        finally:
            inspectReportFile.close()

        #上传，获得URL
        #上传到青云
        result = self.uploadPicContent(inspectReportContent)
        #删除文件
        os.remove(picPath)
        return result

    #生成检测报告函数：生成多个
    def createReport(self, shareJob):
        result_list = []

        vehicle = shareJob.get('vehicle', None)

        external_vehicle_spec = shareJob.get('external_vehicle_spec', None)
        brand = external_vehicle_spec.get('brand', None)
        brandName = brand.get('name', None)
        if brandName is None:
            brandName = ""

        vendor = external_vehicle_spec.get('vendor', None)
        vendorName = vendor.get('name', None)
        if vendorName is None:
            vendorName = ""

        series = external_vehicle_spec.get('series', None)
        seriesName = series.get('name', None)
        if seriesName is None:
            seriesName = ""

        model = external_vehicle_spec.get('model', None)
        modelName = model.get('name', None)
        if modelName is None:
            modelName = ""

        summary = vehicle.get('summary', None)
        license_number = summary.get('license_number', None)
        if license_number is None:
            license_number = ""

        regDate = ""
        vehicle_date = vehicle.get('vehicle_date', None)
        registration_date = vehicle_date.get('registration_date', None)
        if registration_date is not None:
            regDate = str(registration_date)[0:10]

        milleage = 0
        mileage = summary.get('mileage', None)
        if mileage is not None:
            mileage = Decimal(mileage) / Decimal(10000)

        color = self.getColorCode(vehicle)

        vin = vehicle.get('vin', None)
        if vin is None:
            vin = ""

        purpose = summary.get('purpose', None)
        if purpose is None:
            purpose = ""
        carUse = {
            "personal": u"非营运",
            "public": u"营运"
        }
        if purpose != "":
            purpose = carUse[purpose]

        gallery = vehicle.get('gallery', None)
        photos = gallery.get('photos', None)
        url = photos[0].get('url', None)
        if url is None:
            url = ""

        spec_details = shareJob.get("vehicle_spec_detail", {}).get("details", [])
        if len(spec_details) > 11:
            vehicleType = spec_details[11]
        else:
            vehicleType = ""

        number = str(shareJob.get('_id', None))
        curDate = time.strftime('%Y-%m-%d')

        #生成文件1
        outFilepath = './temp/testport.html'
        template = './app/resource/template.html'
        mFile = open(template)
        try:
            content = mFile.read()
        finally:
            mFile.close()

        content = content.replace("\n", "")
        content = content.decode('utf-8','ignore')

        contentReplace = content.replace(u'{{brand}}', brandName + vendorName + seriesName + modelName)
        contentReplace = contentReplace.replace(u'{{licenseNumber}}', license_number)
        contentReplace = contentReplace.replace(u'{{vehicleType}}', vehicleType)
        contentReplace = contentReplace.replace(u'{{registerDate}}', regDate)
        contentReplace = contentReplace.replace(u'{{mileAge}}',  str(mileage))
        contentReplace = contentReplace.replace(u'{{color}}', color)
        contentReplace = contentReplace.replace(u'{{vin}}', vin)
        contentReplace = contentReplace.replace(u'{{vehicleUsage}}', purpose)
        contentReplace = contentReplace.replace(u'{{picture}}', url)
        contentReplace = contentReplace.replace(u'{{number}}', number)
        contentReplace = contentReplace.replace(u'{{date}}', curDate)

        contentReplace = contentReplace.encode('utf-8')
        logger.debug(contentReplace)

        outFile = open(outFilepath, 'w')
        try:
            outFile.write(contentReplace)
        finally:
            outFile.close()

        #TODO:图片一：将生成的testport.html用phantomjs生成图片，然后上传到服务器，得到url，删除该html
        picContent = self.createPic(outFilepath)
        os.remove(outFilepath)
        result_list.append(picContent)

        #上传第二张图,在本地不变直接上传
        picPath = './app/resource/inspectReportTaocheSecond.jpg'
        inspectReportFile = open(picPath)
        inspectReportContent = ''
        try:
            inspectReportContent = inspectReportFile.read()
        finally:
            inspectReportFile.close()

        #上传，获得URL等dict信息
        #上传到青云
        result = self.uploadPicContent(inspectReportContent)
        result_list.append(result)
        return result_list


    # ==========================================
    # 多张检测报告 数组
    # ==========================================
    def uploadInspectionReport(self, shareJob, merchantSubstituteConfig):
        if merchantSubstituteConfig is None:
            return ''
        #不需要检测报告的车辆
        inspectionReport = merchantSubstituteConfig.get('summary',{}).get("inspection_report", None)
        if inspectionReport is None:
            return ''

        #TODO:先判断检测报告是否存在，存放session.db中

        #生成检测报告:
        photo_list = []
        inspectionReport_list = self.createReport(shareJob)
        if 0 == len(inspectionReport_list):
            logger.error('upload picture failed')
            return errorcode.SITE_ERROR, errormsg.SITE_OTHER_ERROR

        num = 1
        for inspectionReport in inspectionReport_list:
            inspectionReport['UppId'] = str(num)
            photo_list.append(inspectionReport)
            num += 1
        return photo_list

        # inspectionReport
    # ==========================================
    # get make content pic
    # ==========================================

    def getSaleId(self, name, mobile):
        host = HOST

        # 发车页面联系人列表
        conn = httplib.HTTPConnection(host, timeout=10)
        url = "/Pages/carsource/sellcar.aspx"
        conn.request("GET", url, headers = self.headers)
        res = conn.getresponse()
        loginResult = self.decodeBody(res.getheaders(), res.read())
        conn.close()

        salesid = None

        # 解析contact
        getDom = lxml.html.fromstring(loginResult)
        options = getDom.xpath('.//select[@id="ContentPlaceHolder1_ddlLinkman"]/option')
        for option in options:
            if option.text.count("400"):
                salesid = option.get('value') #get the last salesid
            if option.text.count(str(mobile)):
                salesid = option.get('value')

        # 如果没找到 那么新建
        if salesid is None:
            salesid = self.createNewContact(name, mobile)

        if salesid is not None:
            return salesid

    def getSaleSecondId(self, name, mobile):
        host = HOST

        # 发车页面联系人列表
        conn = httplib.HTTPConnection(host, timeout=10)
        url = "/Pages/carsource/sellcar.aspx"
        conn.request("GET", url, headers = self.headers)
        res = conn.getresponse()
        loginResult = self.decodeBody(res.getheaders(), res.read())
        conn.close()

        salesid = None

        # 解析contact
        getDom = lxml.html.fromstring(loginResult)
        options = getDom.xpath('.//select[@id="ContentPlaceHolder1_ddlLinkman"]/option')
        for option in options:
            if option.text.count("400"):
                salesid = option.get('value') #get the last salesid
            if option.text.count(str(mobile)):
                salesid = option.get('value')

        # 如果没找到 那么新建
        if salesid is None:
            salesid = self.createNewContact(name, mobile)

        if salesid is not None:
            return salesid

    # 创建销售代表
    def createNewContact(self, name, mobile):
        conn = httplib.HTTPConnection(HOST, timeout=10)
        headers = copy.copy(self.headers)
        headers['Referer'] = 'http://dealer.taoche.com/Pages/store/linkman.aspx'
        headers['Content-Type'] = 'application/x-www-form-urlencoded; charset=UTF-8'
        formData = {"image": "", "name": name, "tel": mobile,
                    "position": "1" , "qrcode": "", "wechat": '', "issms":'0', "isshow":'0', "intro":''}
        conn.request("POST",
                     "/pages/store/ajax/linkmanmanage.ashx?api=edit&dvlid=0&r=" + self.rnd(), urllib.urlencode(formData),
                     headers=headers)
        res = conn.getresponse()
        contactJson = self.decodeBody(res.getheaders(), res.read())
        print urllib.urlencode(formData)

        conn.close()

        contactItem = json.loads(contactJson)
        contactData = contactItem.get('data', None)
        logger.debug("######contactData:" + str(contactData))
        if contactData is not None:
            if str(contactData['tel']) == str(mobile):
                return  contactData['dvlId']
            else:
                return  None


    def deleteNewContact(self, dvlid):

        conn = httplib.HTTPConnection(HOST, timeout=10)
        headers = copy.copy(self.headers)
        headers['Referer'] = 'http://dealer.taoche.com/Pages/store/linkman.aspx'

        conn.request("GET",
                     "/Pages/store/ajax/linkmanmanage.ashx?api=del&dvlid="+dvlid+"&r=" + self.rnd(),
                     headers=headers)
        res = conn.getresponse()
        contactJson = self.decodeBody(res.getheaders(), res.read())

        conn.close()

        contactItem = json.loads(contactJson)
        contactData = contactItem['data']

        if contactData == '删除成功':
            return  True
        else:
            return  None

    # ==========================================
    # getCarSpec
    # ==========================================
    def getCarSpec(self, levelId):  # 获取che168车型id
        modelId = self.specServer.getModelId('taoche', levelId)
        return modelId


    def random_str(self, randomlength):
        a = list(string.ascii_letters)
        random.shuffle(a)
        return ''.join(a[:randomlength])

    def rnd(self):
        return str(random.random())


    # ==========================================
    # remove Vehicle from management desk
    # ==========================================
    def removeVehicle(self,shareJob):
        shareAccount = shareJob.get("share_account", None)
        if shareAccount is None:
            return errorcode.AUTH_ERROR, ""
        if shareAccount.get('account_type', None) == 'public':
            shareAccount['username'] = publicAccount['username']
            shareAccount['password'] = publicAccount['password']

        cookies = self.sessionServer.getSession('taoche', shareAccount['username'])
        if cookies is None:
            result = self.doLogin(shareAccount['username'], shareAccount['password'])
            if not result:
                return errorcode.AUTH_ERROR, errormsg.LOGIN_FAIL
            #self.sessionServer.setSession('taoche', shareAccount['username'], self.cookies)
        else:
            self.cookies = cookies
            ks = self.cookies.keys()
            cookie_list = []
            for k in ks:
                cookie_list.append(k + '=' + self.cookies[k])
            self.headers['Cookie'] = str(string.join(cookie_list, '; '))

        urlForApp = shareJob.get("extra", None)
        #urlForApp = shareJob.get("url", None)
        #if urlForApp is None:
        if urlForApp is None or len(urlForApp) == 0:
            return errorcode.DATA_ERROR, errormsg.VEHICLE_URL_EMPTY

        print '\turlForApp:',urlForApp
        logger.debug('urlForApp:'+urlForApp)

        # http://dealer.taoche.com/Pages/carsource/carinfo.aspx?ucarid=4871702
        pRule = r'ucarid=(\d+)'
        pageList = re.compile(pRule).findall(urlForApp)
        if len(pageList):
            backendId = pageList[0]
        else:
            logger.debug("error:get pageId failed!")
            backendId = ""
        print '\tpageId:',backendId
        logger.debug( 'pageId' + backendId)

        '''
        #get urlForApp
        conn = httplib.HTTPConnection("dealer.taoche.com", timeout=10)
        headers = copy.copy(self.headers)
        conn.request("GET", urlForApp, headers=headers)
        res = conn.getresponse()
        resHeader = res.getheaders()
        resBody = res.read()
        resHtml = self.decodeBody(resHeader, resBody)
        conn.close()
        '''

        #POST http://dealer.taoche.com/Pages/carsource/onsalelist.aspx
        headers = copy.copy(self.headers)
        headers["Content-Type"] = "multipart/form-data; boundary=----WebKitFormBoundaryeglSTkfp7AnkLleb"
        print "\theaders:",headers

        boundaryHeader = '------WebKitFormBoundaryeglSTkfp7AnkLleb'
        boundary = boundaryHeader + "\r\n" + "Content-Disposition:form-data;" + "name="
        formData = ""
        formData += boundary + "\"__EVENTTARGET\"" + "\r\n\r\n" + "ctl00$ContentPlaceHolder1$lbtnDeleteCommand" +"\r\n"
        formData += boundary + "\"ctl00$ContentPlaceHolder1$hidSingleUcarId\"" + "\r\n\r\n" + backendId + "\r\n"
        #formData += boundary + "\"ctl00$ContentPlaceHolder1$btnDel\"" + "\r\n\r\n" + u"确定" +"\r\n"

        formData += boundaryHeader + "--"
        print "\nformData:\n",formData
        logger.debug("\nformData:\n"+formData)
        headers["Content-Length"] = len(formData)

        url = '/Pages/carsource/onsalelist.aspx'
        conn = httplib.HTTPConnection("dealer.taoche.com", timeout=10)
        conn.request("POST", url, formData, headers=headers)
        myres = conn.getresponse()
        resStatus = myres.status
        result = self.decodeBody(myres.getheaders(), myres.read())
        conn.close()

        print '\tresStatus:',resStatus
        #print "\tresult:\n",result
        if result.count('删除失败') >0:
            return errorcode.SITE_ERROR, errormsg.VEHICLE_REMOVE_FAIL
        else:
            return errorcode.SUCCESS, ""


    # ==========================================
    # update Vehicle price from management desk
    # ==========================================
    def updateVehicle(self,shareJob):
        shareAccount = shareJob.get("share_account", None)
        if shareAccount is None:
            return errorcode.AUTH_ERROR, ""
        if shareAccount.get('account_type', None) == 'public':
            shareAccount['username'] = publicAccount['username']
            shareAccount['password'] = publicAccount['password']

        logger.debug("**********taoche update vehicle***********")
        cookies = self.sessionServer.getSession('taoche', shareAccount['username'])
        if cookies is None:
            result = self.doLogin(shareAccount['username'], shareAccount['password'])
            if not result:
                return errorcode.AUTH_ERROR, errormsg.LOGIN_FAIL
            #self.sessionServer.setSession('taoche', shareAccount['username'], self.cookies)
        else:
            self.cookies = cookies
            ks = self.cookies.keys()
            cookie_list = []
            for k in ks:
                cookie_list.append(k + '=' + self.cookies[k])
            self.headers['Cookie'] = str(string.join(cookie_list, '; '))

        urlForApp = shareJob.get("extra", None)
        #urlForApp = shareJob.get("url", None)
        #if urlForApp is None:
        if urlForApp is None or len(urlForApp) == 0:
            return errorcode.DATA_ERROR, errormsg.VEHICLE_URL_EMPTY
        logger.debug('urlForApp:'+urlForApp)

        #1.0 get请求修改   http://dealer.taoche.com/Pages/carsource/sellcar.aspx?ucarid=4744166
        #url:           http://dealer.taoche.com/Pages/carsource/carinfo.aspx?ucarid=4744166
        pRule = r'(\d+)'
        pageList = re.compile(pRule).findall(urlForApp)
        if len(pageList):
            pageId = pageList[0]
        else:
            logger.debug("error:get pageId failed!")
            pageId = ""
        logger.debug( 'pageId:' + pageId)

        editUrl = '/Pages/carsource/sellcar.aspx?ucarid='+pageId
        logger.debug("get url:"+str(editUrl))
        conn = httplib.HTTPConnection('dealer.taoche.com', timeout=10)
        self.headers['Referer'] = 'http://dealer.taoche.com/Pages/carsource/onsalelist.aspx?mbid=0&brandid=0&carid=0&key='
        headers = copy.copy(self.headers)
        conn.request("GET", editUrl, headers=headers)
        res = conn.getresponse()
        editHtml = self.decodeBody(res.getheaders(), res.read())
        logger.debug("res:"+str(res))
        if res.status!=200:
            return errorcode.SITE_ERROR, "编辑页面出错"

        #2.0 post
        #url: http://dealer.taoche.com/Pages/carsource/sellcar.aspx?ucarid=4744166
        # =========================
        # get vehicle

        vehicle = shareJob.get("vehicle", None)
        merchantSubstituteConfig = shareJob.get("merchant_substitute_config", None)
        externalSpec = shareJob.get("external_vehicle_spec", None)

        if vehicle is None:
            logger.error("sharejob vehicle missing")
            return errorcode.DATA_ERROR, errormsg.VEHICLE_EMPTY

        user = vehicle.get("user", None)
        if user is None:
            logger.error("sharejob user missing")
            return errorcode.DATA_ERROR, errormsg.USER_EMPTY

        (name, mobile) = self.getContact(shareJob)

        # =========================
        # get provice and city code and name
        merchant = vehicle.get('merchant', None)
        address = merchant.get('address', None)
        if address is None:
            logger.error("sharejob address missing")
            return errorcode.DATA_ERROR, errormsg.ADDRESS_EMPTY
        provinceCode = address.get('province_code', None)
        if provinceCode is None:
            logger.error("sharejob province missing")
            return errorcode.DATA_ERROR, errormsg.PROVINCE_EMPTY
        cityCode = address.get('city_code', None)
        if cityCode is None:
            logger.error("sharejob city missing")
            return errorcode.DATA_ERROR, errormsg.CITY_EMPTY

        taocheProvinceCode = self.cityTaoche.getProvinceCode(provinceCode)
        taocheProvinceName = self.cityTaoche.getProvinceName(provinceCode)
        taocheCityCode = self.cityTaoche.getCityCode(cityCode)
        taocheCityName = self.cityTaoche.getCityName(cityCode)


        if taocheProvinceCode is None:
            logger.error(str(provinceCode) + "provinceCode not match")
            return errorcode.DATA_ERROR, str(provinceCode) + "无法匹配到淘车的省级代码"
        if taocheProvinceName is None:
            logger.error(str(provinceCode) + "provinceName not match")
            return errorcode.DATA_ERROR, str(provinceCode) + "无法匹配到淘车的省级名称"
        if taocheCityCode is None:
            logger.error(str(cityCode) + "cityCode not match")
            return errorcode.DATA_ERROR, str(cityCode) + "无法匹配到淘车的城市代码"
        if taocheCityName is None:
            logger.error(str(cityCode) + "cityName not match")
            return errorcode.DATA_ERROR, str(cityCode) + "无法匹配到淘车的城市名称"

        # =========================
        # get or make saleId

        # salesid = '292397'
        salesid = self.getSaleId(name,mobile)
        if salesid is None:
            logger.error("salesid missing")
            return errorcode.LOGIC_ERROR, errormsg.SALEID_EMPTY
        logger.debug("salesid=" + salesid)

         # =========================
        # 第二联系人
        salesSecondId = ""
        if merchantSubstituteConfig is not None:
            extraContact = merchantSubstituteConfig.get("extra_contact", None)
            phone = extraContact.get("phone",None)
            if phone is not None:
                salesSecondId = self.getSaleSecondId(extraContact.get("name"),extraContact.get("phone"))
                if salesSecondId is None:
                    logger.error("salesSecondId missing")
                logger.debug("salesSecondId=" + salesSecondId)

        # =========================
        # get spec
        # big part
        spec = vehicle.get("spec", None)
        summary = vehicle.get("summary", None)
        desc = vehicle.get("desc", None)

        if spec is None:
            logger.error("vehicle spec missing")
            return errorcode.DATA_ERROR, errormsg.VEHICLE_SPEC_EMPTY

        if summary is None:
            logger.error("vehicle summary missing")
            return errorcode.DATA_ERROR, errormsg.VEHICLE_SUMMARY_EMPTY

        if desc is None:
            logger.error("vehicle desc missing")
            return errorcode.DATA_ERROR, errormsg.VEHICLE_SUMMARY_EMPTY

        # small part

        # spec
        levelId = spec.get("level_id", None)
        if levelId is None:
            logger.error("levelId missing")
            return errorcode.DATA_ERROR, errormsg.VEHICLE_SPEC_EMPTY
        logger.debug("levelId=" + levelId)


        # viewState
        conn = httplib.HTTPConnection(HOST, timeout=10)
        conn.request("GET", 'http://dealer.taoche.com/Pages/carsource/sellcar.aspx', headers = self.headers)
        res = conn.getresponse()
        pageResult = self.decodeBody(res.getheaders(), res.read())
        conn.close()

        getDom = lxml.html.fromstring(pageResult)
        VIEWSTATE = getDom.xpath('.//input[@id="__VIEWSTATE"]/@value')[0]

        #构造form by yjy

        form = {}
        form['__VIEWSTATE'] = VIEWSTATE
        form['__SCROLLPOSITIONX'] = 0
        form['__SCROLLPOSITIONY'] = 2045
        form['__EVENTTARGET'] = 'ctl00$ContentPlaceHolder1$btnSubmit'
        form['__EVENTARGUMENT'] = ''
        form['ctl00$ContentPlaceHolder1$txtCarTitle'] = '一证在手 把车贷走'

        # 车型库匹配 yjy
        form['ctl00$ContentPlaceHolder1$hidSelfCarId'] = 0
        form['ctl00$ContentPlaceHolder1$hidMainBrandId'] = externalSpec.get("brand").get("id", None)
        form['ctl00$ContentPlaceHolder1$hidMainBrandName'] = externalSpec.get("brand").get("name", None) #'奥迪'
        form['ctl00$ContentPlaceHolder1$hidMainBrandGroup'] = externalSpec.get("brand").get("fchar", None)
        form['ctl00$ContentPlaceHolder1$hidSerialId'] = externalSpec.get("series").get("id", None)
        form['ctl00$ContentPlaceHolder1$hidSerialName'] = externalSpec.get("series").get("name", None)
        form['ctl00$ContentPlaceHolder1$hidCarId'] = externalSpec.get("model").get("id", None)
        form['ctl00$ContentPlaceHolder1$hidCarGroup'] = externalSpec.get("model").get("year", None)
        combineCarName = externalSpec.get("model").get("year", None)[2:] + externalSpec.get("model").get("name", None)
        form['ctl00$ContentPlaceHolder1$hidCarName'] = combineCarName
        form['ctl00$ContentPlaceHolder1$hidSerialGroup'] = externalSpec.get("vendor").get("name", None)
        form['inputGearBox'] = externalSpec.get("summary").get("gear", '自动')

        form['ctl00$ContentPlaceHolder1$hidEditOrAdd'] = '0' #0添加  1编辑
        form['ctl00$ContentPlaceHolder1$hidBasicSetCarId'] = ''
        form['ctl00$ContentPlaceHolder1$hidBasicSets'] = ''
        form['ctl00$ContentPlaceHolder1$selExhaustValue'] = '-1'
        form['ctl00$ContentPlaceHolder1$txtEvalue'] = ''
        # 车型配置 自定义
        # form['basicSet'] = [1,4,5,6,8,9,10,12]
        form['ctl00$ContentPlaceHolder1$hidStandardCarTypeConfig'] = 000000000000000000
        form['ctl00$ContentPlaceHolder1$txtSelfConfig'] = '最多可输入3个配置，逗号隔开'
        #color and innercolor
        form['ctl00$ContentPlaceHolder1$hidColor'] = self.getColorCode(vehicle)
        form['innerColor'] = self.getInterior(vehicle)
        form['ctl00$ContentPlaceHolder1$hidInnerColor'] = self.getInterior(vehicle)
        form['isLicensed'] = 1
        form['ctl00$ContentPlaceHolder1$hidIsLicensed'] = 1
        form['ctl00$ContentPlaceHolder1$txtDrivingMileage'] = self.getMileage(vehicle)

        # get location and dom pass
        # TODO 地区匹配 yjy
        form['ctl00$ContentPlaceHolder1$txtLicenseCity'] = taocheCityName
        form['ctl00$ContentPlaceHolder1$hidLicenseProviceId'] = taocheProvinceCode
        form['ctl00$ContentPlaceHolder1$hidLicenseCityId'] = taocheCityCode
        form['ctl00$ContentPlaceHolder1$hidLicenseProviceName'] = taocheProvinceName
        form['ctl00$ContentPlaceHolder1$hidLicenseCityName'] = taocheCityName
        form['ctl00$ContentPlaceHolder1$hidLicenseProviceIndex'] = 0.06451612903225806
        form['ctl00$ContentPlaceHolder1$hidLicenseCityIndex'] = 1
        form['ctl00$ContentPlaceHolder1$hidLicenseBakProviceId'] = taocheProvinceCode

        form['ctl00$ContentPlaceHolder1$hidLicenseCityIndex'] = 1
        form['ctl00$ContentPlaceHolder1$hidLicenseBakProviceId'] = taocheProvinceCode

        # 3个时间 上牌时间 年检有效期 商业保险有效期
        registrationDate = vehicle.get("vehicle_date").get("registration_date").astimezone(tz.HKT)
        if registrationDate is not None:
            form['ctl00$ContentPlaceHolder1$hidBuyCarDate'] = str(registrationDate.year) + '/' + str(registrationDate.month) + '/1 0:00:00'

        inspectionDate = vehicle.get("vehicle_date").get("inspection_date")
        if inspectionDate is not None:
            form['ctl00$ContentPlaceHolder1$hidExamineExpireDate'] = str(inspectionDate.year) + '/' + str(inspectionDate.month) + '/1 0:00:00'

        commercialInsuranceExpireDate = vehicle.get("vehicle_date").get("commercial_insurance_expire_date")
        if commercialInsuranceExpireDate is not None:
            form['ctl00$ContentPlaceHolder1$hidInsuranceExpireDate'] = str(commercialInsuranceExpireDate.year) + '/' + str(commercialInsuranceExpireDate.month) + '/1 0:00:00'
        else:
            form['ctl00$ContentPlaceHolder1$hidInsuranceExpireDate'] = str(inspectionDate.year) + '/' + str(inspectionDate.month) + '/1 0:00:00'

        # 图片视频 yjy
        # TODO photoList
        form['isCards'] = 0
        form['ctl00$ContentPlaceHolder1$hidIsCards'] = 0
        form['ctl00$ContentPlaceHolder1$txtVinCode'] = self.getVehicleVin(vehicle)
        form['ctl00$ContentPlaceHolder1$hidDriveLicensePic'] = self.uploadDrivingLicense(vehicle.get("summary",None))
        form['ctl00$ContentPlaceHolder1$hidvideojson'] = '{"videoid":"0"}'
        form['ctl00$ContentPlaceHolder1$hiduploadedVideoid'] = 0
        form['ctl00$ContentPlaceHolder1$hiduploadingVideoid'] = ''

        # TODO NEW 特色服务
        form['hiddelysuitId'] = 46 # 特色服务 默认
        form['hidservicetd_1'] = 0 #原厂质保
        form['hidservicetd_2'] = self.getQualityAssuranceTime(merchantSubstituteConfig)#延长质保
        form['hidservicetd_3'] = self.getIncludeTransferFee(vehicle)
        form['hidservicetd_1_date'] = ''
        form['hid_WarrantTime'] = ''

        # 保障车源
        consumerGuarantee = self.getConsumerGuarantee(merchantSubstituteConfig)
        form['r_iswp'] = consumerGuarantee
        form['hid_iswp'] = consumerGuarantee
        if consumerGuarantee is 1:
            inspectionList = self.uploadInspectionReport(shareJob, merchantSubstituteConfig)
            form['ctl00$ContentPlaceHolder1$hidJcImageJson'] = json.dumps(inspectionList)


        # 一句话说明
        form['ctl00$ContentPlaceHolder1$txtSlogan'] = self.getDescBrief(vehicle.get("desc", None))


        # 运营类型 yjy
        form['carType'] = self.getUsage(vehicle)
        form['ctl00$ContentPlaceHolder1$hidCarType'] = self.getUsage(vehicle)

        # 定期保养 yjy
        form['maintainRecord'] = self.getMaintenance(vehicle)
        form['ctl00$ContentPlaceHolder1$hidMaintainRecord'] = self.getMaintenance(vehicle)

        # 3个不知道有用么,yjy
        form['ctl00$ContentPlaceHolder1$txtZBMonth'] = ''
        form['ctl00$ContentPlaceHolder1$txtZBMileage'] = ''
        form['ctl00$ContentPlaceHolder1$hidTransferAgent'] = ''

        form['ctl00$ContentPlaceHolder1$txtStateDescription'] = self.getContentVal(shareJob, Symbol='\r\n')
        form['ctl00$ContentPlaceHolder1$txtDisplayPrice'] = self.getQuotedPrice(vehicle)
        form['ctl00$ContentPlaceHolder1$txtLowestPrice'] = self.getQuotedPrice(vehicle)

        form['ctl00$ContentPlaceHolder1$ddlLinkman'] = salesid
        form['ctl00$ContentPlaceHolder1$hidDvlId'] = salesid
        form['ctl00$ContentPlaceHolder1$ddlLinkman2'] = salesSecondId  #第二联系人
        form['ctl00$ContentPlaceHolder1$hidDvlId2'] = salesSecondId   #第二联系人
        form['ctl00$ContentPlaceHolder1$hidHasSecondLinkman'] = 1
        form['ctl00$ContentPlaceHolder1$hiddealerservice'] = self.getQuotedPriceIncludeTransferFee(vehicle)  #?
        form['ctl00$ContentPlaceHolder1$hidDraftId'] = ''
        # form['ctl00$ContentPlaceHolder1$hidapplayservice'] = '1,2,3,4,5,6,7,'

        #照片：[待修改yjy]
        picContentList = self.getUpdatePic(editHtml)
        logger.debug(picContentList)
        form['ctl00$ContentPlaceHolder1$hidImageJson'] = picContentList

        (success, msg) = self.postUpdateVehicle(form, pageId)
        if success:
            # self.deleteNewContact(salesid)
            return errorcode.SUCCESS, msg
        return errorcode.SITE_ERROR, msg

    def postUpdateVehicle(self, form,pageId):
        logger.debug(form)

        conn = httplib.HTTPConnection(HOST, timeout=10)
        headers = copy.copy(self.headers)
        headers['Content-Length'] = len(form)

        boundaryHeader = "------WebKitFormBoundary" + self.random_str(16)
        headers['Referer'] = 'http://dealer.taoche.com/Pages/carsource/sellcar.aspx?ucarid=' + pageId
        headers['Host'] = HOST
        headers["Content-Type"] = "multipart/form-data; boundary=" + boundaryHeader

        formString = ''
        boundary = "--" + boundaryHeader

        for (key,value) in form.items():
            # if key is 'basicSet':
            #     for set in value:
            #         formString += boundary + '\r\n' + 'Content-Disposition: form-data; name="'+key+'"\r\n\r\n'
            #         formString += str(set) + "\r\n"
            # else:
            formString += boundary + '\r\n' + 'Content-Disposition: form-data; name="'+key+'"\r\n\r\n'
            formString += str(value) + "\r\n"

        formString += boundary + "--"

        headers['Content-Length'] = len(formString)

        postUrl = '/Pages/carsource/sellcar.aspx?ucarid=' + pageId
        conn.request("POST", postUrl, formString, headers=headers)

        #get 'http://dealer.taoche.com/Pages/carsource/ok.aspx?ucarid=5218027&isadd=0&setTime=11'
        url = 'http://dealer.taoche.com/Pages/carsource/ok.aspx?ucarid='+ pageId +'&isadd=0&setTime=11'
        conn = httplib.HTTPConnection('dealer.taoche.com', timeout=10)
        headers = copy.copy(self.headers)
        conn.request("GET", url, headers=headers)
        res = conn.getresponse()
        content = res.read()
        result = self.decodeBody(res.getheaders(), content)
        conn.close()
        #logger.debug("res:"+str(res))
        if result.count("车源成功"):
            return True, u"更改成功"
        return False, u"更改失败"

    def getUpdatePic(self, html):
        picContentList = []
        pRule = r'UppId.*'
        picInfo = re.compile(pRule).findall(html)
        if len(picInfo):
            picInfo = picInfo[0]
        else:
            picInfo = ""
            logger.debug("get picInfo error!")

        picRule = r'\w*.jpg'
        picName = re.compile(picRule).findall(picInfo)

        mdRule = r'\w{32}'
        mdList = re.compile(mdRule).findall(picInfo)
        for i in range(0,len(picName)):
            picJson = {}
            picJson["UppId"] = i+1
            picJson["PicturePath"] = picName[i]
            picJson["PictureDesc"] = ''
            picJson["Angle"] = 0
            picJson["Md5"] = mdList[i]
            picContentList.append(picJson)

        return picContentList

    def getDescBrief(self, desc):
        if desc is None:
            return ''
        else:
            brief = desc.get("brief", '')
            return brief

    # 特色服务-免费过户
    def getIncludeTransferFee(self, vehicle):
        transferFee = vehicle.get("price").get("quoted_price_include_transfer_fee", None)
        transferFeeString = ''
        if transferFee is None:
            transferFeeString = 0
        else:
            transferFeeString = 1
        return transferFeeString

    # 特色服务-延长质保 淘车没有质保公里
    def getQualityAssuranceTime(self, merchantSubstituteConfig):
        if merchantSubstituteConfig is None:
            return 0
        quality_assurance_time = merchantSubstituteConfig.get('summary',{}).get('quality_assurance_time', None)
        result = ''
        if quality_assurance_time is None:
            result = 0
        elif quality_assurance_time > 0:
            result = 1
        else:
            result = 0
        return result

    # 保障车源 - 消费保障等
    def getConsumerGuarantee(self, merchantSubstituteConfig):
        if merchantSubstituteConfig is None:
            return 0
        consumerGuarantee = merchantSubstituteConfig.get('summary',{}).get('consumer_guarantee', None)
        result = ''
        if consumerGuarantee is None:
            result = 0
        elif consumerGuarantee is True:
            result = 1
        else:
            result = 0
        return result

    def getVehicleVin(self,vehicle):
        vinCode = vehicle.get("vin", None)

        if vinCode is None:
            return ''
        else:
            return vinCode



