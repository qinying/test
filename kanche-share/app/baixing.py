#!/usr/bin/python
# -*- coding: UTF-8 -*-

import json
import re
import tz
from urlparse import urlparse

import zlib
import httplib
import urllib
import string
import copy
from decimal import *
from StringIO import StringIO
import errormsg
from cityBaixing import CityBaixing
import resize
import time

import lxml
import lxml.html
import errorcode
import logger
from base import BaseSharer

publicAccount = {
    "username": u"15300067246",
    "password": u"111206bai"
}


class BaixingSharer(BaseSharer):
    def __init__(self, sessionServer, specServer):
        super(BaixingSharer, self).__init__(sessionServer, specServer)
        self.cityBaixing = CityBaixing()


    def doLogin(self, username, password):
        result = False
        host = "www.baixing.com"
        uri = "/oz/login/x"
        codec = "utf8"
        conn = httplib.HTTPConnection(host, timeout=10)
        conn.request("GET", uri, headers=self.headers)
        getResponse = conn.getresponse()
        getHeaders = getResponse.getheaders()
        self.setCookies(getHeaders)
        getHtml = zlib.decompress(getResponse.read(), 16 + zlib.MAX_WBITS).decode(codec)
        getDom = lxml.html.fromstring(getHtml)
        token = getDom.xpath('.//input[@name="token"]/@value')[0]
        key = getDom.xpath('.//input[@name="8cb44b44cba8fde"]/@value')[0]
        formData = {"identity": username, "password": password, "token": token, "8cb44b44cba8fde": key}
        headers = copy.copy(self.headers)
        headers["Content-type"] = "application/x-www-form-urlencoded"
        headers["Referer"] = host
        conn.request("POST", uri, urllib.urlencode(formData), headers=headers)
        postResponse = conn.getresponse()
        postHeaders = postResponse.getheaders()
        logger.debug("--postHeaders--\n" + str(postHeaders))
        postHtml = zlib.decompress(postResponse.read(), 16 + zlib.MAX_WBITS).decode(codec)
        if postHtml.lstrip().startswith("<div class='alert'>"):
            self.setCookies(postHeaders)
            logger.debug("--headers--\n" + str(self.headers))
            result = True
        conn.close()
        return result

    '''
    def shareVehicle(self, shareJob):
        shareAccount = shareJob.get("share_account", None)
        if shareAccount is None:
            return errorcode.AUTH_ERROR, ""
        if shareAccount.get('account_type', None) == 'public':
            shareAccount['username'] = publicAccount['username']
            shareAccount['password'] = publicAccount['password']

        cookies = self.sessionServer.getSession('baixing', shareAccount['username'])
        if cookies is None:
            result = self.doLogin(shareAccount['username'], shareAccount['password'])
            if not result:
                return errorcode.AUTH_ERROR, errormsg.LOGIN_FAIL
            self.sessionServer.setSession('baixing', shareAccount['username'], self.cookies)
        else:
            self.cookies = cookies
            ks = self.cookies.keys()
            cookie_list = []
            for k in ks:
                cookie_list.append(k + '=' + self.cookies[k])
            self.headers['Cookie'] = str(string.join(cookie_list, '; '))

        vehicle = shareJob.get("vehicle", None)
        if vehicle is None:
            logger.error("vehicle missing")
            return errorcode.LOGIC_ERROR, errormsg.VEHICLE_EMPTY

        user = vehicle.get('user', None)
        if user is None:
            # return False
            return errorcode.DATA_ERROR, errormsg.USER_EMPTY
        address = user.get('address', None)
        if address is None:
            # return False
            return errorcode.DATA_ERROR, errormsg.ADDRESS_EMPTY
        districtCode = address.get('district_code', None)
        if districtCode is None:
            # return
            return errorcode.DATA_ERROR, errormsg.DISTRICT_EMPTY
        cityName = self.cityBaixing.getName(districtCode)
        baixingCityCode = self.cityBaixing.getCode(districtCode)
        if cityName is None:
            logger.error(str(baixingCityCode) + "无法匹配到百姓的城市名称")
            return errorcode.DATA_ERROR, str(baixingCityCode) + "无法匹配到百姓的城市名称"
        if baixingCityCode is None:
            logger.error(str(baixingCityCode) + "无法匹配到百姓的城市代码")
            return errorcode.DATA_ERROR, str(baixingCityCode) + "无法匹配到百姓的城市代码"

        host = str(cityName) + ".baixing.com"
        uri = "/fabu/ershouqiche"
        codec = "utf8"
        conn = httplib.HTTPConnection(host, timeout=10)
        conn.request("GET", uri, headers=self.headers)
        getResponse = conn.getresponse()
        getHeaders = getResponse.getheaders()

        self.setCookies(getHeaders)
        ks = self.cookies.keys()
        cookie_list = []
        for k in ks:
            cookie_list.append(k + '=' + self.cookies[k])
        self.headers['Cookie'] = string.join(cookie_list, '; ')
        print("--self.cookies--\n" + str(self.cookies))

        getHtml = self.decodeBody(getHeaders, getResponse.read())

        if getHtml.count(u'付费发布提醒') > 0:
            return errorcode.SITE_ERROR, "百姓网是本地的，超过城市发布限制时需要付费才能发布."
        getDom = lxml.html.fromstring(getHtml)

        spec = vehicle.get("spec", None)
        if spec is None:
            return errorcode.LOGIC_ERROR, errormsg.VEHICLE_SPEC_EMPTY

        specDetail = shareJob.get("vehicle_spec_detail", None)
        if specDetail is None:
            return errorcode.LOGIC_ERROR, errormsg.VEHICLE_SPEC_EMPTY

        token = getDom.xpath('.//input[@name="token"]/@value')[0]

        accountMobile = getDom.xpath('//*[@id="id_contact"]/div/input/@value')[0]
        if shareAccount.get('account_type', None) == 'public':
            # mobile = publicAccount.get('phone')
            (contactName, mobile) = self.getContact(shareJob)
        else:
            (contactName, mobile) = self.getContact(shareJob)
            #mobile = str(user['public_phone'])
        externalVehicleSpec = shareJob.get('external_vehicle_spec')
        brand = str(externalVehicleSpec.get('brand').get('id'))

        includeTransferFee = vehicle.get("price").get("quoted_price_include_transfer_fee", None)
        transferFee = '否'
        if includeTransferFee is not None and includeTransferFee:
            transferFee = '是'

        #详细地址
        merchant = vehicle['merchant']
        address = merchant['address']
        address_detail = address['detail']
        if address_detail is None:
            address_detail = ""

        #qq
        qq = ""
        merchant_substitute_config = shareJob.get('merchant_substitute_config', None)
        if merchant_substitute_config is not None:
            social = merchant_substitute_config.get('social', None)
            if social is not None:
                qq = social.get('qq', None)

        registrationDate = vehicle.get("vehicle_date").get("registration_date").astimezone(tz.HKT)
        form = {
            'token': str(token),
            'wanted': '0',
            'title': str(spec['brand']) + str(spec['series']) + str(spec['sale_name']),
            '车品牌': brand,
            '车系列': str(spec['brand']) + str(spec['series']),
            '车型': str(spec['series']) + str(spec['sale_name']),
            # '类型': 'm177927',
            '年份[0]': str(registrationDate.year),  # str(vehicle['spec']['year_group']) + str("年"),
            '年份[1]': str(registrationDate.month),
            '行驶里程': str(Decimal(vehicle['summary']['mileage']) / Decimal(10000)),
            '价格': str(Decimal(self.getPrice(shareJob)) / Decimal(10000)),
            'content': str(self.getContentVal_baixing(shareJob)),
            '地区[]': str(baixingCityCode),
            '具体地点': str(address_detail),
            'QQ号': str(qq),
            'contact': mobile,
            '车辆颜色': str(self.getColor(vehicle)),
            '排量': str(specDetail['details'][23]),
            '变速箱': str(specDetail['details'][42]),
            '燃油类型': u'汽油',
            '车辆用途': u'家用',
            '年检[0]':'',
            '年检[1]':'',
            '交强险[0]':'',
            '交强险[1]':'',
            '商业险[0]':'',
            '商业险[1]':'',
            '承担过户费': u'包含',
            '行驶证': u'齐全',
            '登记证': u'齐全',
            '购车发票': u'齐全',
            '维修记录': u'齐全',
            '购置税': u'齐全',
            '重大事故': u'无',
            '能否过户': u'能',
            '能否按揭': u'能'
            #'购置税': str(self.getBooleanText(vehicle, "document", "purchase_tax")),
            #'行驶证': str(self.getBooleanText(vehicle, "document", "registration_certificate")),
            #'购车发票': str(self.getBooleanText(vehicle, "document", "property")),
            #'维修记录': str(self.getBooleanText(vehicle, "document", "maintenance_manual")),
            #'重大事故': str(self.getBooleanText(vehicle, "summary", "accident")),
            #'承担过户费': transferFee
        }

        formData = urllib.urlencode(form)

        # Upload images
        gallery = vehicle.get("gallery", None)
        if gallery is None:
            logger.error("gallery missing")
            return errorcode.LOGIC_ERROR, errormsg.PHOTO_NOT_ENOUGH
        imageConfig = getDom.xpath('//*[@id="id_images"]/div/script/text()')[0]
        logger.debug("Baixing image config from xpath = " + imageConfig)
        imageConfig = imageConfig.replace('imageConfig = ', '')
        imageJson = json.loads(imageConfig)
        logger.debug("Baixing image config json = " + json.dumps(imageJson))
        photoList = self.uploadPics(gallery.get("photos", []), imageJson)
        imgs = ''
        for img in photoList:
            imgs += "&images[]=" + urllib.quote(img)

        formData += '&images[]=' + imgs
        logger.debug("baixing form:" + formData)

        headers = copy.copy(self.headers)
        if mobile != accountMobile:
            self.confirmSendIfApplicable(host, mobile, accountMobile, headers)

        headers['Content-Type'] = 'application/x-www-form-urlencoded'
        headers['Content-Length'] = len(formData)

        conn.request("POST", uri, formData, headers=headers)
        postResponse = conn.getresponse()
        postHeaders = postResponse.getheaders()
        status = postResponse.status
        postHtml = self.decodeBody(postHeaders, postResponse.read())

        conn.close()
        logger.debug(postHtml)
        if status == 302:
            url = self.getViewUrl(host, postHeaders)
            return errorcode.SUCCESS, url
        else:
            logger.debug(postHtml)
            # print formData
        return errorcode.LOGIC_ERROR, errormsg.SITE_OTHER_ERROR
    '''

    @staticmethod
    def getViewUrl(host, postHeaders):
        if "location" in str(postHeaders):
            for header in postHeaders:
                if header[0].lower() == 'location':
                    return "http://" + host + header[1]
        return None

    def confirmSendIfApplicable(self, host, mobile, accountMobile, headers):
        # /df/auth/?mobile=18611164626&category=ershouqiche
        # /df/auth/?mobile=&category=ershouqiche&apply=1
        # /c/ev/fabu_daifa_show
        # mobile:15300012344
        # dfmobile:15300066914
        # category:ershouqiche

        conn = httplib.HTTPConnection(host, timeout=10)
        path = '/c/ev/fabu_daifa_show?mobile=' + mobile + '&dfmobile=' + accountMobile + '&category=ershouqiche'
        conn.request("GET", path, headers=headers)
        res = conn.getresponse()
        html = self.decodeBody(res.getheaders(), res.read())
        conn.close()
        logger.debug("path " + path + ", response =" + html)

        conn = httplib.HTTPConnection(host, timeout=10)
        path = '/df/auth?mobile=' + mobile + '&category=ershouqiche'
        conn.request("GET", path, headers=headers)
        res = conn.getresponse()
        html = self.decodeBody(res.getheaders(), res.read())
        conn.close()
        if html.count(u'我们已用短信通知对方进行授权') == 0:
            path = '/df/auth?mobile=' + mobile + '&category=ershouqiche&apply=1'
            conn = httplib.HTTPConnection(host, timeout=10)
            conn.request("GET", path, headers=headers)
            res = conn.getresponse()
            html = self.decodeBody(res.getheaders(), res.read())
            conn.close()
            logger.debug("send confirmed ")


    @staticmethod
    def getColor(vehicle):
        result = "其他"
        colorMap = {"black": "黑", "white": "白", "red": "红", "yellow": "黄",
                    "blue": "蓝", "green": "绿"}
        summary = vehicle.get("summary", None)
        if summary is not None:
            color = summary.get("color", None)
            result = colorMap.get(color, "其他")
        return result

    def uploadPicContent(self, content, imageConfig):
        # {"uploadUrl":"http:\/\/v0.api.upyun.com\/bximg\/",
        # "uploadParams":
        # {"policy":"",
        # "signature":""},
        # "vendorName":"upyun",
        # "imageSuffix":"#up",
        # "fileKey":"file"}
        uploadUrl = imageConfig.get('uploadUrl')
        params = imageConfig.get('uploadParams')
        policy = params.get('policy')
        imageSuffix = imageConfig.get('imageSuffix')
        signature = params.get('signature')
        host = uploadUrl.replace('http://', '')
        host = host.replace('/bximg/', '')
        logger.debug("Baxing upload image host = " + host)
        conn = httplib.HTTPConnection(host, timeout=10)
        headers = copy.copy(self.headers)
        # jsessionid = self.cookies.get("JSESSIONID", None)

        # logger.debug(jsessionid)
        img = StringIO(content)
        smallImg = StringIO()
        resize.resize(img, (800, 600), False, smallImg)
        boundaryHeader = "----pluploadboundary" + str(self.millis())
        headers['Referer'] = 'http://s.baixing.net/swf/uploader/swfupload.swf?preventswfcaching=' + str(self.millis())
        headers['Origin'] = 'http://s.baixing.net'
        headers["Content-Type"] = "multipart/form-data; boundary=" + boundaryHeader
        content = smallImg.getvalue()
        boundary = "--" + boundaryHeader
        picForm = boundary + '\r\n' + 'Content-Disposition: form-data; name="policy"\r\n\r\n'
        picForm += str(policy) + '\r\n'
        picForm += boundary + '\r\n' + 'Content-Disposition: form-data; name="signature"\r\n\r\n'
        picForm += str(signature) + '\r\n'
        picForm += boundary + '\r\n' + 'Content-Disposition: form-data; name="file"; filename="' + str(
            self.millis()) + '.jpg"\r\nContent-Type: image/jpeg\r\n\r\n'
        picForm += str(content) + '\r\n'
        picForm += boundary + "--"
        headers['Content-Length'] = len(picForm)
        logger.debug('upload image form = ' + picForm)
        conn.request("POST", "/bximg/",
                     picForm,
                     headers=headers)
        res = conn.getresponse()
        result = self.decodeBody(res.getheaders(), res.read())
        conn.close()

        jsonResult = json.loads(result)
        if jsonResult.get('code') == 200:
            imgUrl = str(jsonResult.get('url')) + str(imageSuffix)
            return imgUrl
        return None

    def uploadPics(self, photos, imageConfig):
        photo_list = []
        photos = photos[:12]  # 最多12张图baixing
        for photo in photos:
            url = photo.get("url", None)
            if url is None:
                continue
            o = urlparse(url)
            host = o.netloc
            uri = o.path

            upload = self.sessionServer.getUpload('baixing', uri)
            logger.debug('--upload-- \n' + str(upload))
            if upload is not None:
                upload = upload.encode('utf-8', 'ignore')
                res = upload
            else:
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
                res = self.uploadPicContent(content, imageConfig)
                if res is not None:
                    self.sessionServer.setUpload('baixing.com', uri, res)
            if res is not None:
                photo_list.append(res)
        return photo_list

    @staticmethod
    def getGearbox(part):
        if part['gearbox'].count(u"自") > 0:
            return u"自动"
        return u"手动"

    @staticmethod
    def millis():
        return int(round(time.time() * 1000))

    @staticmethod
    def getBooleanText(vehicle, category, field):
        documentMap = {True: "齐全", False: "不齐全"}
        accidentMap = {True: "有", False: "无"}
        transferFeeMap = {True: "是", False: "否"}
        if category is "document":
            document = vehicle.get(category, None)
            if document is not None:
                key = document.get(field, None)
                result = documentMap.get(key, "")
                return result
        elif category is "summary":
            summary = vehicle.get(category, None)
            if summary is not None:
                if field is "accident":
                    key = summary.get(field, None)
                    result = accidentMap.get(key, "")
                    return result
        return ""
    
    def removeVehicle(self,shareJob):
        shareAccount = shareJob.get("share_account", None)
        if shareAccount is None:
            return errorcode.AUTH_ERROR, ""
        if shareAccount.get('account_type', None) == 'public':
            shareAccount['username'] = publicAccount['username']
            shareAccount['password'] = publicAccount['password']

        cookies = self.sessionServer.getSession('baixing', shareAccount['username'])
        if cookies is None:
            result = self.doLogin(shareAccount['username'], shareAccount['password'])
            if not result:
                return errorcode.AUTH_ERROR, errormsg.LOGIN_FAIL
            self.sessionServer.setSession('baixing', shareAccount['username'], self.cookies)
        else:
            self.cookies = cookies
            ks = self.cookies.keys()
            cookie_list = []
            for k in ks:
                cookie_list.append(k + '=' + self.cookies[k])
            self.headers['Cookie'] = str(string.join(cookie_list, '; '))

        urlForApp = shareJob.get("url", None)
        if urlForApp is not None and len(urlForApp) > 0:
            print urlForApp
            adID = re.compile("[0-9]\d{4,}").findall(urlForApp)[0]
            conn = httplib.HTTPConnection('www.baixing.com', timeout=10)
            url = "/xinxi/delete?adId=" + adID + "&view=0"
            headers = copy.copy(self.headers)
            conn.request("POST", url, headers=headers)
            res = conn.getresponse()
            result = self.decodeBody(res.getheaders(), res.read())
            print result
            if result.count("success") > 0:
                return errorcode.SUCCESS, ""
            else:
                return errorcode.SITE_ERROR, errormsg.VEHICLE_REMOVE_FAIL
        else:
            return errorcode.DATA_ERROR, errormsg.VEHICLE_URL_EMPTY
    
    def getPageHtml(self, host, uri):
        conn = httplib.HTTPConnection(host, timeout=10)
        conn.request("GET", uri, headers=self.headers)
        getResponse = conn.getresponse()
        getHeaders = getResponse.getheaders()
        strhtml = self.decodeBody(getHeaders, getResponse.read())
        conn.close()
        return strhtml, getHeaders
    
    def initShareJob(self, shareJob):
        shareAccount = shareJob.get("share_account", None)
        if shareAccount is None:
            return errorcode.AUTH_ERROR, ""
        if shareAccount.get('account_type', None) == 'public':
            shareAccount['username'] = publicAccount['username']
            shareAccount['password'] = publicAccount['password']

        cookies = self.sessionServer.getSession('baixing', shareAccount['username'])
        if cookies is None:
            result = self.doLogin(shareAccount['username'], shareAccount['password'])
            if not result:
                return errorcode.AUTH_ERROR, errormsg.LOGIN_FAIL
            self.sessionServer.setSession('baixing', shareAccount['username'], self.cookies)
        else:
            self.cookies = cookies
            ks = self.cookies.keys()
            cookie_list = []
            for k in ks:
                cookie_list.append(k + '=' + self.cookies[k])
            self.headers['Cookie'] = str(string.join(cookie_list, '; '))

        vehicle = shareJob.get("vehicle", None)
        if vehicle is None:
            logger.error("vehicle missing")
            return errorcode.LOGIC_ERROR, errormsg.VEHICLE_EMPTY

        user = vehicle.get('user', None)
        if user is None:
            # return False
            return errorcode.DATA_ERROR, errormsg.USER_EMPTY
        address = user.get('address', None)
        if address is None:
            # return False
            return errorcode.DATA_ERROR, errormsg.ADDRESS_EMPTY
        districtCode = address.get('district_code', None)
        if districtCode is None:
            # return
            return errorcode.DATA_ERROR, errormsg.DISTRICT_EMPTY
        cityName = self.cityBaixing.getName(districtCode)
        baixingCityCode = self.cityBaixing.getCode(districtCode)
        if cityName is None:
            logger.error(str(baixingCityCode) + "无法匹配到百姓的城市名称")
            return errorcode.DATA_ERROR, str(baixingCityCode) + "无法匹配到百姓的城市名称"
        if baixingCityCode is None:
            logger.error(str(baixingCityCode) + "无法匹配到百姓的城市代码")
            return errorcode.DATA_ERROR, str(baixingCityCode) + "无法匹配到百姓的城市代码"
            
        spec = vehicle.get("spec", None)
        if spec is None:
            return errorcode.LOGIC_ERROR, errormsg.VEHICLE_SPEC_EMPTY

        specDetail = shareJob.get("vehicle_spec_detail", None)
        if specDetail is None:
            return errorcode.LOGIC_ERROR, errormsg.VEHICLE_SPEC_EMPTY
            
        parseResult = {}
        parseResult['cityCode'] = str(baixingCityCode)
        parseResult['cityName'] = str(cityName)
        parseResult['host'] = str(cityName) + ".baixing.com"
        return parseResult

    def getContentVal_baixing(self, shareJob):
        Symbol = "\r\n"
        lateral = "——"*20
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
                    if site == 'baixing.com':
                        description = i.get('description', None)
                        description = string.replace(description, '\n', Symbol)
            content += description
            content += Symbol + str(vehicle['_id'])

        # 统一说明 追加
        if globalDisable == False:
            if share_account.get("account_type", None) == "substitute":
                content += Symbol*2 + '看车网，发现二手好车。提供专业的咨询和购车指导，保证车源信息真实准确。凡通过看车网成交车辆，我们将提供90天内不限公里的延期质保! 二手车质量我们保证 !' + Symbol
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

            content += lateral
            content += Symbol*4

        content += str(vehicle['_id'])
        if "" == content:
            content = u"无车辆说明，请添加至10个字以上"
        return content


    ###########################
    ##发车；share && update
    ##########################
    def postVehicle(self,shareJob, parseResult, queryId):
        shareAccount = shareJob.get("share_account", None)
        vehicle = shareJob.get("vehicle", None)
        user = vehicle.get('user', None)
        address = user.get('address', None)
        spec = vehicle.get("spec", None)
        specDetail = shareJob.get("vehicle_spec_detail", None)
        externalVehicleSpec = shareJob.get('external_vehicle_spec')
        
        iQueryId = queryId.encode('utf8') if type(queryId) == unicode else queryId
        uri = '/fabu/'+iQueryId
        if ( 2==len(parseResult)):
            return errorcode.LOGIC_ERROR, parseResult[1];
        html, heads = self.getPageHtml(parseResult['host'], uri)
        if html.count(u'您近期多次发布错类信息，目前账号被临时禁发两天'):
            return errorcode.SITE_ERROR, u'账号被临时禁发'
        
        self.setCookies(heads)
        ks = self.cookies.keys()
        cookie_list = []
        for k in ks:
            cookie_list.append(k + '=' + self.cookies[k])
        self.headers['Cookie'] = string.join(cookie_list, '; ')
        
        hxs = lxml.html.fromstring(html)

        token = hxs.xpath('//input[@name="token"]/@value')[0]
        accountMobile = hxs.xpath('//*[@id="id_contact"]/div/input/@value')[0]
        
        if shareAccount.get('account_type', None) == 'public':
            (contactName, mobile) = self.getContact(shareJob)
        else:
            (contactName, mobile) = self.getContact(shareJob)
        
        brand = str(externalVehicleSpec.get('brand').get('id'))

        includeTransferFee = vehicle.get("price").get("quoted_price_include_transfer_fee", None)
        transferFee = '不包含'
        if includeTransferFee is not None and includeTransferFee:
            transferFee = '包含'

        registrationDate = vehicle.get("vehicle_date").get("registration_date")
        inspectionDate = vehicle.get("vehicle_date").get("inspection_date")
        commercialInsuranceExpireDate = vehicle.get("vehicle_date").get("commercial_insurance_expire_date")
        if commercialInsuranceExpireDate is not None:
            commercialInsuranceExpireDate = commercialInsuranceExpireDate
            commercialInsuranceExpireDateYear = commercialInsuranceExpireDate.year
            commercialInsuranceExpireDateMonth = commercialInsuranceExpireDate.month
        else:
            commercialInsuranceExpireDate = inspectionDate
            commercialInsuranceExpireDateYear = inspectionDate.year
            commercialInsuranceExpireDateMonth = inspectionDate.month

        compulsoryInsuranceExpireDate = vehicle.get("vehicle_date").get("compulsory_insurance_expire_date")
        if compulsoryInsuranceExpireDate is not None:
            compulsoryInsuranceExpireDate = compulsoryInsuranceExpireDate
            compulsoryInsuranceExpireDateYear = compulsoryInsuranceExpireDate.year
            compulsoryInsuranceExpireDateMonth = compulsoryInsuranceExpireDate.month
        else:
            compulsoryInsuranceExpireDate = inspectionDate
            compulsoryInsuranceExpireDateYear = inspectionDate.year
            compulsoryInsuranceExpireDateMonth = inspectionDate.month


        form = {
            'token': str(token),
            'wanted': '0',
            'title': str(spec['brand']) + str(spec['series']) + str(spec['sale_name']),
            '车品牌': brand,
            '车系列': str(spec['brand']) + str(spec['series']),
            '车型': str(spec['series']) + str(spec['sale_name']),
            '类型': 'm177927',
            '年份[0]': str(registrationDate.year),
            '年份[1]': str(registrationDate.month),
            '行驶里程': str(Decimal(vehicle['summary']['mileage']) / Decimal(10000)),
            '价格': str(Decimal(self.getPrice(shareJob)) / Decimal(10000)),
            'content': str(self.getContentVal_baixing(shareJob)),
            '地区[]': parseResult['cityCode'],
            'contact': mobile,
            '车辆颜色': str(self.getColor(vehicle)),
            '排量': str(specDetail['details'][23]),
            '变速箱': str(specDetail['details'][42]),
            '燃油类型':str('汽油'),
            '排放标准':str(specDetail['details'][10]),
            '车辆用途':str('家用'),
            '年检[0]':str(inspectionDate.year),
            '年检[1]':str(inspectionDate.month),
            '交强险[0]':str(compulsoryInsuranceExpireDateYear),
            '交强险[1]':str(compulsoryInsuranceExpireDateMonth),
            '商业险[0]':str(commercialInsuranceExpireDateYear),
            '商业险[1]':str(commercialInsuranceExpireDateMonth),
            '登记证':str('齐全'),
            '能否过户':str('能'),
            '能否按揭':str('能'),

            '购置税': str(self.getBooleanText(vehicle, "document", "purchase_tax")),
            '行驶证': str(self.getBooleanText(vehicle, "document", "registration_certificate")),
            '购车发票': str('齐全'), # document.property
            '维修记录': str(self.getBooleanText(vehicle, "document", "maintenance_manual")),
            '重大事故': str(self.getBooleanText(vehicle, "summary", "accident")),
            '承担过户费': transferFee,
            'skipKeyword': 1
        }
        
        #photoList
        if iQueryId.decode('utf8').isnumeric() :
            photoList = hxs.xpath('//input[@name="images[]"]/@value')
        else:
            gallery = vehicle.get("gallery", None)
            if gallery is None:
                logger.error("gallery missing")
                return errorcode.LOGIC_ERROR, errormsg.PHOTO_NOT_ENOUGH
            imageConfig = hxs.xpath('//*[@id="id_images"]/div/script/text()')[0]
            logger.debug("Baixing image config from xpath = " + imageConfig)
            imageConfig = imageConfig.replace('imageConfig = ', '')
            imageJson = json.loads(imageConfig)
            logger.debug("Baixing image config json = " + json.dumps(imageJson))
            photoList = self.uploadPics(gallery.get("photos", []), imageJson)
            
        formData = urllib.urlencode(form)
        imgs = ''
        for img in photoList:
            imgs += "&images[]=" + urllib.quote(img)
        formData += '&images[]=' + imgs
        
        headers = copy.copy(self.headers)
        if mobile != accountMobile:
            self.confirmSendIfApplicable(parseResult['host'], mobile, accountMobile, headers)

        headers['Content-Type'] = 'application/x-www-form-urlencoded'
        headers['Content-Length'] = len(formData)

        conn = httplib.HTTPConnection(parseResult['host'], timeout=10)
        conn.request("POST", uri, formData, headers=headers)
        postResponse = conn.getresponse()
        postHeaders = postResponse.getheaders()
        status = postResponse.status
        postHtml = self.decodeBody(postHeaders, postResponse.read())

        conn.close()
        logger.debug(postHtml)
        if status == 302:
            url = self.getViewUrl(parseResult['host'], postHeaders)
            return errorcode.SUCCESS, url
        else:
            if postHtml.count(u'分期贷款买车'):
                logger.debug(postHtml)
                return errorcode.SITE_ERROR, errormsg.VEHICLE_DUPLICATED

            if postHtml.count(u'重复信息'):
                logger.debug(postHtml)
                return errorcode.SITE_ERROR, errormsg.VEHICLE_DUPLICATED

        return errorcode.LOGIC_ERROR, errormsg.SITE_OTHER_ERROR

    
    def updateVehicle(self, shareJob):
        parseResult = self.initShareJob(shareJob)
        
        urlForApp = shareJob.get("url", None)
        if urlForApp is None or urlForApp=='':
            return errorcode.DATA_ERROR, '车辆url为空'
            
        queryId = re.findall('(\d+)\.html', urlForApp)
        if queryId is None:
            return errorcode.DATA_ERROR, "车辆ID为空"
        elif len(queryId) <1:
            return errorcode.DATA_ERROR, "车辆ID为空"
        else:
            queryId = queryId[-1]
            
        tmp = self.postVehicle(shareJob, parseResult, queryId)
        print tmp
        return tmp
        
    def shareVehicle(self, shareJob):
        parseResult = self.initShareJob(shareJob)
        
        tmp = self.postVehicle(shareJob, parseResult, 'ershouqiche')
        print tmp
        return tmp

