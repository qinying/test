#!/usr/bin/python
# -*- coding: UTF-8 -*-

import tz
import httplib
import urllib
import lxml.html
import random
import string
import re
import copy
import json
from decimal import *
import resize
import errorcode
import errormsg
import logger
from urlparse import urlparse
from StringIO import StringIO
from dt8601 import IsoDate
from base import BaseSharer
import zlib
import config

data = {
    "share_account": {
        "username": "安伟达二手车",
        "password": "123456"
    },
    "vehicle": {

    }
}

publicAccount = {
    "username": u"石家庄市朗拓二手车",
    "password": u"123456"
    #"username": u"北京看看车二手车",
    #"password": u"2wsx1qazk2scc1"
}

timeout_che168 = 20

class Che168Sharer(BaseSharer):
    def __init__(self, sessionServer, specServer):
        super(Che168Sharer, self).__init__(sessionServer, specServer)
        self.headers["Referer"] = "http://dealer.che168.com"

    '''def setCookies(self, headers):
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
        logger.debug(str(self.headers))'''

    def doLogin(self, username, password):
        conn = httplib.HTTPConnection("dealers.che168.com", timeout=timeout_che168)
        conn.request("GET", "/", headers=self.headers)
        res = conn.getresponse()
        resHeaders = res.getheaders()
        resRead = res.read()
        self.setCookies(resHeaders)

        try:
            html = self.decodeBody(resHeaders, resRead)
        except:
            return False

        html = html.decode('GB18030')
        dom = lxml.html.fromstring(html)
        checkCodeImageUrls = dom.xpath('.//span[@class="num_pic m110"]/img/@src')
        if len(checkCodeImageUrls) == 0:
            return False
        checkCodeImageUrl = checkCodeImageUrls[0]
        logger.debug("captcha url:" + str(checkCodeImageUrl))
        conn.close()

        conn = httplib.HTTPConnection("dealers.che168.com", timeout=timeout_che168)
        conn.request("GET", checkCodeImageUrl, headers=self.headers)
        res = conn.getresponse()
        self.setCookies(res.getheaders())
        imageData = res.read()
        conn.close()
        image = StringIO(imageData)
        captcha = self.getCaptcha(image, imageData)

        if captcha is None:
            return False

        validcode = captcha["text"]

        conn = httplib.HTTPConnection("dealers.che168.com", timeout=timeout_che168)

        url = "/Handler/Login/Login.ashx?"
        username = urllib.quote(username.encode("GB18030"))
        password = urllib.quote(password.encode("GB18030"))
        url = url + 'name=' + username
        url = url + '&pwd=' + password
        url = url + '&validcode=' + validcode.strip()
        url += '&remember=false'
        url = url + '&req=' + str(random.random())

        conn.request("GET", url, headers = self.headers)
        #print url
        res = conn.getresponse()
        resHeaders = res.getheaders()
        resRead = res.read()
        loginResult = self.decodeBody(resHeaders, resRead)
        loginResult = loginResult.decode('GB18030')
        if not loginResult.startswith(u"var code='1';"):
            return False
        logger.debug("loginResult=" + loginResult)
        self.setCookies(res.getheaders())
        return True

    def shareVehicle(self, shareJob):
        shareAccount = shareJob.get("share_account", None)
        if shareAccount is None:
            logger.error("login fail")
            return errorcode.AUTH_ERROR, errormsg.LOGIN_FAIL
        if shareAccount.get('account_type', None) == 'public':
            shareAccount['username'] = publicAccount['username']
            shareAccount['password'] = publicAccount['password']

        logger.debug("che168 shareVehicle")
        cookies = self.sessionServer.getSession('che168', shareAccount['username'])
        if cookies is None:
            res = self.doLogin(shareAccount['username'], shareAccount['password'])
            if not res:
                logger.debug("login error")
                return errorcode.AUTH_ERROR, errormsg.LOGIN_FAIL
            self.sessionServer.setSession('che168', shareAccount['username'], self.cookies)
        else:
            self.cookies = cookies
            ks = self.cookies.keys()
            cookie_list = []
            for k in ks:
                cookie_list.append(k + '=' + self.cookies[k])
            self.headers['Cookie'] = string.join(cookie_list, '; ')

        logger.debug("self.cookies" + str(self.cookies))
        vehicle = shareJob.get("vehicle", None)
        if vehicle is None:
            logger.error("vehicle missing")
            return errorcode.LOGIC_ERROR, errormsg.VEHICLE_EMPTY

        '''user = vehicle.get("user", None)
        if user is None:
            return errorcode.LOGIC_ERROR, "car user not found"
        mobile = user.get("mobile", None)
        if mobile is None:
            return errorcode.LOGIC_ERROR, "user mobile not found"
        public_phone = user.get("public_phone", None)
        if public_phone is not None:
            if len(public_phone) > 10:
                mobile = public_phone'''
        account = shareAccount["username"]
        (username, mobile) = self.getContact(shareJob)

        salesid = self.getSiteContact(account,username, mobile)
        if salesid is None:
            logger.error("salesid missing")
            return errorcode.LOGIC_ERROR, errormsg.SALEID_EMPTY
        logger.debug("salesid=" + salesid)

        spec = vehicle.get("spec", None)
        if spec is None:
            logger.error("spec missing")
            return errorcode.DATA_ERROR, errormsg.VEHICLE_SPEC_EMPTY
        levelId = spec.get("level_id", None)
        if levelId is None:
            logger.error("levelId missing")
            return errorcode.DATA_ERROR, errormsg.VEHICLE_SPEC_EMPTY
        logger.debug("levelId=" + levelId)

        #(specid, specDetail) = self.getCarSpec(levelId)
        externalSpec = shareJob.get("external_vehicle_spec", None)
        if externalSpec is None:
            logger.error("external spec missing")
            return errorcode.SPEC_ERROR, errormsg.EXTERNAL_SPEC_EMPTY

        logger.debug(json.dumps(externalSpec.get("series", None)))
        externalSpecModelId = externalSpec['model']['id']

        #一句话标题
        promotionWords = u'此车可贷款 只需身份证'
        brief = vehicle.get('desc', None).get('brief', None)
        if brief is not None:
            promotionWords = brief.strip('\n')
        title = externalSpec['series']['name'] + ' ' + externalSpec['model']['name'] + promotionWords

        logger.debug("externalSpecModelId=" + externalSpecModelId)
        logger.debug("title=" + title)
        part = self.getPart(externalSpecModelId)

        #yjy,get photos:
        gallery = vehicle.get("gallery", None)
        if gallery is None:
            logger.error("gallery missing")
            return errorcode.DATA_ERROR, errormsg.PHOTO_NOT_ENOUGH
        photoList = self.uploadPics(gallery.get("photos", []))

        logger.debug(json.dumps(photoList))
        (success, msg) = self.postVehicle(shareJob, externalSpec, title, part, photoList, salesid, username)
        if success:
            return errorcode.SUCCESS, msg
        return errorcode.SITE_ERROR, errormsg.SITE_OTHER_ERROR

    @staticmethod
    def getColor(shareJob):
        summary = shareJob.get("summary", None)
        if summary is None:
            return 1
        color = summary.get("color", "black")
        if color == "black":
            return 1

        return 1

    doc = '''
    infoid=0
    &carname=%25E5%25A5%25A5%25E8%25BF%25AAA4%25202008%25E6%25AC%25BE%25201.8T%2520%25E4%25B8%25AA%25E6%2580%25A7%25E9%25A3%258E%25E6%25A0%25BC%25E7%2589%2588
    &brandid=33
    &seriesid=19
    &specid=3623
    &options=3,4,5,7,10,11,12,13,17,18
    &displa=1.8
    &gearbos=%u81EA%u52A8
    &iscontainfee=0
    &price=30
    &mileage=2
    &pid=110000
    &cid=110100
    &registedate=2009-1
    &Examine=2015-1
    &Insurance=2015-1
    &Taxtime=2015
    &TransferTimes=1
    &CarUse=1
    &colorcode=1
    &linkman=%u9500%u552E%u4EE3%u8868
    &linkmanid=77789
    &remark=%u963F%u65B9%u4F4Df%u989Dw%u6076%u6CD5
    &CertificateType=0
    &pictures=/2014/7/2/5684793102249695720.jpg,/2014/7/2/5615321909832493424.jpg
    &examinepics=
    &fromType=0
    '''

    def getOptions(self, model_id):
        # http://dealer.che168.com/Handler/CarManager/SalesCarPart.ashx?cd=gca&spid=100576
        headers = copy.copy(self.headers)
        uri = '/Handler/CarManager/SalesCarPart.ashx?cd=gca&spid=' + str(model_id)
        conn = httplib.HTTPConnection('dealer.che168.com', timeout=timeout_che168)
        conn.request("GET", uri, headers=headers)
        res = conn.getresponse()
        resHeaders = res.getheaders()
        resRead = res.read()
        content = self.decodeBody(resHeaders, resRead)
        content = content.decode('GB18030')
        logger.debug("content=" + str(content))

        if res.status != 200:
            return "3,4,5,7,10,11,12,13,17,18"
        else:
            contentJson = json.loads(content)
            carOption = contentJson['CarOption']
            return str(carOption)


    #@staticmethod
    #def getGearbox(part):
    #    if part['gearbox'].count(u"自") > 0 :
    #        return u"自动"
    #    return u"手动"

    @staticmethod
    def getGearbox(spec_details):
        if spec_details[42].count(u"自") > 0 :
            return u"自动"
        return u"手动"

    @staticmethod
    def makePhotos(photoList):
        photos = []
        for photo in photoList:
            photos.append(photo['msg'])
        return ",".join(photos)

    @staticmethod
    def getDate(shareJob, type):
        typeDict = {
            1: "registration_date",
            2: "inspection_date",
            3: "commercial_insurance_expire_date",
            4: "compulsory_insurance_expire_date"
        }
        vehicle = shareJob.get("vehicle", None)
        if vehicle is not None:
            vehicleDate = vehicle.get('vehicle_date', None)
            if vehicleDate is not None:
                mDate = vehicleDate.get(typeDict[type], None)
                if mDate is None:
                    d = mDate
                else:
                    d = mDate.astimezone(tz.HKT)
        return d

    @staticmethod
    def getColorCode(shareJob):
        colorCode = "11"
        colorTable = {"black": "1", "white": "2", "red":"5", "yellow":"8",
            "blue":"6", "green":"7", "purple":"10", "silver":"3", "grey": "4",
            "champagne": "9", "other": "11"}
        vehicle = shareJob.get("vehicle", None)
        if vehicle is not None:
            summary = vehicle.get("summary", None)
            if summary is not None:
                color = summary.get("color", None)
                colorCode = colorTable.get(color, "11")
        return colorCode

    def getTradeTimes(self, shareJob):
        tradeTime = 0
        vehicle = shareJob['vehicle']
        try:
            tradeTime = int(vehicle['summary'].get('trade_times', 0))
        except Exception as e:
            tradeTime = 0
        return tradeTime

    def getSeriesSpec(self, brandid, seriesid):
        pass


    def uploadLicensePic(self, drivingLicenseUrl):
        photo_list = []
        o = urlparse(drivingLicenseUrl)
        host = o.netloc
        uri = o.path

        upload = self.sessionServer.getUpload('che168', uri)
        logger.debug('--upload-- \n' + str(upload))
        if upload is not None:
            res = json.loads(upload)
        else:
            if host == 'pic.kanche.com':
                host = 'kanche-pic.qiniudn.com'
            conn = httplib.HTTPConnection(host, timeout=timeout_che168)
            headers = copy.copy(self.headers)
            del headers['Cookie']
            headers['Referer'] = "www.kanche.com"
            conn.request("GET", uri, headers = headers)
            res = conn.getresponse()
            content = res.read()
            conn.close()
            #TODO:对于行驶证，此函数不一样，待抓包修改
            res = self.uploadPicContent(content)
            logger.debug(str(res))
            if (res is not None) and (res.has_key("success") and (res["success"] == 1)):
                self.sessionServer.setUpload('che168', uri, json.dumps(res))
        if (res is not None) and (res.has_key("success") and (res["success"] == 1)):
            photo_list.append(res)
        return photo_list

    def postVehicle(self, shareJob, externalSpec, title, part, photoList, salesid, username):
        publishUrl = '/car/publish'
        conn = httplib.HTTPConnection('dealers.che168.com', timeout=timeout_che168)
        headers = copy.copy(self.headers)
        conn.request("GET", publishUrl, headers=headers)
        res = conn.getresponse()
        logger.debug("res:"+str(res))
        if res.status != 200:
            return errorcode.SITE_ERROR, errormsg.VEHICLE_REMOVE_FAIL
        validcode = ''
        self.setCookies(res.getheaders())
        carRes = res.read()
        html = self.decodeBody(res.getheaders(), carRes)
        html = html.decode('GB18030')
        if html.count(u'验证码') == 0:
            validcode = 'undefined'
            conn.close()
        else:
            dom = lxml.html.fromstring(html)
            checkCodeImageUrls = dom.xpath('.//span[@class="num_pic m110"]/img/@src')
            if len(checkCodeImageUrls) == 0:
                return False
            checkCodeImageUrl = checkCodeImageUrls[0]
            conn.close()

            headers = {}#self.headers
            headers['Host'] = 'dealers.che168.com'
            conn = httplib.HTTPConnection("dealers.che168.com", timeout=timeout_che168)
            conn.request("GET", checkCodeImageUrl, headers=headers)
            res = conn.getresponse()
            resHeader = res.getheaders()
            logger.debug("resHeader === " + str(resHeader))
            self.setCookies(resHeader)
            imageData = res.read()
            conn.close()
            image = StringIO(imageData)
            captcha = self.getCaptcha(image, imageData)

            if captcha is None:
                return False
            validcode = captcha["text"]

        vehicle = shareJob['vehicle']

        price =vehicle.get('price', None)
        if price is None:
            logger.error('price missing')
            return errorcode.DATA_ERROR, errormsg.PRICE_EMPTY

        spec_details = shareJob['vehicle_spec_detail']['details']
        #brandid = specDetail['brandId']
        brandid = externalSpec['brand']['id']
        #seriesid = specDetail['seriesId']
        seriesid = externalSpec['series']['id']
        specid = externalSpec['model']['id']
        form = "infoid=0"
        form += "&carname=" + urllib.quote(urllib.quote(title.encode('utf-8')))
        form += "&brandid=" + str(brandid)
        form += "&seriesid=" + str(seriesid)
        form += "&specid=" + str(specid)
        #TODO:options 是什么?
        form += "&options=" + self.getOptions(specid)
        form += "&displa=" + spec_details[23] #part['displa']
        form += "&gearbos=" + self.getGearbox(spec_details).encode("unicode_escape").upper().replace("\\U", "%u")


        #是否包含过户费:
        quoted_price_include_transfer_fee = price.get('quoted_price_include_transfer_fee', True)
        if quoted_price_include_transfer_fee:
            form += "&iscontainfee=1"
        else:
            form += "&iscontainfee=0"
        #form += "&iscontainfee=0"

        #vincode:没有vin码就不需要字段
        #vin码和行驶证同时有或者同时无
        summary = vehicle.get('summary', None)
        # drivingLicenseUrl = summary.get('driving_license_picture', None)
        vin_picture_url = summary.get("vin_picture", None)

        vincode = vehicle.get("vin", None)
        if (vincode is None) or (vin_picture_url is None) or ('' == vin_picture_url):
            pass
        else:
            form += "&vincode=" + vincode

            #行驶证换为vin照片
            picList = []
            if vin_picture_url is not None:
                picList = self.uploadLicensePic(vin_picture_url)
            if len(vin_picture_url):
                photo = picList[0]['msg']
            else:
                photo = ""
            form += "&xs_certify=" + photo

        MerchantSubstituteConfig = shareJob.get('merchant_substitute_config', None)
        if MerchantSubstituteConfig is not None:
            merchant_summary = MerchantSubstituteConfig.get('summary', None)
            if merchant_summary is not None:
                #质保时间
                QualityAssDate = merchant_summary.get('quality_assurance_time', None)
                if QualityAssDate is not None:
                    form += "&QualityAssDate=" + str(int(QualityAssDate))

                #质保公里
                QualityAssMile = merchant_summary.get('quality_assurance_mile', None)
                if QualityAssMile is not None:
                    form += "&QualityAssMile=" + str(QualityAssMile/10000.0)

        form += "&price=" + str(Decimal(self.getPrice(shareJob)) / Decimal(10000))
        form += "&mileage=" + str(Decimal(vehicle['summary']['mileage']) / Decimal(10000))
        form += "&pid=" + str(shareJob['vehicle']['merchant']['address']['province_code'])
        form += "&cid=" + str(shareJob['vehicle']['merchant']['address']['city_code'])

        '''share
        1: "registration_date",
        2: "inspection_date",
        3: "commercial_insurance_expire_date",
        4: "compulsory_insurance_expire_date"
        '''
        registedate = self.getDate(shareJob, 1)
        if registedate is None:
            form += "&registedate="+"2016-6"
        else:
            form += "&registedate="+ str(registedate.year) + "-" + str(registedate.month)
        Examine = self.getDate(shareJob, 2)
        if Examine is None:
            form += "&Examine=" + "2016-6"
        else:
            form += "&Examine="+str(Examine.year) + '-' + str(Examine.month)
        Insurance = self.getDate(shareJob, 3)
        if Insurance is None:
            form += "&Insurance=" + str(Examine.year) + "-" + str(Examine.month)
        else:
            form += "&Insurance=" + str(Insurance.year) + "-" + str(Insurance.month)
        #FIXME：Taxtime只有年？？？
        Taxtime = self.getDate(shareJob, 4)
        if Taxtime is None:
            form += "&Taxtime=" + str(Examine.year)
        else:
            form += "&Taxtime=" + str(Taxtime.year)

        form += "&TransferTimes=" + str(self.getTradeTimes(shareJob))
        form += "&CarUse=1"
        form += "&colorcode=" + self.getColorCode(shareJob)
        form += "&linkman="+urllib.quote(username.encode('utf-8'))
        form += "&linkmanid=" + str(salesid)
        #TODO fix bug
        # a = '刘先生(020-62644497)'
        # form += "&linkman="+urllib.quote(a)
        # form += "&linkmanid=118468"

        Symbol = "\r\n"
        lateral = "——"*23
        form += "&remark=" + urllib.quote(self.getContentVal(shareJob, Symbol, lateral).encode('utf-8'))
        #TODO：certificateType什么意思？
        form += "&CertificateType=0"
        form += "&pictures=" + self.makePhotos(photoList)
        #form += "&examinepics="
        form += "&fromType=0"
        form += "&fueltype=1"
        form += "&isFreeCheckCar=0"
        form += "&validcode=" + validcode
        # form += "&isSelectedPromise=0"
        # form += "&isvalidvincode=0"
        # form += "&saleDealerPrice="
        # form += "&vincode=LGBG22E047Y106663"
        # form += "&xs_certify=/escimg/g8/M01/32/66/autohomecar__wKjBz1aTloyAb5OfAAGPKOvQxEs632.jpg"



        logger.debug(form)
        conn = httplib.HTTPConnection("dealers.che168.com", timeout=timeout_che168)
        headers = copy.copy(self.headers)
        headers['Content-Length'] = len(form)
        headers['Content-Type'] = 'application/x-www-form-urlencoded; charset=UTF-8'
        conn.request("POST", "/Handler/CarManager/SaleCar.ashx", form, headers = headers)
        res = conn.getresponse()
        carRes = res.read()#.decode("GB18030")
        result = self.decodeBody(res.getheaders(), res.read())

        logger.debug(carRes)
        carRes = carRes.split('|')
        if (len(carRes) == 2) and (carRes[0] == '0'):
            url = "http://www.che168.com/dealer/" + str(self.cookies['2scDealerId']) + "/" + carRes[1] +".html"
            return True, url
        return False, "carRes"

    def uploadPicContent(self, content):
        conn = httplib.HTTPConnection("upload.che168.com", timeout=timeout_che168)
        headers = copy.copy(self.headers)

        img = StringIO(content)
        smallImg = StringIO()
        resize.resize(img, (600, 600), False, smallImg)
        content = smallImg.getvalue()

        conn.request("POST", "/UploadImage.ashx?infoid=1000", content, headers = headers)
        try:
            res = conn.getresponse()
            resHeaders = res.getheaders()
            logger.debug(str(resHeaders))
            photoRes = self.decodeBody(resHeaders, res.read())
        except Exception as e:
            logger.debug(str(e))
            ret = None
            return ret

        #print photoRes#.decode("GB18030")
        conn.close()
        try:
            ret = json.loads(photoRes)
        except Exception as e:
            #ret = json.loads('[{"msg": "/2014/7/5/5525213967984534785.jpg", "img": "http://www.autoimg.cn/2scimg/2014/7/5/m_5525213967984534785.jpg", "success": 1}]')
            logger.debug(str(e))
            logger.debug(urllib.quote(photoRes))
            ret = None
        return ret

    def uploadPics(self, photos):
        photo_list = []
        if len(photos) < 1:
            logger.error('photo is less than 1')
            return errorcode.DATA_ERROR, errormsg.PHOTO_NOT_ENOUGH

        photos = photos[:16] #最多16张图
        for photo in photos:
            url = photo.get("url", None)
            if url is None:
                continue
            o = urlparse(url)
            host = o.netloc
            uri = o.path

            upload = self.sessionServer.getUpload('che168', uri)
            logger.debug('--upload-- \n' + str(upload))
            if upload is not None:
                res = json.loads(upload)
            else:
                host = 'pic.kanche.com'
                # if host == 'pic.kanche.com':
                #     host = 'kanche-pic.qiniudn.com'
                conn = httplib.HTTPConnection(host, timeout=timeout_che168)
                headers = copy.copy(self.headers)
                del headers['Cookie']
                headers['Referer'] = "www.kanche.com"
                headers['Host'] = host

                conn.request("GET", uri, headers = headers)
                res = conn.getresponse()
                content = res.read()
                conn.close()
                res = self.uploadPicContent(content)
                logger.debug(str(res))
                if (res is not None) and (res.has_key("success") and (res["success"] == 1)):
                    self.sessionServer.setUpload('che168', uri, json.dumps(res))
            if (res is not None) and (res.has_key("success") and (res["success"] == 1)):
                photo_list.append(res)
        return photo_list

    #def getCarSpec(self, levelId):  #获取che168车型id
    #    modelId = self.specServer.getModelId('che168', levelId)
    #    return modelId

    def getPart(self, specid):
        conn = httplib.HTTPConnection("dealer.che168.com", timeout=timeout_che168)
        headers = copy.copy(self.headers)
        conn.request("GET", "/Handler/CarManager/SalesCarPart.ashx?cd=gca&spid=" + str(specid), headers = headers)
        res = conn.getresponse()
        resHeaders = res.getheaders()
        resRead = res.read()
        part = self.decodeBody(resHeaders, resRead)
        part = part.decode('GB18030')
        logger.debug("part=" + part)
        conn.close()
        return json.loads(part)

    def createNewContact(self, username, mobile):
        conn = httplib.HTTPConnection("dealer.che168.com", timeout=timeout_che168)
        headers = copy.copy(self.headers)
        encoded_username = ""
        for c in username:
            encoded_username += "%u" + ("%x"%ord(c)).upper()
        conn.request("GET", "/Handler/SaleMan/SaveSaleMan.ashx?Name=" + encoded_username + "&Mobile=" + mobile + "&QQ=&weixin=&pic=&file=", headers = headers)
        res = conn.getresponse()
        resHeaders = res.getheaders()
        resRead = res.read()
        html = self.decodeBody(resHeaders, resRead)
        html = html.decode('GB18030')
        conn.close()
        html = html.split('|')
        if len(html) > 1:
            return html[1]
        return None

    def getSiteContact(self, account, username, mobile):
        HOST = "dealer.che168.com"
        # if account in config.che168VIPAccountList:
        #     HOST = "dealer.che168.com"
        # else:
        #     HOST = "dealers.che168.com"

        conn = httplib.HTTPConnection(HOST, timeout=timeout_che168)
        headers = copy.copy(self.headers)
        conn.request("GET", "/car/publish/?s=1", headers=headers)
        res = conn.getresponse()
        resHeaders = res.getheaders()
        resRead = res.read()
        html = self.decodeBody(resHeaders, resRead)
        html = html.decode('GB18030')
        html = html.replace("gb2312", "utf-8")
        dom = lxml.html.fromstring(html)
        contactItems = dom.xpath('//*[@id="sh_linkMan_div"]/a/@rel')
        conn.close()
        if len(contactItems) == 0:
            return self.createNewContact(username, mobile)
        logger.debug(str(contactItems))
        for salesid in contactItems:
            # if self.checkCurrentContact(salesid, mobile) is True:
            return salesid
        return self.createNewContact(username, mobile)

    def getHtmlImglist (self, html):
        #post:      pictures=/2014/12/18/5638330436415868208.jpg,...
        #src:       http://www.autoimg.cn/2scimg/web/dealeradmin/images/pic16.jpg
        photoList = []
        pRule = r'http://www.autoimg.cn/2scimg/.*.jpg'
        plist = re.compile(pRule).findall(html)
        if len(plist):
            plist = plist[0]
        else:
            logger.debug("get photolist error")
            plist = ""
        # plist = plist.split(',')

        pRule = r'(/20.*.jpg)'
        for li in plist:
            photo = re.compile(pRule).findall(li)
            if len(photo):
                photoList.append(photo[0])
            else:
                continue
        return photoList

    def removeVehicle(self,shareJob):
        shareAccount = shareJob.get("share_account", None)
        if shareAccount is None:
            logger.error("login fail")
            return errorcode.AUTH_ERROR, errormsg.LOGIN_FAIL
        if shareAccount.get('account_type', None) == 'public':
            shareAccount['username'] = publicAccount['username']
            shareAccount['password'] = publicAccount['password']

        logger.debug("che168 removeVehicle")
        cookies = self.sessionServer.getSession('che168', shareAccount['username'])
        if cookies is None:
            res = self.doLogin(shareAccount['username'], shareAccount['password'])
            if not res:
                logger.debug("login error")
                return errorcode.AUTH_ERROR, errormsg.LOGIN_FAIL
            self.sessionServer.setSession('che168', shareAccount['username'], self.cookies)
        else:
            self.cookies = cookies
            ks = self.cookies.keys()
            cookie_list = []
            for k in ks:
                cookie_list.append(k + '=' + self.cookies[k])
            self.headers['Cookie'] = string.join(cookie_list, '; ')

        urlForApp = shareJob.get("url", None)
        if urlForApp is not None and len(urlForApp) > 0:
            dealerid = re.compile("[0-9]\d{5}").findall(urlForApp)[0]
            infoid = re.compile("[0-9]\d{6}").findall(urlForApp)[0]
            conn = httplib.HTTPConnection('dealer.che168.com', timeout=timeout_che168)
            # 删除
            # url = "/Handler/CarManager/CarOperate.ashx?dealerid=" + dealerid + "&action=del&status=2&infoid=" + infoid + "&price=&buyname=&buyMobile="
            #下架
            #/Handler/CarManager/CarOperate.ashx?dealerid=216813&action=overtime&status=1&infoid=6657254&price=&buyname=&buyMobile=&sourcePic=undefined&vinPic=undefined&vinCode=undefined
            url = "/Handler/CarManager/CarOperate.ashx?dealerid=" + dealerid + "&action=overtime&status=1&infoid=" + infoid + "&price=&buyname=&buyMobile=&sourcePic=undefined&vinPic=undefined&vinCode=undefined"
            print url
            headers = copy.copy(self.headers)
            conn.request("GET", url, headers=headers)
            res = conn.getresponse()
            result = self.decodeBody(res.getheaders(), res.read())
            print result
            if result == "1":
                return errorcode.SUCCESS, ""
            else:
                return errorcode.SITE_ERROR, errormsg.VEHICLE_REMOVE_FAIL
        else:
            return errorcode.DATA_ERROR, errormsg.VEHICLE_URL_EMPTY

    # =======================================================
    # update Vehicle for che168 by yjy on 2014-12-15
    # =======================================================
    def updateVehicle(self, shareJob):
        logger.debug("che168 update vehicle")
        #登陆模块：
        shareAccount = shareJob.get("share_account", None)
        if shareAccount is None:
            logger.error("get shareAccount failed")
            return errorcode.AUTH_ERROR, errormsg.LOGIN_FAIL
        if shareAccount.get('account_type', None) == 'public':
            shareAccount['username'] = publicAccount['username']
            shareAccount['password'] = publicAccount['password']

        #cookies = self.sessionServer.getSession('che168', shareAccount['username'])
        cookies = None
        if cookies is None:
            res = self.doLogin(shareAccount['username'], shareAccount['password'])
            if not res:
                logger.debug("login error")
                return errorcode.AUTH_ERROR, errormsg.LOGIN_FAIL
            self.sessionServer.setSession('che168', shareAccount['username'], self.cookies)
        else:
            self.cookies = cookies
            ks = self.cookies.keys()
            cookie_list = []
            for k in ks:
                cookie_list.append(k + '=' + self.cookies[k])
            self.headers['Cookie'] = string.join(cookie_list, '; ')

        #获取修改的车源url中id，以及post
        urlForApp = shareJob.get("url", None)
        if (urlForApp is not None) and (len(urlForApp) > 0):
            idInfo = re.compile("[0-9]{7}").findall(str(urlForApp))
            if len(idInfo):
                id = idInfo[0]
            else:
                id = ""
                logger.debug("get dealerid failed in che168 update vehicle")

            #1.0 get请求修改
            #http://dealer.che168.com/Handler/CarManager/CarOperate.ashx?action=getSaleDealerPrice&infoId=6402915&dealerId=216816
            dealerid = str(self.cookies['2scDealerId'])
            editUrl = '/Handler/CarManager/CarOperate.ashx?action=getSaleDealerPrice&infoId=%s&dealerId=%s' % (id, dealerid)
            logger.debug("get url:"+str(editUrl))
            conn = httplib.HTTPConnection('dealer.che168.com', timeout=timeout_che168)
            headers = copy.copy(self.headers)
            conn.request("GET", editUrl, headers=headers)
            res = conn.getresponse()
            logger.debug("res:"+str(res))
            carRes1 = res.read()
            #'{"success":0,"price":"0.0000","issale":0}'
            if res.status!=200:
                return errorcode.SITE_ERROR, 'che168 update failed'

            #获取验证码：
            validcode = ''
            self.setCookies(res.getheaders())
            carRes = res.read()#.decode("GB18030")
            html = self.decodeBody(res.getheaders(),carRes)
            html = html.decode('GB18030')
            #html = res.read().decode('GB18030')
            if html.count(u'验证码') == 0:
                validcode = 'undefined'
                conn.close()
            else:
                dom = lxml.html.fromstring(html)
                checkCodeImageUrls = dom.xpath('.//span/img[@src]/@src')
                if len(checkCodeImageUrls) == 0:
                    return False
                checkCodeImageUrl = checkCodeImageUrls[0]
                conn.close()

                headers = {}#self.headers
                headers['Host'] = 'dealer.che168.com'
                conn = httplib.HTTPConnection("dealer.che168.com", timeout=timeout_che168)
                conn.request("GET", checkCodeImageUrl, headers=headers)
                res = conn.getresponse()
                resHeader = res.getheaders()
                logger.debug("resHeader === " + str(resHeader))
                self.setCookies(resHeader)
                imageData = res.read()
                conn.close()
                image = StringIO(imageData)
                captcha = self.getCaptcha(image, imageData)

                if captcha is None:
                    return False
                validcode = captcha["text"]


            #2.0 post 发车
            #http://dealer.che168.com/Handler/CarManager/CarOperate.ashx?dealerid=216816&action=setprice&status=1&infoid=6402915&price=3.30&buyname=&buyMobile=&sourcePic=undefined&vinPic=undefined&vinCode=undefined
            vehicle = shareJob.get('vehicle', None)
            if vehicle is None or vehicle == '':
                return errorcode.DATA_ERROR, u'缺少车辆信息'
            price = vehicle.get('price', None)
            if price is None or '' == price:
                return errorcode.DATA_ERROR, u'车辆价格为空'
            newPrice = price.get('quoted_price', None)
            if newPrice is None or '' == newPrice:
                return errorcode.DATA_ERROR, u'车辆价格为空'
            newPrice = Decimal(newPrice)/Decimal(10000)

            updateUrl = '/Handler/CarManager/CarOperate.ashx?dealerid=%s&action=setprice&status=1&infoid=%s&price=%s&buyname=&buyMobile=&sourcePic=undefined&vinPic=undefined&vinCode=%s' % (dealerid, id, newPrice, validcode)
            conn = httplib.HTTPConnection('dealer.che168.com', timeout=timeout_che168)
            headers = copy.copy(self.headers)
            conn.request("GET", updateUrl, headers=headers)
            res = conn.getresponse()
            logger.debug("res:"+str(res))
            if res.status != 200:
                return errorcode.SITE_ERROR, 'che68 update failed'
            return errorcode.SUCCESS, 'che168 update success'

