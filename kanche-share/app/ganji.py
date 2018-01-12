#!/usr/bin/python
# -*- coding: UTF-8 -*-

import httplib
import urllib
import re
import sys
import random
import time
import json
import zlib
import string
import copy
import requests
import data_model
from decimal import *
from datetime import date
from urlparse import urlparse
from StringIO import StringIO

import lxml.html
import tz
import logger
import errorcode
import errormsg
import resize
import cityGanji
from dt8601 import IsoDate
from base import BaseSharer

publicAccount = {
    # "username":u"kccs02",
    # "password":u"1a2s3d"
    "username": u"石家庄看车网",
    "password": u"asasas"
}


class GanjiSharer(BaseSharer):
    def __init__(self, sessionServer, specServer):
        super(GanjiSharer, self).__init__(sessionServer, specServer)
        self.postCount = 0
        self.session = requests.session()
        self.util = data_model.DataModelUtil()

    def doLogin(self, username, password):
        conn = httplib.HTTPSConnection("passport.ganji.com", timeout=10)
        url = '/login.php'
        conn.request("GET", url, headers=self.headers)
        res = conn.getresponse()
        headers = res.getheaders()
        html = zlib.decompress(res.read(), 16 + zlib.MAX_WBITS)
        html = html.decode('utf-8')
        # print html
        print headers
        self.setCookies(headers)
        hashRe = re.search("hash__ = \'(?P<hash>.*)\';", html)
        hash__ = hashRe.group("hash")
        print hash__
        conn.close()

        timestamp = int(time.time())
        conn = httplib.HTTPSConnection("passport.ganji.com", timeout=10)
        url = '/login.php?callback=t&username=%s&password=%s&checkCode=&setcookie=1&second=&parentfunc=&redirect_in_iframe=&next=&__hash__=%s&_=%d' % (
            urllib.quote(username.encode("utf-8")), urllib.quote(password.encode("utf-8")), hash__, timestamp)
        print url
        conn.request("GET", url, headers=self.headers)
        res = conn.getresponse()
        headers = res.getheaders()
        print headers
        self.setCookies(headers)
        html = res.read().decode('utf-8')
        # print html
        conn.close()
        msgRe = re.search("t\((?P<msg>.*)\)", html)
        msg = msgRe.group("msg")
        print msg
        resObj = json.loads(msg)
        if resObj['status'] != 1:
            if resObj['type'].startswith('need_captcha'):
                # login with captcha
                timestamp = int(time.time())
                conn = httplib.HTTPSConnection("passport.ganji.com", timeout=10)
                checkCodeImageUrl = '/ajax.php?dir=captcha&module=login_captcha&nocache=%d' % timestamp
                conn.request("GET", checkCodeImageUrl, headers=self.headers)
                res = conn.getresponse()
                self.setCookies(res.getheaders())
                imageData = res.read()
                conn.close()
                image = StringIO(imageData)

                # DONE: edit by jesse to improve captcha service
                captcha = self.getCaptcha(image, imageData)

                if captcha is None:
                    return False
                validcode = captcha["text"]

                conn = httplib.HTTPSConnection("passport.ganji.com", timeout=10)
                url = '/login.php?callback=t&username=%s&password=%s&checkCode=%s&setcookie=14&second=&parentfunc=&redirect_in_iframe=&next=&__hash__=%s&_=%d' % (
                    urllib.quote(username.encode("utf-8")), urllib.quote(password.encode("utf-8")), validcode, hash__,
                    timestamp)
                logger.debug(url)
                conn.request("GET", url, headers=self.headers)
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

    def get_hash(self):
        h = self.session.get('https://passport.ganji.com/login.php')
        root = lxml.html.fromstring(h.text)
        scripts = root.xpath(u'//script')
        target = scripts[len(scripts) - 1].text
        __hash__ = re.search('"__hash__":"(?P<hash>.*)"', target).group('hash')
        return __hash__

    def getCheckCode(self, checkCodeUrl):
        conn = httplib.HTTPConnection("www.ganji.com", timeout=10)
        conn.request("GET", checkCodeUrl, headers=self.headers)
        res = conn.getresponse()
        self.setCookies(res.getheaders())
        imageData = res.read()
        conn.close()
        image = StringIO(imageData)

        captcha = self.getCaptcha(image, imageData)
        if captcha is None:
            return None
        checkCode = captcha["text"]
        return checkCode

    def shareVehicle(self, shareJob):
        shareAccount = shareJob.get("share_account", None)
        if shareAccount is None:
            return errorcode.AUTH_ERROR, ""
        if shareAccount.get('account_type', None) == 'public':
            shareAccount['username'] = publicAccount['username']
            shareAccount['password'] = publicAccount['password']

        logger.debug("ganji shareVehicle")
        # cookies = self.sessionServer.getSession('ganji', shareAccount['username'])
        # 赶集不要cookie太短
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
        (success, msg) = self.postShareVehicle(shareJob, '0')
        return success, msg

    ############
    # 发车
    ############
    def postShareVehicle(self, shareJob, id):
        vehicle = shareJob.get("vehicle", None)
        if vehicle is None:
            logger.error("vehicle missing")
            return errorcode.DATA_ERROR, errormsg.VEHICLE_EMPTY
        price = vehicle.get('price', None)
        quoted_price_include_transfer_fee = price.get('quoted_price_include_transfer_fee', None)
        if quoted_price_include_transfer_fee is None:
            quoted_price_include_transfer_fee = False

        merchant = vehicle.get('merchant', None)
        merchant_address = merchant.get('address', None)
        districtCode = merchant_address.get('district_code', None)
        if districtCode is None:
            districtCode = merchant_address.get('city_code', None)
            if districtCode is None:
                return errorcode.DATA_ERROR, errormsg.DISTRICT_EMPTY

        user = vehicle.get("user", None)
        if user is None:
            logger.error("user missing")
            return errorcode.DATA_ERROR, errormsg.USER_EMPTY

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
        # logger.debug("title=" + title)
        gallery = vehicle.get("gallery", None)
        if gallery is None:
            logger.error("gallery missing")
            return errorcode.DATA_ERROR, errormsg.PHOTO_NOT_ENOUGH

        merchant_substitute_config = shareJob.get('merchant_substitute_config', None)

        city = cityGanji.CityGanji()
        cityCode = city.getName(districtCode)  # cc
        conn = httplib.HTTPConnection("www.ganji.com", timeout=10)
        logger.info("cityName: " + cityCode)
        conn.request("GET",
                     "/pub/pub.php?act=pub&method=load&cid=6&mcid=14&domain=" + city.getName(districtCode) + "&deal=1#",
                     headers=self.headers)
        checkCodeUrl = None
        res = conn.getresponse()
        resHeaders = res.getheaders()
        logger.debug("resHeaders=" + str(resHeaders))
        # self.setCookies(resHeaders)
        resBody = self.decodeBody(resHeaders, res.read())
        try:
            dom = lxml.html.fromstring(resBody)
            showCodeStyle = dom.xpath('//*[@id="showcode"]/@style')
            checkCodeUrls = dom.xpath('//*[@id="img_checkcode"]/@src')
            logger.debug(showCodeStyle)
            if len(showCodeStyle) > 0 and showCodeStyle[0].count('none') == 0 and len(checkCodeUrls) > 0:
                checkCodeUrl = checkCodeUrls[0]
        except Exception as e:
            logger.error(e)
            pass

        checkCode = ""
        if checkCodeUrl is not None:
            checkCode = self.getCheckCode(checkCodeUrl)
            logger.debug(checkCode)

        # text:车型车型model'大众 高尔夫 2010款 高尔夫6 1.6 双离合 豪华版', #
        text = str(external_vehicle_spec['brand']['name']) + str(external_vehicle_spec['series']['name']) + str(
            external_vehicle_spec['model']['name'])

        car_id = external_vehicle_spec['model']['key']

        # license_date,license_math
        d = self.getDate(shareJob)  # 获取的是初等时间share
        inspection_date = self.getInspectionDate(shareJob)
        compulsor_date = self.getCompulsorInsuranceExpireDate(shareJob)
        license_date = str(d.year)
        license_math = str(d.month)
        road_haul = str(Decimal(shareJob['vehicle']['summary']['mileage']) / Decimal(10000))

        # price
        price = str(Decimal(self.getPrice(shareJob)) / Decimal(10000))

        # transfer_fee
        if quoted_price_include_transfer_fee:
            transfer_fee = "1"
        else:
            transfer_fee = "0"

        (username, phone) = self.getContact(shareJob)

        back_phone = ''
        if merchant_substitute_config is not None:
            extra_contact = merchant_substitute_config.get('extra_contact', None)
            back_phone = ''
            back_phone = extra_contact.get('phone', None)
            if back_phone is None:
                back_phone = ''

        # district_id :495(绿园区)
        district_id = city.getCode(districtCode)

        photos = []
        photoList = self.uploadPics(gallery.get("photos", []))
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
        photoData = json.dumps([photos, []])

        # 行驶证
        # FIXME:merchant_substitute_config.description_switch.merchant_disable
        merchant_disable = True
        if merchant_substitute_config is not None:
            description_switch = merchant_substitute_config.get('description_switch', None)
            if description_switch is not None:
                merchant_disable = description_switch.get('merchant_disable', None)

        licenseDic = self.uploadLicensePic(vehicle, merchant_disable)  # list
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
                # "image": 'gjfs05/M04/8E/BA/CgEHm1VB8MbFR7qsAADmNiRi7Vc870.jpg',
                # "thumb_image": "gjfs05/M04/8E/BA/CgEHm1VB8MbFR7qsAADmNiRi7Vc870_90-75c_6-0.jpg",
                "thumb_image": license_info['thumbUrl'],
                "width": license_info['image_info'][0],
                "height": license_info['image_info'][1],
                "id": license_info['guid'],
                "is_new": True
            }
            licensePic.append(p)
            licenseStr = json.dumps([licensePic, []])

        # ad_title
        ad_title = self.promotionWords(vehicle, isSelectedBDwords=False)

        # vin
        vehicle = shareJob.get('vehicle', None)
        vin = vehicle.get('vin', None)
        if vin is None:
            vin = ''

        car_color = self.getColorCode(shareJob)

        Symbol = "\r\n"
        lateral = "——" * 20
        contentVal = ''
        if self.loanable(vehicle):
            contentVal = self.getContentVal_finance(shareJob, Symbol, lateral)
        else:
            contentVal = self.getContentVal(shareJob, Symbol, lateral)
        photoList = self.uploadPics(gallery.get("photos", []))
        logger.debug(json.dumps(photoList))
        headers = copy.copy(self.headers)
        headers[
            'Referer'] = 'http://www.ganji.com/pub/pub.php?act=pub&method=load&cid=6&mcid=14&domain=' + cityCode + '&deal=1&domain=bj'
        headers['Content-Type'] = 'application/x-www-form-urlencoded'
        formDict = {
            'major_category_id': "14",
            'auto_type': '0',
            'autotype': '0',
            'beforeAudit': '',
            'show_before_audit': '',
            'show_before_audit_reason': '',
            'origin': 'vehicle_bang',
            'text': str(text),  #
            'car_id': str(car_id),  #
            'license_date': str(license_date),  #
            'license_math': str(license_math),  #
            'road_haul': str(road_haul),  #
            'accidents': '1',
            'car_color': str(car_color),
            'price': str(price),  #
            'transfer_fee[]': str(transfer_fee),  #
            'wholesale_price': '',  #
            'transfer_num': '0',
            'person': str(username),  #
            'district_id': str(district_id),  #
            'phone': str(phone),  #
            'back_phone': str(back_phone),  #
            'agent': '2',
            'images': str(photoData),  #
            'ad_title': str(ad_title),
            'description': str(contentVal),
            'imageSecond': str(licenseStr),
            'vin': str(vin),  #
            'checkcode': str(checkCode),
            'id': str(id)
        }
        formData = urllib.urlencode(formDict)
        headers['Content-Length'] = len(formData)

        bangbangCookie = copy.copy(self.cookies)
        bangbangCookie['ershouche_activity'] = 12
        bangbangCookie['vehicle_bang_lead'] = 1
        headers['Cookie'] = string.join(['%s=%s;' % (key, value) for (key, value) in bangbangCookie.items()])

        # 发车
        uri = '/pub/pub.php?method=submit&cid=6&mcid=14&deal=1&origin=vehicle_bang&act=pub&domain=' + cityCode

        conn = httplib.HTTPConnection("www.ganji.com", timeout=10)
        conn.request("POST", uri, formData, headers=headers)
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
                        return errorcode.SUCCESS, url
                    # TODO: 个人账号发车成功后的url需要从网页中获取
                    if location.count('free_bang') > 0:
                        logger.debug("个人账户发布成功")
                        return errorcode.SUCCESS, location
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

            # TODO:替换重复车源
            if err_msg.count("您已发布过类似信息") > 0:
                res.close()
                return errorcode.DATA_ERROR, u'重复车源'

        logger.debug("error:" + err_msg)

        # print err_msg.encode('utf-8')
        return errorcode.NETWORK_ERROR, err_msg

    ############
    # 改价：
    ############
    def postUpdateVehicle(self, shareJob, puid, id):
        vehicle = shareJob.get("vehicle", None)
        if vehicle is None:
            logger.error("vehicle missing")
            return errorcode.DATA_ERROR, errormsg.VEHICLE_EMPTY
        price = vehicle.get('price', None)
        quoted_price_include_transfer_fee = price.get('quoted_price_include_transfer_fee', None)
        if quoted_price_include_transfer_fee is None:
            quoted_price_include_transfer_fee = False

        merchant = vehicle.get('merchant', None)
        merchant_address = merchant.get('address', None)
        districtCode = merchant_address.get('district_code', None)
        if districtCode is None:
            districtCode = merchant_address.get('city_code', None)
            if districtCode is None:
                return errorcode.DATA_ERROR, errormsg.DISTRICT_EMPTY

        user = vehicle.get("user", None)
        if user is None:
            logger.error("user missing")
            return errorcode.DATA_ERROR, errormsg.USER_EMPTY
        '''
        address = user.get('address', None)
        if address is None:
            #return False
            return errorcode.DATA_ERROR, errormsg.ADDRESS_EMPTY
        districtCode = address.get('district_code', None)
        if districtCode is None:
            #return
            return errorcode.DATA_ERROR, errormsg.DISTRICT_EMPTY
        '''

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

        city = cityGanji.CityGanji()
        cityCode = city.getName(districtCode)
        conn = httplib.HTTPConnection("www.ganji.com", timeout=10)
        logger.info("cityName: " + city.getName(districtCode))
        conn.request("GET",
                     "/pub/pub.php?act=pub&method=load&cid=6&mcid=14&domain=" + city.getName(districtCode) + "&deal=1#",
                     headers=self.headers)
        checkCodeUrl = None
        res = conn.getresponse()
        resHeaders = res.getheaders()
        logger.debug("resHeaders=" + str(resHeaders))
        # self.setCookies(resHeaders)
        resBody = self.decodeBody(resHeaders, res.read())
        try:
            dom = lxml.html.fromstring(resBody)
            showCodeStyle = dom.xpath('//*[@id="showcode"]/@style')
            checkCodeUrls = dom.xpath('//*[@id="img_checkcode"]/@src')
            logger.debug(showCodeStyle)
            if len(showCodeStyle) > 0 and showCodeStyle[0].count('none') == 0 and len(checkCodeUrls) > 0:
                checkCodeUrl = checkCodeUrls[0]
        except Exception as e:
            logger.error(e)
            pass

        checkCode = ""
        if checkCodeUrl is not None:
            checkCode = self.getCheckCode(checkCodeUrl)
            # print checkCode
            logger.debug(checkCode)

        # text:车型车型model'大众 高尔夫 2010款 高尔夫6 1.6 双离合 豪华版', #
        text = str(external_vehicle_spec['brand']['name']) + str(external_vehicle_spec['series']['name']) + str(
            external_vehicle_spec['model']['name'])

        # car_id: 1188
        car_id = external_vehicle_spec['model']['key']

        # license_date,license_math
        d = self.getDate(shareJob)  # 获取的是初等时间share
        inspection_date = self.getInspectionDate(shareJob)
        compulsor_date = self.getCompulsorInsuranceExpireDate(shareJob)
        license_date = str(d.year)
        license_math = str(d.month)
        road_haul = str(Decimal(shareJob['vehicle']['summary']['mileage']) / Decimal(10000))

        # price
        price = str(Decimal(self.getPrice(shareJob)) / Decimal(10000))

        # transfer_fee
        if quoted_price_include_transfer_fee:
            transfer_fee = "1"
        else:
            transfer_fee = "0"

        # person, phone
        (username, phone) = self.getContact(shareJob)

        # back_phone
        back_phone = ''
        if merchant_substitute_config is not None:
            extra_contact = merchant_substitute_config.get('extra_contact', None)
            back_phone = ''
            back_phone = extra_contact.get('phone', None)
            if back_phone is None:
                back_phone = ''

        # district_id :174
        district_id = city.getCode(districtCode)

        # images
        photos = []
        photoList = self.uploadPics(gallery.get("photos", []))
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
        photoData = json.dumps([photos, []])

        # 行驶证
        # FIXME:merchant_substitute_config.description_switch.merchant_disable
        merchant_disable = True
        if merchant_substitute_config is not None:
            description_switch = merchant_substitute_config.get('description_switch', None)
            if description_switch is not None:
                merchant_disable = description_switch.get('merchant_disable', None)

        licenseDic = self.uploadLicensePic(vehicle, merchant_disable)  # list
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
                # "image": 'gjfs05/M04/8E/BA/CgEHm1VB8MbFR7qsAADmNiRi7Vc870.jpg',
                # "thumb_image": "gjfs05/M04/8E/BA/CgEHm1VB8MbFR7qsAADmNiRi7Vc870_90-75c_6-0.jpg",
                "thumb_image": license_info['thumbUrl'],
                "width": license_info['image_info'][0],
                "height": license_info['image_info'][1],
                "id": license_info['guid'],
                "is_new": True
            }
            licensePic.append(p)
            licenseStr = json.dumps([licensePic, []])

        # ad_title
        ad_title = self.promotionWords(vehicle, isSelectedBDwords=False)

        # vin
        vehicle = shareJob.get('vehicle', None)
        vin = vehicle.get('vin', None)
        if vin is None:
            vin = ''

        car_color = self.getColorCode(shareJob)
        Symbol = "\r\n"
        lateral = "——" * 20
        contentVal = ''
        if self.loanable(vehicle):
            contentVal = self.getContentVal_finance(shareJob, Symbol, lateral)
        else:
            contentVal = self.getContentVal(shareJob, Symbol, lateral)
        photoList = self.uploadPics(gallery.get("photos", []))
        logger.debug(json.dumps(photoList))
        headers = copy.copy(self.headers)
        # 改价dict
        formDict = {
            'major_category_id': "14",
            'auto_type': '0',
            'autotype': '0',
            'beforeAudit': '',
            'show_before_audit': '',
            'show_before_audit_reason': '',
            'origin': 'vehicle_bang',
            # 'year_style': str(u'年款'),
            # 'transfer_fee[]': str(transfer_fee),
            # 'tag_url': 'sunata',
            # 'tag_text': str(u'现代索纳塔'),
            # 'air_displacement': '2',
            # 'gearbox': '2',
            'text': str(text),  #
            'car_id': str(car_id),  #
            'license_date': str(license_date),  #
            'license_math': str(license_math),  #
            'road_haul': str(road_haul),  #
            'accidents': '1',
            'car_color': str(car_color),  #
            'price': str(price),  #
            'wholesale_price': '',  #
            'transfer_num': '0',
            'person': str(username),  #
            'district_id': str(district_id),  #
            'phone': str(phone),  #
            'back_phone': str(back_phone),  #
            'agent': '2',
            'images': str(photoData),  #
            'ad_title': str(ad_title),
            'description': str(contentVal),
            'imageSecond': str(licenseStr),
            'vin': str(vin),  #
            'checkcode': str(checkCode),
            'puid': str(puid),
            'isHave': '',
            'id': str(id)
        }
        formData = urllib.urlencode(formDict)
        headers['Content-Length'] = len(formData)
        headers['Content-Type'] = 'application/x-www-form-urlencoded'
        headers['Host'] = 'www.ganji.com'
        headers['Origin'] = 'http://www.ganji.com'
        headers[
            'Referer'] = 'http://www.ganji.com/pub/pub.php?method=load&cid=6&mcid=14&deal=1&origin=vehicle_bang&act=update&id=' + str(
            id) + '&domain=bj'

        bangbangCookie = copy.copy(self.cookies)
        bangbangCookie['ershouche_activity'] = 1
        bangbangCookie['vehicle_bang_lead'] = 1
        headers['Cookie'] = string.join(['%s=%s;' % (key, value) for (key, value) in bangbangCookie.items()])

        logger.debug('headers:' + str(headers))
        logger.debug('cookie:' + str(headers['Cookie']))
        # uri = 'pub/pub.php?method=submit&cid=6&mcid=14&deal=1&origin=vehicle_bang&act=update&id=' + str(id) + '&domain=' + str(cityCode)
        uri = '/pub/pub.php?method=submit&cid=6&mcid=14&deal=1&origin=vehicle_bang&act=update&id=' + str(
            id) + '&domain=' + str(cityCode)
        # http://www.ganji.com/pub/pub.php?method=submit&cid=6&mcid=14&deal=1&origin=vehicle_bang&act=update&id=6032685&domain=bj


        conn = httplib.HTTPConnection("www.ganji.com", timeout=10)
        conn.request("POST", uri, formData, headers=headers)
        res = conn.getresponse()
        status = res.status
        resData = res.read()
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
                        return errorcode.SUCCESS, url
                    # TODO: 个人账号发车成功后的url需要从网页中获取
                    if location.count('free_bang') > 0:
                        logger.debug("update success")
                        return errorcode.SUCCESS, location
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

            # TODO:替换重复车源
            if err_msg.count("您已发布过类似信息") > 0:
                res.close()
                return errorcode.DATA_ERROR, u'重复车源'
        logger.debug("error:" + err_msg)

        # print err_msg.encode('utf-8')
        return errorcode.NETWORK_ERROR, err_msg

    def replaceVehicle(self, city, dom):
        # 1.0 post /pub/pub.php?cid=6&mcid=14&act=pub&method=similarSubmit&domain=
        vehicleInfo = dom.xpath('//form[@id="id_post_form"]/input[@name="request_id"]/@value')
        if len(vehicleInfo) > 0:
            # ershouche142769890768
            vehicleInfo = vehicleInfo[0]
        else:
            return False, ""

        boundary = "-" * 27 + str(int(random.random() * sys.maxint)) + str(int(random.random() * 10000000000))
        # boundary = "-"*29 +  "18777692192475874211525960508"
        formStr = '--' + boundary + '\r\n' + 'Content-Disposition: form-data; name="request_id"\r\n\r\n'
        formStr += vehicleInfo + '\r\n'
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
        # bangbangCookie['vehicle_bang_promote_status_363275351_v1'] = True
        headers['Cookie'] = string.join(
            ['%s=%s;' % (key, urllib.quote(value)) for (key, value) in bangbangCookie.items()])
        # headers['Cookie']['ganji_uuid'] = ''

        conn = httplib.HTTPConnection(host, timeout=10)
        conn.request("POST", uri, formStr, headers=headers)
        res = conn.getresponse()
        resHeaders = res.getheaders()
        resBody = res.read()
        html = self.decodeBody(resHeaders, resBody)
        logger.debug("resHeaders:" + str(resHeaders))
        logger.debug("html:" + str(html))
        status = res.status
        if status != 302:
            return False, u'发布过类似车源，替换失败2'
        else:
            for i in resHeaders:
                # logger.debug(str(i[0]) + str(i[1]))
                if i[0] == 'location':
                    location = i[1]

            # 2.0 gethttp://bj.ganji.com/common/success.php?id=5651168&title=%E5%A4%A7%E4%BC%97%E5%B8%95%E8%90%A8%E7%89%B9%E9%A2%86%E9%A9%AD+2007%E6%AC%BE+1.8T+%E8%87%AA%E5%8A%A8+VIP+%E5%AF%BC%E8%88%AA%E7%89%88&category=vehicle&type=1&district_id=0&bang=1
            # //div/p[@class]/a[@href]
            host = str(city) + '.ganji.com'

            uri = re.findall(r'\/common.*bang=1', location)
            if len(uri):
                uri = uri[0]
            else:
                return False, u'发布过类似车源，获取uri失败'

            headers = copy.copy(self.headers)
            headers['Host'] = host
            headers['Referer'] = 'http://www.ganji.com/pub/pub.php?act=pub&cid=6&mcid=14&method=submit&domain=' + str(
                city)
            headers['Connection'] = 'keep-alive'
            headers['ganji_uuid'] = '2191522399241345036172'
            headers['ganji_xuuid'] = 'b91da319-ecf1-4d9e-f64b-d4a4624b1da8'
            headers['ErshoucheDetailPageScreenType'] = '1280'
            headers['vehicle_list_view_type'] = 1
            headers['ershouche_activity'] = 12
            headers['statistics_clientid'] = 'me'

            bangbangCookie = copy.copy(self.cookies)
            headers['Cookie'] = string.join(
                ['%s=%s;' % (key, urllib.quote(value)) for (key, value) in bangbangCookie.items()])

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
                # 3.0 http://www.ganji.com/common/success.php?id=5671682&title=%E5%A4%A7%E4%BC%97%E5%B8%95%E8%90%A8%E7%89%B9%E9%A2%86%E9%A9%AD+2007%E6%AC%BE+1.8T+%E8%87%AA%E5%8A%A8+VIP+%E5%AF%BC%E8%88%AA%E7%89%88&category=vehicle&type=1&district_id=0&bang=1&domain=bj
                # //div[@class='release-success clearfix']/div/div/p[@class='st1']/a[1]/@href

                headers = copy.copy(self.headers)
                headers['Referer'] = 'http://' + host + uri

                for i in resHeaders:
                    # logger.debug(str(i[0]) + str(i[1]))
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
                headers['Cookie'] = string.join(
                    ['%s=%s;' % (key, urllib.quote(value)) for (key, value) in bangbangCookie.items()])

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

    @staticmethod
    def getColorCode(shareJob):
        vehicle = shareJob.get("vehicle")
        color = vehicle.get("summary").get('color')
        if color is None:
            logger.error("color missing")
            # return errorcode.LOGIC_ERROR, ""
            return "1"  # 默认为黑色
        logger.debug("color=" + color)

        # colorCode = "14" #其它
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
                    # d = IsoDate.from_iso_string(registrationDate)
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
            return d.replace(year=d.year + years)
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
                    # d = IsoDate.from_iso_string(registrationDate)
                    d = registrationDate.astimezone(tz.HKT)
        return d

    def getCompulsorInsuranceExpireDate(self, shareJob):
        d = self.getInspectionDate(shareJob)
        # 如果不存在，默认等于年检时间
        vehicle = shareJob.get("vehicle", None)
        if vehicle is not None:
            vehicleDate = vehicle.get('vehicle_date', None)
            if vehicleDate is not None:
                registrationDate = vehicleDate.get('compulsory_insurance_expire_date', None)
                if registrationDate is not None:
                    # d = IsoDate.from_iso_string(registrationDate)
                    d = registrationDate.astimezone(tz.HKT)
        return d

    def uploadPics(self, photos):
        photo_list = []
        photos = photos[:30]  # 最多15张图
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

                conn.request("GET", uri, headers=headers)
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
        guid = "guid_1_%d_%d" % (int(time.time() * 10000), int(random.random() * sys.maxint / 1000))
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

    def removeVehicle(self, job):
        account = self.util.get_account(job)
        if account is None:
            return errorcode.AUTH_ERROR, errormsg.LOGIN_FAIL
        if account.get("share_account", None) is 'public':
            usr = publicAccount['username']
            pwd = publicAccount['password']
        else:
            usr = account['username']
            pwd = account['password']
        successful = self.doLogin(usr, pwd)
        if not successful:
            return errorcode.AUTH_ERROR, errormsg.LOGIN_FAIL
        url = job.get('url', None)
        h = self.session.get(url)
        if h.status_code == 200:
            root = lxml.html.fromstring(h.text)
            ref = root.xpath(u'//div[@class="sub-menu"]/a[@class="btn_post_delete"]/@data-ref').pop(0)
            data = json.loads(ref)
            domain = urlparse(h.url).netloc.split('.').pop(0)
            param = {
                'puid': data['puid'],
                'domain': domain,
                'nocache': long(time.time()),
                'post_url': h.url.split('?').pop(0)
            }
            h = self.session.get('http://www.ganji.com/common/post/rm.php', params=param, headers=self.headers)
            root = lxml.html.fromstring(h.text)
            title = root.xpath(u'//form[@action="/common/post/rm_survey.php"]/div[@class="st-con"]/h1').pop(0).text
            if title == str(u'您的删帖原因？'):
                return errorcode.SUCCESS, "remove success - ganji"
            else:
                print(title)
                return errorcode.DATA_ERROR, "remove failed - ganji"
        elif h.status_code == 404:
            return errorcode.SUCCESS, "remove success - ganji - 404"
        else:
            return errorcode.DATA_ERROR, "remove failed - ganji"

    def updateVehicle(self, shareJob):
        shareAccount = shareJob.get("share_account", None)
        if shareAccount is None:
            return errorcode.AUTH_ERROR, ""
        if shareAccount.get('account_type', None) == 'public':
            shareAccount['username'] = publicAccount['username']
            shareAccount['password'] = publicAccount['password']

        logger.debug("ganji updateVehicle")
        # cookies = self.sessionServer.getSession('ganji', shareAccount['username'])
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

        puid, id = self.getRealId(urlForApp)

        logger.debug("ganji vehicleId:" + str(puid))
        if puid is None:
            return errorcode.DATA_ERROR, errormsg.VEHICLE_URL_EMPTY

        (success, msg) = self.postUpdateVehicle(shareJob, puid, id)

        if success == errorcode.SUCCESS:
            return errorcode.SUCCESS, msg
        logger.error(msg)
        return errorcode.SITE_ERROR, msg

    def getRealId(self, urlForApp):
        combie_id = re.compile("\d+").findall(urlForApp)
        id = combie_id[1]
        if combie_id[0]:
            location_url = urlForApp.split('ganji.com')[-1]
            tempUrl = re.compile("\/\/.*com").findall(urlForApp)
            host = tempUrl[0].split('//')[-1]

            conn = httplib.HTTPConnection(host, timeout=10)
            conn.request("GET", location_url, headers=self.headers)
            res = conn.getresponse()
            status = res.status
            resHeaders = res.getheaders()
            conn.close()
            if status == 301:
                for header in resHeaders:
                    if header[0].lower() == u'location':
                        location = header[1]
                        queryId = re.compile("[0-9]\d{3,}").findall(location)
                        return queryId[0], id
            else:
                logger.error(errormsg.VEHICLE_URL_EMPTY)
                return errorcode.SITE_ERROR, errormsg.VEHICLE_URL_EMPTY

        else:
            queryId = re.compile("[0-9]\d{3,}").findall(urlForApp)[0]
            return queryId, id

    # def getTitle(self, vehicle):
    #     desc = vehicle.get('desc', None)
    #     if desc is None:
    #         return ''
    #     brief = desc.get('brief', '')
    #     if brief is None:
    #         brief = ''
    #     return brief

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
            conn.request("GET", uri, headers=headers)
            res = conn.getresponse()
            content = res.read()
            conn.close()
            res = self.uploadPicContent_license(content)
            logger.debug(str(res))
            if (res is not None) and (res.has_key("error") and (res["error"] == 0)):
                self.sessionServer.setUpload('ganji', uri, json.dumps(res))
        photo_list.append(res)
        return photo_list
