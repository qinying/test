#!/usr/bin/python
# -*- coding: UTF-8 -*-
import copy
import httplib
from StringIO import StringIO
import json
import time
import string
import urllib
from urlparse import urlparse
from decimal import Decimal
import random

import zlib
import tz
import re
import resize
import logger
import lxml
import errorcode
import errormsg
from base import BaseSharer


publicAccount = {
    "username": u"beijingesc01",
    "password": u"123123"
}

HOST = "v.51auto.com"
CODEC = "GBK"
MAX_PIC = 15
timeout = 60

class FOAutoSharer(BaseSharer):
    def __init__(self, sessionServer, specServer):
        super(FOAutoSharer, self).__init__(sessionServer, specServer)

    @staticmethod
    def millis():
        return int(round(time.time() * 1000))

    def doLogin(self, username, password):
        host = HOST
        codec = CODEC
        conn = httplib.HTTPConnection(host, timeout=timeout)
        conn.request("GET", "/control/VerifyUser?" + self.rnd(), headers=self.headers)
        res = conn.getresponse()
        self.setCookies(res.getheaders())
        html = self.decodeBody(res.getheaders(), res.read())
        html = html.decode(codec)
        dom = lxml.html.fromstring(html)
        # /ValidateCode?type=login&rand='+ Math.round(Math.random() * 100000)
        forwardUrl = dom.xpath('//*[@name="forward"]/@value')[0]
        conn.close()

        validcode = None

        if html.count(u"验证码") > 0:
            checkCodeImageUrl = '/ValidateCode?type=login&rand=' + str(round(random.random() * 100000))

            conn = httplib.HTTPConnection(host, timeout=timeout)
            conn.request("GET", checkCodeImageUrl, headers=self.headers)
            res = conn.getresponse()
            self.setCookies(res.getheaders())
            imageData = res.read()
            imageData2 = zlib.decompress(imageData, 16+zlib.MAX_WBITS)
            conn.close()
            image = StringIO(imageData2)
            captcha = self.getCaptcha(image, imageData)

            if captcha is None:
                return False

            validcode = captcha["text"]

        conn = httplib.HTTPConnection(host, timeout=timeout)
        url = "/control/VerifyUser?" + self.rnd()

        logger.debug(forwardUrl)
        formData = {"forward": forwardUrl, "username": username.encode(codec), "password": password, "autoLogin": "1"}
        if validcode is not None:
            formData["ValidateCode"] = validcode

        headers = copy.copy(self.headers)
        headers["Content-type"] = "application/x-www-form-urlencoded"
        headers["Referer"] = host
        conn.request("POST", url, urllib.urlencode(formData), headers=headers)

        res = conn.getresponse()
        result = self.decodeBody(res.getheaders(), res.read())
        result = result.decode(codec)
        conn.close()

        if result.lstrip().startswith("<SCRIPT LANGUAGE"):
            self.setCookies(res.getheaders())
            return True
        return False


    def loadNewVehiclePage(self):
        conn = httplib.HTTPConnection(HOST, timeout=timeout)
        headers = copy.copy(self.headers)
        #logger.debug(headers)

        ks = self.cookies.keys()
        cookie_list = []
        for k in ks:
            if "51autoUserId" == self.cookies[k]:
                cookie_list.append(k + '=' + self.cookies[k])
                #cookie_list.append(k + '=' + urllib.quote(u'北京二手车网'));
            else:
                cookie_list.append(k + '=' + self.cookies[k])
        self.headers['Cookie'] = string.join(cookie_list, '; ')

        logger.debug(headers)

        #http://v.51auto.com/control/DealerPublishAd?opt%A3%BDnew&d=1431575657771
        new_vehicle_url = "/control/DealerPublishAd?opt=new&rd=" + str(self.millis()) + "&" + self.rnd()
        conn.request("GET", new_vehicle_url, headers=headers)
        res = conn.getresponse()
        html = self.decodeBody(res.getheaders(), res.read())
        conn.close()
        html = html.decode(CODEC)
        html = html.replace("gbk", "utf-8")
        dom = lxml.html.fromstring(html)
        return dom

    def loadEditVehicleDom(self,pageid ):
        conn = httplib.HTTPConnection(HOST, timeout=timeout)
        headers = copy.copy(self.headers)
        # http://www.51auto.com/control/AdUpdate?adID=2450176&rd=476
        edit_vehicle_url = "/control/AdUpdate?adID=" + pageid + "&rd="
        conn.request("GET", edit_vehicle_url, headers=headers)
        res = conn.getresponse()
        html = self.decodeBody(res.getheaders(), res.read())
        conn.close()
        html = html.decode(CODEC)
        html = html.replace("gbk", "utf-8")
        dom = lxml.html.fromstring(html)
        return dom

    def loadEditVehicleHtml(self,pageid ):
        conn = httplib.HTTPConnection(HOST, timeout=timeout)
        headers = copy.copy(self.headers)
        # http://www.51auto.com/control/AdUpdate?adID=2450176&rd=476
        edit_vehicle_url = "/control/AdUpdate?adID=" + pageid + "&rd="
        conn.request("GET", edit_vehicle_url, headers=headers)
        res = conn.getresponse()
        html = self.decodeBody(res.getheaders(), res.read())
        conn.close()
        html = html.decode(CODEC)
        html = html.replace("gbk", "utf-8")
        #dom = lxml.html.fromstring(html)
        return html


    def retrieveSalesId(self, dom, mobile):
        salesid = None
        options = dom.xpath('//*[@id="salerId"]/option')
        for option in options:
            if option.text.count(str(mobile)):
                salesid = option.get("value")
        return salesid
        '''
        #http://v.51auto.com/control/DealerPublishAd?opt=new
        conn = httplib.HTTPConnection(HOST, timeout=timeout)
        headers = copy.copy(self.headers)
        conn.request('GET', '/control/DealerPublishAd?opt=new', headers=headers)
        res = conn.getresponse()
        html = self.decodeBody(res.getheaders(), res.read())
        conn.close()

        if html.count(mobile) > 0:
            return True
        '''


    def shareVehicle(self, shareJob):
        shareAccount = shareJob.get("share_account", None)
        if shareAccount is None:
            return errorcode.AUTH_ERROR, ""
        if shareAccount.get('account_type', None) == 'public':
            shareAccount['username'] = publicAccount['username']
            shareAccount['password'] = publicAccount['password']

        logger.debug("51auto shareVehicle")
        # cookies = self.sessionServer.getSession('51auto', shareAccount['username'])
        cookies = None
        if cookies is None:
            res = self.doLogin(shareAccount['username'], shareAccount['password'])
            if not res:
                logger.debug("login error")
                return errorcode.AUTH_ERROR, errormsg.LOGIN_FAIL
            self.sessionServer.setSession('51auto', shareAccount['username'], self.cookies)
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

        user = vehicle.get("user", None)
        if user is None:
            return errorcode.LOGIC_ERROR, errormsg.USER_EMPTY

        # if shareAccount.get('account_type', None) == 'public':
        (name, mobile) = self.getContact(shareJob)
        #     mobile = publicAccount.get('phone')
        #     name = publicAccount.get("name", None)
        # else:
        #     mobile = user.get("public_phone", None)
        #     name = user.get("name", None)

        if mobile is None:
            return errorcode.LOGIC_ERROR, errormsg.MOBILE_EMPTY
        if name is None:
            return errorcode.LOGIC_ERROR, errormsg.USER_EMPTY

        spec = vehicle.get("spec", None)
        if spec is None:
            logger.error("spec missing")
            return errorcode.LOGIC_ERROR, errormsg.VEHICLE_SPEC_EMPTY
        levelId = spec.get("level_id", None)
        if levelId is None:
            logger.error("levelId missing")
            return errorcode.LOGIC_ERROR, errormsg.VEHICLE_SPEC_EMPTY
        logger.debug("levelId=" + levelId)

        dom = self.loadNewVehiclePage()

        salesid = self.retrieveSalesId(dom, mobile)
        # 如果没有销售代表,则创建一个
        if salesid is None:
            if self.createNewContact(mobile, name):
                # 创建成功, 重新加载发车页面
                dom = self.loadNewVehiclePage()
                # 重新匹配销售代表
                salesid = self.retrieveSalesId(dom, mobile)

        if salesid is None:
            return errorcode.SITE_ERROR, errormsg.PARAMETER_UNRESOLVED
        logger.debug("salesid=" + str(salesid))

        form = dict()

        form['subID'] = dom.xpath('//*[@id="publish"]/input[@name="subID"]/@value')[0]
        form['provinceID'] = dom.xpath('//*[@id="publish"]/input[@name="provinceID"]/@value')[0]
        form['zoneID'] = dom.xpath('//*[@id="publish"]/input[@name="zoneID"]/@value')[0]
        form['ID'] = 0
        form['adID'] = dom.xpath('//*[@id="publish"]/input[@name="adID"]/@value')[0]
        form['combo'] = dom.xpath('//*[@id="publish"]/input[@name="combo"]/@value')[0]
        form['priority'] = dom.xpath('//*[@id="publish"]/input[@name="priority"]/@value')[0]
        form['validdays'] = dom.xpath('//*[@id="publish"]/input[@name="validdays"]/@value')[0]
        form['vctypebelong'] = dom.xpath('//*[@id="publish"]/input[@name="vctypebelong"]/@value')[0]
        form['service'] = "5,7,3,8,2,6,4,11"
        form['rank'] = 0
        form["salerId"] = salesid
        form["telephone"] = mobile
        form["usage"] = self.getUsage(vehicle)
        summary = vehicle.get("summary")
        maintenance = summary.get("maintenance")
        if maintenance:
            form['repair_recorder'] = 1
        else:
            form['repair_recorder'] = 0

        mileage = summary.get("mileage");
        if mileage is not None:
            form["distance"] = str(Decimal(mileage) / Decimal(10000))

        price = self.getPrice(shareJob)
        if price is not None:
            form["price"] = str(Decimal(price) / Decimal(10000))
        includeTransferFee = vehicle.get("price").get("quoted_price_include_transfer_fee", None)
        transferFee = 0
        if includeTransferFee is not None and includeTransferFee:
            transferFee = 1
        form["transferFee"] = transferFee
        form["isShow"] = 0

        # vin码
        vin = vehicle.get("vin", None)
        if vin is None:
            vin = ""
        form["vin"] = str(vin)

        form['color'] = self.getColorCode(shareJob)
        interior = summary.get('interior', None)
        innerColor = 0
        if interior is not None and interior.count(u'深'):
            innerColor = 1
        form["innerColor"] = innerColor
        form["transfer"] = self.getTransferTimes(vehicle)

        # 车辆卖点 share:
        sellingPoint = vehicle.get("desc").get("brief")
        if '' == sellingPoint:
            sellingPoint = u'此车可贷款 只需身份证'
        if sellingPoint is not None:
            form["sellingPoint"] = sellingPoint.encode(CODEC)

        # 车辆描述
        # description = self.getContentVal_51auto(shareJob)
        Symbol = "\r\n"
        lateral = "——"*25
        description = self.getContentVal(shareJob, Symbol=Symbol, lateral=lateral)
        if description is not None:
            form["description"] = description.encode(CODEC)

        registrationDate = vehicle.get("vehicle_date").get("registration_date").astimezone(tz.HKT)
        if registrationDate is not None:
            form["reg_year"] = registrationDate.year
            form["reg_month"] = registrationDate.month
            if '' == form['reg_year']:
                form['reg_year'] = 2015
            if '' == form['reg_month']:
                form['reg_month'] = 5

        inspectionDate = vehicle.get("vehicle_date").get("inspection_date")
        if inspectionDate is not None:
            form["mot_year"] = inspectionDate.year
            form["mot_month"] = inspectionDate.month
            if '' == form['mot_year']:
                form['mot_year'] = 2016
            if '' == form['mot_month']:
                form['mot_month'] = 6

        compulsoryInsuranceExpireDate = vehicle.get("vehicle_date").get("compulsory_insurance_expire_date")
        if compulsoryInsuranceExpireDate is not None:
            form["insurance_year"] = compulsoryInsuranceExpireDate.year
            form["insurance_month"] = compulsoryInsuranceExpireDate.month
            if '' == form['insurance_year']:
                form['insurance_year'] = form['mot_year']
            if '' == form['insurance_month']:
                form['insurance_month'] = form['mot_month']

        docs = vehicle.get("document")
        if docs.get("purchase_tax"):
            form['surtax'] = 1
        else:
            form['surtax'] = 0

        form['driving_license'] = 1

        if docs.get("transfer_ticket"):
            form['invoice'] = 1
        else:
            form['invoice'] = 0
        form['repair_recorder'] = 1

        # form['make'] = "PGDF"
        # form['family'] = "307"
        # form['yearGroupId'] = "200900"
        # form['file'] = "LY001482"
        externalVehicleSpec = shareJob.get('external_vehicle_spec')
        if externalVehicleSpec is None:
            return errorcode.DATA_ERROR, errormsg.EXTERNAL_SPEC_EMPTY
        form['make'] = str(externalVehicleSpec.get('vendor').get('id'))
        form['family'] = str(externalVehicleSpec.get('series').get('id'))

        # yearGroupId: 201100
        # 车型库更新后的兼容性:
        mfd = externalVehicleSpec.get('model').get('mfd', None)
        if mfd is None:
            mfd = externalVehicleSpec.get('model').get('year', "") + "00"
        form['yearGroupId'] = mfd


        form['file'] = str(externalVehicleSpec.get('model').get('id'))

        gallery = vehicle.get("gallery", None)
        if gallery is None:
            logger.error("gallery missing")
            return errorcode.LOGIC_ERROR, errormsg.PHOTO_NOT_ENOUGH
        photoList = self.uploadPics(gallery.get("photos", []))
        # photoList = []
        # photoList.append('http://picture.51auto.com/tmp/pic820140823190004-u2h5G.jpeg')
        logger.debug(json.dumps(photoList))
        photoKeys = self.makePhotos(photoList)
        form['pics'] = photoKeys  # pics
        form['fpic'] = photoKeys[0]  # feature pic
        (success, msg) = self.postVehicle(form)
        if success:
            msg = self.reUrl(shareJob)
            return errorcode.SUCCESS, msg
        return errorcode.LOGIC_ERROR, errormsg.SITE_OTHER_ERROR

    @staticmethod
    def makePhotos(photoList):
        photos = []
        for photo in photoList:
            # 'http://picture.51auto.com/tmp/pic820140823190004-u2h5G.jpeg'
            path = photo.replace('http://picture.51auto.com', '')
            photos.append(path)
        return ",".join(photos)

    @staticmethod
    def getColorCode(shareJob):
        colorCode = "0"
        colorTable = {"black": "1", "white": "2", "red": "5", "yellow": "8",
                      "blue": "6", "green": "7", "purple": "11", "silver": "13", "grey": "3",
                      "champagne": "10", "other": "0"}
        vehicle = shareJob.get("vehicle", None)
        if vehicle is not None:
            summary = vehicle.get("summary", None)
            if summary is not None:
                color = summary.get("color", None)
                colorCode = colorTable.get(color, "0")
        return colorCode

    def postVehicle(self, form):
        # logger.debug(form)
        ks = self.cookies.keys()
        cookie_list = []
        for k in ks:
            cookie_list.append(k + '=' + self.cookies[k])
        self.headers['Cookie'] = string.join(cookie_list, '; ')
        # http://www.51auto.com/control/DealerPublishAd?action=publishSubmit
        conn = httplib.HTTPConnection(HOST, timeout=timeout)
        headers = copy.copy(self.headers)
        #TODO:此处不能限制长度？？？？
        #headers['Content-Length'] = len(form)
        headers['Content-Type'] = 'application/x-www-form-urlencoded'
        conn.request("POST", "/control/DealerPublishAd?action=publishSubmit&" + self.rnd(), urllib.urlencode(form),
                     headers=headers)
        res = conn.getresponse()
        carRes = self.decodeBody(res.getheaders(), res.read())
        result = carRes.decode(CODEC)
        logger.debug(result)

        if result.count(u'车源发布成功') > 0:
            logger.debug("success for 51")
            return True, ""

        logger.debug("failed for 51")
        return False, ""

    def uploadPicContent(self, content):
        # http://www.51auto.com/AttachFileSubmit;jsessionid=9889D41ED01FC8ACCB17C40CA448EBCF-n2?model=new&leval=1&picId=pic8
        # FILEID:http://picture.51auto.com/tmp/pic820140821135536-hU5ws.jpg
        conn = httplib.HTTPConnection(HOST, timeout=timeout)
        headers = copy.copy(self.headers)
        jsessionid = self.cookies.get("JSESSIONID", None)

        logger.debug(jsessionid)
        img = StringIO(content)
        smallImg = StringIO()
        resize.resize(img, (600, 600), False, smallImg)
        boundaryHeader = "----pluploadboundary1408600538106"
        headers['Referer'] = 'http://www.51auto.com/static/js/plupload/plupload.flash.swf?77792'
        headers['Origin'] = 'http://www.51auto.com'
        headers["Content-Type"] = "multipart/form-data; boundary=" + boundaryHeader
        content = smallImg.getvalue()
        boundary = "--" + boundaryHeader
        picForm = boundary + '\r\n' + 'Content-Disposition: form-data; name="name"\r\n\r\n'
        picForm += "aa.jpg\r\n"
        picForm += boundary + '\r\n' + 'Content-Disposition: form-data; name="file"; filename="aa.jpg"\r\nContent-Type: image/jpeg\r\n\r\n'
        picForm += str(content) + '\r\n'
        picForm += boundary + "--"
        headers['Content-Length'] = len(picForm)
        conn.request("POST", "/AttachFileSubmit;jsessionid" + str(jsessionid) + "?model=new&leval=1&picId=pic8",
                     picForm,
                     headers=headers)
        res = conn.getresponse()
        result = self.decodeBody(res.getheaders(), res.read())

        conn.close()

        result = result.decode(CODEC)

        if result.count(u"http") > 0:
            return result.replace('FILEID:', '')
        return None

    def uploadPics(self, photos):
        photo_list = []
        photos = photos[:MAX_PIC]  # 最多15张图
        for photo in photos:
            url = photo.get("url", None)
            if url is None:
                continue
            o = urlparse(url)
            host = o.netloc
            uri = o.path

            upload = self.sessionServer.getUpload('51auto', uri)
            logger.debug('--upload-- \n' + str(upload))
            if upload is not None:
                res = json.loads(upload)
            else:
                host = 'pic.kanche.com'
                # if host == 'pic.kanche.com':
                #     host = 'kanche-pic.qiniudn.com'
                conn = httplib.HTTPConnection(host, timeout=timeout)
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
                    photo_list.append(result)
        return photo_list

    def getCarSpec(self, levelId):  # 获取che168车型id
        modelId = self.specServer.getModelId('51auto', levelId)
        return modelId


    # 创建销售代表
    def createNewContact(self, mobile, name):

        conn = httplib.HTTPConnection(HOST, timeout=timeout)
        headers = copy.copy(self.headers)
        headers['Content-Type'] = 'application/x-www-form-urlencoded'
        formData = {"invoke": "new", "role": "12", "isLogin": "1", "name": name.encode(CODEC), "mobile": mobile,
                    "pagemobile": str(mobile), "accountID": str(mobile) + str(random.randint(0, 10000)),
                    "pswd": str(mobile), "login": '1'}
        conn.request("POST",
                     "/control/DealerEmployee?" + self.rnd(), urllib.urlencode(formData),
                     headers=headers)
        res = conn.getresponse()
        html = self.decodeBody(res.getheaders(), res.read())
        conn.close()

        html = html.decode(CODEC)

        #http://v.51auto.com/control/DealerPublishAd?opt=new
        conn = httplib.HTTPConnection(HOST, timeout=timeout)
        headers = copy.copy(self.headers)
        conn.request('GET', '/control/DealerPublishAd?opt=new', headers=headers)
        res = conn.getresponse()
        html = self.decodeBody(res.getheaders(), res.read())
        conn.close()

        if html.count(mobile.encode('utf-8')):
            return True
            # salesidRe = re.findall('javascript\:removeEmployee\((?P<salesid>.*)\)', html)
            # salesid = None
            # if salesidRe is not None:
            # len = len(salesidRe)
            # salesid = salesidRe.get(len - 1)
            #
            # if salesid is not None:
            # return salesid
            # # return self.getContact(mobile);
        return False

    @staticmethod
    def rnd():
        return str(random.random())

    # 根据手机号获得销售代表ID
    def get51Contact(self, mobile):
        host = HOST
        conn = httplib.HTTPConnection(host, timeout=timeout)
        headers = copy.copy(self.headers)
        formData = {"mobile": str(mobile)}  # , "canLogin": "", "mail": "", "role": "", "name": ""}
        headers['Content-Type'] = 'application/x-www-form-urlencoded'
        conn.request("POST", "/control/DealerEmployeeList", urllib.urlencode(formData), headers=headers)
        res = conn.getresponse()
        html = self.decodeBody(res.getheaders(), res.read())
        conn.close()
        html = html.decode(CODEC)

        # javascript:removeEmployee(850007)
        salesidRe = re.search('javascript\:removeEmployee\((?P<salesid>.*)\)', html)
        salesid = None
        if salesidRe is not None:
            salesid = salesidRe.group('salesid')

        if salesid is not None:
            return salesid
        return self.createNewContact(mobile)

    @staticmethod
    def getUsage(vehicle):
        # 非营运 0, 营运1, 营转非2, 租赁车4,试驾车5
        purpose = vehicle.get("summary").get("purpose")
        if purpose == "business":
            return 1
        if purpose == "personal":
            return 0
        if purpose == "lease":
            return 4
        return 0

    @staticmethod
    def getTransferTimes(vehicle):
        # 过户次数, 100 未知, 99 0次(一手车), 1, 2, 3, 4, 5 (次), 10 为5次以上
        tradeTimes = vehicle.get('summary').get('trade_times')
        if tradeTimes == 0:
            return 99
        if 0 < tradeTimes < 6:
            return tradeTimes
        if tradeTimes > 5:
            return 10
        return 100

    def removeVehicle(self,shareJob):
        shareAccount = shareJob.get("share_account", None)
        if shareAccount is None:
            return errorcode.AUTH_ERROR, ""
        if shareAccount.get('account_type', None) == 'public':
            shareAccount['username'] = publicAccount['username']
            shareAccount['password'] = publicAccount['password']

        logger.debug("51auto removeVehicle")
        # cookies = self.sessionServer.getSession('51auto', shareAccount['username'])
        cookies = None
        if cookies is None:
            res = self.doLogin(shareAccount['username'], shareAccount['password'])
            if not res:
                logger.debug("login error")
                return errorcode.AUTH_ERROR, errormsg.LOGIN_FAIL
            self.sessionServer.setSession('51auto', shareAccount['username'], self.cookies)
        else:
            self.cookies = cookies
            ks = self.cookies.keys()
            cookie_list = []
            for k in ks:
                cookie_list.append(k + '=' + self.cookies[k])
            self.headers['Cookie'] = string.join(cookie_list, '; ')

        urlForApp = shareJob.get("url", None)
        # if len(urlForApp):
        if urlForApp is not None and len(urlForApp) > 0:
            queryIds = re.compile("[0-9]\d{3,}").findall(urlForApp)[0]
            conn = httplib.HTTPConnection(HOST, timeout=timeout)
            url = "/control/MyAuto?page=6&salerId=-1&action=setExpire&queryIds=" + queryIds
            print url
            headers = copy.copy(self.headers)
            conn.request("GET", url, headers=headers)
            res = conn.getresponse()
            postHeader = res.getheaders()
            logger.debug("--postHeaders--\n" + str(postHeader))
            logger.debug("--post--\n" + res.read())
            return errorcode.SUCCESS, ""
        else:
            return errorcode.DATA_ERROR, errormsg.VEHICLE_URL_EMPTY

    # =======================================================
    # update Vehicle for 51auto by yjy on 2014-12-16
    # =======================================================
    def updateVehicle(self,shareJob):
        shareAccount = shareJob.get("share_account", None)
        if shareAccount is None:
            return errorcode.AUTH_ERROR, ""
        if shareAccount.get('account_type', None) == 'public':
            shareAccount['username'] = publicAccount['username']
            shareAccount['password'] = publicAccount['password']

        logger.debug("51auto update vehicle")
        # cookies = self.sessionServer.getSession('51auto', shareAccount['username'])

        cookies = None
        # 登陆模块：
        if cookies is None:
            res = self.doLogin(shareAccount['username'], shareAccount['password'])
            if not res:
                logger.debug("login error")
                return errorcode.AUTH_ERROR, errormsg.LOGIN_FAIL
            self.sessionServer.setSession('51auto', shareAccount['username'], self.cookies)
        else:
            self.cookies = cookies
            ks = self.cookies.keys()
            cookie_list = []
            for k in ks:
                cookie_list.append(k + '=' + self.cookies[k])
            self.headers['Cookie'] = string.join(cookie_list, '; ')

        # 补齐post表单:
        urlForApp = shareJob.get("url", None)
        if urlForApp is None or len(urlForApp) == 0 :
            logger.debug("get url failed")
            return errorcode.DATA_ERROR, errormsg.VEHICLE_URL_EMPTY
        else:
            # pageid
            queryIds = re.compile("[0-9]\d{3,}").findall(urlForApp)
            if len(queryIds) == 0:
                logger.debug("get id failed")
                return False
            pageid = queryIds[0]

            vehicle = shareJob.get("vehicle", None)
            if vehicle is None:
                logger.error("vehicle missing")
                return errorcode.LOGIC_ERROR, errormsg.VEHICLE_EMPTY
            # vehicle items:
            user = vehicle.get("user", None)
            if user is None:
                return errorcode.LOGIC_ERROR, errormsg.USER_EMPTY
            (name, mobile) = self.getContact(shareJob)

            if mobile is None:
                return errorcode.LOGIC_ERROR, errormsg.MOBILE_EMPTY
            if name is None:
                return errorcode.LOGIC_ERROR, errormsg.USER_EMPTY

            spec = vehicle.get("spec", None)
            if spec is None:
                logger.error("spec missing")
                return errorcode.LOGIC_ERROR, errormsg.VEHICLE_SPEC_EMPTY
            levelId = spec.get("level_id", None)
            if levelId is None:
                logger.error("levelId missing")
                return errorcode.LOGIC_ERROR, errormsg.VEHICLE_SPEC_EMPTY
            logger.debug("levelId=" + levelId)

            # 编辑页面 get 请求
            # dom = self.loadEditVehicleDom(pageid)
            html = self.loadEditVehicleHtml(pageid)
            dom = lxml.html.fromstring(html)

            salesid = self.retrieveSalesId(dom, mobile)
            # 如果没有销售代表,则创建一个
            if salesid is None:
                if self.createNewContact(mobile, name):
                    # 创建成功, 重新加载发车页面
                    dom = self.loadEditVehiclePage(pageid,html)
                    # 重新匹配销售代表
                    salesid = self.retrieveSalesId(dom, mobile)

            if salesid is None:
                return errorcode.SITE_ERROR, errormsg.PARAMETER_UNRESOLVED
            logger.debug("salesid=" + str(salesid))

            form = dict()
            form['subID'] = dom.xpath('//*[@id="publish"]/input[@name="subID"]/@value')[0]
            form['provinceID'] = dom.xpath('//*[@id="publish"]/input[@name="provinceID"]/@value')[0]
            form['zoneID'] = dom.xpath('//*[@id="publish"]/input[@name="zoneID"]/@value')[0]
            form['ID'] = dom.xpath('//*[@id="publish"]/input[@name="ID"]/@value')[0]                 #add form by yjy:
            form['adID'] = dom.xpath('//*[@id="publish"]/input[@name="adID"]/@value')[0]
            form['combo'] = dom.xpath('//*[@id="publish"]/input[@name="combo"]/@value')[0]
            form['priority'] = dom.xpath('//*[@id="publish"]/input[@name="priority"]/@value')[0]
            form['validdays'] = dom.xpath('//*[@id="publish"]/input[@name="validdays"]/@value')[0]
            form['vctypebelong'] = dom.xpath('//*[@id="publish"]/input[@name="vctypebelong"]/@value')[0]
            form['service'] = "5,7,3,8,2,6,4,11"
            form['rank'] = 0
            form["salerId"] = salesid
            form["telephone"] = mobile
            form["usage"] = self.getUsage(vehicle)
            summary = vehicle.get("summary")
            maintenance = summary.get("maintenance");
            if maintenance:
                form['repair_recorder'] = 1
            else:
                form['repair_recorder'] = 0

            mileage = summary.get("mileage")
            if mileage is not None:
                form["distance"] = str(Decimal(mileage) / Decimal(10000))

            price = self.getPrice(shareJob)
            if price is not None:
                form["price"] = str(Decimal(price) / Decimal(10000))
            includeTransferFee = vehicle.get("price").get("quoted_price_include_transfer_fee", None)
            transferFee = 0
            if includeTransferFee is not None and includeTransferFee:
                transferFee = 1
            form["transferFee"] = transferFee
            # form["isShow"] = 0
            form["vin"] = vehicle.get("vin")
            form['color'] = self.getColorCode(shareJob)
            interior = summary.get('interior', None)
            innerColor = 0
            if interior is not None and interior == 'dark':
                innerColor = 1
            form["innerColor"] = innerColor
            form["transfer"] = self.getTransferTimes(vehicle)

            # 车辆卖点 update:
            sellingPoint = vehicle.get("desc").get("brief")
            if '' == sellingPoint:
                sellingPoint = u'此车可贷款 只需身份证'
            if sellingPoint is not None:
                form["sellingPoint"] = sellingPoint.encode(CODEC)

            # 车辆描述
            # description = self.getContentVal_51auto(shareJob)
            Symbol = "\r\n"
            lateral = "——"*25
            description = self.getContentVal(shareJob, Symbol=Symbol, lateral=lateral)
            if description is not None:
                form["description"] = description.encode(CODEC)

            registrationDate = vehicle.get("vehicle_date").get("registration_date").astimezone(tz.HKT)
            if registrationDate is not None:
                form["reg_year"] = registrationDate.year
                form["reg_month"] = registrationDate.month
                if '' == form['reg_year']:
                    form['reg_year'] = 2015
                if '' == form['reg_month']:
                    form['reg_month'] = 5

            inspectionDate = vehicle.get("vehicle_date").get("inspection_date")
            if inspectionDate is not None:
                form["mot_year"] = inspectionDate.year
                form["mot_month"] = inspectionDate.month
                if '' == form['mot_year']:
                    form['mot_year'] = 2016
                if '' == form['mot_month']:
                    form['mot_month'] = 6

            compulsoryInsuranceExpireDate = vehicle.get("vehicle_date").get("compulsory_insurance_expire_date")
            if compulsoryInsuranceExpireDate is not None:
                form["insurance_year"] = compulsoryInsuranceExpireDate.year
                form["insurance_month"] = compulsoryInsuranceExpireDate.month
                if '' == form['insurance_year']:
                    form['insurance_year'] = form['mot_year']
                if '' == form['insurance_month']:
                    form['insurance_month'] = form['mot_month']

            # 车船税 update
            form['roadtoll_year'] = form['mot_year']

            docs = vehicle.get("document")
            if docs.get("purchase_tax"):
                form['surtax'] = 1
            else:
                form['surtax'] = 0
            form['driving_license'] = 1

            if docs.get("transfer_ticket"):
                form['invoice'] = 1
            else:
                form['invoice'] = 0

            externalVehicleSpec = shareJob.get('external_vehicle_spec')
            if externalVehicleSpec is None:
                return errorcode.DATA_ERROR, errormsg.EXTERNAL_SPEC_EMPTY
            form['make'] = str(externalVehicleSpec.get('vendor').get('id'))
            form['family'] = str(externalVehicleSpec.get('series').get('id'))

            # yearGroupId: 201100
            # 车型库更新后的兼容性:
            mfd = externalVehicleSpec.get('model').get('mfd', None)
            if mfd is None:
                mfd = externalVehicleSpec.get('model').get('year', "") + "00"
            form['yearGroupId'] = mfd

            form['file'] = str(externalVehicleSpec.get('model').get('id'))

            # get pics from native:
            # change native photoList by yjy:
            photoList = self.getHtmlImglist(html)
            # logger.debug(json.dumps(photoList))
            fpic = photoList[0]
            pRule = r'pic.*'
            fpic = re.compile(pRule).findall(fpic)
            # form['fpic'] = urllib.quote_plus(fpic[0]) # feature pic
            form['fpic'] = fpic[0]
            photoKeys = ",".join(photoList)
            # form['pics'] = urllib.quote_plus(photoKeys)  # pics
            form['pics'] = photoKeys
            # end of change

            (success, msg) = self.postUpdateVehicle(form)
            if success:
                return errorcode.SUCCESS, msg
            return errorcode.LOGIC_ERROR, errormsg.SITE_OTHER_ERROR

    def postUpdateVehicle(self, form):
        # logger.debug(form)
        # http://www.51auto.com/control/DealerPublishAd?action=publishSubmit
        conn = httplib.HTTPConnection(HOST, timeout=timeout)
        headers = copy.copy(self.headers)
        # headers['Content-Length'] = len(form)
        headers['Content-Type'] = 'application/x-www-form-urlencoded'
        
        formData = urllib.urlencode(form)
        formData += '&provinceID=-1'
        formData += '&rank=0'
        formData += '&newPrice='
        formData += '&noPro=0'
        #车船使用税有效期

        conn.request("POST", "/control/DealerPublishAd?action=publishSubmit&" + self.rnd(), formData,
                     headers=headers)
        res = conn.getresponse()
        carRes = self.decodeBody(res.getheaders(), res.read())
        result = carRes.decode(CODEC)
        #logger.debug(result)
        print '+++++++++++++++++++++++++++++\n', formData, '\n+++++++++++++++++++++++++++++'

        if result.count(u'车源发布成功') > 0:
            return True, "update success"
        return False, ""

    def getHtmlImglist (self, html):
        #post:      /car/201412/17/pic820141217142231-Lqmdt.jpg,/car
        #src:       http://picture.51auto.com/car/201412/17/pic820141217145043-HkW0Q.jpg
        photoList = []
        pRule = r'(addPicToShow.*)'
        plist = re.compile(pRule).findall(html)
        #pRule = r'(/car.*(\.jpg)$)'
        pRule = r'(/car.*.jpg)'
        for li in plist:
            photo = re.compile(pRule).findall(li)
            #urllib.quote(self.getTitleVal(externalSpec, carInfo).encode('utf-8'))
            #photoList.append(urllib.quote_plus(photo[0].encode('utf-8')))
            photoList.append(photo[0])
        return photoList

    def checkUrlId(self, pageId, jobId):
        headers = copy.copy(self.headers)
        ##此处改网站仍然在使用旧版
        conn = httplib.HTTPConnection('www.51auto.com', timeout=10)
        url = "/buycar/%s.html" % pageId
        conn.request("GET", url, headers=headers)
        res1 = conn.getresponse()
        strhtml = self.decodeBody(res1.getheaders(), res1.read())
        url = 'http://www.51auto.com'+url
        return url,strhtml.find(jobId)>0


    ##
    #get url from the sent vehicle list:
    ##
    def reUrl(self, shareJob):
        vehicle = shareJob.get('vehicle', None)
        headers = copy.copy(self.headers)
        conn = httplib.HTTPConnection(HOST, timeout=timeout)
        url = "/control/MyAuto"
        headers['Host'] = 'www.51auto.com'
        headers['Referer'] = 'http://www.51auto.com/control/MyAutoDefault'
        conn.request("GET", url, headers=headers)
        res1 = conn.getresponse()
        strhtml = self.decodeBody(res1.getheaders(), res1.read())
        #print strhtml
        hxs = lxml.html.fromstring(strhtml.decode('gbk'))
        htmlurl = hxs.xpath(u'//span[@class="select_all"]/input/@value')
        time.sleep(0.8)
        for urlId in htmlurl:
            #默认为第一个:
            #检查第一个:
            pageId,checkFlag = self.checkUrlId(urlId, str(vehicle['_id']))
            print pageId,checkFlag,str(vehicle['_id'])
            if checkFlag:
                return pageId
        return ""

