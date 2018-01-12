# -*- coding: UTF-8 -*-
import httplib
from StringIO import StringIO
import urllib
import string
import random
import logger
import lxml
import time
import lxml.html
from multiprocessing import Process, Value, Lock
import base
from cookies import Cookie
import config
from pymongo import MongoClient

class che168Refresh(object):

    def __init__(self):
        self.headers = {
            "Accept":"application/json",
            "Content-Type" : "application/json",
            "Host":"dealer.che168.com",
            "Referer":"http://dealer.che168.com/car/carlist/?s=null&overtime=null&order=2"
        }
        self.baseheaders = {
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Encoding": "gzip,deflate,sdch",
            "Accept-Language": "en-US,en;q=0.8,zh-CN;q=0.6,zh-TW;q=0.4",
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_8_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/35.0.1916.114 Safari/537.36",
            "Host":"dealer.che168.com",
            "Referer":"http://dealer.che168.com/"
        }
        self.cookies = {}
        self.account = {
            "username": u"北京看看车二手车",
            "password": u"2wsx1qazk2scc1"
        }
        self.accountCookies = {}
        self.process = Process(target=self.refresh, args=())
        self.process.start()

    def refresh(self):
        client = MongoClient(config.mongoServer)
        db = client.kanche
        collection = db.share_job
        try:
            while True:
                logger.debug("-------车168刷新开始-------")
                items = collection.find({"share_account.website":"che168.com","status":"done","vehicle.contracted":True,"url":{"$nin":["null","None"]},"share_account.username":{"$nin":["null","None"]},"share_account.password":{"$nin":["null","None"]}},{"url":1,"share_account.username":1,"share_account.password":1})
                for item in items:
                    hasUrl = item.has_key("url") and item["url"] is not None
                    hasUsername = item.has_key("share_account") and item["share_account"].has_key("username") and item["share_account"]["username"] is not None
                    hasPass = item.has_key("share_account") and item["share_account"].has_key("password") and item["share_account"]["password"] is not None
                    if hasUrl and hasUsername and hasPass:
                        self.account["username"] = item["share_account"]["username"]
                        self.account["password"] = item["share_account"]["password"]
                        #获取cookie
                        if self.accountCookies.has_key(self.account["username"]):
                            self.headers["Cookie"] = self.accountCookies[self.account["username"]]
                            if self.headers["Cookie"] is not None:
                                (dealerid,infoid) = self.getIdByUrl(item["url"])
                                if dealerid is not False and infoid is not False:
                                    self.reflashVehicles(dealerid,infoid,item["url"])
                            else:
                                logger.debug("没有cookie")
                            self.headers.pop("Cookie",None)
                        else:
                            loginSuccess = self.doLogin(self.account["username"],self.account["password"])
                            if loginSuccess:
                                self.accountCookies[self.account['username']] = urllib.urlencode(self.cookies).replace("&",";")
                                self.headers["Cookie"] = self.accountCookies[self.account["username"]]
                                if self.headers["Cookie"] is not None:
                                    (dealerid,infoid) = self.getIdByUrl(item["url"])
                                    if dealerid is not False and infoid is not False:
                                        self.reflashVehicles(dealerid,infoid,item["url"])
                                else:
                                    logger.debug("没有cookie")
                                self.headers.pop("Cookie",None)
                logger.debug("-------车168刷新结束-------")
                self.accountCookies = {}
                time.sleep(3600)
        except Exception as e:
            logger.error("Exception: " + str(e))

    def getIdByUrl(self,url):
        if type(url) is unicode:
            if url.find("infoid") is -1:
                idArray = url.split("/")
                dealerid = idArray[-2]
                infoid = idArray[-1].replace(".html","")
                return dealerid, infoid
            else:
                return False, False
        else:
            return False, False

    def reflashVehicles(self,dealerid=None,infoid=None,url=None):
        if dealerid is None or infoid is None or url is None:
            return "error"
        else:
            conn = httplib.HTTPConnection("dealer.che168.com", timeout=10)
            conn.request("GET", "/Handler/CarManager/CarOperate.ashx?dealerid="+dealerid+"&action=setsell&infoid="+infoid+"&status=null&price=&buyMobile=&buyname=", "", self.headers)
            response = conn.getresponse().read()
            conn.close()

    def doLogin(self, username, password):
        if self.baseheaders.has_key("Cookie"):
            self.baseheaders.pop("Cookie", None)
            self.cookies = {}
        if self.headers.has_key("Cookie"):
            self.headers.pop("Cookie",None)
        conn = httplib.HTTPConnection("dealer.che168.com", timeout=10)
        conn.request("GET", "/","", self.baseheaders)
        res = conn.getresponse()
        resHeaders = res.getheaders()
        resRead = res.read()
        self.setCookies(resHeaders)
        html = base.BaseSharer.decodeBody(resHeaders, resRead)
        html = html.decode('GB18030')
        dom = lxml.html.fromstring(html)
        checkCodeImageUrls = dom.xpath('.//span/img[@src]/@src')
        if len(checkCodeImageUrls) == 0:
            return False
        checkCodeImageUrl = checkCodeImageUrls[0]
        conn.close()

        conn = httplib.HTTPConnection("dealer.che168.com", timeout=10)
        conn.request("GET", checkCodeImageUrl,"", self.baseheaders)
        res = conn.getresponse()
        self.setCookies(res.getheaders())
        imageData = res.read()
        conn.close()
        image = StringIO(imageData)
        captcha = base.BaseSharer.getCaptcha(image, imageData)

        if captcha is None:
            return False

        validcode = captcha["text"]

        conn = httplib.HTTPConnection("dealer.che168.com", timeout=10)

        url = "/Handler/Login/Login.ashx?"
        username = urllib.quote(username.encode("GB18030"))
        password = urllib.quote(password.encode("GB18030"))
        url = url + 'name=' + username
        url = url + '&pwd=' + password
        url = url + '&validcode=' + validcode.strip()
        url += '&remember=false'
        url = url + '&req=' + str(random.random())

        conn.request("GET", url,"", self.baseheaders)
        res = conn.getresponse()
        resHeaders = res.getheaders()
        resRead = res.read()
        loginResult = base.BaseSharer.decodeBody(resHeaders, resRead)
        loginResult = loginResult.decode('GB18030')
        if not loginResult.startswith(u"var code='1';"):
            return False
        logger.debug("loginResult=" + loginResult)
        self.setCookies(res.getheaders())
        return True

    def setCookies(self,headers, encode=False):
        def next_token_is_not_semi(s):
            for i in  xrange(len(s)):
                if s[i] == ';':
                    return False
                if s[i] == '=':
                    return True
            return True

        def parse_one_cookie(set_cookie_str):
            state = 0
            for i in xrange(len(set_cookies_str)):
                if state == 0 and set_cookies_str[i] == '=':
                    state = 1
                elif state == 1 and set_cookies_str[i] == ';':
                    state = 0
                if state == 0 and set_cookies_str[i] == ',':
                    return  set_cookies_str[:i], set_cookies_str[i+1:].strip()
                if state == 1 and set_cookies_str[i] == ',' and next_token_is_not_semi(set_cookies_str[i+1:]):
                    return  set_cookies_str[:i], set_cookies_str[i+1:].strip()
                else:
                    continue
            return set_cookie_str, ""

        for header in headers:
            if header[0].lower() == 'set-cookie':
                set_cookies_str = header[1]
                while len(set_cookies_str) > 0:
                    (one_cookie_str,set_cookies_str) = parse_one_cookie(set_cookies_str)
                    cookie = Cookie.from_string(one_cookie_str)
                    if encode:
                        self.cookies[cookie.name] = urllib.quote(cookie.value.encode('utf-8'))
                    else:
                        self.cookies[cookie.name] = cookie.value.encode('utf-8')
        ks = self.cookies.keys()
        cookie_list = []
        for k in ks:
            cookie_list.append(k + '=' + self.cookies[k])
        self.baseheaders['Cookie'] = string.join(cookie_list, '; ')
        logger.debug(str(self.baseheaders))

