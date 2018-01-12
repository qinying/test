#!/usr/bin/python
# -*- coding: UTF-8 -*-

import httplib
import urllib
import lxml.html
import re
import tz
import sys
import random
import time
import json
import zlib
import logger
import errorcode
import errormsg
import string
import copy
from urlparse import urlparse
from decimal import *
import resize
import cityGanji
from datetime import datetime
from datetime import date
from dt8601 import IsoDate
from urlparse import urlparse
from base import BaseSharer
from StringIO import StringIO


publicAccount =  {
    #"username":u"kccs02",
    #"password":u"1a2s3d"
    "username": u"石家庄看车网",
    "password": u"asasas"
}


class GanjiSharer(BaseSharer):
    def __init__(self, sessionServer, specServer):
        super(GanjiSharer, self).__init__(sessionServer, specServer)
        self.postCount = 0


    def doLogin(self, username, password):
        conn = httplib.HTTPSConnection("passport.ganji.com", timeout=10)
        url = '/login.php'
        conn.request("GET", url, headers = self.headers)
        res = conn.getresponse()
        headers = res.getheaders()
        html = zlib.decompress(res.read(), 16+zlib.MAX_WBITS)
        html = html.decode('utf-8')
        #print html
        print headers
        self.setCookies(headers)
        hashRe = re.search("hash__ = \'(?P<hash>.*)\';", html)
        hash__ = hashRe.group("hash")
        print hash__
        conn.close()

        timestamp = int(time.time())
        conn = httplib.HTTPSConnection("passport.ganji.com", timeout=10)
        url = '/login.php?callback=t&username=%s&password=%s&checkCode=&setcookie=1&second=&parentfunc=&redirect_in_iframe=&next=&__hash__=%s&_=%d' % (urllib.quote(username.encode("utf-8")), urllib.quote(password.encode("utf-8")), hash__, timestamp)
        print url
        conn.request("GET", url, headers = self.headers)
        res = conn.getresponse()
        headers = res.getheaders()
        print headers
        self.setCookies(headers)
        html = res.read().decode('utf-8')
        #print html
        conn.close()
        msgRe = re.search("t\((?P<msg>.*)\)", html)
        msg = msgRe.group("msg")
        print msg
        resObj = json.loads(msg)
        if resObj['status'] != 1:
            if resObj['type'].startswith('need_captcha'):
                #login with captcha
                timestamp = int(time.time())
                conn = httplib.HTTPSConnection("passport.ganji.com", timeout=10)
                checkCodeImageUrl = '/ajax.php?dir=captcha&module=login_captcha&nocache=%d'% timestamp
                conn.request("GET", checkCodeImageUrl, headers = self.headers)
                res = conn.getresponse() 
                self.setCookies(res.getheaders())
                imageData = res.read()
                conn.close()
                image = StringIO(imageData)
                captcha = self.getCaptcha(image, imageData)
                if captcha is None:
                    return False
                validcode = captcha["text"]

                conn = httplib.HTTPSConnection("passport.ganji.com", timeout=10)
                url = '/login.php?callback=t&username=%s&password=%s&checkCode=%s&setcookie=14&second=&parentfunc=&redirect_in_iframe=&next=&__hash__=%s&_=%d' % (urllib.quote(username.encode("utf-8")), urllib.quote(password.encode("utf-8")), validcode, hash__, timestamp)
                logger.debug(url)
                conn.request("GET", url, headers = self.headers)
                res = conn.getresponse()
                headers = res.getheaders()
                print headers
                self.setCookies(headers)
                html = res.read().decode('utf-8')
                conn.close()
                msgRe = re.search("t\((?P<msg>.*)\)", html)
                msg = msgRe.group("msg")
                print msg
                resObj = json.loads(msg)
                if resObj['status'] != 1:
                    return False
            else:
                return False
        self.setCookies(headers)
        return True

    def getCheckCode(self, checkCodeUrl):
        conn = httplib.HTTPConnection("www.ganji.com", timeout=10)
        conn.request("GET", checkCodeUrl, headers = self.headers)
        res = conn.getresponse()
        self.setCookies(res.getheaders())
        imageData = res.read()
        conn.close()
        image = StringIO(imageData)
        # write capture
        # fd = open("a.png", "w")
        # fd.write(imageData)
        # fd.close()

        captcha = self.getCaptcha(image, imageData)
        if captcha is None:
            return None
        checkCode = captcha["text"]
        return checkCode

    def getContentVal_ganji(self, shareJob):
        Symbol = "\r\n"
        #Symbol = ""
        lateral = "——"*20
        #lateral = ""
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
                    if site == 'ganji.com':
                        description = i.get('description', None)
                        description = string.replace(description, '\n', Symbol)
            content += description
            content += Symbol + str(vehicle['_id'])

        # 统一说明 追加
        if globalDisable == False:
            if share_account.get("account_type", None) == "substitute":
                content += Symbol*2 + '看车网，发现二手好车。提供专业的咨询和购车指导，保证车源信息真实准确。 二手车质量我们保证 !' + Symbol
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
        if '' == content:
            content = u'缺少车辆描述,车辆描述少于10个字';
        return content

    def shareVehicle(self, shareJob):
        shareAccount = shareJob.get("share_account", None)
        if shareAccount is None:
            return errorcode.AUTH_ERROR, ""
        if shareAccount.get('account_type', None) == 'public':
            shareAccount['username'] = publicAccount['username']
            shareAccount['password'] = publicAccount['password']

        logger.debug("ganji shareVehicle")
        #cookies = self.sessionServer.getSession('ganji', shareAccount['username'])
        #赶集不要cookie太短
        cookies = None
        if cookies is None:
            res = self.doLogin(shareAccount['username'], shareAccount['password'])
            if not res:
                logger.debug("login error")
                return errorcode.AUTH_ERROR, errormsg.LOGIN_FAIL
            #self.sessionServer.setSession('ganji', shareAccount['username'], self.cookies)
            if 'loginact' in self.cookies:
                del self.cookies['loginact']
            ks = self.cookies.keys()
            cookie_list = []
            for k in ks:
                cookie_list.append(k + '=' + self.cookies[k])
            self.headers['Cookie'] = string.join(cookie_list, '; ')
        else:
            self.cookies = cookies
            ks = self.cookies.keys()
            cookie_list = []
            for k in ks:
                cookie_list.append(k + '=' + self.cookies[k])
            self.headers['Cookie'] = string.join(cookie_list, '; ')

        logger.debug("self.cookies = " + str(self.cookies))
        logger.debug("header.Cookie = " + str(self.headers['Cookie']))
        vehicle = shareJob.get("vehicle", None)
        if vehicle is None:
            logger.error("vehicle missing")
            return errorcode.DATA_ERROR, errormsg.VEHICLE_EMPTY
        price = vehicle.get('price', None)
        quoted_price_include_transfer_fee = price.get('quoted_price_include_transfer_fee', None)
        if quoted_price_include_transfer_fee is None:
            quoted_price_include_transfer_fee = False

        user = vehicle.get("user", None)
        if user is None:
            logger.error("user missing")
            return errorcode.DATA_ERROR, errormsg.USER_EMPTY
        address = user.get('address', None)
        if address is None:
            #return False
            return errorcode.DATA_ERROR, errormsg.ADDRESS_EMPTY
        districtCode = address.get('district_code', None)
        if districtCode is None:
            #return
            return errorcode.DATA_ERROR, errormsg.DISTRICT_EMPTY
        mobile = user.get("mobile", None)
        if mobile is None:
            return errorcode.DATA_ERROR, errormsg.MOBILE_EMPTY

        spec = vehicle.get("spec", None)
        if spec is None:
            logger.error("spec missing")
            return errorcode.DATA_ERROR, errormsg.VEHICLE_SPEC_EMPTY
        levelId = spec.get("level_id", None)
        if levelId is None:
            logger.error("levelId missing")
            return errorcode.LOGIC_ERROR, errormsg.VEHICLE_SPEC_EMPTY
        logger.debug("levelId=" + levelId)
        vehicle_spec_detail = shareJob.get("vehicle_spec_detail", None)
        if vehicle_spec_detail is None:
            return errorcode.DATA_ERROR, errormsg.VEHICLE_SPEC_EMPTY
        external_vehicle_spec = shareJob.get("external_vehicle_spec", None)
        if external_vehicle_spec is None:
            return errorcode.DATA_ERROR, errormsg.EXTERNAL_SPEC_EMPTY
        external_vehicle_model_id = external_vehicle_spec['model']['id']
        logger.debug(str(external_vehicle_spec))
        if external_vehicle_spec['model']['key'] == '0':
            title = external_vehicle_spec['vendor']['name'] + spec['year_group'] + ' ' + spec['sale_name']
        else:
            title = external_vehicle_spec['vendor']['name'] + external_vehicle_spec['model']['name']
        logger.debug("external_vehicle_model_id=" + external_vehicle_model_id)
        logger.debug("title=" + title)
        gallery = vehicle.get("gallery", None)
        if gallery is None:
            logger.error("gallery missing")
            return errorcode.DATA_ERROR, errormsg.PHOTO_NOT_ENOUGH

        merchant_substitute_config = shareJob.get('merchant_substitute_config', None)
        phone = ''
        if merchant_substitute_config is not None:
            extra_contact = merchant_substitute_config.get('extra_contact', None)
            phone = ''
            phone = extra_contact.get('phone', None)
            if phone is None:
                phone = ''

        city = cityGanji.CityGanji()
        conn = httplib.HTTPConnection("www.ganji.com", timeout=10)
        logger.info("cityName: "+city.getName(districtCode))
        conn.request("GET", "/pub/pub.php?act=pub&method=load&cid=6&mcid=14&domain="+city.getName(districtCode)+"&deal=1#", headers=self.headers)
        checkCodeUrl = None
        res = conn.getresponse()
        resHeaders = res.getheaders()
        logger.debug("resHeaders=" + str(resHeaders))
        #self.setCookies(resHeaders)
        resBody = self.decodeBody(resHeaders, res.read())
        try:
            dom = lxml.html.fromstring(resBody)
            #print resBody
            showCodeStyle = dom.xpath('//*[@id="showcode"]/@style')
            checkCodeUrls = dom.xpath('//*[@id="img_checkcode"]/@src')
            #print showCodeStyle
            logger.debug(showCodeStyle)
            if len(showCodeStyle) > 0 and showCodeStyle[0].count('none') == 0 and len(checkCodeUrls) > 0:
                checkCodeUrl = checkCodeUrls[0]
        except Exception as e:
            logger.error(e)
            pass

        checkCode = None
        if checkCodeUrl is not None:
            checkCode = self.getCheckCode(checkCodeUrl)
            #print checkCode
            logger.debug(checkCode)

        photoList = self.uploadPics(gallery.get("photos", []))
        logger.debug(json.dumps(photoList))
        headers = copy.copy(self.headers)
        boundaryHeader = "-----------" +  str(int (random.random() * sys.maxint / 1000))
        headers['Referer'] = 'http://www.ganji.com/pub/pub.php?act=pub&method=load&cid=6&mcid=14&domain=' + city.getName(districtCode) + '&deal=1&domain=bj'
        headers["Content-Type"] = "multipart/form-data; boundary=" + boundaryHeader
        boundary = "--" + boundaryHeader
        formStr = boundary + '\r\n' + 'Content-Disposition: form-data; name="major_category_id"\r\n\r\n'
        formStr += "14\r\n"
        formStr += boundary + '\r\n' + 'Content-Disposition: form-data; name="auto_type"\r\n\r\n'
        formStr += "0\r\n"
        formStr += boundary + '\r\n' + 'Content-Disposition: form-data; name="autotype"\r\n\r\n'
        formStr += "0\r\n"
        formStr += boundary + '\r\n' + 'Content-Disposition: form-data; name="beforeAudit"\r\n\r\n'
        formStr += "false\r\n"
        formStr += boundary + '\r\n' + 'Content-Disposition: form-data; name="show_before_audit"\r\n\r\n'
        formStr += "0\r\n"
        formStr += boundary + '\r\n' + 'Content-Disposition: form-data; name="show_before_audit_reason"\r\n\r\n'
        formStr += "\r\n"
        formStr += boundary + '\r\n' + 'Content-Disposition: form-data; name="origin"\r\n\r\n'
        formStr += "vehicle_bang\r\n"
        formStr += boundary + '\r\n' + 'Content-Disposition: form-data; name="deal_type"\r\n\r\n'
        formStr += "1\r\n"
        formStr += boundary + '\r\n' + 'Content-Disposition: form-data; name="minor_category"\r\n\r\n'
        formStr += str(external_vehicle_spec['brand']['name']) + "\r\n"
        formStr += boundary + '\r\n' + 'Content-Disposition: form-data; name="minorCategory"\r\n\r\n'
        formStr += str(','.join([external_vehicle_spec['brand']['id'], external_vehicle_spec['brand']['spell'], external_vehicle_spec['brand']['name']])) + "\r\n"
        formStr += boundary + '\r\n' + 'Content-Disposition: form-data; name="tag"\r\n\r\n'
        formStr += str(','.join([external_vehicle_spec['series']['id'], external_vehicle_spec['series']['key'], external_vehicle_spec['series']['name']])) + "\r\n"
        formStr += boundary + '\r\n' + 'Content-Disposition: form-data; name="car"\r\n\r\n'
        formStr += str(external_vehicle_spec['model']['id']) + "\r\n"
        formStr += boundary + '\r\n' + 'Content-Disposition: form-data; name="user_defined_category"\r\n\r\n'
        if external_vehicle_spec['model']['key'] == '0':
            formStr += str(spec['sale_name'] + ' ' + spec['year_group']) + "\r\n"
        else:
            formStr += str(external_vehicle_spec['model']['name']) + "\r\n"
        formStr += boundary + '\r\n' + 'Content-Disposition: form-data; name="car_color"\r\n\r\n'
        formStr += self.getColorCode(shareJob) + "\r\n"

        #0=自动，1=手动
        formStr += boundary + '\r\n' + 'Content-Disposition: form-data; name="gearbox"\r\n\r\n'
        if vehicle_spec_detail['details'][42].count(u'自'):
            formStr += "2\r\n"
        else:
            formStr += "1\r\n"

        formStr += boundary + '\r\n' + 'Content-Disposition: form-data; name="air_displacement"\r\n\r\n'
        formStr += vehicle_spec_detail['details'][23] + "\r\n"
        formStr += boundary + '\r\n' + 'Content-Disposition: form-data; name="accidents"\r\n\r\n'
        formStr += "1\r\n"
        d = self.getDate(shareJob)                                      #获取的是初等时间share
        inspection_date = self.getInspectionDate(shareJob)
        compulsor_date = self.getCompulsorInsuranceExpireDate(shareJob)

        formStr += boundary + '\r\n' + 'Content-Disposition: form-data; name="license_date"\r\n\r\n'
        formStr += str(d.year) + "\r\n"
        formStr += boundary + '\r\n' + 'Content-Disposition: form-data; name="license_year"\r\n\r\n'
        formStr += str(d.year) + "\r\n"
        formStr += boundary + '\r\n' + 'Content-Disposition: form-data; name="license_math"\r\n\r\n'
        formStr += str(d.month) + "\r\n"
        formStr += boundary + '\r\n' + 'Content-Disposition: form-data; name="insurance_year_add"\r\n\r\n'
        formStr += str(inspection_date.year) + "\r\n"
        formStr += boundary + '\r\n' + 'Content-Disposition: form-data; name="insurance_month_add"\r\n\r\n'
        formStr += str(inspection_date.month) + "\r\n"
        formStr += boundary + '\r\n' + 'Content-Disposition: form-data; name="strong_insurance_year"\r\n\r\n'
        formStr += str(compulsor_date.year) + "\r\n"
        formStr += boundary + '\r\n' + 'Content-Disposition: form-data; name="strong_insurance_month"\r\n\r\n'
        formStr += str(compulsor_date.month) + "\r\n"
        formStr += boundary + '\r\n' + 'Content-Disposition: form-data; name="road_haul"\r\n\r\n'
        formStr += str(Decimal(shareJob['vehicle']['summary']['mileage']) / Decimal(10000)) + "\r\n"
        formStr += boundary + '\r\n' + 'Content-Disposition: form-data; name="price"\r\n\r\n'
        formStr += str(Decimal(self.getPrice(shareJob)) / Decimal(10000)) + "\r\n"
        formStr += boundary + '\r\n' + 'Content-Disposition: form-data; name="wholesale_price"\r\n\r\n'
        formStr += "\r\n"

        #是否含过户费 1=是
        formStr += boundary + '\r\n' + 'Content-Disposition: form-data; name="transfer_fee"\r\n\r\n'
        if quoted_price_include_transfer_fee:
            formStr += "1\r\n"
        else:
            formStr += "0\r\n"


        photos = []
        for photo in photoList:
            photo_info = photo['info'][0]
            p = {
                "image": photo_info['url'],
                "thumb_image": photo_info['thumbUrl'],
                "width": photo_info['image_info'][0],
                "height": photo_info['image_info'][1],
                "id": photo_info['guid'],
                "is_new": True
            }
            photos.append(p)

        #照片
        formStr += boundary + '\r\n' + 'Content-Disposition: form-data; name="images"\r\n\r\n'
        formStr += json.dumps([photos, []]) + "\r\n"
        #视频
        formStr += boundary + '\r\n' + 'Content-Disposition: form-data; name="is_video_upload"\r\n\r\n'
        formStr += "0\r\n"
        formStr += boundary + '\r\n' + 'Content-Disposition: form-data; name="video_unique"\r\n\r\n'
        formStr += "\r\n"
        #标题
        title = ""
        if external_vehicle_spec['model']['key'] == '0':
            title = external_vehicle_spec['vendor']['name'] + spec['year_group'] + ' ' + spec['sale_name']
        else:
            title = external_vehicle_spec['vendor']['name'] + external_vehicle_spec['model']['name']
        logger.debug("external_vehicle_model_id=" + external_vehicle_model_id)
        logger.debug("title=" + title)
        #不能超过15字符
        title = title[0:14*3]
        formStr += str(title) + '\r\n'

        #一句话标题
        ad_title = self.getTitle(vehicle)
        if '' == ad_title:
            ad_title = u'手续全 包过户'
        formStr += boundary + '\r\n' + 'Content-Disposition: form-data; name="ad_title"\r\n\r\n'
        formStr += ad_title + "\r\n"

        #车辆说明
        formStr += boundary + '\r\n' + 'Content-Disposition: form-data; name="description"\r\n\r\n'
        formStr += self.getContentVal_ganji(shareJob) + "\r\n"
        #add comments for ganji vehicles in description



        #TODO 是否在4s店保修期内 2=否 1=是
        formStr += boundary + '\r\n' + 'Content-Disposition: form-data; name="four_s"\r\n\r\n'
        formStr += "1\r\n"
        '''
        n = datetime.utcnow()
        if n.year - d.year <= 2:
            formStr += "1\r\n"
        else:
            formStr += "2\r\n"
        '''

        #行驶证 share
        #FIXME:merchant_substitute_config.description_switch.merchant_disable
        merchant_disable = True
        if merchant_substitute_config is not None:
            description_switch = merchant_substitute_config.get('description_switch', None)
            if description_switch is not None:
                merchant_disable = description_switch.get('merchant_disable', None)

        formStr += boundary + '\r\n' + 'Content-Disposition: form-data; name="imageSecond"\r\n\r\n'
        licenseDic = self.uploadLicensePic(vehicle, merchant_disable) #list
        if licenseDic is None:
            licenseStr = ''
        else:
            if dict == type(licenseDic):
                license_info = licenseDic['info'][0]
            if list == type(licenseDic):
                license_info = licenseDic[0]['info'][0]
            licensePic = []
            p = {
                "image": license_info['url'],
                #"image": 'gjfs05/M04/8E/BA/CgEHm1VB8MbFR7qsAADmNiRi7Vc870.jpg',
                #"thumb_image": "gjfs05/M04/8E/BA/CgEHm1VB8MbFR7qsAADmNiRi7Vc870_90-75c_6-0.jpg",
                "thumb_image": license_info['thumbUrl'],
                "width": license_info['image_info'][0],
                "height": license_info['image_info'][1],
                "id": license_info['guid'],
                "is_new": True
            }
            licensePic.append(p)
            licenseStr = json.dumps([licensePic, []])

        formStr += licenseStr + "\r\n"

        (username, mobile) = self.getContact(shareJob)
        # mobile = "18610205279"
        formStr += boundary + '\r\n' + 'Content-Disposition: form-data; name="person"\r\n\r\n'
        formStr += str(username) + "\r\n"
        formStr += boundary + '\r\n' + 'Content-Disposition: form-data; name="agent"\r\n\r\n'
        formStr += "2\r\n"
        formStr += boundary + '\r\n' + 'Content-Disposition: form-data; name="phone"\r\n\r\n'
        formStr += str(mobile) + "\r\n"

        #备用联系电话
        formStr += boundary + '\r\n' + 'Content-Disposition: form-data; name="back_phone"\r\n\r\n'
        formStr += str(phone) + "\r\n"
        #看车地点
        formStr += boundary + '\r\n' + 'Content-Disposition: form-data; name="district_id"\r\n\r\n'
        formStr += city.getCode(districtCode) + "\r\n"
        formStr += boundary + '\r\n' + 'Content-Disposition: form-data; name="checkcode"\r\n\r\n'
        if checkCode is None:
            formStr += "\r\n"
        else:
            formStr += checkCode + "\r\n"
        formStr += boundary + '\r\n' + 'Content-Disposition: form-data; name="id"\r\n\r\n'
        formStr += "0\r\n"
        formStr += boundary + "--"

        (success, msg) = self.postVehicle(headers, formStr, city.getName(districtCode))
        if success:
            return errorcode.SUCCESS, msg
        logger.error(msg)
        return errorcode.SITE_ERROR, msg

        # self.postCount = self.postCount + 1
        # print ''
        # print '-----PostCount'+ str(self.postCount) + '-------'
        # print ''
        # self.shareVehicle(shareJob)


    def postVehicle(self, headers, form, city):
        logger.debug(form)

        # self.cookies['ganji_uuid'] = '4482440840381636086775'
        # self.cookies['citydomain'] = 'bj'
        self.cookies['citydomain'] = city

        # ks = self.cookies.keys()
        # cookie_list = []
        # for k in ks:
        #     cookie_list.append(k + '=' + self.cookies[k])
        # headers['Cookie'] = string.join(cookie_list, '; ')

        # conn = httplib.HTTPConnection("tuiguang.ganji.com", timeout=10)
        # conn.request("GET", "/che2/?mod=car_source_pub", headers=headers)
        # res = conn.getresponse()
        # self.setCookies(res.getheaders())
        # conn.close()

        #print form
        if type(form) == type(u''):
            form = form.encode("utf-8")
        headers['Content-Length'] = len(form)
        headers['Referer'] = "http://www.ganji.com/pub/pub.php?method=load&cid=6&mcid=14&deal=1&origin=vehicle_bang&act=pub&domain="+city

        bangbangCookie = copy.copy(self.cookies)
        bangbangCookie['ershouche_activity'] = 1
        bangbangCookie['vehicle_bang_lead'] = 1

        headers['Cookie'] = string.join(['%s=%s;' % (key, value) for (key, value) in bangbangCookie.items()])

        conn = httplib.HTTPConnection("www.ganji.com", timeout=10)
        conn.request("POST", "/pub/pub.php?act=pub&cid=6&mcid=14&method=submit&domain=" + city, form,
                     headers=headers)
        res = conn.getresponse()
        status = res.status
        resHeaders = res.getheaders()
        err_msg = "网站出错"
        if status == 302:
            logger.debug(resHeaders)
            for header in resHeaders:
                if header[0].lower() == u'location':
                    location = header[1]
                    o = urlparse(location)
                    host = o.netloc
                    uri = o.path + '?' + o.query
                    #print host
                    #print uri
                    conn = httplib.HTTPConnection("www.ganji.com", timeout=10)
                    conn.request("GET", uri, headers=self.headers)
                    res = conn.getresponse()
                    resHeaders = res.getheaders()
                    html = self.decodeBody(resHeaders, res.read())

                    dom = lxml.html.fromstring(html)
                    data = dom.xpath('//span[@id="bdshare"]/@data')
                    if len(data) > 0:
                        o = json.loads(data[0].replace("'", '"'))
                        url = 'http://' + host + o['url']
                        return True, url
                    #TODO: 个人账号发车成功后的url需要从网页中获取
                    if location.count('free_bang') > 0:
                        logger.debug("个人账户发布成功")
                        return True, location
        else:
            html = self.decodeBody(resHeaders, res.read())
            logger.debug("---err response---\n" + html)
            dom = lxml.html.fromstring(html)
            err_msg_type_a = dom.xpath('//div[@class="block_cont"]/p/span/text()')
            err_msgs = dom.xpath('//div[@class="cont_error_img"]/p/text()')
            if len(err_msgs) > 0:
                err_msg = err_msgs[0]
            if len(err_msg_type_a) > 0:
                err_msg = err_msg_type_a[0]

            #TODO:替换重复车源
            if err_msg.count("您已发布过类似信息")>0:
                res.close()
                url = dom.xpath('//p/a/@href')
                if len(url) >0 :
                    url = url[0]

                (success, msg) = self.replaceVehicle(city, dom)
                if success:
                    return True, msg
                else:
                    return False, msg

                    #return True, url
        logger.debug("error:"+ err_msg)

        #print err_msg.encode('utf-8')
        return False, err_msg

    def replaceVehicle(self, city, dom):
        #1.0 post /pub/pub.php?cid=6&mcid=14&act=pub&method=similarSubmit&domain=
        vehicleInfo = dom.xpath('//form[@id="id_post_form"]/input[@name="request_id"]/@value')
        if len(vehicleInfo) >0 :
            #ershouche142769890768
            vehicleInfo = vehicleInfo[0]
        else:
            return  False, ""

        boundary = "-"*27 +  str(int (random.random() * sys.maxint)) + str(int (random.random() * 10000000000))
        #boundary = "-"*29 +  "18777692192475874211525960508"
        formStr = '--' + boundary + '\r\n' + 'Content-Disposition: form-data; name="request_id"\r\n\r\n'
        formStr += vehicleInfo +'\r\n'
        formStr += '--' + boundary + "--"
        host = 'www.ganji.com'
        uri = '/pub/pub.php?cid=6&mcid=14&act=pub&method=similarSubmit&domain='
        headers = copy.copy(self.headers)
        headers['Referer'] = 'http://www.ganji.com/pub/pub.php?act=pub&cid=6&mcid=14&method=submit&domain=' + str(city)
        headers['Host'] = host
        headers['Content-Type'] = 'multipart/form-data; boundary=' + boundary
        headers['Content-Length'] = len(formStr)

        bangbangCookie = copy.copy(self.cookies)
        bangbangCookie['ershouche_activity'] = '12'
        bangbangCookie['ganji_uuid'] = '2191522399241345036172'
        bangbangCookie['vehicle_list_view_type'] = '1'
        bangbangCookie['ErshoucheDetailPageScreenType'] = '1280'
        bangbangCookie['vehicle_bang_promote_status_363275351_v1'] = 'true'
        #bangbangCookie['vehicle_bang_promote_status_363275351_v1'] = True
        headers['Cookie'] = string.join(['%s=%s;' % (key, urllib.quote(value)) for (key, value) in bangbangCookie.items()])
        #headers['Cookie']['ganji_uuid'] = ''

        conn = httplib.HTTPConnection(host, timeout=10)
        conn.request("POST", uri, formStr, headers=headers)
        res = conn.getresponse()
        resHeaders = res.getheaders()
        resBody = res.read()
        html = self.decodeBody(resHeaders, resBody)
        logger.debug("resHeaders:" + str(resHeaders))
        logger.debug("html:"+str(html))
        status = res.status
        if status != 302:
            return False, u'发布过类似车源，替换失败2'
        else:
            for i in resHeaders:
                #logger.debug(str(i[0]) + str(i[1]))
                if i[0] == 'location':
                    location = i[1]

            #2.0 gethttp://bj.ganji.com/common/success.php?id=5651168&title=%E5%A4%A7%E4%BC%97%E5%B8%95%E8%90%A8%E7%89%B9%E9%A2%86%E9%A9%AD+2007%E6%AC%BE+1.8T+%E8%87%AA%E5%8A%A8+VIP+%E5%AF%BC%E8%88%AA%E7%89%88&category=vehicle&type=1&district_id=0&bang=1
            #//div/p[@class]/a[@href]
            host = str(city) + '.ganji.com'

            uri = re.findall(r'\/common.*bang=1', location)
            if len(uri):
                uri = uri[0]
            else:
                return False, u'发布过类似车源，获取uri失败'

            headers = copy.copy(self.headers)
            headers['Host'] = host
            headers['Referer'] = 'http://www.ganji.com/pub/pub.php?act=pub&cid=6&mcid=14&method=submit&domain=' + str(city)
            headers['Connection'] = 'keep-alive'
            headers['ganji_uuid'] = '2191522399241345036172'
            headers['ganji_xuuid'] = 'b91da319-ecf1-4d9e-f64b-d4a4624b1da8'
            headers['ErshoucheDetailPageScreenType'] = '1280'
            headers['vehicle_list_view_type'] = 1
            headers['ershouche_activity'] = 12
            headers['statistics_clientid'] = 'me'

            bangbangCookie = copy.copy(self.cookies)
            headers['Cookie'] = string.join(['%s=%s;' % (key, urllib.quote(value)) for (key, value) in bangbangCookie.items()])

            conn = httplib.HTTPConnection('www.' + host, timeout=10)
            conn.request("GET", uri, headers=headers)
            res = conn.getresponse()
            resHeaders = res.getheaders()
            resBody = res.read()
            status = res.status
            html = self.decodeBody(resHeaders, resBody)
            logger.debug("resheaders:" + str(resHeaders))
            logger.debug("html:" + str(html))

            if status != 302:
                return False, u'发布过类似车源，替换失败1'
            else:
                #3.0 http://www.ganji.com/common/success.php?id=5671682&title=%E5%A4%A7%E4%BC%97%E5%B8%95%E8%90%A8%E7%89%B9%E9%A2%86%E9%A9%AD+2007%E6%AC%BE+1.8T+%E8%87%AA%E5%8A%A8+VIP+%E5%AF%BC%E8%88%AA%E7%89%88&category=vehicle&type=1&district_id=0&bang=1&domain=bj
                #//div[@class='release-success clearfix']/div/div/p[@class='st1']/a[1]/@href

                headers = copy.copy(self.headers)
                headers['Referer'] = 'http://' + host + uri

                for i in resHeaders:
                    #logger.debug(str(i[0]) + str(i[1]))
                    if i[0] == 'location':
                        location = i[1]
                uri = re.findall(r'\/common.*', location)
                if len(uri):
                    uri = uri[0]
                else:
                    return False, "发布过类似车源，获取uri失败2"


                host = 'www.ganji.com'
                headers['Host'] = host
                headers['Connection'] = 'keep-alive'
                headers['ganji_uuid'] = '2191522399241345036172'
                headers['ganji_xuuid'] = 'b91da319-ecf1-4d9e-f64b-d4a4624b1da8'
                headers['ErshoucheDetailPageScreenType'] = '1280'
                headers['vehicle_list_view_type'] = 1
                headers['ershouche_activity'] = 12
                headers['statistics_clientid'] = 'me'

                bangbangCookie = copy.copy(self.cookies)
                headers['Cookie'] = string.join(['%s=%s;' % (key, urllib.quote(value)) for (key, value) in bangbangCookie.items()])


                conn = httplib.HTTPConnection(host, timeout=10)
                conn.request("GET", uri, headers=headers)
                res = conn.getresponse()
                resHeaders = res.getheaders()
                resBody = res.read()
                status = res.status
                html = self.decodeBody(resHeaders, resBody)
                logger.debug("resheaders:" + str(resHeaders))
                logger.debug("html:" + str(html))
                if not html.count(u'发布成功'):
                    return False, u'发布过类似车源，获取URL失败2'
                else:
                    getDom = lxml.html.fromstring(html)
                    url = getDom.xpath(r"//div[@class='release-success clearfix']/div/div/p[@class='st1']/a[1]/@href")
                    if not len(url):
                        return False, u'发布过类似车源，获取URL失败1'
                    else:
                        url = url[0]
                        return True, url

    '''@staticmethod
    def getContactName(shareJob):
        contact = u'销售代表'
        vehicle = shareJob.get('vehicle', None)
        user = vehicle.get('user', None)
        if user is not None:
            name = user.get('name', None)
            if name is not None:
                contact = name
        return contact

    @staticmethod
    def getContactPhone(shareJob):
        phone = u'13800000000'
        vehicle = shareJob.get('vehicle', None)
        user = vehicle.get('user', None)
        if user is not None:
            mobile = user.get('mobile', None)
            if mobile is not None:
                phone = mobile
        return phone'''

    @staticmethod
    def getColorCode(shareJob):
        vehicle = shareJob.get("vehicle")
        color = vehicle.get("summary").get('color')
        if color is None:
            logger.error("color missing")
            #return errorcode.LOGIC_ERROR, ""
            return "1" #默认为黑色
        logger.debug("color=" + color)

        #colorCode = "14" #其它
        colorTable = {"black": "1", "white": "2", "red": "6", "yellow": "9", "multi": "13", "orange": "10",
                    "brown": "5", "blue": "7", "green": "8", "purple": "12", "silver": "3", "grey": "4",
                      "champagne": "11", "other": "14"}

        colorCode = colorTable.get(color, "14")
        return colorCode


    @staticmethod
    def getDate(shareJob):
        d = IsoDate.from_iso_string('2015-05-09T00:00:00.000+08:00')
        vehicle = shareJob.get("vehicle", None)
        if vehicle is not None:
            vehicleDate = vehicle.get('vehicle_date', None)
            if vehicleDate is not None:
                registrationDate = vehicleDate.get('registration_date', None)
                if registrationDate is not None:
                    #d = IsoDate.from_iso_string(registrationDate)
                    d = registrationDate.astimezone(tz.HKT)
        return d

    @staticmethod
    def add_years(d, years):
        """Return a date that's `years` years after the date (or datetime)
        object `d`. Return the same calendar date (month and day) in the
        destination year, if it exists, otherwise use the following day
        (thus changing February 29 to March 1).

        """
        try:
            return d.replace(year = d.year + years)
        except ValueError:
            return d + (date(d.year + years, 1, 1) - date(d.year, 1, 1))

    def getInspectionDate(self, shareJob):
        d = self.add_years(self.getDate(shareJob), 1)

        vehicle = shareJob.get("vehicle", None)
        if vehicle is not None:
            vehicleDate = vehicle.get('vehicle_date', None)
            if vehicleDate is not None:
                registrationDate = vehicleDate.get('inspection_date', None)
                if registrationDate is not None:
                    #d = IsoDate.from_iso_string(registrationDate)
                    d = registrationDate.astimezone(tz.HKT)
        return d

    def getCompulsorInsuranceExpireDate(self, shareJob):
        d = self.getInspectionDate(shareJob)
        #如果不存在，默认等于年检时间
        vehicle = shareJob.get("vehicle", None)
        if vehicle is not None:
            vehicleDate = vehicle.get('vehicle_date', None)
            if vehicleDate is not None:
                registrationDate = vehicleDate.get('compulsory_insurance_expire_date', None)
                if registrationDate is not None:
                    #d = IsoDate.from_iso_string(registrationDate)
                    d = registrationDate.astimezone(tz.HKT)
        return d

    def uploadPics(self, photos):
        photo_list = []
        photos = photos[:15] #最多15张图
        for photo in photos:
            url = photo.get("url", None)
            if url is None:
                continue
            o = urlparse(url)
            host = o.netloc
            uri = o.path

            upload = self.sessionServer.getUpload('ganji', uri)
            logger.debug('--upload-- \n' + str(upload))
            if upload is not None:
                res = json.loads(upload)
            else:
                host = 'pic.kanche.com'
                # if host == 'pic.kanche.com':
                #     host = 'kanche-pic.qiniudn.com'
                conn = httplib.HTTPConnection(host, timeout=10)
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
                if (res is not None) and (res.has_key("error") and (res["error"] == 0)):
                    self.sessionServer.setUpload('ganji', uri, json.dumps(res))
            if (res is not None) and (res.has_key("error") and (res["error"] == 0)):
                photo_list.append(res)
        return photo_list

    def uploadPicContent(self, content):
        # http://www.51auto.com/AttachFileSubmit;jsessionid=9889D41ED01FC8ACCB17C40CA448EBCF-n2?model=new&leval=1&picId=pic8
        # FILEID:http://picture.51auto.com/tmp/pic820140821135536-hU5ws.jpg
        conn = httplib.HTTPConnection("image.ganji.com", timeout=10)
        headers = copy.copy(self.headers)

        img = StringIO(content)
        smallImg = StringIO()
        resize.resize(img, (800, 800), False, smallImg)
        boundaryHeader = "----pluploadboundary1408600538106"
        headers['Referer'] = 'http://www.51auto.com/static/js/plupload/plupload.flash.swf?77792'
        headers["Content-Type"] = "multipart/form-data; boundary=" + boundaryHeader
        content = smallImg.getvalue()
        boundary = "--" + boundaryHeader
        picForm = boundary + '\r\n' + 'Content-Disposition: form-data; name="maxSize"\r\n\r\n'
        picForm += "10485760\r\n"
        picForm += boundary + '\r\n' + 'Content-Disposition: form-data; name="resizeImage"\r\n\r\n'
        picForm += "true\r\n"
        picForm += boundary + '\r\n' + 'Content-Disposition: form-data; name="resizeWidth"\r\n\r\n'
        picForm += "800\r\n"
        picForm += boundary + '\r\n' + 'Content-Disposition: form-data; name="resizeHeight"\r\n\r\n'
        picForm += "600\r\n"
        picForm += boundary + '\r\n' + 'Content-Disposition: form-data; name="createThumb"\r\n\r\n'
        picForm += "false\r\n"
        picForm += boundary + '\r\n' + 'Content-Disposition: form-data; name="thumbWidth"\r\n\r\n'
        picForm += "80\r\n"
        picForm += boundary + '\r\n' + 'Content-Disposition: form-data; name="thumbHeight"\r\n\r\n'
        picForm += "80\r\n"
        picForm += boundary + '\r\n' + 'Content-Disposition: form-data; name="thumbCutEnable"\r\n\r\n'
        picForm += "true\r\n"
        picForm += boundary + '\r\n' + 'Content-Disposition: form-data; name="minWidth"\r\n\r\n'
        picForm += "0\r\n"
        picForm += boundary + '\r\n' + 'Content-Disposition: form-data; name="minHeight"\r\n\r\n'
        picForm += "0\r\n"
        picForm += boundary + '\r\n' + 'Content-Disposition: form-data; name="uploadDir"\r\n\r\n'
        picForm += "vehicle\r\n"
        picForm += boundary + '\r\n' + 'Content-Disposition: form-data; name="MAX_FILE_SIZE"\r\n\r\n'
        picForm += "10485760\r\n"
        picForm += boundary + '\r\n' + 'Content-Disposition: form-data; name="type"\r\n\r\n'
        picForm += "gif,jpg,jpeg,png,bmp\r\n"
        picForm += boundary + '\r\n' + 'Content-Disposition: form-data; name="_guid"\r\n\r\n'
        guid = "guid_1_%d_%d" % (int(time.time() * 10000), int (random.random() * sys.maxint / 1000))
        picForm += guid + "\r\n"

        picForm += boundary + '\r\n' + 'Content-Disposition: form-data; name="file"; filename="aa.jpg"\r\nContent-Type: image/jpeg\r\n\r\n'
        picForm += str(content) + '\r\n'
        picForm += boundary + "--"
        headers['Content-Length'] = len(picForm)
        conn.request("POST", "/upload.php",
                     picForm,
                     headers=headers)
        res = conn.getresponse()
        result = self.decodeBody(res.getheaders(), res.read())

        conn.close()

        result = result.decode("utf-8")
        try:
            obj = json.loads(result)
            logger.info(result)
            obj['info'][0]['guid'] = guid
            return obj
        except Exception as e:
            logger.debug(str(e))
        return None

    def uploadPicContent_license(self, content):
        # http://www.51auto.com/AttachFileSubmit;jsessionid=9889D41ED01FC8ACCB17C40CA448EBCF-n2?model=new&leval=1&picId=pic8
        # FILEID:http://picture.51auto.com/tmp/pic820140821135536-hU5ws.jpg
        conn = httplib.HTTPConnection("image.ganji.com", timeout=10)
        headers = copy.copy(self.headers)

        img = StringIO(content)
        smallImg = StringIO()
        resize.resize(img, (600, 450), True, smallImg)
        boundaryHeader = "----pluploadboundary1408600538106"
        headers['Referer'] = 'http://www.51auto.com/static/js/plupload/plupload.flash.swf?77792'
        headers["Content-Type"] = "multipart/form-data; boundary=" + boundaryHeader
        content = smallImg.getvalue()
        boundary = "--" + boundaryHeader
        picForm = boundary + '\r\n' + 'Content-Disposition: form-data; name="maxSize"\r\n\r\n'
        picForm += "10485760\r\n"
        picForm += boundary + '\r\n' + 'Content-Disposition: form-data; name="resizeImage"\r\n\r\n'
        picForm += "true\r\n"
        picForm += boundary + '\r\n' + 'Content-Disposition: form-data; name="resizeWidth"\r\n\r\n'
        picForm += "600\r\n"
        picForm += boundary + '\r\n' + 'Content-Disposition: form-data; name="resizeHeight"\r\n\r\n'
        picForm += "450\r\n"
        picForm += boundary + '\r\n' + 'Content-Disposition: form-data; name="resizeCutEnable"\r\n\r\n'
        picForm += "true\r\n"
        picForm += boundary + '\r\n' + 'Content-Disposition: form-data; name="createThumb"\r\n\r\n'
        picForm += "false\r\n"
        picForm += boundary + '\r\n' + 'Content-Disposition: form-data; name="thumbWidth"\r\n\r\n'
        picForm += "90\r\n"
        picForm += boundary + '\r\n' + 'Content-Disposition: form-data; name="thumbHeight"\r\n\r\n'
        picForm += "75\r\n"
        picForm += boundary + '\r\n' + 'Content-Disposition: form-data; name="thumbCutEnable"\r\n\r\n'
        picForm += "true\r\n"
        picForm += boundary + '\r\n' + 'Content-Disposition: form-data; name="minWidth"\r\n\r\n'
        picForm += "0\r\n"
        picForm += boundary + '\r\n' + 'Content-Disposition: form-data; name="minHeight"\r\n\r\n'
        picForm += "0\r\n"
        picForm += boundary + '\r\n' + 'Content-Disposition: form-data; name="uploadDir"\r\n\r\n'
        picForm += "vehicle\r\n"
        picForm += boundary + '\r\n' + 'Content-Disposition: form-data; name="MAX_FILE_SIZE"\r\n\r\n'
        picForm += "10485760\r\n"
        picForm += boundary + '\r\n' + 'Content-Disposition: form-data; name="type"\r\n\r\n'
        picForm += "gif,jpg,jpeg,png,bmp\r\n"
        picForm += boundary + '\r\n' + 'Content-Disposition: form-data; name="_guid"\r\n\r\n'
        randomStr = str(int(random.random() * sys.maxint / 1000))[0:16]
        guid = "guid_1_%d_%d" % (int(time.time() * 10000), int(randomStr))
        picForm += guid + "\r\n"

        picForm += boundary + '\r\n' + 'Content-Disposition: form-data; name="file"; filename="aa.jpg"\r\nContent-Type: image/jpeg\r\n\r\n'
        picForm += str(content) + '\r\n'
        picForm += boundary + "--"
        headers['Content-Length'] = len(picForm)
        conn.request("POST", "/upload.php",
                     picForm,
                     headers=headers)
        res = conn.getresponse()
        result = self.decodeBody(res.getheaders(), res.read())

        conn.close()

        result = result.decode("utf-8")
        try:
            obj = json.loads(result)
            logger.info(result)
            obj['info'][0]['guid'] = guid
            return obj
        except Exception as e:
            logger.debug(str(e))
        return None

    # ==========================================
    # remove Vehicle from management desk
    # ==========================================
    def removeVehicle(self,shareJob):
        print '\tgo into removeVehicle'
        shareAccount = shareJob.get("share_account", None)
        if shareAccount is None:
            return errorcode.AUTH_ERROR, ""
        if shareAccount.get('account_type', None) == 'public':
            shareAccount['username'] = publicAccount['username']
            shareAccount['password'] = publicAccount['password']

        #cookies = self.sessionServer.getSession('ganji', shareAccount['username'])
        cookies = None
        if cookies is None:
            result = self.doLogin(shareAccount['username'], shareAccount['password'])
            if not result:
                return errorcode.AUTH_ERROR, errormsg.LOGIN_FAIL
            #self.sessionServer.setSession('ganji', shareAccount['username'], self.cookies)
        else:
            self.cookies = cookies
            ks = self.cookies.keys()
            cookie_list = []
            for k in ks:
                cookie_list.append(k + '=' + self.cookies[k])
            self.headers['Cookie'] = str(string.join(cookie_list, '; '))

        urlForApp = shareJob.get("url", None)
        if urlForApp is None or len(urlForApp) == 0:
            return errorcode.DATA_ERROR, errormsg.VEHICLE_URL_EMPTY
        print '\turlForApp:',urlForApp

        pageId = self.getRealId(urlForApp);


        #http://bj.ganji.com/ershouche/14103112_5223294.htm?_rtm=1 [app may get]
        #http://bj.ganji.com/ershouche/1219465967x.htm [we need]
        #pRule = r'([0-9]{10})'

        # value = urlForApp.find("_")
        # if value:
        #     #get urlForApp: http://bj.ganji.com/ershouche/14103112_5223294.htm?_rtm=1
        #     headers = copy.copy(self.headers)
        #     conn = httplib.HTTPConnection("www.ganji.com", timeout=10)
        #     conn.request("GET", urlForApp, headers=headers)
        #     res1 = conn.getresponse()
        #     print "res1.status",res1.status
        #     if res1.status != 301:
        #         return errorcode.AUTH_ERROR, errormsg.VEHICLE_REMOVE_FAIL
        #     urlForApp = res1.getheader("Location")
        #
        # pRule = r'(\d+)'
        # pageList = re.compile(pRule).findall(urlForApp)
        # if len(pageList):
        #     pageId = pageList[0]
        #     #pageId = pageList[-1]
        # else:
        #     logger.debug("error:get pageId failed!")
        #     pageId = ""
        # print '\tpageId:',pageId
        logger.debug("pageId:"+str(pageId) )
        
        #edit by david 2014-10-22
        headers = copy.copy(self.headers)
        formData = 'one=%s,0&permanently=0&isOutside='%pageId
        headers['Origin'] = 'http://www.ganji.com'
        headers['Referer'] = 'http://www.ganji.com/vip/my_post_list.php'
        headers['X-Requested-With'] = 'XMLHttpRequest'
        headers['Content-Type'] = 'application/x-www-form-urlencoded; charset=UTF-8'
        url = "/vip/ajax/rm_post.php"
        
        conn = httplib.HTTPConnection("www.ganji.com", timeout=10)
        conn.request("POST", url,formData, headers=headers)
        res1 = conn.getresponse()
        print "res1.status",res1.status
        if res1.status == 200:
            return errorcode.SUCCESS, ""
        else:
            return errorcode.SITE_ERROR, errormsg.VEHICLE_REMOVE_FAIL
        #edit end
        
    def updateVehicle(self, shareJob):
        shareAccount = shareJob.get("share_account", None)
        if shareAccount is None:
            return errorcode.AUTH_ERROR, ""
        if shareAccount.get('account_type', None) == 'public':
            shareAccount['username'] = publicAccount['username']
            shareAccount['password'] = publicAccount['password']

        logger.debug("ganji shareVehicle")
        #cookies = self.sessionServer.getSession('ganji', shareAccount['username'])
        cookies = None
        if cookies is None:
            res = self.doLogin(shareAccount['username'], shareAccount['password'])
            if not res:
                logger.debug("login error")
                return errorcode.AUTH_ERROR, errormsg.LOGIN_FAIL
            # self.sessionServer.setSession('ganji', shareAccount['username'], self.cookies)
            if 'loginact' in self.cookies:
                del self.cookies['loginact']
            ks = self.cookies.keys()
            cookie_list = []
            for k in ks:
                cookie_list.append(k + '=' + self.cookies[k])
            self.headers['Cookie'] = string.join(cookie_list, '; ')
        else:
            self.cookies = cookies
            ks = self.cookies.keys()
            cookie_list = []
            for k in ks:
                cookie_list.append(k + '=' + self.cookies[k])
            self.headers['Cookie'] = string.join(cookie_list, '; ')

        logger.debug("self.cookies = " + str(self.cookies))
        logger.debug("header.Cookie = " + str(self.headers['Cookie']))


        urlForApp = shareJob.get("url", None)

        queryId = self.getRealId(urlForApp);

        logger.debug("ganji vehicleId:"+str(queryId))
        if queryId is None:
            return errorcode.DATA_ERROR, errormsg.VEHICLE_URL_EMPTY

        # queryId 1291121891
        # http://tuiguang.ganji.com/che2/?mod=car_source_pub&post_act=update&puid=1291121891&pub_type=1
        # get normalRealId


        conn = httplib.HTTPConnection('tuiguang.ganji.com', timeout=10)
        location_url = '/che2/?mod=car_source_pub&post_act=update&puid='+queryId+'&pub_type=1'
        conn.request("GET", location_url, headers = self.headers)
        res = conn.getresponse()
        tangResult = self.decodeBody(res.getheaders(), res.read())
        conn.close()

        getDom = lxml.html.fromstring(tangResult)

        if tangResult.count(u'不正确'):
            errorMessage = getDom.xpath('//a/text()')
            if errorMessage is not None:
                errorMessage = errorMessage[0]
            else:
                errorMessage = errormsg.SITE_OTHER_ERROR
            logger.error(errorMessage)
            return errorcode.SITE_ERROR, errorMessage

        normalRealUrl = getDom.xpath('//iframe[@id="pubIframe"]/@src')[0]

        realId = re.search("&id=(.*)&domain", normalRealUrl).group(1)
        realUrl = normalRealUrl.split('ganji.com')[-1]

        conn = httplib.HTTPConnection('www.ganji.com', timeout=10)
        conn.request("GET", realUrl, headers = self.headers)
        res = conn.getresponse()
        updateResult = self.decodeBody(res.getheaders(), res.read())
        conn.close()

        if (updateResult.count('没有修改权限')):
            uploadedImages = ''
            logger.debug("get uploadedImages error")
        else:
            uploadedRe = re.search("upoadedImages* :(.*),setCover", updateResult)
            uploadedImagesString = uploadedRe.group(1)
            uploadedImages = json.loads(uploadedImagesString)


        photos = []
        for image in uploadedImages:
            p = {
                "image": image['image'],
                "thumb_image": image['thumb_image'],
                "id": image['id']
            }
            photos.append(p)

        

        vehicle = shareJob.get("vehicle", None)
        if vehicle is None:
            logger.error("vehicle missing")
            return errorcode.DATA_ERROR, errormsg.VEHICLE_EMPTY

        price = vehicle.get('price', None)
        quoted_price_include_transfer_fee = price.get('quoted_price_include_transfer_fee', None)
        if quoted_price_include_transfer_fee is None:
            quoted_price_include_transfer_fee = False

        merchant_substitute_config = shareJob.get('merchant_substitute_config', None)
        phone = ''
        if merchant_substitute_config is not None:
            extra_contact = merchant_substitute_config.get('extra_contact', None)
            phone = ''
            phone = extra_contact.get('phone', None)
            if phone is None:
                phone = ''



        user = vehicle.get("user", None)
        if user is None:
            logger.error("user missing")
            return errorcode.DATA_ERROR, errormsg.USER_EMPTY
        address = user.get('address', None)
        if address is None:
            #return False
            return errorcode.DATA_ERROR, errormsg.ADDRESS_EMPTY

        districtCode = address.get('district_code', None)
        if districtCode is None:
            #return
            return errorcode.DATA_ERROR, errormsg.DISTRICT_EMPTY
        mobile = user.get("mobile", None)
        if mobile is None:
            return errorcode.DATA_ERROR, errormsg.MOBILE_EMPTY

        spec = vehicle.get("spec", None)
        if spec is None:
            logger.error("spec missing")
            return errorcode.DATA_ERROR, errormsg.VEHICLE_SPEC_EMPTY
        levelId = spec.get("level_id", None)
        if levelId is None:
            logger.error("levelId missing")
            return errorcode.LOGIC_ERROR, errormsg.VEHICLE_SPEC_EMPTY
        logger.debug("levelId=" + levelId)
        vehicle_spec_detail = shareJob.get("vehicle_spec_detail", None)
        if vehicle_spec_detail is None:
            return errorcode.DATA_ERROR, errormsg.VEHICLE_SPEC_EMPTY
        external_vehicle_spec = shareJob.get("external_vehicle_spec", None)
        if external_vehicle_spec is None:
            return errorcode.DATA_ERROR, errormsg.EXTERNAL_SPEC_EMPTY
        external_vehicle_model_id = external_vehicle_spec['model']['id']
        logger.debug(str(external_vehicle_spec))
        if external_vehicle_spec['model']['key'] == '0':
            title = external_vehicle_spec['vendor']['name'] + spec['year_group'] + ' ' + spec['sale_name']
        else:
            title = external_vehicle_spec['vendor']['name'] + external_vehicle_spec['model']['name']
        logger.debug("external_vehicle_model_id=" + external_vehicle_model_id)
        logger.debug("title=" + title)
        gallery = vehicle.get("gallery", None)
        if gallery is None:
            logger.error("gallery missing")
            return errorcode.DATA_ERROR, errormsg.PHOTO_NOT_ENOUGH
        city = cityGanji.CityGanji()
        conn = httplib.HTTPConnection("www.ganji.com", timeout=10)
        logger.info("cityName: "+city.getName(districtCode))


        conn.request("GET", realUrl, headers=self.headers)
        checkCodeUrl = None
        res = conn.getresponse()
        resHeaders = res.getheaders()
        logger.debug("resHeaders=" + str(resHeaders))
        #self.setCookies(resHeaders)
        resBody = self.decodeBody(resHeaders, res.read())
        try:
            dom = lxml.html.fromstring(resBody)
            #print resBody
            showCodeStyle = dom.xpath('//*[@id="showcode"]/@style')
            checkCodeUrls = dom.xpath('//*[@id="img_checkcode"]/@src')
            #print showCodeStyle
            logger.debug(showCodeStyle)
            if len(showCodeStyle) > 0 and showCodeStyle[0].count('none') == 0 and len(checkCodeUrls) > 0:
                checkCodeUrl = checkCodeUrls[0]
        except Exception as e:
            logger.error(e)
            pass

        checkCode = None
        if checkCodeUrl is not None:
            checkCode = self.getCheckCode(checkCodeUrl)
            #print checkCode
            logger.debug(checkCode)

        headers = copy.copy(self.headers)
        boundaryHeader = "-----------" +  str(int (random.random() * sys.maxint / 1000))
        headers['Referer'] = 'http://www.ganji.com/pub/pub.php?act=pub&method=load&cid=6&mcid=14&domain=' + city.getName(districtCode) + '&deal=1&domain=bj'
        headers["Content-Type"] = "multipart/form-data; boundary=" + boundaryHeader
        boundary = "--" + boundaryHeader
        formStr = boundary + '\r\n' + 'Content-Disposition: form-data; name="major_category_id"\r\n\r\n'
        formStr += "14\r\n"
        formStr += boundary + '\r\n' + 'Content-Disposition: form-data; name="auto_type"\r\n\r\n'
        formStr += "0\r\n"
        formStr += boundary + '\r\n' + 'Content-Disposition: form-data; name="autotype"\r\n\r\n'
        formStr += "0\r\n"
        formStr += boundary + '\r\n' + 'Content-Disposition: form-data; name="beforeAudit"\r\n\r\n'
        formStr += "false\r\n"
        formStr += boundary + '\r\n' + 'Content-Disposition: form-data; name="show_before_audit"\r\n\r\n'
        formStr += "0\r\n"
        formStr += boundary + '\r\n' + 'Content-Disposition: form-data; name="show_before_audit_reason"\r\n\r\n'
        formStr += "\r\n"
        formStr += boundary + '\r\n' + 'Content-Disposition: form-data; name="origin"\r\n\r\n'
        formStr += "vehicle_bang\r\n"
        formStr += boundary + '\r\n' + 'Content-Disposition: form-data; name="deal_type"\r\n\r\n'
        formStr += "1\r\n"
        formStr += boundary + '\r\n' + 'Content-Disposition: form-data; name="minor_category"\r\n\r\n'
        formStr += str(external_vehicle_spec['brand']['name']) + "\r\n"
        formStr += boundary + '\r\n' + 'Content-Disposition: form-data; name="minorCategory"\r\n\r\n'
        formStr += str(','.join([external_vehicle_spec['brand']['id'], external_vehicle_spec['brand']['spell'], external_vehicle_spec['brand']['name']])) + "\r\n"
        formStr += boundary + '\r\n' + 'Content-Disposition: form-data; name="tag"\r\n\r\n'
        formStr += str(','.join([external_vehicle_spec['series']['id'], external_vehicle_spec['series']['key'], external_vehicle_spec['series']['name']])) + "\r\n"
        formStr += boundary + '\r\n' + 'Content-Disposition: form-data; name="car"\r\n\r\n'
        formStr += str(external_vehicle_spec['model']['id']) + "\r\n"
        formStr += boundary + '\r\n' + 'Content-Disposition: form-data; name="user_defined_category"\r\n\r\n'
        if external_vehicle_spec['model']['key'] == '0':
            formStr += str(spec['sale_name'] + ' ' + spec['year_group']) + "\r\n"
        else:
            formStr += str(external_vehicle_spec['model']['name']) + "\r\n"
        formStr += boundary + '\r\n' + 'Content-Disposition: form-data; name="car_color"\r\n\r\n'
        formStr += self.getColorCode(shareJob) + "\r\n"
        formStr += boundary + '\r\n' + 'Content-Disposition: form-data; name="gearbox"\r\n\r\n'
        formStr += "1\r\n"
        formStr += boundary + '\r\n' + 'Content-Disposition: form-data; name="air_displacement"\r\n\r\n'
        formStr += vehicle_spec_detail['details'][23] + "\r\n"
        formStr += boundary + '\r\n' + 'Content-Disposition: form-data; name="accidents"\r\n\r\n'
        formStr += "1\r\n"
        d = self.getDate(shareJob)                                      #获取的是初等时间update
        inspection_date = self.getInspectionDate(shareJob)
        compulsor_date = self.getCompulsorInsuranceExpireDate(shareJob)

        formStr += boundary + '\r\n' + 'Content-Disposition: form-data; name="license_date"\r\n\r\n'
        formStr += str(d.year) + "\r\n"
        formStr += boundary + '\r\n' + 'Content-Disposition: form-data; name="license_year"\r\n\r\n'
        formStr += str(d.year) + "\r\n"
        formStr += boundary + '\r\n' + 'Content-Disposition: form-data; name="license_math"\r\n\r\n'
        formStr += str(d.month) + "\r\n"
        formStr += boundary + '\r\n' + 'Content-Disposition: form-data; name="insurance_year_add"\r\n\r\n'
        formStr += str(inspection_date.year) + "\r\n"
        formStr += boundary + '\r\n' + 'Content-Disposition: form-data; name="insurance_month_add"\r\n\r\n'
        formStr += str(inspection_date.month) + "\r\n"
        formStr += boundary + '\r\n' + 'Content-Disposition: form-data; name="strong_insurance_year"\r\n\r\n'
        formStr += str(compulsor_date.year) + "\r\n"
        formStr += boundary + '\r\n' + 'Content-Disposition: form-data; name="strong_insurance_month"\r\n\r\n'
        formStr += str(compulsor_date.month) + "\r\n"
        formStr += boundary + '\r\n' + 'Content-Disposition: form-data; name="road_haul"\r\n\r\n'
        formStr += str(Decimal(shareJob['vehicle']['summary']['mileage']) / Decimal(10000)) + "\r\n"
        formStr += boundary + '\r\n' + 'Content-Disposition: form-data; name="price"\r\n\r\n'
        formStr += str(Decimal(self.getPrice(shareJob)) / Decimal(10000)) + "\r\n"
        formStr += boundary + '\r\n' + 'Content-Disposition: form-data; name="wholesale_price"\r\n\r\n'
        formStr += "\r\n"

        #是否含过户费 1=是
        formStr += boundary + '\r\n' + 'Content-Disposition: form-data; name="transfer_fee"\r\n\r\n'
        if quoted_price_include_transfer_fee:
            formStr += "1\r\n"
        else:
            formStr += "0\r\n"

        #车辆照片
        formStr += boundary + '\r\n' + 'Content-Disposition: form-data; name="images"\r\n\r\n'
        formStr += json.dumps([photos, []]) + "\r\n"
        #视频
        formStr += boundary + '\r\n' + 'Content-Disposition: form-data; name="is_video_upload"\r\n\r\n'
        formStr += "0\r\n"
        formStr += boundary + '\r\n' + 'Content-Disposition: form-data; name="video_unique"\r\n\r\n'
        formStr += "\r\n"
        formStr += boundary + '\r\n' + 'Content-Disposition: form-data; name="title"\r\n\r\n'
        #标题
        title = ""
        if external_vehicle_spec['model']['key'] == '0':
            title = external_vehicle_spec['vendor']['name'] + spec['year_group'] + ' ' + spec['sale_name']
        else:
            title = external_vehicle_spec['vendor']['name'] + external_vehicle_spec['model']['name']
        logger.debug("external_vehicle_model_id=" + external_vehicle_model_id)
        logger.debug("title=" + title)
        #不能超过15字符
        title = title[0:14*3]
        formStr += str(title) + '\r\n'

        #一句话标题
        ad_title = self.getTitle(vehicle)
        if '' == ad_title:
            ad_title = u'手续全 包过户'
        formStr += boundary + '\r\n' + 'Content-Disposition: form-data; name="ad_title"\r\n\r\n'
        formStr += ad_title + "\r\n"

        formStr += boundary + '\r\n' + 'Content-Disposition: form-data; name="description"\r\n\r\n'
        formStr += self.getContentVal_ganji(shareJob) + "\r\n"



        #TODO 是否在4s店保修期内 2=否 1=是
        formStr += boundary + '\r\n' + 'Content-Disposition: form-data; name="four_s"\r\n\r\n'
        formStr += "1\r\n"
        '''
        n = datetime.utcnow()
        if n.year - d.year <= 2:
            formStr += "1\r\n"
        else:
            formStr += "2\r\n"
        '''

        #行驶证 update
        #FIXME:merchant_substitute_config.description_switch.merchant_disable
        merchant_disable = True
        if merchant_substitute_config is not None:
            description_switch = merchant_substitute_config.get('description_switch', None)
            if description_switch is not None:
                merchant_disable = description_switch.get('merchant_disable', None)

        formStr += boundary + '\r\n' + 'Content-Disposition: form-data; name="imageSecond"\r\n\r\n'
        licenseDic = self.uploadLicensePic(vehicle, merchant_disable) #list
        if licenseDic is None:
            licenseStr = ''
        else:
            if dict == type(licenseDic):
                license_info = licenseDic['info'][0]
            if list == type(licenseDic):
                license_info = licenseDic[0]['info'][0]
            licensePic = []
            p = {
                "image": license_info['url'],
                #"image": 'gjfs05/M04/8E/BA/CgEHm1VB8MbFR7qsAADmNiRi7Vc870.jpg',
                #"thumb_image": "gjfs05/M04/8E/BA/CgEHm1VB8MbFR7qsAADmNiRi7Vc870_90-75c_6-0.jpg",
                "thumb_image": license_info['thumbUrl'],
                "width": license_info['image_info'][0],
                "height": license_info['image_info'][1],
                "id": license_info['guid'],
                "is_new": True
            }
            licensePic.append(p)
            licenseStr = json.dumps([licensePic, []])

        formStr += licenseStr + "\r\n"

        (username, mobile) = self.getContact(shareJob)
        # mobile = "18610205279"
        formStr += boundary + '\r\n' + 'Content-Disposition: form-data; name="person"\r\n\r\n'
        formStr += str(username) + "\r\n"
        formStr += boundary + '\r\n' + 'Content-Disposition: form-data; name="agent"\r\n\r\n'
        formStr += "2\r\n"

        formStr += boundary + '\r\n' + 'Content-Disposition: form-data; name="phone"\r\n\r\n'
        formStr += str(mobile) + "\r\n"

        #备用联系电话
        formStr += boundary + '\r\n' + 'Content-Disposition: form-data; name="back_phone"\r\n\r\n'
        formStr += str(phone) + "\r\n"
        #看车地区
        formStr += boundary + '\r\n' + 'Content-Disposition: form-data; name="district_id"\r\n\r\n'
        formStr += city.getCode(districtCode) + "\r\n"
        formStr += boundary + '\r\n' + 'Content-Disposition: form-data; name="checkcode"\r\n\r\n'
        if checkCode is None:
            formStr += "\r\n"
        else:
            formStr += checkCode + "\r\n"

        formStr += boundary + '\r\n' + 'Content-Disposition: form-data; name="puid"\r\n\r\n'
        formStr += str(queryId)+"\r\n"
        formStr += boundary + '\r\n' + 'Content-Disposition: form-data; name="id"\r\n\r\n'
        formStr += str(realId)+"\r\n"
        formStr += boundary + "--"

        (success, msg) = self.postUpdateVehicle(headers, formStr, city.getName(districtCode))
        if success:
            return errorcode.SUCCESS, msg
        logger.error(msg)
        return errorcode.SITE_ERROR, errormsg.SITE_OTHER_ERROR

    def postUpdateVehicle(self, headers, form, city):
        logger.debug(form)

        # self.cookies['ganji_uuid'] = '4482440840381636086775'
        # self.cookies['citydomain'] = 'bj'
        self.cookies['citydomain'] = city

        # ks = self.cookies.keys()
        # cookie_list = []
        # for k in ks:
        #     cookie_list.append(k + '=' + self.cookies[k])
        # headers['Cookie'] = string.join(cookie_list, '; ')

        # conn = httplib.HTTPConnection("tuiguang.ganji.com")
        # conn.request("GET", "/che2/?mod=car_source_pub", headers=headers)
        # res = conn.getresponse()
        # self.setCookies(res.getheaders())
        # conn.close()

        #print form
        if type(form) == type(u''):
            form = form.encode("utf-8")
        headers['Content-Length'] = len(form)
        headers['Referer'] = "http://www.ganji.com/pub/pub.php?method=load&cid=6&mcid=14&deal=1&origin=vehicle_bang&act=pub&domain="+city

        bangbangCookie = copy.copy(self.cookies)
        bangbangCookie['ershouche_activity'] = 1
        bangbangCookie['vehicle_bang_lead'] = 1

        headers['Cookie'] = string.join(['%s=%s;' % (key, value) for (key, value) in bangbangCookie.items()])

        conn = httplib.HTTPConnection("www.ganji.com", timeout=10)

        conn.request("POST", "/pub/pub.php?act=update&cid=6&mcid=14&method=submit&domain=" + city, form,
                     headers=headers)
        res = conn.getresponse()
        status = res.status
        resHeaders = res.getheaders()
        err_msg = "网站出错"
        if status == 302:
            logger.debug(resHeaders)
            for header in resHeaders:
                if header[0].lower() == u'location':
                    #carIdRe = re.search('id=(?P<carId>[0-9]*)&', header[1])
                    #carId = carIdRe.group("carId")
                    #logger.debug(carId)
                    #return True,"http://bj.ganji.com/ershouche/%sx.htm"%(carId,
                    location = header[1]
                    o = urlparse(location)
                    host = o.netloc
                    uri = o.path + '?' + o.query
                    #print host
                    #print uri
                    conn = httplib.HTTPConnection("www.ganji.com", timeout=10)
                    conn.request("GET", uri, headers=self.headers)
                    res = conn.getresponse()
                    resHeaders = res.getheaders()
                    html = self.decodeBody(resHeaders, res.read())
                    #print resHeaders
                    #print html
                    '''status = res.status
                    if status == 302:
                        logger.debug(resHeaders)
                        for header in resHeaders:
                            if header[0].lower() == u'location':'''
                    dom = lxml.html.fromstring(html)
                    data = dom.xpath('//span[@id="bdshare"]/@data')
                    if len(data) > 0:
                        o = json.loads(data[0].replace("'", '"'))
                        url = 'http://' + host + o['url']
                        #return True, url
                        return True, "修改成功"
                        # 58修改价格后的url会自动跳转到发布时的url
                    #TODO: 个人账号发车成功后的url需要从网页中获取
                    if location.count('free_bang') > 0:
                        logger.debug("个人账户发布成功")
                        #return True, location
                        return True, "修改成功"
                    logger.debug("---err response---\n" + html)
        else:
            #print status
            #logger.debug(resHeaders)
            html = self.decodeBody(resHeaders, res.read())
            dom = lxml.html.fromstring(html)
            err_msgs = dom.xpath('//div[@class="cont_error_img"]/p/text()')
            if len(err_msgs) > 0:
                err_msg = err_msgs[0]
        logger.debug(err_msg)

        #print err_msg.encode('utf-8')
        return False, err_msg

    def getRealId(self, urlForApp):

        combie_id = re.compile("\d+_\d+").findall(urlForApp)
        if combie_id[0]:
            location_url = urlForApp.split('ganji.com')[-1]
            tempUrl = re.compile("\/\/.*com").findall(urlForApp)
            host = tempUrl[0].split('//')[-1]

            conn = httplib.HTTPConnection(host, timeout=10)
            conn.request("GET", location_url, headers = self.headers)
            res = conn.getresponse()
            status = res.status
            resHeaders = res.getheaders()
            conn.close()
            if status == 301:
                for header in resHeaders:
                    if header[0].lower() == u'location':
                        location = header[1]
                        queryId = re.compile("[0-9]\d{3,}").findall(location)
                        return queryId[0]
            else:
                logger.error( errormsg.VEHICLE_URL_EMPTY)
                return errorcode.SITE_ERROR, errormsg.VEHICLE_URL_EMPTY

        else:
            queryId = re.compile("[0-9]\d{3,}").findall(urlForApp)[0]
            return queryId

    def getTitle(self, vehicle):
        desc = vehicle.get('desc', None)
        if desc is None:
            return None
        brief = desc.get('brief', None)
        if brief is None:
            return None
        return brief

    def uploadLicensePic(self, vehicle, merchant_disable):
        summary = vehicle.get('summary', None)
        drivingLicenseUrl = summary.get('driving_license_picture', None)
        if merchant_disable or merchant_disable is None:
            return None
        if (drivingLicenseUrl is None or drivingLicenseUrl == '') and (merchant_disable is False):
            picPath = './app/resource/drivingLicensePictureIfNone.jpg'

            drivingLicenseFile = open(picPath)
            drivingLicenseContent = ''

            try:
                drivingLicenseContent = drivingLicenseFile.read()
            finally:
                drivingLicenseFile.close()

            res = self.uploadPicContent(drivingLicenseContent)

            if res is not None:
                return res
            else:
                return None

        photo_list = []
        o = urlparse(drivingLicenseUrl)
        host = o.netloc
        uri = o.path

        upload = self.sessionServer.getUpload('ganji', uri)
        logger.debug('--upload-- \n' + str(upload))

        if upload is not None:
            res = json.loads(upload)
        else:

            if host == 'pic.kanche.com':
                host = 'kanche-pic.qiniudn.com'
            conn = httplib.HTTPConnection(host, timeout=10)
            headers = copy.copy(self.headers)
            del headers['Cookie']
            headers['Referer'] = "www.kanche.com"
            conn.request("GET", uri, headers = headers)
            res = conn.getresponse()
            content = res.read()
            conn.close()
            res = self.uploadPicContent_license(content)
            logger.debug(str(res))
            if (res is not None) and (res.has_key("error") and (res["error"] == 0)):
                self.sessionServer.setUpload('ganji', uri, json.dumps(res))
        photo_list.append(res)
        return photo_list
