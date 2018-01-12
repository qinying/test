#!/usr/bin/python
# -*- coding: UTF-8 -*-

#import os
import json
import copy
import zlib
import httplib
import urllib
import random
from urlparse import urlparse
import string
from cStringIO import StringIO
import subprocess
from decimal import *
import time
import requests
import re
import tz
import errormsg
import zimu
import resize
import lxml.html
import errorcode
import logger
from base import BaseSharer
from city582 import City852
from dt8601 import IsoDate
import utils
import socket
from lxml import html as hx
from bson.json_util import loads

socket.setdefaulttimeout(30)
timeout_58 = 30
g_pic_retry_times = 3 # 图片重试次数

data = {
    "account": {
        #"username": "goqnz_p2",
        "username": "北京看看车二手车",
        "password": "asasas"
    },
    "vehicle": {

    }
}

publicAccount = {
    #"username": u"18610205279",
    #"password": u"mengqian2"
    "username": u"看车二手车石家庄2014",
    "password": u"kankanqwe123"
    #"username":u"18005819169",
    #"password":"110110"
}


#单日上限50条	: 福州、广州、杭州、合肥、武汉、郑州、长沙、南宁、无锡、东莞、上海、
fiftyCityLimitList = ['350100', '440100', '330100', '340100', '420100', '410100', '430100', '450100', '320200', '441900', '310100']
#单日上限100条	北京、厦门、成都、重庆/ 深圳、苏州、南京、沈阳/ 哈尔滨、西安、大连、昆明 /温州、呼和浩特、包头、济南 /长春、佛山、天津、宁波/ 石家庄、青岛
hundCityLimitList = ['110100', '350200', '510100', '500100',
                     '440300', '320500', '320100', '210100',
                     '230100', '610100', '210200', '530100',
                     '330300', '150100', '150200', '370100',
                     '220100', '440600', '120100', '330200',
                     '130100', '370200']

class FESharer(BaseSharer):
    def __init__(self, sessionServer, specServer):
        super(FESharer, self).__init__(sessionServer, specServer)
        self.headers["Referer"] = "http://passport.58.com/login/"
        self.city582 = City852()

    def shareVehicle(self, shareJob):
        logger.debug("58 shareVehicle")
        shareAccount = shareJob.get("share_account", None)
        if shareAccount is None:
            return errorcode.DATA_ERROR, "缺少帐号"
        if shareAccount.get('account_type', None) == 'public':
            shareAccount['username'] = publicAccount['username']
            shareAccount['password'] = publicAccount['password']

        vehicle = shareJob.get("vehicle", None)
        merchant = vehicle.get('merchant', None)
        address = merchant.get('address', None)
        if address is None:
            #return False
            return errorcode.DATA_ERROR, errormsg.ADDRESS_EMPTY
        cityCode = address.get('city_code', None)

        ###check share_account
        website = '58.com'
        limit = 1000 #default
        if cityCode in fiftyCityLimitList:
            limit = 50
        if cityCode in hundCityLimitList:
            limit = 100

        #临时去掉
        check = self.isInnerAccountLimit(website, shareAccount['username'], limit, deadline="day")
        if not check:
            return errorcode.DATA_ERROR, errormsg.OUTER_ACCOUNT_LIMIT

        cookies = self.sessionServer.getSession('58', shareAccount['username'])
        logger.debug('-------session cookies---------\n' + str(cookies))

        if cookies is None:
            logger.debug("do login 58")
            res = self.doLogin(shareAccount['username'], shareAccount['password'])
            if not res:
                logger.error("login error")
                return errorcode.AUTH_ERROR, errormsg.LOGIN_FAIL
            self.sessionServer.setSession('58', shareAccount['username'], self.cookies)
        else:
            self.cookies = cookies
            ks = self.cookies.keys()
            cookie_list = []
            for k in ks:
                cookie_list.append(k + '=' + self.cookies[k])
            self.headers['Cookie'] = string.join(cookie_list, '; ')
        logger.debug(str(self.headers))


        vehicle = shareJob.get("vehicle", None)
        if vehicle is None:
            logger.debug("vehicle missing")
            return errorcode.DATA_ERROR, errormsg.VEHICLE_EMPTY
        user = vehicle.get("user", None)
        if user is None:
            return errorcode.DATA_ERROR, errormsg.USER_EMPTY
        mobile = user.get("mobile", None)
        if mobile is None:
            return errorcode.DATA_ERROR, errormsg.MOBILE_EMPTY

        spec = vehicle.get("spec", None)
        if spec is None:
            logger.debug("spec missing")
            return errorcode.DATA_ERROR, errormsg.VEHICLE_SPEC_EMPTY
        levelId = spec.get("level_id", None)
        if levelId is None:
            logger.debug("levelId missing")
            return errorcode.DATA_ERROR, errormsg.VEHICLE_SPEC_EMPTY
        logger.debug("levelId=" + levelId)
        #(specid, specDetail) = self.getCarSpec(levelId)
        externalSpec = shareJob.get("external_vehicle_spec", None)
        if externalSpec is None:
            logger.error("external spec missing")
            return errorcode.SPEC_ERROR, errormsg.EXTERNAL_SPEC_EMPTY
        logger.debug(str(externalSpec))
        externalSpecModelId = externalSpec['model']['id']
        logger.debug("externalSpecModelId=" + externalSpecModelId)
        gallery = vehicle.get("gallery", None)
        if gallery is None:
            logger.debug("gallery missing")
        watermark = shareJob.get("merchant_substitute_config", {}).get("watermark", None)
        photoList = self.uploadPics(gallery.get("photos", []), watermark)
        #如果图片上传失败，为None
        if photoList is None:
            return errorcode.SITE_ERROR, errormsg.PICTURE_UPLOAD_ERROR

        summary = vehicle.get("summary", None)
        if summary is None:
            drivingLicensePicture = None
        else:
            drivingLicensePicture = self.uploadDrivingLicensePicture(summary.get("driving_license_picture", None))

        logger.debug(json.dumps(photoList))

        (success, msg) = self.postVehicle(shareJob, externalSpec, photoList, drivingLicensePicture)
        if success == errorcode.SUCCESS:
            #upsert account num for 58
            #临时去掉
            self.upsertAccountNum(website, shareAccount['username'], limit, deadline="day")
            return success, msg

        return success, msg

    def getPostPage(self, code):
        conn = httplib.HTTPConnection("post.58.com", timeout=timeout_58)
        headers = copy.copy(self.headers)
        headers['Host'] = 'post.58.com'
        #headers['Referer'] = 'http://post.58.com/' + code
        conn.request("GET", "/v" + code + "/29/s5", headers=headers)
        logger.debug("/v" + code + "/29/s5")
        res = conn.getresponse()
        resHeaders = res.getheaders()
        logger.debug(str(resHeaders))
        self.setCookies(resHeaders, encode = True)
        #html = zlib.decompress(res.read(), 16+zlib.MAX_WBITS)
        html = self.decodeBody(resHeaders, res.read())
        html = html.decode('utf-8')
        #print html

        conn.close()

        #所有为普通账号走的通道：
        if html.count(u"您访问的页面居然不存在") > 0:
            headers['Host'] = 'post.58.com'
            #headers['Referer'] = 'http://post.58.com/' + code
            conn.request("GET", "/" + code + "/29/s5", headers = headers)
            logger.debug( "/" + code + "/29/s5")
            res = conn.getresponse()
            resHeaders = res.getheaders()
            logger.debug(str(resHeaders))
            self.setCookies(resHeaders, encode = True)
            #html = zlib.decompress(res.read(), 16+zlib.MAX_WBITS)
            html = self.decodeBody(resHeaders, res.read())
            html = html.decode('utf-8')
            #print html

            conn.close()

            return code, html
        code = 'v' + code
        return code, html

    def isVIP(self, shareJob):
        vehicle = shareJob.get("vehicle", None)
        merchant = vehicle.get('merchant', None)
        address = merchant.get('address', None)
        if address is None:
            #return False
            return errorcode.DATA_ERROR, errormsg.ADDRESS_EMPTY
        cityCode = address.get('city_code', None)
        if cityCode is None:
            #return
            return errorcode.DATA_ERROR, errormsg.CITY_EMPTY
        code = self.city582.getCode(cityCode)

        (url_code, html) = self.getPostPage(code)
        if not url_code.startswith('v'):
            return True
        return False

    '''
    # 判断是否为诚信车商
    '''
    @staticmethod
    def is_integrity_merchant(vehicle, username):
        try:
            city_code = str(vehicle.get('merchant').get('address').get('city_code'))
        except:
            city_code = 0
        # 合肥、长沙、佛山、杭州、沈阳、温州、武汉、南宁
        not_integrity_merchant_city_list = ['340100', '430100', '440600', '330100', '210100', '330300', '420100', '450100']
        not_integrity_merchant_account_list = ['n1c310', 'n1g9929', 'n1g509', 'n1g609', 'n1g972', 'n1g312', 'n1g506',
                                               'n1g820', 'n1e0217', 'n1e010305', u'精品车行A', u'陈利平2021']

        if username in not_integrity_merchant_account_list:
            return False
        if city_code in not_integrity_merchant_city_list:
            return False
        return True

    def postVehicleMobile(self, carInfo, externalSpec, photoList, code, cityCode):
        Symbol = "\n"
        lateral = "——"*20
        vehicle = carInfo.get('vehicle')

        form = "brand=" + str(externalSpec['brand']['spell'])
        form += "&chexi=" + str(externalSpec['series']['key'])
        if externalSpec['model']['key'] == '0':
            pass
        else:
            try:
                form += "&carchexing=" + str(externalSpec['summary']['carchexing']['v'])
            except Exception as e:
                pass
        form += "&cheshenyanse=" + self.getCheshenyanseVal(carInfo)
        form += "&buytime=" + str(self.getDate(carInfo).year)
        form += "&rundistance=" + self.getRundistanceVal(carInfo)
        if self.loanable(vehicle=vehicle):
            form += "&Content=" + urllib.quote(self.getContentVal_finance_58(carInfo, Symbol, lateral).encode('utf-8'))
        else:
            form += "&Content=" + urllib.quote(self.getContentVal(carInfo, Symbol, lateral).encode('utf-8'))

        form += "&MinPrice=" + self.getMinProceVal(carInfo)
        form += "&Title=" + urllib.quote(self.getTitleVal(externalSpec, carInfo, vehicle).encode('utf-8'))
        form += "&goblianxiren=" + urllib.quote(self.getGoblianxirenVal(carInfo).encode('utf-8'))
        form += "&Phone=" + self.getPhoneVal(carInfo)
        form += "&isBiz=0"
        form += "&type=0"
        form += "&Pic=" + urllib.quote_plus(self.bashgetPicValMobile(photoList))
        form += "&gobquzhi=" + urllib.quote_plus(self.getGobquzhiValMobile(carInfo, externalSpec, carInfo, code))
        form += "&formatsource=listpublish"
        form += "&headerData="
        form += "&shoujishipai=617383"
        form += "&hidPostParam=0"

        logger.debug("-------------form-----------\n" + form)
        conn = httplib.HTTPConnection("p.webapp.58.com", timeout=timeout_58)
        headers = copy.copy(self.headers)
        headers['Host'] = 'p.webapp.58.com'
        headers['Referer'] = 'http://p.webapp.58.com/' + str(code) + '/29/s5?s5&topcate=car&currentcate=ershouche&id=29&location=1,1142,1203&geotype=baidu&geoia=40.003795,116.486807&formatsource=home&cversion=5.8.0.1&os=android'
        headers['Content-Type'] = 'application/x-www-form-urlencoded'
        headers['Accept'] = 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'
        headers['Accept-Encoding'] = 'gzip,deflate'
        headers['Content-Length'] = len(form)
        headers['Origin'] = 'http://p.webapp.58.com'
        headers['Accept-Encoding'] = 'gzip, deflate'
        headers['Accept-Charset'] = 'utf-8, iso-8859-1, utf-16, *;q=0.7'
        conn.request("POST", "/" + str(code) + "/29/s5/submit?&topcate=car&currentcate=ershouche&id=29&location=1,1142,1203&geotype=baidu&geoia=40.003801,116.486767&formatsource=home&cversion=5.8.0.1&os=android", form, headers = headers)
        res = conn.getresponse()
        body = res.read()
        logger.debug(json.dumps(headers))
        resHeaders = res.getheaders()
        self.setCookies(resHeaders, encode = True)
        logger.debug(str(resHeaders))
        logger.debug("res.read:"+str(body))

        html = self.decodeBody(resHeaders,body)
        html = html.decode('utf-8')
        conn.close()
        #logger.debug("---html---\n" + str(html))

        if html.count(u'发布成功') > 0:
            carIdRe = re.search('\"home\",\"(?P<carId>.*)\"\);', html)
            carId = carIdRe.group('carId')
            cityName = self.city582.getName(cityCode)
            url = 'http://'+cityName+'.58.com/ershouche/'+carId+"x.shtml"
            return errorcode.SUCCESS, url
        #return (errorcode.LOGIC_ERROR, html)
        #TODO: 需要研究发车数量超过限制的返回信息
        if html.count(u'该条信息已经被发布过') > 0:
            return errorcode.SITE_ERROR, errormsg.VEHICLE_DUPLICATED
        if html.count(u'可免费发布的车源数量已用完') > 0:
            return errorcode.SITE_ERROR, u"可免费发布的车源数量已用完"
        return errorcode.SITE_ERROR, errormsg.SITE_OTHER_ERROR

    def postVehicle(self, carInfo, externalSpec, photoList, drivingLicensePicture):
        vehicle = carInfo.get("vehicle", None)
        merchant = vehicle.get('merchant', None)
        address = merchant.get('address', None)
        if address is None:
            #return False
            return errorcode.DATA_ERROR, errormsg.ADDRESS_EMPTY
        vehicle_date = vehicle.get('vehicle_date', None)
        if vehicle_date is None:
            return errorcode.DATA_ERROR, "缺少用户信息"
        cityCode = address.get('city_code', None)
        if cityCode is None:
            #return
            return errorcode.DATA_ERROR, errormsg.CITY_EMPTY
        code = self.city582.getCode(cityCode)

        username = carInfo.get('share_account').get("username")

        (url_code, html) = self.getPostPage(code)

        if html.count(u"您的账户已被冻结") >0:
            return errorcode.SITE_ERROR, u"您的账户已被冻结"

        #如果是免费小账号，走手机app发车通道[非vip，非付费小账号]
        #判断小账号是否要钱
        account_flag = 0.
        if html.count(u"发布本车源将花费")>0:
            account_flag = 1

        #TODO:需要到网页端确认?
        #if

        if (not url_code.startswith('v')) and (0 == account_flag):
            return self.postVehicleMobile(carInfo, externalSpec, photoList, code, cityCode)


        #如果是vip，付费小账号，走网页发车通道
        fcookieRe = re.search("\$\.c\.fk\.i\(\'(?P<fcookie>[0-9a-z\-]{36})\'\)", html)
        if fcookieRe is None:
            #return False
            return errorcode.LOGIC_ERROR, errormsg.PARAMETER_UNRESOLVED
        fcookie = fcookieRe.group("fcookie")
        #print fcookie
        logger.debug("fcookie=" + fcookie)
        bianhaoRe = re.search('\$\(\"#xinxibianhao\"\)\.val\(\'(?P<bianhao>.*)\'\);', html)
        bianhao = bianhaoRe.group('bianhao')
        # #print bianhao
        # logger.debug("bianhao=" + bianhao)
        # iqas_mcvalueRe = re.search("var iqas_mcvalue = \'(?P<mcvalue>[0-9]{13})\'", html)
        # if iqas_mcvalueRe is None:
        #     #return False
        #     return errorcode.LOGIC_ERROR, errormsg.PARAMETER_UNRESOLVED
        # iqas_mcvalue = iqas_mcvalueRe.group("mcvalue")
        # #print iqas_mcvalue
        # logger.debug("iqas_mcvalue=" + iqas_mcvalue)
        # iqas_mcformulaRe = re.search("var iqas_mcformula = \'(?P<mcformula>.*)\';", html)
        # if iqas_mcformulaRe is None:
        #     #return False
        #     return errorcode.LOGIC_ERROR, errormsg.PARAMETER_UNRESOLVED
        # iqas_mcformula = iqas_mcformulaRe.group("mcformula")
        # #print iqas_mcformula
        # logger.debug("iqas_mcformula=" + iqas_mcformula)
        # child = subprocess.Popen(["./app/jsfunc/eval.js"], stdin=subprocess.PIPE, stdout=subprocess.PIPE)
        # iqas_mcvalue = child.communicate(iqas_mcformula)[0]
        # #iqas_mcvalue = "0212634716904157147153110121"
        # #print iqas_mcvalue
        # logger.debug("iqas_mcvalue=" + iqas_mcvalue)
        conn = httplib.HTTPConnection("tracklog.58.com", timeout=timeout_58)
        headers = copy.copy(self.headers)
        headers['Host'] = 'tracklog.58.com'
        headers['Referer'] = 'http://post.58.com/' + url_code
        conn.request("GET", "/referrer4.js", headers=headers)
        res = conn.getresponse()
        resHeaders = res.getheaders()
        #print resHeaders
        logger.debug("resHeaders="+str(resHeaders))
        self.setCookies(resHeaders, encode=True)
        boundaryHeader = '----WebKitFormBoundarykvyRkkPjZTyZguCW'
        boundary = '--' + boundaryHeader
        formStr = ""
        vin = self.getVin(vehicle)
        if vin is not None:
            formStr += boundary + "\r\n" + vin
        formStr += boundary + "\r\n" + self.getZimu(externalSpec)
        formStr += boundary + "\r\n" + self.getSpecV('brand', externalSpec['brand']['spell'])
        formStr += boundary + "\r\n" + self.getSpecV('chexi', externalSpec['series']['key'])

        # if externalSpec['series'].get('object_type', None) is not None:
        #     if externalSpec['series']['object_type'].get("v", None) is not None:
        #         formStr += boundary + "\r\n" + self.getSpecV('ObjectType', externalSpec['series']['object_type']['v'])

        # 车辆类型
        object_type = '1'
        if externalSpec['series'].get('object_type', None) is not None:
            if externalSpec['series']['object_type'].get("v", None) is not None:
                object_type = externalSpec['series']['object_type']['v']
        formStr += boundary + "\r\n" + self.getSpecV('ObjectType', object_type)

        # 58有没有model的 key = 0
        if externalSpec['model']['key'] == '0':
            pass
        else:
            formStr += boundary + "\r\n" + self.getSpecV('carchexing', externalSpec['model']['key'])

            # edit by jesse on 2016-03-22, default displacment value
            displacementV = self.getDisplacementV(externalSpec, carInfo)
            if '' == displacementV:
                displacementV = '408957'
            formStr += boundary + "\r\n" + self.getSpecV('displacement', displacementV)


            formStr += boundary + "\r\n" + self.getSpecV('gearbox', externalSpec['summary']['gearbox']['v'])
            # formStr += boundary + "\r\n" + self.getSpecV('gearbox', self.getGearBoxT(externalSpec, carInfo))
            ##formStr += boundary + "\r\n" + self.getSpecV('kucheid', externalSpec['model']['kucheid']['v'])

            #Fixme：车型库升级兼容性:
            # edit by jesse on 2016-03-22, default displacment value
            #formStr += boundary + "\r\n" + self.getSpecV('shangshishijian', externalSpec['model']['shangshishijian']['v'])
            formStr += boundary + "\r\n" + self.getShangshishijian(externalSpec, 'v')
            #formStr += boundary + "\r\n" + self.getSpecV('yczb_cheling', externalSpec['summary']['yczb_cheling']['v'])
            formStr += boundary + "\r\n" + self.getYczb_cheling(externalSpec, 'v')
            #formStr += boundary + "\r\n" + self.getSpecV('yczb_licheng', externalSpec['summary']['yczb_licheng']['v'])
            formStr += boundary + "\r\n" + self.getYczb_licheng(externalSpec, 'v')
        try:
            formStr += boundary + "\r\n" + self.getSpecV('madein', externalSpec['vendor']['v'])
        except Exception as e:
            pass
        if externalSpec['series']['chexibieming'].get('v', None) is not None:
            formStr += boundary + "\r\n" + self.getChexibieming(externalSpec)
        formStr += boundary + "\r\n" + self.getErscpinpai(externalSpec)
        formStr += boundary + "\r\n" + self.getRundistanceqj(carInfo)
        formStr += boundary + "\r\n" + self.getChelingqj()
        formStr += boundary + "\r\n" + self.getBuytime(carInfo)
        formStr += boundary + "\r\n" + self.getShangpaiyuefen(vehicle_date) #上牌月份
        formStr += boundary + "\r\n" + self.getEmpty('buyfrom')
        #formStr += boundary + "\r\n" + self.getEmpty('baoyang')
        formStr += boundary + "\r\n" + self.getString('baoyang', '515673')
        formStr += boundary + "\r\n" + self.getEmpty('yunying')
        formStr += boundary + "\r\n" + self.getString('shiguqk', '515713')
        formStr += boundary + "\r\n" + self.getEmpty('neishi')
        formStr += boundary + "\r\n" + self.getEmpty('syxian')
        formStr += boundary + "\r\n" + self.getEmpty('shouxu')
        formStr += boundary + "\r\n" + self.getCheshenyanse(carInfo)
        #formStr += boundary + "\r\n" + self.getChexingyanse(carInfo)
        formStr += boundary + "\r\n" + self.getZbjcfanwei(carInfo)
        formStr += boundary + "\r\n" + self.getPic(photoList)
        formStr += boundary + "\r\n" + self.getPicTag(photoList)
        formStr += boundary + "\r\n" + self.getEmpty('picdesc1')
        formStr += boundary + "\r\n" + self.getEmpty('picdesc2')
        formStr += boundary + "\r\n" + self.getEmpty('picdesc3')
        formStr += boundary + "\r\n" + self.getEmpty('picdesc4')
        formStr += boundary + "\r\n" + self.getEmpty('picdesc5')
        formStr += boundary + "\r\n" + self.getEmpty('picdesc6')
        formStr += boundary + "\r\n" + self.getEmpty('picdesc7')
        formStr += boundary + "\r\n" + self.getEmpty('picdesc8')
        formStr += boundary + "\r\n" + self.getImageLoad()
        formStr += boundary + "\r\n" + self.getRundistance(carInfo)
        formStr += boundary + "\r\n" + self.getMinPrice(carInfo)
        formStr += boundary + "\r\n" + self.getMinPricej(carInfo)
        formStr += boundary + "\r\n" + self.getInstallment(carInfo)

        # 保障车源 - 消费保障等 - 发车
        merchantSubstituteConfig = carInfo.get("merchant_substitute_config", None)
        '''
        if merchantSubstituteConfig is not None:
            consumerGuarantee = self.getConsumerGuarantee(merchantSubstituteConfig)
            if consumerGuarantee is 1:
                formStr += boundary + "\r\n" + self.getDefault('mfghProxy','1')  #免费过户
                formStr += boundary + "\r\n" + self.getDefault('qtktProxy','1')  #7天可退
                formStr += boundary + "\r\n" + self.getDefault('qtkt','1')  #7天可退
        '''
        formStr += boundary + "\r\n" + self.getDefault('mfghProxy', '1')  #免费过户
        formStr += boundary + "\r\n" + self.getDefault('qtktProxy', '1')  #7天可退
        if self.is_integrity_merchant(vehicle, username):
            qtkt = '1'
        else:
            qtkt = '0'
        formStr += boundary + "\r\n" + self.getDefault('qtkt', qtkt)  #7天可退

        #标题
        formStr += boundary + "\r\n" + self.getTitle(externalSpec, carInfo, vehicle)
        formStr += boundary + "\r\n" + self.getContent(carInfo)

        formStr += boundary + "\r\n" + self.getGoblianxiren(carInfo)
        #formStr += boundary + "\r\n" + self.getFaburen()
        formStr += boundary + "\r\n" + self.getPhone(carInfo)
        formStr += boundary + "\r\n" + self.getIM(carInfo.get("merchant_substitute_config", {}))
        formStr += boundary + "\r\n" + self.getQitadianhua(carInfo.get("merchant_substitute_config", {}))
        formStr += boundary + "\r\n" + self.getCaraddress(merchantSubstituteConfig, vehicle.get("merchant", {}))
        formStr += boundary + "\r\n" + self.getType()
        if externalSpec['model']['key'] == '0':
            pass
        else:
            formStr += boundary + "\r\n" + self.getCspailiang(externalSpec, carInfo)
            formStr += boundary + "\r\n" + self.getBiansuqi(externalSpec, carInfo)
        formStr += boundary + "\r\n" + self.getEmpty('shigumiaoshu')
        # 各种时间yjy
        formStr += boundary + "\r\n" + self.getTypeDate('cjshijian', vehicle_date)
        formStr += boundary + "\r\n" + self.getTypeDate('qxshijian', vehicle_date)
        formStr += boundary + "\r\n" + self.getTypeDate('syshijian', vehicle_date)
        #add by yjy on 20150317 发车

        formStr += boundary + "\r\n" + self.getXinxibianhao(bianhao)
        formStr += boundary + "\r\n" + drivingLicensePicture
        formStr += boundary + "\r\n" + self.getYczhibao(externalSpec)
        formStr += boundary + "\r\n" + self.getDefault('xbsx', '1')

        #vinstate - 发车
        formStr += boundary + "\r\n" + self.getDefault('vinstate', '1')

        #免费过户
        formStr += boundary + "\r\n" + self.getIncludeTransferFee(vehicle, username)
        formStr += boundary + "\r\n" + self.getShangpainianyue(carInfo)
        formStr += boundary + "\r\n" + self.getCateapplyed()
        formStr += boundary + "\r\n" + self.getLocalapplyed(code)
        formStr += boundary + "\r\n" + self.getShifoufufeifabu()
        formStr += boundary + "\r\n" + self.getShifouyishou()
        formStr += boundary + "\r\n" + self.getEscwltv2()
        formStr += boundary + "\r\n" + self.getPaifangbiaozhun()
        formStr += boundary + "\r\n" + self.getWanglintongbieming()
        formStr += boundary + "\r\n" + self.getCanjiapaimai()
        formStr += boundary + "\r\n" + self.getIqasMcresult("")
        formStr += boundary + "\r\n" + self.getCubePostJsonkey()
        formStr += boundary + "\r\n" + self.getHiddenForPara()
        formStr += boundary + "\r\n" + self.getGobquzhi(externalSpec, carInfo, code)
        formStr += boundary + "\r\n" + self.getGobalsokey(externalSpec, carInfo, code)
        formStr += boundary + "\r\n" + self.getFcookie(fcookie)
        #条框增加地址
        formStr += boundary + "\r\n" + self.getHiddenTextBoxJoinValue(externalSpec, carInfo, vehicle)

        formStr += boundary + "\r\n" + self.getXiaobaoOption()
        formStr += boundary + "--"
        if type(formStr == type(u'')):
            formStr = formStr.encode('utf-8')
        #print formStr
        #logger.debug("formStr=" + str(formStr))
        conn = httplib.HTTPConnection("post.58.com", timeout=timeout_58)
        headers = copy.copy(self.headers)
        headers['Host'] = 'post.58.com'
        headers['Referer'] = 'http://post.58.com/' + url_code + '/29/s5/'
        headers['Content-Type'] = 'multipart/form-data; boundary=' + boundaryHeader
        headers['Content-Length'] = len(formStr)
        headers['Host'] = 'post.58.com'
        headers['Origin'] = 'http://post.58.com'
        postUrl = "/" + url_code + "/29/s5/submit?source=car&rand="+str(random.random())

        conn.request("POST", postUrl, formStr, headers=headers)
        res = conn.getresponse()
        #print json.dumps(headers)
        #print url_code
        print res.status, res.reason
        logger.debug("headers="+json.dumps(headers))
        resHeaders = res.getheaders()
        self.setCookies(resHeaders, encode=True)
        #print resHeaders
        logger.debug("****************************")
        logger.debug("status: "+str(res.status))
        logger.debug("reason: "+str(res.reason))
        logger.debug("resHeaders=" + str(resHeaders))
        logger.debug("****************************")

        content = res.read()
        html = self.decodeBody(resHeaders, content)
        #zlib.decompress(res.read(), 16+zlib.MAX_WBITS)
        html = html.decode('utf-8')
        conn.close()
        #print "---html---"
        #print html
        logger.debug("---html---\n" + html)

        #免费时的发车
        if html.count('c.user.loginsuccess_callback') > 0:
            return self.postVehicleMobile(carInfo, carInfo, externalSpec, photoList, code, cityCode)

        if html.count(u'您的电话已被冻结') > 0:
            return errorcode.SITE_ERROR, u'您的电话已被冻结'

        '''
        if html.count('postsuccess') == 0:
            return errorcode.SITE_ERROR, errormsg.SITE_OTHER_ERROR
        '''

        # 如果检测是否有跳转
        # if html.count('location.href') > 0:
        #     jumpLocationRe = re.search("location.href = \'(?P<href>.*)\'", html)
        #     locationHref = jumpLocationRe.group('href')
        #     conn = httplib.HTTPConnection("post.58.com", timeout=10)

        #conn = None
        #postsuccess = ""
        headers = copy.copy(self.headers)
        #if not url_code.startswith('v'):

        #same
        '''
        <script type="text/javascript">top.location.href = '/postsuccess/0/20702417573130/?source=car&postsms=&callsms=0&score=75&phone=&divert=0&call58bb=&tuiguang_option=&paysuccess=true';</script>
        '''
        postsuccessRe = re.search('top\.location\.href = \'(?P<postsuccess>.*)\';', html)
        if postsuccessRe is not None:
            postsuccess = postsuccessRe.group('postsuccess')
            carIdRe = re.search('0/(?P<carId>.*)/\?', postsuccess)
            carId = carIdRe.group('carId')
            logger.debug("postsuccess = " + postsuccess)
            conn = httplib.HTTPConnection("post.58.com", timeout=timeout_58)
            headers['Host'] = 'post.58.com'
            headers['Referer'] = 'http://post.58.com/' + url_code + '/29/s5'
        else:
            postsuccessRe = re.search('vip_postsuccess\((?P<postsuccessJson>.*)\)<', html)
            if postsuccessRe is not None:
                postsuccessJson = postsuccessRe.group('postsuccessJson')
                logger.debug("postsuccessJson=" + postsuccessJson)
                postsuccessObj = json.loads(postsuccessJson)
                carId = postsuccessObj['infoid']
                jz_key = postsuccessObj['jz_key']
                postsuccess = "/cheyuanreceiver?infoid=%s&type=1&jzKey=%s&money=0.0&infoState=1"%(carId, jz_key)
                conn = httplib.HTTPConnection("info.vip.58.com", timeout=timeout_58)
                headers['Referer'] = 'http://info.vip.58.com/postcheyuan/?masteriframe=true&displocalid=%s&dispcateid=29&r=0.4967958819988352'%code
            else:
                postsuccessRe = re.search('postsuccess/'+url_code+"/(?P<carId>.*)/\?", html)
                if postsuccessRe is not None:
                #if html.count("postsuccess/" + url_code + "/") > 0:
                    #logger.debug("postsuccess without url return")
                    #print html
                    carId = postsuccessRe.group('carId')
                    cityName = self.city582.getName(cityCode)
                    url = 'http://'+cityName+'.58.com/ershouche/'+carId+"x.shtml"
                    logger.debug("---url---\n" + url)
                    return errorcode.SUCCESS, url
                else:
                    postsuccessRe = re.search('parent\.location\.href = \'(?P<postsuccess>.*)\';', html)
                    if postsuccessRe is not None:
                        postsuccess = postsuccessRe.group('postsuccess')
                        #get html from postSuccessUrl
                        conn = httplib.HTTPConnection("post.58.com", timeout=timeout_58)
                        headers['Host'] = 'post.58.com'
                        headers['Referer'] = 'http://post.58.com/' + url_code + '/29/s5'
                        carId = None
                    else:
                        return errorcode.SITE_ERROR, "url跳转错误"
        conn.request("GET", postsuccess, headers=headers)

        res = conn.getresponse()
        #print json.dumps(headers)
        logger.debug("headers=" + json.dumps(headers))
        resHeaders = res.getheaders()
        #print resHeaders
        logger.debug("resHeaders=" + str(resHeaders))
        html = zlib.decompress(res.read(), 16+zlib.MAX_WBITS)
        #html = res.read()
        html = html.decode('utf-8')
        #print "---------html---------"
        #print html
        logger.debug("---html---\n" + html)
        cityName = self.city582.getName(cityCode)
        if carId is None:
            carIdRe = re.search('ershouche\/(?P<carId>.*)x.shtml', html)
            carId = carIdRe.group('carId')
        url = 'http://'+cityName+'.58.com/ershouche/'+carId+"x.shtml"
        #print "---url---"
        #print url
        logger.debug("---url---\n" + url)
        return errorcode.SUCCESS, url

    @staticmethod
    def getZimu(specDetail):
        code =  zimu.getZimuCode(specDetail['brand']['name'])
        return 'Content-Disposition: form-data; name="zimu"\r\n\r\n' + str(code) + '\r\n'

    @staticmethod
    def getVin(vehicle):
        vin = vehicle.get("vin", None)
        if vin  is None:
            return None
        return 'Content-Disposition: form-data; name="vin"\r\n\r\n' + str(vin) + '\r\n'

    @staticmethod
    def getSpecV(name, v):
        #v =  specDetail[vname]
        return 'Content-Disposition: form-data; name="' + name + '"\r\n\r\n' + str(v) + '\r\n'

    @staticmethod
    def getYczb_cheling(externalSpec, type):
        mValue = ""
        summary = externalSpec.get('summary', None)
        yczb_cheling = summary.get('yczb_cheling', None)
        if yczb_cheling is not None:
            mValue = yczb_cheling.get(type, "")
        if mValue is None:
            mValue = ""
        if 't' == type:
            return mValue
        else:
            return 'Content-Disposition: form-data; name=yczb_cheling' + '\r\n\r\n' + str(mValue) + '\r\n'

    @staticmethod
    def getYczb_licheng(externalSpec, type):
        mValue = ""
        summary = externalSpec.get('summary', None)
        yczb_licheng = summary.get('yczb_licheng', None)
        if yczb_licheng is not None:
            mValue = yczb_licheng.get(type, "")
        if mValue is None:
            mValue = ""
        if 't' == type:
            return mValue
        else:
            return 'Content-Disposition: form-data; name=yczb_licheng' + '\r\n\r\n' + str(mValue) + '\r\n'

    @staticmethod
    def getShangshishijian(externalSpec, type):
        default_mValue = '681443'
        mValue = default_mValue
        model = externalSpec.get('model', None)
        shangshishijian = model.get('shangshishijian', None)
        if shangshishijian is not None:
            mValue = shangshishijian.get(type, default_mValue)
        if mValue is None or '' == mValue:
            mValue = default_mValue
        if 't' == type:
            return mValue
        else:
            return 'Content-Disposition: form-data; name="shangshishijian"' + '\r\n\r\n' + str(mValue) + '\r\n'


    @staticmethod
    def getChexibieming(externalSpec):
        return 'Content-Disposition: form-data; name="chexibieming"\r\n\r\n' + externalSpec['series']['chexibieming']['v'] + '\r\n'

    @staticmethod
    def getErscpinpai(externalSpec):
        #print specDetail['brandt']
        #print specDetail['seriest']
        erscpinpai = (externalSpec['brand']['name'] + externalSpec['series']['name'])
        return 'Content-Disposition: form-data; name="erscpinpai"\r\n\r\n' + erscpinpai.encode('utf-8') + '\r\n'

    def getRundistanceqj(self, carInfo):
        rundistanceqj = self.getMileAgeRangeDigit(carInfo)
        return 'Content-Disposition: form-data; name="rundistanceqj"\r\n\r\n' + rundistanceqj + '\r\n'

    @staticmethod
    def getChelingqj():
        chelingqj = "2008_2010"
        return 'Content-Disposition: form-data; name="chelingqj"\r\n\r\n' + chelingqj + '\r\n'
    
    def getBuytime(self, carInfo):
        buytime = str(self.getDate(carInfo).year)
        return 'Content-Disposition: form-data; name="buytime"\r\n\r\n' + buytime + '\r\n'

    @staticmethod
    def getShangpaiyuefen(vehicle_date):
        registration_date = vehicle_date.get('registration_date', None)
        registration_date = registration_date.astimezone(tz.HKT)
        month = registration_date.month

        cardinal = 515681
        shangpaiyuefen = str(cardinal + int(month) - 1)

        #shangpaiyuefen = str(month)
        return 'Content-Disposition: form-data; name="shangpaiyuefen"\r\n\r\n' + shangpaiyuefen + '\r\n'

    @staticmethod
    def getEmpty(name):
        return 'Content-Disposition: form-data; name="' + name + '"\r\n\r\n' + "" + '\r\n'

    @staticmethod
    def getDefault(name, value):
        return 'Content-Disposition: form-data; name="' + name + '"\r\n\r\n' + value + '\r\n'


    @staticmethod
    def getString(name, value):
        return 'Content-Disposition: form-data; name="' + name + '"\r\n\r\n' + value + '\r\n'

    @staticmethod
    def getTypeDate(name, vehicle_date):
        '''
        cjshijian   2016|1
        qxshijian   2016|1
        syshijian   2016|1
        '''
        typeDict = {
            "cjshijian": "compulsory_insurance_expire_date",
            #cjshijian暂不知什么意义
            "qxshijian": "compulsory_insurance_expire_date",
            "syshijian": "commercial_insurance_expire_date",
            "inspection": "inspection_date"
        }
        value = ""
        date = vehicle_date.get(typeDict[name], None)
        if date is None:
            date = vehicle_date.get(typeDict["inspection"], None)
            year = date.year
            month = date.month
            if name == 'syshijian' and year < 2017:
                year = 2016
                month = 12
            value = (str(year) + "|" + str(month)).encode('utf-8')
        else:
            date = date.astimezone(tz.HKT)
            year = date.year
            month = date.month
            if name == 'syshijian' and year < 2017:
                year = 2016
                month = 12
            value = (str(year) + "|" + str(month)).encode('utf-8')
        return 'Content-Disposition: form-data; name="' + name + '"\r\n\r\n' + value + '\r\n'

    @staticmethod
    def getColorChinese(carInfo):
        colorTable = {"black": "黑色", "white": "白色", "silver":"银色", "grey":"灰色", 
            "brown":"棕色", "red":"红色", "blue":"蓝色", "green":"绿色", "yellow": "黄色", 
            "orange": "橙色", "purple": "紫色", "champagne":"金色", "multi":"其它", "other": "其它"}
        res = "黑色"
        vehicle = carInfo.get("vehicle", None)
        if vehicle is not None:
            summary = vehicle.get("summary", None)
            if summary is not None:
                color = summary.get("color", None)
                res = colorTable.get(color, "黑色")
        return res

    @staticmethod
    def getCheshenyanseVal(carInfo):

        colorTable = {"black": "1", "white": "2", "silver":"3", "grey":"4", 
            "brown":"11", "red":"6", "blue":"7", "green":"8", "yellow": "9", 
            "orange": "10", "purple": "12", "champagne":"13", "multi":"14", "other": "14"}
        '''
        colorTable = {"black": "黑色", "white": "白色", "silver":"银色", "grey":"灰色",
                      "brown":"棕色", "red":"红色", "blue":"蓝色", "green":"绿色", "yellow": "黄色",
                      "orange": "橙色", "purple": "紫色", "champagne":"金色", "multi":"其它", "other": "其它"}
        '''
        cheshencode = "1"
        vehicle = carInfo.get("vehicle", None)
        if vehicle is not None:
            summary = vehicle.get("summary", None)
            if summary is not None:
                color = summary.get("color", None)
                cheshencode = colorTable.get(color, "1")
        return cheshencode

    def getZbjcfanwei(self, carInfo):
        return 'Content-Disposition: form-data; name="zbjcfanwei"\r\n\r\n' + "524249" + '\r\n'

    def getChexingyanse(self, carInfo):
        return 'Content-Disposition: form-data; name="chexingyanse"\r\n\r\n' + "515986" + '\r\n'

    def getCheshenyanse(self, carInfo):
        cheshenyanse = self.getCheshenyanseVal(carInfo)
        return 'Content-Disposition: form-data; name="cheshenyanse"\r\n\r\n' + cheshenyanse + '\r\n'

    @staticmethod
    def getPicVal(photoList):
        photos = []
        for photo in photoList[:16]:
            if type(photo) != type(u'') and type(photo) != type(''):
                #print type(photo)
                #print photo
                logger.debug(str(photo))
                continue
            photos.append("/p1/big/" + photo.encode('utf-8'))
        photos = "|".join(photos)
        return photos

    @staticmethod
    def bashgetPicValMobile(photoList):
        photos = []
        for photo in photoList[:16]:
            if type(photo) != type(u'') and type(photo) != type(''):
                #print type(photo)
                #print photo
                logger.debug(str(photo))
                continue
            #photos.append("/mobile/big/" + photo.encode('utf-8'))
            photos.append("/p1/big/".encode("utf-8") + photo.encode('utf-8'))

        photos = "|".join(photos)
        #photos = photos.replace("/","%2F")
        return photos

    def getPic(self, photoList):
        photos = self.getPicVal(photoList)
        return 'Content-Disposition: form-data; name="pic"\r\n\r\n' + photos + '\r\n'

    @staticmethod
    def getPicTag(photoList):
        photos = []
        for photo in photoList:
            #print type(photo)
            photos.append('')
        photos = "|".join(photos)
        #print photos
        return 'Content-Disposition: form-data; name="pictag"\r\n\r\n' + photos + '\r\n'

    @staticmethod
    def getImageLoad():
        return 'Content-Disposition: form-data; name="imageLoad"; filename=""' + '\r\n' + 'Content-Type: application/octet-stream\r\n\r\n' + '' + '\r\n'

    @staticmethod
    def getMileAgeData(carInfo):
        mileage = 1
        vehicle = carInfo.get("vehicle", None)
        if vehicle is not None:
            summary = vehicle.get("summary", None)
            if summary is not None:
                mileage = summary.get("mileage", None)
                if mileage is None:
                    mileage = 1
                else:
                    mileage /= 10000
        return mileage

    @staticmethod
    def getMileAgeRange(carInfo):
        mileage = 1
        vehicle = carInfo.get("vehicle", None)
        if vehicle is not None:
            summary = vehicle.get("summary", None)
            if summary is not None:
                mileage = summary.get("mileage", None)
                if mileage is None:
                    mileage = 1
                else:
                    mileage /= 10000

        if mileage < 1:
            return '1万公里内'
        elif 1 <= mileage < 3:
            return "1-3万公里"
        elif 3 <= mileage < 5:
            return "3-5万公里"
        elif 5 <= mileage < 8:
            return "5-8万公里"
        elif 8 <= mileage < 12:
            return "8-12万公里"
        elif 12 <= mileage < 18:
            return "12-18万公里"
        else:
            return '18万公里以上'

    @staticmethod
    def getMileAgeRangeDigit(carInfo):
        mileage = 1
        vehicle = carInfo.get("vehicle", None)
        if vehicle is not None:
            summary = vehicle.get("summary", None)
            if summary is not None:
                mileage = summary.get("mileage", None)
                if mileage is None:
                    mileage = 1
                else:
                    mileage /= 10000

        if mileage < 1:
            return '0_1'
        elif 1 <= mileage < 3:
            return "1_3"
        elif 3 <= mileage < 5:
            return "3_5"
        elif 5 <= mileage < 8:
            return "5_8"
        elif 8 <= mileage < 12:
            return "8_12"
        elif 12 <= mileage < 18:
            return "12_18"
        else:
            return '18_999999'

    @staticmethod
    def getRundistanceVal(carInfo):
        rundistance = '1'
        vehicle = carInfo.get("vehicle", None)
        if vehicle is not None:
            summary = vehicle.get("summary", None)
            if summary is not None:
                mileage = summary.get("mileage", None)
                if mileage is not None:
                    rundistance = str(Decimal(mileage) / Decimal(10000))
        return rundistance

    def getRundistance(self, carInfo):
        rundistance = self.getRundistanceVal(carInfo)
        return 'Content-Disposition: form-data; name="rundistance"\r\n\r\n' + rundistance + '\r\n'

    @staticmethod
    def getPriceData(carInfo):
        price = 1
        vehicle = carInfo.get("vehicle", None)
        if vehicle is not None:
            price = vehicle.get("price", None)
            if price is not None:
                quotedPrice = price.get("quoted_price", None)
                if quotedPrice is not None:
                    quotedPrice = int(round(Decimal(quotedPrice) / 100) * 100)
                    price = Decimal(quotedPrice) / Decimal(10000)
        return price

    @staticmethod
    def getMinProceVal(carInfo):
        minprice = '1'
        vehicle = carInfo.get("vehicle", None)
        if vehicle is not None:
            price = vehicle.get("price", None)
            if price is not None:
                quotedPrice = price.get("quoted_price", None)
                if quotedPrice is not None:
                    quotedPrice = int(round(Decimal(quotedPrice) / 100) * 100)
                    minprice = str(Decimal(quotedPrice) / Decimal(10000))
        return minprice

    def getMinPrice(self, carInfo):
        minprice = self.getMinProceVal(carInfo)
        return 'Content-Disposition: form-data; name="MinPrice"\r\n\r\n' + minprice + '\r\n'

    # 保障车源 - 消费保障等
    def getConsumerGuarantee(self, merchantSubstituteConfig):
        consumerGuarantee = merchantSubstituteConfig.get('summary', {}).get('consumer_guarantee', None)
        result = ''
        if consumerGuarantee is None:
            result = 0
        elif consumerGuarantee is True:
            result = 1
        else:
            result = 0
        return result

    # 默认分期
    def getInstallment(self, carInfo):
        return 'Content-Disposition: form-data; name="installment"\r\n\r\n' + '678611' + '\r\n'

    def getYearRange(self, carInfo):
        d = self.getDate(carInfo)
        yearDiff = 2014 - d.year
        yearRange = "1年以内"
        if yearDiff < 1:
            yearRange = "1年以内"
        elif 1 <= yearDiff < 3:
            yearRange = "1-3年"
        elif 3 <= yearDiff < 5:
            yearRange = "3-5年"
        elif 3 <= yearDiff < 5:
            yearRange = "5-8年"
        elif 8 <= yearDiff < 10:
            yearRange = "8-10年"
        elif yearDiff >= 10:
            yearRange = "10年以上"
        return yearRange

    @staticmethod
    def getDate(carInfo):
        d = IsoDate.from_iso_string('2014-06-01T00:00:00.000+08:00')
        vehicle = carInfo.get("vehicle", None)
        if vehicle is not None:
            vehicleDate = vehicle.get('vehicle_date', None)
            if vehicleDate is not None:
                registrationDate = vehicleDate.get('registration_date', None)
                if registrationDate is not None:
                    d = registrationDate.astimezone(tz.HKT)
        return d

    @staticmethod
    def getPriceRange(carInfo):
        minpricej = '0-1万'
        vehicle = carInfo.get("vehicle", None)
        if vehicle is not None:
            price = vehicle.get("price", None)
            if price is not None:
                quotedPrice = price.get("quoted_price", None)
                if quotedPrice is not None:
                    quotedPrice = int(round(Decimal(quotedPrice) / 100) * 100)
                    minprice = quotedPrice / 10000.
                    if minprice < 1:
                        minpricej = "0-1万"
                    elif 1 <= minprice < 2:
                        minpricej = "1-2万"
                    elif 2 <= minprice < 3:
                        minpricej = "2-3万"
                    elif 3 <= minprice < 5:
                        minpricej = "3-5万"
                    elif 5 <= minprice < 8:
                        minpricej = "5-8万"
                    elif 8 <= minprice < 12:
                        minpricej = "8-12万"
                    elif 12 <= minprice < 18:
                        minpricej = "12-18万"
                    elif 18 <= minprice < 24:
                        minpricej = "18-24万"
                    elif 24 <= minprice < 40:
                        minpricej = "24-40万"
                    elif minprice >= 40:
                        minpricej = "40万以上"
        return minpricej

    @staticmethod
    def getMinPricej(carInfo):
        minpricej = '0_1'
        vehicle = carInfo.get("vehicle", None)
        if vehicle is not None:
            price = vehicle.get("price", None)
            if price is not None:
                quotedPrice = price.get("quoted_price", None)
                if quotedPrice is not None:
                    quotedPrice = int(round(Decimal(quotedPrice) / 100) * 100)
                    minprice = quotedPrice / 10000.
                    if minprice < 1:
                        minpricej = "0_1"
                    elif 1 <= minprice < 2:
                        minpricej = "1_2"
                    elif 2 <= minprice < 3:
                        minpricej = "2_3"
                    elif 3 <= minprice < 5:
                        minpricej = "3_5"
                    elif 5 <= minprice < 8:
                        minpricej = "5_8"
                    elif 8 <= minprice < 12:
                        minpricej = "8_12"
                    elif 12 <= minprice < 18:
                        minpricej = "12_18"
                    elif 18 <= minprice < 24:
                        minpricej = "18_24"
                    elif 24 <= minprice < 40:
                        minpricej = "24_40"
                    elif minprice >= 40:
                        minpricej = "40_999999"
        return 'Content-Disposition: form-data; name="MinPriceqj"\r\n\r\n' + minpricej + '\r\n'

    @staticmethod
    def getDescBriefValue(carInfo):
        default = u"车况非常好"
        vehicle = carInfo.get('vehicle', None)
        if vehicle is None:
            return default
        desc = vehicle.get('desc', None)
        if desc is None:
            return default
        brief = desc.get('brief', '')
        if brief is None:
            return default
        return brief

    def getTitleVal(self, externalSpec, carInfo, vehicle):
        promotionWords = self.promotionWords(vehicle, False)
        title = ''
        if externalSpec['model']['key'] == '0':
            vehicleSpec = carInfo['vehicle']['spec']
            title = (externalSpec['brand']['name'] + externalSpec['series']['name'] + u' ' + vehicleSpec['sale_name'] + u' ' + vehicleSpec['year_group'])
        else:
            title = (externalSpec['brand']['name'] + externalSpec['series']['name'] + u' ' + externalSpec['model']['name'])
        return title + promotionWords

    def getTitle(self, externalSpec, carInfo, vehicle):
        title = self.getTitleVal(externalSpec, carInfo, vehicle)
        return 'Content-Disposition: form-data; name="Title"\r\n\r\n' + title.encode('utf-8') + '\r\n'

    def getContent(self, shareJob):
        Symbol = "\n"
        lateral = "——"*0
        if self.loanable(vehicle=shareJob.get('vehicle')):
            content = self.getContentVal_finance_58(shareJob, Symbol, lateral)
        else:
            content = self.getContentVal(shareJob, Symbol, lateral)

        return 'Content-Disposition: form-data; name="Content"\r\n\r\n' + content.encode('utf-8') + '\r\n'

    def getGoblianxirenVal(self, carInfo):
        (contact, _) = self.getContact(carInfo)
        return contact

    def getGoblianxiren(self, carInfo):
        contact = self.getGoblianxirenVal(carInfo)
        return 'Content-Disposition: form-data; name="goblianxiren"\r\n\r\n' + contact.encode('utf-8') + '\r\n'

    @staticmethod
    def getFaburen():
        return 'Content-Disposition: form-data; name="faburen"\r\n\r\n' + '0' + '\r\n'

    def getPhoneVal(self, carInfo):
        #phone = u'13800000000'
        #vehicle = carInfo.get('vehicle', None)
        #user = vehicle.get('user', None)
        #if user is not None:
        #    mobile = user.get('mobile', None)
        #    if mobile is not None:
        #        phone = mobile
        #return phone
        (username, mobile) = self.getContact(carInfo)
        return mobile

    def getIMVal(self, merchantSubstituteConfig):
       social = merchantSubstituteConfig.get("social", {})
       qq = social.get("qq", '')
       return qq

    def getQitadianhuaVal(self, merchantSubstituteConfig):
        extraContact = merchantSubstituteConfig.get("extra_contact", {})
        phone = extraContact.get("phone", '')
        if phone is None:
            phone = ''
        return phone

    def getCaraddressVal(self, merchantSubstituteConfig, merchant):
        merchantDisable = True
        if merchantSubstituteConfig is not None:
            description_switch = merchantSubstituteConfig.get('description_switch', None)
            if description_switch is not None:
                merchantDisable = description_switch.get('merchant_disable', None)
                if merchantDisable is None:
                    merchantDisable = True
        address = merchant.get("address", {})
        if merchantDisable is False:
            detail = address.get("detail", '')
            return detail
        else:
            province_name = address.get('province_name', '')
            city_name = address.get('city_name', '')
            return province_name.encode('utf-8') + city_name.encode('utf-8')

    def getPhone(self, carInfo):
        phone = self.getPhoneVal(carInfo)
        return 'Content-Disposition: form-data; name="Phone"\r\n\r\n' + phone.encode('utf-8') + '\r\n'

    def getIM(self, merchantSubstituteConfig):
        im = self.getIMVal(merchantSubstituteConfig)
        if im is None:
            im = ""
        else:
            im = str(im)
        return 'Content-Disposition: form-data; name="IM"\r\n\r\n' + im.encode('utf-8') + '\r\n'

    def getQitadianhua(self, merchantSubstituteConfig):
        phone = self.getQitadianhuaVal(merchantSubstituteConfig)
        if {} == phone:
            phone = ""
        else:
            phone = str(phone)
        return 'Content-Disposition: form-data; name="qitadianhua"\r\n\r\n' + phone.encode('utf-8') + '\r\n'

    def getCaraddress(self, merchantSubstituteConfig, merchant):
        address = self.getCaraddressVal(merchantSubstituteConfig, merchant)
        if {} == address:
            address = ""
        return 'Content-Disposition: form-data; name="caraddress"\r\n\r\n' + address + '\r\n'

    @staticmethod
    def getType():
        return 'Content-Disposition: form-data; name="type"\r\n\r\n' + '0' + '\r\n'

    def getGearBoxT(self, externalSpec, carInfo):
        local_gearboxt = carInfo['vehicle_spec_detail']['details'][42]
        gearboxt = ''
        try:
            gearboxt = externalSpec['summary']['gearbox']['t']
            if gearboxt is None:
                gearboxt = local_gearboxt
        except Exception as e:
            gearboxt = local_gearboxt
        if gearboxt != u'手动':
            gearboxt = u'自动'
        return gearboxt

    def getGearBoxV(self, externalSpec, carInfo):
        gearboxv= u''
        try:
            gearboxv = externalSpec['summary']['gearbox']['t']
            if gearboxv is None:
                gearboxv = u''
        except Exception as e:
            gearboxDict = {
                u"自动": "408822",
                u"手动": "408815"
            }
            gearboxt = self.getGearboxT(externalSpec, carInfo)
            gearboxv = u'自动'
            if gearboxt == u'手动':
                gearboxv = gearboxDict[u'手动']
            else:
                gearboxv = gearboxDict[u'自动']

        return gearboxv


    def getDisplacementT(self, externalSpec, carInfo):
        local_displacementt = carInfo['vehicle_spec_detail']['details'][23]
        try:
            displacementt = externalSpec['summary']['displacement']['t']
            if displacementt is None:
                displacementt = local_displacementt
        except Exception as e:
            displacementt = local_displacementt
        return displacementt

    def getDisplacementV(self, externalSpec, carInfo):
        '''edit by jesse on 2016-03-01'''
        local_displacementt = carInfo['vehicle_spec_detail']['details'][23]
        try:
            displacementV = externalSpec['summary']['displacement']['v']
            if displacementV is None:
                displacementV = local_displacementt
        except Exception as e:
            displacementV = local_displacementt
        return displacementV

        # '''
        # 修改 by jesse on 2015-7-15 22:42
        # '''
        # displacementT = self.getDisplacementT(externalSpec, carInfo)
        # return displacementT
        '''
        if externalSpec['summary'].get('displacement', None) is not None:
            if externalSpec['summary']['displacement'].get('v', None) is not None:
               return externalSpec['summary']['displacement']['v']

        displacementT = self.getDisplacementT(externalSpec, carInfo)
        with open("./data/58displacementTV.json", "r") as f:
            d = json.load(f)
            if d.has_key(displacementT):
                return d[displacementT]
            else:
                logger.debug('get distplacement V error!')
                return ''
        return ''
        '''

    def getCspailiang(self, externalSpec, carInfo):
        #local_displacementt = carInfo['vehicle_spec_detail']['details'][23]
        #try:
        #    displacementt = externalSpec['summary']['displacement']['t']
        #except Exception as e:
        #    displacementt = local_displacementt
        displacementt = self.getDisplacementT(externalSpec, carInfo)
        return 'Content-Disposition: form-data; name="cspailiang"\r\n\r\n' + str(displacementt) + '\r\n'

    @staticmethod
    def getBiansuqi(externalSpec, carInfo):
        local_gearboxt = carInfo['vehicle_spec_detail']['details'][42]
        summary = externalSpec.get('summary', None)
        if summary is None:
            gearboxt = local_gearboxt
        else:
            gearbox = summary.get('summary', None)
            if gearbox is None:
                gearboxt = local_gearboxt
            else:
                gearboxt = gearbox.get('t', None)
        if gearboxt is None:
            gearboxt = local_gearboxt
        return 'Content-Disposition: form-data; name="biansuqi"\r\n\r\n' + str(gearboxt) + '\r\n'

    @staticmethod
    def getXinxibianhao(bianhao):
        return 'Content-Disposition: form-data; name="xinxibianhao"\r\n\r\n' + bianhao.encode('utf-8') + '\r\n'

    @staticmethod
    def getYczhibao(externalSpec):
        #yczhibao = externalSpec['summary']['yczb_licheng']['v']
        yczhibao = '525379'
        return 'Content-Disposition: form-data; name="yczhibao"\r\n\r\n' + str(yczhibao) + '\r\n'

    # 免费过户
    def getIncludeTransferFee(self, vehicle, username):
        # transferFee = vehicle.get("price").get("quoted_price_include_transfer_fee", None)
        if self.is_integrity_merchant(vehicle, username):
            transferFeeString = 1  # 包过户
        else:
            transferFeeString = 0
        return 'Content-Disposition: form-data; name="mianfeiguohu"\r\n\r\n' + str(transferFeeString) + '\r\n'


    @staticmethod
    def getShangpainianyue(carInfo):
        shangpainianyue = "201006"
        vehicle_date = carInfo['vehicle']['vehicle_date']
        registration_date = vehicle_date.get("registration_date", None).astimezone(tz.HKT)
        if registration_date is not None:
            shangpainianyue = "%d%2.2d"%(registration_date.year, registration_date.month)
        return 'Content-Disposition: form-data; name="shangpainianyue"\r\n\r\n' + shangpainianyue.encode('utf-8') + '\r\n'

    @staticmethod
    def getCateapplyed():
        return 'Content-Disposition: form-data; name="cateapplyed"\r\n\r\n' + '29' + '\r\n'

    @staticmethod
    def getLocalapplyed(code):
        return 'Content-Disposition: form-data; name="localapplyed"\r\n\r\n' + str(code) + '\r\n'

    @staticmethod
    def getShifoufufeifabu():
        return 'Content-Disposition: form-data; name="shifoufufeifabu"\r\n\r\n' + '0' + '\r\n'

    @staticmethod
    def getShifouyishou():
        return 'Content-Disposition: form-data; name="shifouyishou"\r\n\r\n' + '0' + '\r\n'

    @staticmethod
    def getEscwltv2():
        return 'Content-Disposition: form-data; name="escwltv2"\r\n\r\n' + '0' + '\r\n'

    @staticmethod
    def getPaifangbiaozhun():
        return 'Content-Disposition: form-data; name="paifangbiaozhun"\r\n\r\n' + '408' + '\r\n'

    @staticmethod
    def getWanglintongbieming():
        return 'Content-Disposition: form-data; name="wanglintongbieming"\r\n\r\n' + '北京看看车科技有限公司' + '\r\n'

    @staticmethod
    def getCanjiapaimai():
        return 'Content-Disposition: form-data; name="canjiapaimai"\r\n\r\n' + '0' + '\r\n'

    @staticmethod
    def getIqasMcresult(iqas_mcresult):
        return 'Content-Disposition: form-data; name="iqas_mcresult"\r\n\r\n' + str(iqas_mcresult).strip() + '\r\n'

    @staticmethod
    def getCubePostJsonkey():
        #cube_post_jsonkey = '{"jzJson":null,"znJson":null,"zdJson":null,"jzFee":"0","znFee":"0","zdFee":"0","jzCop":"0","znCop":"0","zdCop":"0","sourceId":"1501","productId":"100002","showZd":1,"showZn":0,"showCpt":0,"showCpc":0}'
        cube_post_jsonkey = '{"jzJson":null,"znJson":null,"zdJson":null,"jzFee":"0","znFee":"0","zdFee":"0","jzCop":"0","znCop":"0","zdCop":"0","sourceId":"1507","productId":"100002","secondCateId":"29","dispSecondCateId":"29","cityId":"1","dispCityId":"1","showZd":1,"showZn":1,"showCpt":0,"showCpc":1}'
        return 'Content-Disposition: form-data; name="cube_post_jsonkey"\r\n\r\n' + str(cube_post_jsonkey) + '\r\n'

    @staticmethod
    def getHiddenForPara():
        #HiddenForPara = '5863:zimu|5866:brand|5867:chexi|2539:ObjectType|5868:carchexing|5871:displacement|5872:gearbox|5880:kucheid|6809:shangshishijian|7068:yczb_cheling|7069:yczb_licheng|5870:madein|6808:chexibieming|5865:rundistanceqj|5883:chelingqj|1196:buytime|6860:shangpaiyuefen|6852:buyfrom|6855:baoyang|6853:yunying|4922:shiguqk|6856:chengse|6857:neishi|6866:neishiquexian|6869:syxian|6859:shouxu|4917:cheshenyanse|5864:MinPriceqj'
        #HiddenForPara = '5863:zimu|5866:brand|5867:chexi|2539:ObjectType|5868:carchexing|5871:displacement|5872:gearbox|5880:kucheid|6809:shangshishijian|6810:chexingyanse|6851:jibense|7067:zbjcfanwei|7068:yczb_cheling|7069:yczb_licheng|5870:madein|6808:chexibieming|5865:rundistanceqj|5883:chelingqj|1196:buytime|6860:shangpaiyuefen|6852:buyfrom|6855:baoyang|6853:yunying|4922:shiguqk|6856:chengse|6857:neishi|6866:neishiquexian|6869:syxian|6859:shouxu|4917:cheshenyanse|5864:MinPriceqj'
        HiddenForPara = '5863:zimu|5866:brand|5867:chexi|2539:ObjectType|5868:carchexing|5871:displacement|5872:gearbox|5880:kucheid|6809:shangshishijian|7068:yczb_cheling|7069:yczb_licheng|5870:madein|6808:chexibieming|4922:shiguqk|5865:rundistanceqj|5883:chelingqj|1196:buytime|6860:shangpaiyuefen|6852:buyfrom|6855:baoyang|6853:yuny'
        return 'Content-Disposition: form-data; name="HiddenForPara"\r\n\r\n' + str(HiddenForPara) + '\r\n'

    def getGobquzhiVal(self, externalSpec, carInfo, code):
        gobquzhi = ''
        fchar = externalSpec['brand']['fchar']
        if fchar is None or fchar == '':
            # fchar = self.getZimu(externalSpec)
            fchar = zimu.getFirstChar(externalSpec['brand']['name'])

        gobquzhi = gobquzhi + 'zimu=' + fchar
        gobquzhi = gobquzhi + '&brand=' + urllib.quote(externalSpec['brand']['name'].encode('utf-8'))
        gobquzhi = gobquzhi + '&chexi=' + urllib.quote(externalSpec['series']['name'].encode('utf-8'))
        if externalSpec['series'].get('object_type', None) is not None:
            if externalSpec['series']['object_type'].get('t', None) is not None:
                gobquzhi = gobquzhi +'&objecttype=' + urllib.quote(externalSpec['series']['object_type']['t'].encode('utf-8'))

        if externalSpec['model']['key'] == '0':
            pass
        else:
            gobquzhi = gobquzhi + '&carchexing=' + urllib.quote(externalSpec['model']['name'].encode('utf-8'))
            gobquzhi = gobquzhi + '&displacement=' + self.getDisplacementT(externalSpec, carInfo)

            # gobquzhi = gobquzhi + '&gearbox=' + urllib.quote(externalSpec['summary']['gearbox']['t'].encode('utf-8'))
            gobquzhi = gobquzhi + '&gearbox=' + urllib.quote(self.getGearBoxT(externalSpec, carInfo).encode('utf-8'))
            # gobquzhi = gobquzhi + '&kucheid=' + str(externalSpec['model']['kucheid']['t'])
            # gobquzhi = gobquzhi + '&shangshishijian=' + str(externalSpec['model']['shangshishijian']['t'])
            # TODO: by jesse
            # gobquzhi = gobquzhi + '&kucheid=' + '297979'

            gobquzhi = gobquzhi + '&shangshishijian=' + self.getShangshishijian(externalSpec, 't')
            # gobquzhi += "&tingshoushijian=" + "2003"

            #Fixme:车型库升级兼容性
            #gobquzhi = gobquzhi + '&yczb_cheling=' + str(externalSpec['summary']['yczb_cheling']['t'])
            # gobquzhi = gobquzhi + '&yczb_cheling=' + self.getYczb_cheling(externalSpec, 't')
            #gobquzhi = gobquzhi + '&yczb_licheng=' + str(externalSpec['summary']['yczb_licheng']['t'])
            # gobquzhi = gobquzhi + '&yczb_licheng=' + self.getYczb_licheng(externalSpec, 't')
        # gobquzhi = gobquzhi + '&zbjcfanwei=1'
        gobquzhi = gobquzhi + '&madein=' + urllib.quote(externalSpec['vendor']['name'].encode('utf-8'))
        if externalSpec['series']['chexibieming'].get('c', None) is not None:
            gobquzhi = gobquzhi + '&chexibieming=' + urllib.quote(externalSpec['series']['chexibieming']['t'].encode('utf-8'))
        gobquzhi = gobquzhi + '&rundistanceqj=' + urllib.quote(self.getMileAgeRange(carInfo))
        gobquzhi = gobquzhi + '&chelingqj=' + urllib.quote(self.getYearRange(carInfo))
        gobquzhi = gobquzhi + '&buytime=' + urllib.quote(str(self.getDate(carInfo).year) + '年')
        gobquzhi = gobquzhi + '&shangpaiyuefen=' + urllib.quote(str(self.getDate(carInfo).month) + '月')
        gobquzhi += "&baoyang=" + urllib.quote("是".encode('utf-8'))
        gobquzhi += "&shiguqk=" + urllib.quote("无".encode('utf-8'))
        gobquzhi = gobquzhi + '&cheshenyanse=' + urllib.quote(self.getColorChinese(carInfo))
        # gobquzhi = gobquzhi + '&chexingyanse=' + urllib.quote(self.getColorChinese(carInfo))
        gobquzhi = gobquzhi + '&minpriceqj=' + urllib.quote(self.getPriceRange(carInfo))
        gobquzhi = gobquzhi + '&cateapplyed=' + '29'
        # gobquzhi = gobquzhi + '&baoyang=%E6%98%AF'
        # gobquzhi = gobquzhi + '&shiguqk=%E6%97%A0'
        gobquzhi = gobquzhi + '&localapplyed=' + str(code)
        #gobquzhi = 'zimu=M&brand=%E9%A9%AC%E8%87%AA%E8%BE%BE&chexi=%E7%9D%BF%E7%BF%BC&objecttype=%E8%BD%BF%E8%BD%A6&carchexing=2010%E6%AC%BE%202.0%20%E8%B1%AA%E5%8D%8E%E7%89%88&displacement=2.0&gearbox=%E8%87%AA%E5%8A%A8&kucheid=275822&shangshishijian=2009&chexingyanse=%E7%8F%A0%E5%85%89%E9%BB%91&zbjcfanwei=1&yczb_cheling=3&yczb_licheng=6&madein=%E5%90%88%E8%B5%84&chexibieming=%E9%A9%AC%E8%87%AA%E8%BE%BE%E7%9D%BF%E7%BF%BC&rundistanceqj=3-5%E4%B8%87%E5%85%AC%E9%87%8C&chelingqj=1-3%E5%B9%B4&buytime=2012%E5%B9%B4&shangpaiyuefen=3%E6%9C%88&minpriceqj=40%E4%B8%87%E4%BB%A5%E4%B8%8A&cateapplyed=29&localapplyed=1'

        # gobquzhi = 'zimu=B&brand=%E6%9C%AC%E7%94%B0&chexi=%E9%9B%85%E9%98%81&objecttype=%E8%BD%BF%E8%BD%A6&carchexing=2000%E6%AC%BE%202.0%20%E8%87%AA%E5%8A%A8%20EXi%E6%A0%87%E5%87%86%E7%89%88&displacement=2.0&gearbox=%E8%87%AA%E5%8A%A8&kucheid=297979&shangshishijian=2000&tingshoushijian=2003&madein=%E5%90%88%E8%B5%84&chexibieming=%E6%9C%AC%E7%94%B0%E9%9B%85%E9%98%81&rundistanceqj=12-18%E4%B8%87%E5%85%AC%E9%87%8C&chelingqj=10%E5%B9%B4%E4%BB%A5%E4%B8%8A&buytime=2001%E5%B9%B4&shangpaiyuefen=1%E6%9C%88&baoyang=%E6%98%AF&shiguqk=%E6%97%A0&cheshenyanse=%E7%BB%BF&minpriceqj=40%E4%B8%87%E4%BB%A5%E4%B8%8A&cateapplyed=29&localapplyed=222'

        return gobquzhi


    def getGobquzhiValMobile(self, shareJob, externalSpec, carInfo, code):
        gobquzhi = ''
        gobquzhi = gobquzhi + 'brand=' + urllib.quote(externalSpec['brand']['name'].encode('utf-8'))
        gobquzhi = gobquzhi + '&chexi=' + urllib.quote(externalSpec['series']['name'].encode('utf-8'))
        if externalSpec['model']['key'] == '0':
            pass
        else:
            gobquzhi = gobquzhi + '&carchexing=' + urllib.quote(externalSpec['model']['name'].encode('utf-8'))
        gobquzhi = gobquzhi + '&cheshenyanse=' + urllib.quote(self.getColorChinese(carInfo))
        gobquzhi = gobquzhi + '&buytime=' + urllib.quote(str(self.getDate(carInfo).year) + '年')

        Symbol = "\n"
        lateral = "——"*20
        vehicle = shareJob.get('vehicle')
        if self.loanable(vehicle=vehicle):
            gobquzhi += '&Content=' + urllib.quote(str(self.getContentVal_finance_58(shareJob, Symbol, lateral)).encode('utf-8'))
        else:
            gobquzhi += '&Content=' + urllib.quote(str(self.getContentVal(shareJob, Symbol, lateral)).encode('utf-8'))
        gobquzhi += '&type='
        return gobquzhi


    def getGobquzhi(self, externalSpec, carInfo, code):
        gobquzhi = self.getGobquzhiVal(externalSpec, carInfo, code)
        return 'Content-Disposition: form-data; name="gobquzhi"\r\n\r\n' + gobquzhi+ '\r\n'

    def getGobalsokey(self, externalSpec, carInfo, code):
        gobalsokey = []
        gobalsokey.append(zimu.getFirstChar(externalSpec['brand']['name']))
        gobalsokey.append(externalSpec['brand']['name'].encode('utf-8'))
        gobalsokey.append(externalSpec['model']['name'].encode('utf-8'))
        if externalSpec['model']['key'] == '0':
            pass
        else:
            displacementT = self.getDisplacementT(externalSpec, carInfo)
            gobalsokey.append(str(displacementT))

            gobalsokey.append(str(self.getGearBoxT(externalSpec, carInfo).encode('utf-8')))
            #gobalsokey.append(externalSpec['summary']['gearbox']['t'].encode('utf-8'))
            ##gobalsokey.append(str(externalSpec['model']['kucheid']['t']))
            #gobalsokey.append(str(externalSpec['model']['shangshishijian']['t']))
            gobalsokey.append(self.getShangshishijian(externalSpec, 't'))
            #gobalsokey.append(str(externalSpec['summary']['yczb_cheling']['t']))
            gobalsokey.append(self.getYczb_cheling(externalSpec, 't'))
            #gobalsokey.append(str(externalSpec['summary']['yczb_licheng']['t']))
            gobalsokey.append(self.getYczb_licheng(externalSpec, 't'))
        gobalsokey.append(externalSpec['vendor']['name'].encode('utf-8'))
        gobalsokey.append(externalSpec['brand']['name'].encode('utf-8') + externalSpec['series']['name'].encode('utf-8'))
        gobalsokey.append(self.getMileAgeRange(carInfo))
        gobalsokey.append(str(self.getDate(carInfo).year) + '年')
        gobalsokey.append(str(self.getDate(carInfo).month) + '月')
        #gobalsokey.append('是')
        gobalsokey.append(self.getColorChinese(carInfo))
        gobalsokey.append(str(self.getMileAgeData(carInfo)) + '万元')
        gobalsokey.append(str(self.getPriceData(carInfo)) + '万元')
        return 'Content-Disposition: form-data; name="gobalsokey"\r\n\r\n' + "|".join(gobalsokey) + '\r\n'
        #s = 'M|睿翼|2010款 2.0 豪华版|2.0|自动|275822|2009|珠光黑|1|3|6|合资|马自达睿翼|3-5万公里|2012年|3月|3万元|14万元'
        #return 'Content-Disposition: form-data; name="gobalsokey"\r\n\r\n' + s + '\r\n'

    @staticmethod
    def getFcookie(fcookie):
        return 'Content-Disposition: form-data; name="fcookie"\r\n\r\n' + fcookie.encode('utf-8') + '\r\n'

    def getHiddenTextBoxJoinValue(self, externalSpec, carInfo, vehicle):
        contact = u'销售代表'
        promotionWords = self.promotionWords(vehicle, False)
        vehicle = carInfo.get('vehicle', None)
        #user = vehicle.get('user', None)
        #if user is not None:
        #    name = user.get('name', None)
        #    if name is not None:
        #        contact = name
        vin = vehicle.get('vin', None)
        (contact, phone) = self.getContact(carInfo)
        brand = externalSpec['brand']['name'].encode('utf-8')
        series = externalSpec['series']['name'].encode('utf-8')
        model = externalSpec['model']['name'].encode('utf-8')
        #vehicle.user.company_address
        company_address = ""
        user = vehicle.get("user", None)
        if user is not None:
            company_address = user.get("company_address", None)
        if company_address is None:
            company_address = ""
        #hiddenTextBoxJoinValue = ":".join([brand, series, model, brand + series + model, (self.getDescBriefValue(carInfo).encode('utf-8')).strip(), contact.encode('utf-8'), phone.encode("utf-8"), company_address.encode('utf-8')])
        # hiddenTextBoxJoinValue = ":".join([brand, series, model, brand + series + model, contact.encode('utf-8'), phone.encode("utf-8"), company_address.encode('utf-8')])
        hiddenTextBoxJoinValue = ":".join([vin, brand, series, model, brand + series + model, promotionWords, contact.encode('utf-8'), company_address.encode('utf-8')])
        #hiddenTextBoxJoinValue = 'LVXCAHBA8FS012678:陆风:陆风X5:2013款 2.0T 手动 创行版:陆风X5车型 2013款 2.0T 手动 创行版:包过户、一手新车:林先生:福建省福州市闽侯县'
        return 'Content-Disposition: form-data; name="hiddenTextBoxJoinValue"\r\n\r\n' + hiddenTextBoxJoinValue + '\r\n'

    @staticmethod
    def getXiaobaoOption():
        return 'Content-Disposition: form-data; name="xiaobao_option"\r\n\r\n' + '0' + '\r\n'

    # 失败图片重试三次
    def post_pic_content(self, conn, content, headers, times):
        '''
        if times < g_pic_retry_times:
            try:
                conn.request("POST", "/postpic/upload?flash=1", content, headers=headers)
                res = conn.getresponse()
                photo_res = res.read()
            except Exception as e:
                logger.debug(str(e))
                photo_res = self.post_pic_content(conn, content, headers, times + 1)
            return photo_res
        else:
            # end condition
            return None
        '''
        photo_res = None
        while(times < g_pic_retry_times) and (photo_res is None):
            try:
                conn.request("POST", "/postpic/upload?flash=1", content, headers=headers)
                res = conn.getresponse()
                photo_res = res.read()
            except Exception as e:
                logger.debug(str(e))
            times += 1
        return photo_res

    def uploadPicContent(self, content):
        conn = httplib.HTTPConnection("pic.kuche.com", 80)
        headers = copy.copy(self.headers)
        del headers['Cookie']
        img = StringIO(content)
        smallImg = StringIO()
        resize.resize(img, (640, 640), False, smallImg)
        content = smallImg.getvalue()

        headers['Host'] = 'pic.kuche.com'
        headers['Origin'] = 'http://pic2.58.com'
        headers['Referer'] = 'http://pic2.58.com/ui7/post/PictureUpload_zip_s1.swf'
        headers['Content-length'] = len(content)
        headers['Content-type'] = 'application/octet-stream'
        headers['File-Extensions'] = 'jpg'
        headers['Pic-Bulk'] = '0'
        headers['Pic-Cut'] = '0*0*0*0'
        headers['Pic-IsAddWaterPic'] = 'True'
        headers['Pic-Path'] = '/p1/big/'
        headers['Pic-Size'] = '640*640'
        headers['Pic-dpi'] = '0'
        headers['pic-name'] = '/p1/tiny/'

        # logger.debug("picUpload headers=" + str(headers))

        # try:
        #     conn.request("POST", "/postpic/upload?flash=1", content, headers=headers)
        # except:
        #     pass
        # res = conn.getresponse()
        # photoRes = res.read()#.decode("GB18030")
        photoRes = self.post_pic_content(conn, content, headers, times=0)
        logger.debug(str(photoRes))
        conn.close()
        return photoRes

    def uploadPics(self, photos, watermark):
        photo_list = []
        photos = photos[:16]  #最多16张图片
        for photo in photos:
            url = photo.get("url", None)
            print url
            if url is None:
                continue
            o = urlparse(url)
            host = o.netloc
            uri = o.path
            
            #print content
            upload = self.sessionServer.getUpload('58', uri)
            logger.debug("upload=" + str(upload))
            if upload is not None:
                res = upload
            else:
                host = 'pic.kanche.com'
                # if host == 'pic.kanche.com':
                #     host = 'kanche-pic.qiniudn.com'
                if (watermark is not None) and (watermark.get("enable_sites", []).count("58.com")):
                    uri = utils.pic_with_watermark_ali(uri,
                                                       watermark.get("image", ""),
                                                       watermark.get("gravity", "NorthWest"))
                conn = httplib.HTTPConnection(host, timeout=timeout_58)
                headers = copy.copy(self.headers)
                del headers['Cookie']
                headers['Referer'] = "www.kanche.com"
                headers['Host'] = host

                conn.request("GET", uri, headers = headers)
                res = conn.getresponse()
                content = res.read()
                conn.close()
                #上传
                res = self.uploadPicContent(content)
                '''
                try:
                    res = self.uploadPicContent(content)
                except Exception as e:
                    res = None
                '''
                if res is not None:
                    self.sessionServer.setUpload('58', uri, res)
                else:
                    return None
            if res is not None:
                photo_list.append(res)
        return photo_list


    def uploadDrivingLicensePicture(self, url):
        if url is None or url == '':
            picPath = './app/resource/drivingLicensePictureIfNone.jpg'

            drivingLicenseFile = open(picPath)
            drivingLicenseContent = ''

            try:
                drivingLicenseContent = drivingLicenseFile.read()
            finally:
                drivingLicenseFile.close()

            res = self.uploadPicContent(drivingLicenseContent)

            if res is not None:
                return 'Content-Disposition: form-data; name="yczbpic"\r\n\r\n' + 'http://pic.58.com/p1/big/' +str(res) + '\r\n'
            else:
                return None


        o = urlparse(url)
        host = o.netloc
        uri = o.path

        upload = self.sessionServer.getUpload('58', uri)
        logger.debug("upload=" + str(upload))
        if upload is not None:
            res = upload
        else:
            host = 'pic.kanche.com'
            conn = httplib.HTTPConnection(host, timeout=timeout_58)
            headers = copy.copy(self.headers)
            del headers['Cookie']
            headers['Referer'] = "www.kanche.com"
            headers['Host'] = host

            conn.request("GET", uri, headers = headers)
            res = conn.getresponse()
            content = res.read()
            conn.close()
            res = self.uploadPicContent(content)
            if res is not None:
                self.sessionServer.setUpload('58', uri, res)

        if res is not None:
            return 'Content-Disposition: form-data; name="yczbpic"\r\n\r\n' + 'http://pic.58.com/p1/big/' +str(res) + '\r\n'

        return None


    def doLoginWithValidationCode(self, formStr):
        conn = httplib.HTTPConnection("passport.58.com", timeout=timeout_58)
        headers = copy.copy(self.headers)
        conn.request("GET", "/validatecode", headers = headers)
        res = conn.getresponse()
        self.setCookies(res.getheaders(), encode = True)
        imageData = res.read()
        conn.close()
        image = StringIO(imageData)
        captcha = self.getCaptcha(image, imageData)
        if captcha is None:
            return False
        veridationCode = captcha["text"]
        formStr += "&validatecode=" + veridationCode
        conn = httplib.HTTPConnection("passport.58.com", timeout=timeout_58)
        headers = copy.copy(self.headers)
        headers['Content-Type'] = 'application/x-www-form-urlencoded'

        conn.request("POST", "/dounionlogin", formStr, headers = headers)
        logger.debug("duunionlogin formStr=" + str(formStr))
        res = conn.getresponse()
        html = zlib.decompress(res.read(), 16+zlib.MAX_WBITS)
        html = html.decode('utf-8')
        conn.close()
        logger.debug("---doLoginWithValidationCode html---\n" + html)
        if html.count('window.parent.location="http://my.58.com') == 0:
            return False
        resHeader = res.getheaders()
        self.setCookies(resHeader, encode=True)
        logger.debug("---doLoginWithValidationCode resHeader---\n" + str(resHeader))
        return True
        
        
    def getVcode(self, pCookie, pCodekey):
        iHeaders = {
            'cookie':pCookie,
            'Accept':'*/*',
            'Accept-Encoding':'gzip, deflate',
            'User-Agent':'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:45.0) Gecko/20100101 Firefox/45.0'
        }
        iData = requests.get('http://passport.58.com/validcode/get?vcodekey=%s&time=%s'%(pCodekey, time.time()), headers=iHeaders).content
        image = StringIO(iData)
        captcha = self.getCaptcha(image, image_data=iData)
        if captcha is None:
            return None
        else:
            #print captcha
            return captcha['text']
        
        
    def feSetCookies(self, pData):
        iResult = []
        for k,v in pData.items():
            iResult.append(('set-cookie', '%s=%s'%(k,v)))
        self.setCookies(iResult, encode=True)

    def getRSA(self, username, password):
        iHtml = requests.get('http://passport.58.com/pso/viplogin/').text
        dom = hx.fromstring(iHtml)
        iList = dom.xpath('//div[@id="denglu_box_id"]/script/@src')
        if len(iList) == 2:
            if 'static' in iList[0]:
                iJsUrl = iList[0]
                iHtmlUrl = iList[1]
            else:
                iJsUrl = iList[1]
                iHtmlUrl = iList[0]
                
            iPath = re.findall('path=([^\&]+)', iHtmlUrl)
            iPath = urllib.unquote(iPath[0])
            
            iHtml = requests.get(iJsUrl).text
            iTimeSpan = re.findall('var timespan=(\d+)[^;]', iHtml)
            
            iHtml = requests.get(iHtmlUrl).text
            iList = re.findall('<input[^>]*>', iHtml)
            iHtml = ''.join(iList)
            iHtml = '<form>%s</form>'%iHtml
            
            dom = hx.fromstring(iHtml)
            rsaExponent = dom.xpath('//input[@id="rsaExponent"]/@value')
            rsaModulus = dom.xpath('//input[@id="rsaModulus"]/@value')
            
            jsStr = 'var timesign = %s;'%iTimeSpan[0]
            jsStr += "var password_new = '%s';"%password
            jsStr += 'var rsaExponent = "%s";'%rsaExponent[0]
            jsStr += 'var rsaModulus = "%s";'%rsaModulus[0]
            jsStr += 'encryptString(timesign + encodeURIComponent(password_new), rsaExponent, rsaModulus);'
            
            iHtml = requests.get('http://passport.58.com/rsa/ppt_security.js').text
            iHtml = "var window = {'RSAUtils':undefined};" + iHtml
            child = subprocess.Popen(['phantomjs','./app/jsfunc/fe160315.js', iHtml, jsStr], stdin=subprocess.PIPE, stdout=subprocess.PIPE, shell=False)
            rsaPassword = child.stdout.read().strip()
            
            return {
                'path':iPath,
                'timeSpan':iTimeSpan[0],
                'rsaExponent':rsaExponent[0],
                'rsaModulus':rsaModulus[0],
                'rsaPassword':rsaPassword,
                'username':username,
                'password':password
            }
    
    def getLoginBody(self, pRsa, pCode = None):
        iData = [
            'isweak=0&source=&path=%s&password=%s&timesign=%s&isremember=false&callback=successFun&yzmstate=&rsaExponent=%s&rsaModulus=%s&password_value=%s&username=%s&btnSubmit=%s',
            'isweak=0&source=&path=%s&password=%s&timesign=%s&isremember=false&callback=successFun&yzmstate=&rsaExponent=%s&rsaModulus=%s&password_value=%s&username=%s&validcode=%s&vcodekey=%s&btnSubmit=%s'
        ]
        iHeaders = {
            'Accept':'*/*',
            'Accept-Encoding':'gzip, deflate',
            'Content-Type':'application/x-www-form-urlencoded', 
            'User-Agent':'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:45.0) Gecko/20100101 Firefox/45.0'
        }
        if pCode is None:
            iParam = (
                urllib.quote(pRsa['path']),
                pRsa['rsaPassword'],
                pRsa['timeSpan'],
                pRsa['rsaExponent'],
                pRsa['rsaModulus'],
                pRsa['password'],
                urllib.quote(pRsa['username'].encode('utf8')),
                urllib.quote('登录中...')
            )
            iBody = iData[0]%iParam
        else:
            iParam = (
                urllib.quote(pRsa['path']),
                pRsa['rsaPassword'],
                pRsa['timeSpan'],
                pRsa['rsaExponent'],
                pRsa['rsaModulus'],
                pRsa['password'],
                urllib.quote(pRsa['username'].encode('utf8')),
                pCode['vcode'],
                pCode['vkey'],
                urllib.quote('登录中...')
            )
            iBody = iData[1]%iParam
            iHeaders['cookie'] = pCode['cookie']
        iHeaders['Content-Length'] = len(iBody)
        return iBody, iHeaders
    
    def feLoginByCode(self, username, password, pCookie, pVkey):
        iCode = self.getVcode(pCookie, pVkey)
        if iCode is None:
            iCode = self.getVcode(pCookie, pVkey)
            if iCode is None:
                iCode = self.getVcode(pCookie, pVkey)
                if iCode is None:
                    logger.error('验证码解析失败')
                    return False , {'code':-1, 'msg':'验证码解析失败'}
                    
        #username = u'哈尔滨看看车'
        iRsa = self.getRSA(username, password)
        
        iBody, iHeaders = self.getLoginBody(iRsa, {'vkey':pVkey, 'vcode':iCode, 'cookie':pCookie})
        
        
        r = requests.post('http://passport.58.com/login/dologin',data=iBody,headers=iHeaders)
        iStr = r.text[r.text.find('{'):r.text.rfind('}')+1]
        iResult = loads(iStr)
        if iResult['code'] == 0:
            return True, requests.utils.dict_from_cookiejar(r.cookies)
        elif iResult['code'] == 786:
            return False, None
        else:
            return False, iResult
    
    def doLogin(self, username, password):
        iRsa = self.getRSA(username, password)
        if iRsa is None:
            return
        
        r = requests.get('http://passport.58.com/mobileauthcodelogin/ui?callback=mobileloginSuccessFunction&source=pc-login&risktype=1&path=http://my.58.com&errorpath=http://passport.58.com/login')
        iCookies = requests.utils.dict_from_cookiejar(r.cookies)
        
        iData = [
            'isweak=0&source=&path=%s&password=%s&timesign=%s&isremember=false&callback=successFun&yzmstate=&rsaExponent=%s&rsaModulus=%s&password_value=%s&username=%s&btnSubmit=%s',
            'isweak=0&source=&path=%s&password=%s&timesign=%s&isremember=false&callback=successFun&yzmstate=&rsaExponent=%s&rsaModulus=%s&password_value=%s&username=%s&validcode=%s&vcodekey=%s&btnSubmit=%s'
        ]
        
        iParam = (
            urllib.quote(iRsa['path']),
            iRsa['rsaPassword'],
            iRsa['timeSpan'],
            iRsa['rsaExponent'],
            iRsa['rsaModulus'],
            password,
            urllib.quote(username.encode('utf8')),
            urllib.quote('登录中...')
        )
        
        iBody = iData[0]%iParam
        iHeaders = {
            'cookie':iCookies,
            'Content-Length':len(iBody),
            'Accept':'*/*',
            'Accept-Encoding':'gzip, deflate',
            'Content-Type':'application/x-www-form-urlencoded', 
            'User-Agent':'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:45.0) Gecko/20100101 Firefox/45.0'
        }
        
        r = requests.post('http://passport.58.com/login/dologin',data=iBody,headers=iHeaders)
        iStr = r.text[r.text.find('{'):r.text.rfind('}')+1]
        iResult = loads(iStr)
        if iResult['code'] == 0:
            iCookies = requests.utils.dict_from_cookiejar(r.cookies)
            self.feSetCookies(iCookies)
            return True
        elif iResult['code'] in [-1,-2]:
            logger.debug('系统异常')
        elif iResult['code'] == 1:
            logger.debug('账户已被冻结')
        elif iResult['code'] in [2,3]:
            logger.debug('账户需重新验证手机号')
        elif iResult['code'] == 5:
            logger.debug('该用户名不存在')
        elif iResult['code'] == 769:
            print '用户名格式错误'
        elif iResult['code'] == 801:
            logger.debug('密码格式错误')
        elif iResult['code'] == 772:
            logger.debug('密码与账户名不符')
        elif iResult['code'] == 785:
            logger.debug('请输入验证码')
            iVcodekey = iResult['data']['vcodekey']
            (iFlag, iResult) = self.feLoginByCode(username, password, iData[1], iCookies, iVcodekey)
            if iFlag:
                self.feSetCookies(iResult)
                return True
            elif iResult is None:
                (iFlag, iResult) = self.feLoginByCode(username, password, iData[1], iCookies, iVcodekey)
                if iFlag:
                    self.feSetCookies(iResult)
                    return True
                elif iResult is None:
                    (iFlag, iResult) = self.feLoginByCode(username, password, iData[1], iCookies, iVcodekey)
                    if iFlag:
                        self.feSetCookies(iResult)
                        return True
                    elif iResult is None:
                        logger.debug('验证码重试失败')
                    else:
                        logger.debug(iResult)
                else:
                    logger.debug(iResult)
            else:
                logger.debug(iResult)
        else:
            logger.debug(r.text)
        return False
        
    def doLogin_del_by_david(self, username, password):
        conn = httplib.HTTPConnection("passport.58.com", timeout=timeout_58)
        conn.request("GET", "/login/", headers=self.headers)
        res = conn.getresponse()
        logger.debug("---login get header---\n" + str(self.headers))
        resHeader = res.getheaders()
        logger.debug("---login get response header---\n" + str(resHeader))
        #self.setCookies(res.getheaders())
        html = zlib.decompress(res.read(), 16+zlib.MAX_WBITS)
        html = html.decode('utf-8')
        conn.close()
        dom = lxml.html.fromstring(html)
        ptsRe = re.search("pts=(?P<pts>\d{13})", html)
        if ptsRe is None:
            return False
        pts = ptsRe.group("pts")
        #keyRe = re.search('\$\(\"\#p3\"\)\.val\(encryptString\(timesign \+ encodeURIComponent\(\$\(\"\#password\"\)\.val\(\)\), \"(?P<salt>\d{6})\", \"(?P<key>[0-9a-f]*)\"', html)
        keyRe = re.search('\$\(\"\#p3\"\)\.val\(encryptString\(timesign.*\+.*encodeURIComponent\(\$\(\"\#password\"\)\.val\(\)\),.*\"(?P<salt>\d{6})\",.*\"(?P<key>[0-9a-f]*)\"', html)
        if keyRe is None:
            return False
        salt = keyRe.group("salt")
        key = keyRe.group("key")
        logger.debug("pts=%s,salt=%s,key=%s"%(str(pts), str(salt), str(key)))
        child = subprocess.Popen(["./app/jsfunc/felogin.js"], stdin=subprocess.PIPE, stdout=subprocess.PIPE)
        req = {"pts": pts, "salt": salt, "key": key, "password": password}
        res = child.communicate(json.dumps(req))
        logger.debug("phantomJS res=" + res[0])
        if res[0] is None or '' == res[0]:
            res = {}
        else:
            res = json.loads(res[0])
        form = res
        form['cd'] = dom.xpath('//*[@id="cd"]/@value')[0]
        form['ptk'] = dom.xpath('//*[@id="ptk"]/@value')[0]
        form['path'] = dom.xpath('//*/input[@name="path"]/@value')[0]
        form['isweak'] = dom.xpath('//*[@id="isweak"]/@value')[0]
        form['username'] = username.encode("utf-8")
        form['password'] = 'password'
        form['mcresult'] = 'undefined'
        del form['timespan']
        del form['pts']
        logger.debug(str(form))
        conn = httplib.HTTPConnection("passport.58.com", timeout=timeout_58)
        headers = copy.copy(self.headers)
        headers['Content-Type'] = 'application/x-www-form-urlencoded'
        formStr = "cd=" + str(form['cd'])
        formStr += "&isweak=" + str(form['isweak'])
        formStr += "&mcresult=undefined"
        formStr += "&p1=" + form['p1']
        formStr += "&p2=" + form['p2']
        formStr += "&p3=" + form['p3']
        formStr += "&password=password"
        logger.debug("path=" + form['path'])
        formStr += "&path=" + urllib.quote(form['path'])
        formStr += "&ptk=" + form['ptk']
        formStr += '&timesign=' + str(form['timesign'])
        logger.debug("username="+form['username'])
        formStr += "&username=" + urllib.quote(form['username'])

        conn.request("POST", "/dounionlogin", formStr, headers = headers)
        #print urllib.urlencode(form)
        logger.debug(str(formStr))
        res = conn.getresponse()
        html = zlib.decompress(res.read(), 16+zlib.MAX_WBITS)
        html = html.decode('utf-8')
        conn.close()
        logger.debug(str(html))
        if html.count('window.parent.location="http://my.58.com') == 0:
            if html.count(u'请填写验证码') > 0:
                return self.doLoginWithValidationCode(formStr)
            return False
        self.setCookies(res.getheaders(), encode=True)
        return True

    def removeVehicle(self,shareJob):
        logger.debug("58 removeVehicle")
        #self.baseDir = os.path.dirname(os.path.realpath(__file__))
        shareAccount = shareJob.get("share_account", None)
        if shareAccount is None:
            return errorcode.DATA_ERROR, "缺少帐号"
        if shareAccount.get('account_type', None) == 'public':
            shareAccount['username'] = publicAccount['username']
            shareAccount['password'] = publicAccount['password']
        cookies = self.sessionServer.getSession('58', shareAccount['username'])
        logger.debug('-------session cookies---------\n' + str(cookies))
        #print json.dumps(cookies)
        if cookies is None:
            logger.debug("do login 58")
            res = self.doLogin(shareAccount['username'], shareAccount['password'])
            if not res:
                logger.error("login error")
                return errorcode.AUTH_ERROR, errormsg.LOGIN_FAIL
            self.sessionServer.setSession('58', shareAccount['username'], self.cookies)
        else:
            self.cookies = cookies
            ks = self.cookies.keys()
            cookie_list = []
            for k in ks:
                cookie_list.append(k + '=' + self.cookies[k])
            self.headers['Cookie'] = string.join(cookie_list, '; ')
        logger.debug(str(self.headers))

        urlForApp = shareJob.get("url", None)
        queryIds = re.compile("[0-9]\d{3,}").findall(urlForApp)[0]
        logger.debug("vehiId:"+str(queryIds))

        #对于推送中，先取消推送：
        #TODO:判断是否推送中：
        #目前，对于推广中，和非推广中，都可以有取消推送操作，返回结果也一样。【显示推送成功】
        #不在推送中 - "请选择优先推送天数"
        #在推送中 - "取消优先推送"
        #GET: http://info.vip.58.com/promotion/entry/20461397647752/100505/?r=1422759685249
        conn = httplib.HTTPConnection('info.vip.58.com', timeout=timeout_58)
        timestamp = int(time.time())
        url = "/promotion/entry/" + queryIds + "/100505/?r=" + str(timestamp) + "000"
        logger.debug("判断推送:"+str(url))
        headers = copy.copy(self.headers)
        conn.request("GET", url, headers=headers)
        res = conn.getresponse()
        status = res.status
        result = self.decodeBody(res.getheaders(), res.read())
        if 200 == status:
            #不在推送中
            if result.count("请选择优先推送天数") > 0:
                pass

            #在推送中
            elif result.count("取消优先推送") > 0:
                #POST： http://info.vip.58.com/promotion/cancel/20414979467529/100505/
                #response：{"data":0,"msg":"信息取消推送成功！","code":0}
                conn = httplib.HTTPConnection('info.vip.58.com', timeout=timeout_58)
                url = "/promotion/cancel/" + queryIds + "/100505/"
                logger.debug("先取消推送:"+str(url))
                headers = copy.copy(self.headers)
                conn.request("POST", url, headers=headers)
                res = conn.getresponse()
                status = res.status
                result = self.decodeBody(res.getheaders(), res.read())
                if 200 == status:
                    resultDict = json.loads(result)
                    if resultDict is None:
                        return errorcode.SITE_ERROR, errormsg.VEHICLE_REMOVE_FAIL
                    else:
                        resultMsg = resultDict['msg']
                        logger.debug("取消推送:"+str(resultMsg))
                else:
                    return errorcode.SITE_ERROR, errormsg.VEHICLE_REMOVE_FAIL

            else:
                return errorcode.SITE_ERROR, "判断是否在推送中页面发生改变"

        else:
            return errorcode.SITE_ERROR, errormsg.VEHICLE_REMOVE_FAIL

        #开始下架
        #if len(urlForApp):
        if urlForApp is not None and len(urlForApp) > 0:
            if self.isVIP(shareJob):
                #http://info.vip.58.com/deleteinfochecked/
                conn = httplib.HTTPConnection('info.vip.58.com', timeout=timeout_58)
                url = "/deleteinfochecked/"
                print url
                headers = copy.copy(self.headers)
                formData = 'infoIds=' + queryIds
                headers['Content-Type'] = 'application/x-www-form-urlencoded; charset=UTF-8'
                conn.request("POST", url, formData, headers=headers)
                res = conn.getresponse()
                result = self.decodeBody(res.getheaders(), res.read())
                status = res.status
                logger.debug("--post--\n" + res.read())
                conn.close()
                if result == queryIds and status == 200:
                    return errorcode.SUCCESS, ""
                else:
                    return errorcode.SITE_ERROR, errormsg.VEHICLE_REMOVE_FAIL+str(1)
            else:
                #http://info.vip.58.com/delcheyuan/
                conn = httplib.HTTPConnection('info.vip.58.com', timeout=timeout_58)
                url = "/delcheyuan/"
                print url
                headers = copy.copy(self.headers)
                formData = 'infoIds=' + queryIds
                headers['Content-Type'] = 'application/x-www-form-urlencoded; charset=UTF-8'
                conn.request("POST", url, formData, headers=headers)
                res = conn.getresponse()
                postHeader = res.getheaders()
                result = self.decodeBody(res.getheaders(), res.read())
                status = res.status
                logger.debug("--postHeaders--\n" + str(postHeader))
                conn.close()
                if result == queryIds and status == 200:
                    return errorcode.SUCCESS, ""
                else:
                    return errorcode.SITE_ERROR, errormsg.VEHICLE_REMOVE_FAIL+str(2)

        else:
            return errorcode.DATA_ERROR, errormsg.VEHICLE_URL_EMPTY


    def updateVehicle(self, shareJob):
        logger.debug("58 updateVehicle")
        #self.baseDir = os.path.dirname(os.path.realpath(__file__))
        shareAccount = shareJob.get("share_account", None)
        if shareAccount is None:
            return errorcode.DATA_ERROR, "缺少帐号"
        if shareAccount.get('account_type', None) == 'public':
            shareAccount['username'] = publicAccount['username']
            shareAccount['password'] = publicAccount['password']
        cookies = self.sessionServer.getSession('58', shareAccount['username'])
        logger.debug('-------session cookies---------\n' + str(cookies))

        if cookies is None:
            logger.debug("do login 58")
            res = self.doLogin(shareAccount['username'], shareAccount['password'])
            if not res:
                logger.error("login error")
                return errorcode.AUTH_ERROR, errormsg.LOGIN_FAIL
            self.sessionServer.setSession('58', shareAccount['username'], self.cookies)
        else:
            self.cookies = cookies
            ks = self.cookies.keys()
            cookie_list = []
            for k in ks:
                cookie_list.append(k + '=' + self.cookies[k])
            self.headers['Cookie'] = string.join(cookie_list, '; ')
        logger.debug(str(self.headers))


        urlForApp = shareJob.get("url", None)
        queryId = re.compile("[0-9]\d{3,}").findall(urlForApp)[0]
        logger.debug("58 vehicleId:"+str(queryId))
        if queryId is None:
            return errorcode.DATA_ERROR, errormsg.VEHICLE_URL_EMPTY



        vehicle = shareJob.get("vehicle", None)
        if vehicle is None:
            logger.debug("vehicle missing")
            return errorcode.DATA_ERROR, errormsg.VEHICLE_EMPTY
        user = vehicle.get("user", None)
        if user is None:
            return errorcode.DATA_ERROR, errormsg.USER_EMPTY
        mobile = user.get("mobile", None)
        if mobile is None:
            return errorcode.DATA_ERROR, errormsg.MOBILE_EMPTY

        spec = vehicle.get("spec", None)
        if spec is None:
            logger.debug("spec missing")
            return errorcode.DATA_ERROR, errormsg.VEHICLE_SPEC_EMPTY
        levelId = spec.get("level_id", None)
        if levelId is None:
            logger.debug("levelId missing")
            return errorcode.DATA_ERROR, errormsg.VEHICLE_SPEC_EMPTY
        logger.debug("levelId=" + levelId)
        #(specid, specDetail) = self.getCarSpec(levelId)
        externalSpec = shareJob.get("external_vehicle_spec", None)
        if externalSpec is None:
            logger.error("external spec missing")
            return errorcode.SPEC_ERROR, errormsg.EXTERNAL_SPEC_EMPTY
        logger.debug(str(externalSpec))
        externalSpecModelId = externalSpec['model']['id']
        logger.debug("externalSpecModelId=" + externalSpecModelId)

        imgList = self.getHtmlImglist(queryId)


        # gallery = vehicle.get("gallery", None)
        # if gallery is None:
        #     logger.debug("gallery missing")
        # photoList = self.uploadPics(gallery.get("photos", []))
        # logger.debug(json.dumps(photoList))

        summary = vehicle.get("summary", None)
        if summary is None:
            drivingLicensePicture = None
        else:
            drivingLicensePicture = self.uploadDrivingLicensePicture(summary.get("driving_license_picture", None))

        return self.updatePostVehicle(shareJob, externalSpec, imgList, drivingLicensePicture, queryId)


    def getHtmlImglist(self, queryId):
        conn = httplib.HTTPConnection("post.58.com", timeout=10)
        location_url = "/vupdate/"+queryId+'?source=car/'

        updateHeader = copy.copy(self.headers)
        updateHeader['Host'] = 'post.58.com'
        updateHeader['Referer'] = 'http://vip.58.com/app/mci/?PGTID='+str(random.random())
        conn.request("GET", location_url, headers = self.headers)
        res = conn.getresponse()
        updateResult = self.decodeBody(res.getheaders(), res.read())
        conn.close()

        getDom = lxml.html.fromstring(updateResult)

        imgList = []
        # 隐藏的imgList
        inputHiddenImage = getDom.xpath('//div[@id="imglist"]//input[@id="pic"]/@value')[0]
        tmps = inputHiddenImage.split("|")
        for photo in tmps:
            imgList.append(photo.split("/")[-1])
        return imgList

    def updatePostVehicle(self, shareJob, externalSpec, photoList, drivingLicensePicture, queryId):
        vehicle = shareJob.get("vehicle", None)
        carInfo = shareJob
        #if vehicle is None:
        #    return errorcode.DATA_ERROR, "缺少车辆信息"
        username = carInfo.get("share_account").get("username")
        user = vehicle.get('user', None)
        #if user is None:
            #return False
        #    return errorcode.DATA_ERROR, "缺少用户信息"
        vehicle_date = vehicle.get('vehicle_date', None)
        if vehicle_date is None:
            return errorcode.DATA_ERROR, "缺少用户信息"
        '''
        address = user.get('address', None)
        if address is None:
            #return False
            return errorcode.DATA_ERROR, errormsg.ADDRESS_EMPTY
        '''
        merchant = vehicle.get('merchant', None)
        address = merchant.get('address', None)
        cityCode = address.get('city_code', None)
        if cityCode is None:
            #return
            return errorcode.DATA_ERROR, errormsg.CITY_EMPTY
        code = self.city582.getCode(cityCode)


        (url_code, html) = self.getPostPage(code)
        # TODO : postVechicleMobile update
        # if not url_code.startswith('v'):
        #     return self.postVehicleMobile(carInfo, externalSpec, photoList, code, cityCode)

        fcookieRe = re.search("\$\.c\.fk\.i\(\'(?P<fcookie>[0-9a-z\-]{36})\'\)", html)
        if fcookieRe is None:
            #return False
            return errorcode.LOGIC_ERROR, errormsg.PARAMETER_UNRESOLVED
        fcookie = fcookieRe.group("fcookie")
        #print fcookie
        logger.debug("fcookie=" + fcookie)
        bianhaoRe = re.search('\$\(\"#xinxibianhao\"\)\.val\(\'(?P<bianhao>.*)\'\);', html)
        bianhao = bianhaoRe.group('bianhao')
        # #print bianhao
        # logger.debug("bianhao=" + bianhao)
        # iqas_mcvalueRe = re.search("var iqas_mcvalue = \'(?P<mcvalue>[0-9]{13})\'", html)
        # if iqas_mcvalueRe is None:
        #     #return False
        #     return errorcode.LOGIC_ERROR, errormsg.PARAMETER_UNRESOLVED
        # iqas_mcvalue = iqas_mcvalueRe.group("mcvalue")
        # #print iqas_mcvalue
        # logger.debug("iqas_mcvalue=" + iqas_mcvalue)
        # iqas_mcformulaRe = re.search("var iqas_mcformula = \'(?P<mcformula>.*)\';", html)
        # if iqas_mcformulaRe is None:
        #     #return False
        #     return errorcode.LOGIC_ERROR, errormsg.PARAMETER_UNRESOLVED
        # iqas_mcformula = iqas_mcformulaRe.group("mcformula")
        # #print iqas_mcformula
        # logger.debug("iqas_mcformula=" + iqas_mcformula)
        # child = subprocess.Popen(["./app/jsfunc/eval.js"], stdin=subprocess.PIPE, stdout=subprocess.PIPE)
        # iqas_mcvalue = child.communicate(iqas_mcformula)[0]
        # #iqas_mcvalue = "0212634716904157147153110121"
        # #print iqas_mcvalue
        # logger.debug("iqas_mcvalue=" + iqas_mcvalue)
        conn = httplib.HTTPConnection("tracklog.58.com", timeout=10)
        headers = copy.copy(self.headers)
        headers['Host'] = 'tracklog.58.com'
        headers['Referer'] = 'http://post.58.com/' + url_code
        conn.request("GET", "/referrer4.js", headers=headers)
        res = conn.getresponse()
        resHeaders = res.getheaders()
        #print resHeaders
        logger.debug("resHeaders="+str(resHeaders))
        self.setCookies(resHeaders, encode = True)

        '''conn = httplib.HTTPConnection("post.58.com", timeout=10)
        headers = copy.copy(self.headers)
        headers['Host'] = 'post.58.com'
        headers['Referer'] = 'http://post.58.com/' + url_code
        conn.request("GET", "/" + url_code + "/29/s5/", headers = headers)
        res = conn.getresponse()
        resHeaders = res.getheaders()
        logger.debug("resHeaders="+str(resHeaders))'''

        boundaryHeader = '----WebKitFormBoundarykvyRkkPjZTyZguCW'
        # + str(int(random.random() * sys.maxint))
        #str(random.random())
        boundary = '--' + boundaryHeader
        #fd = open('rootPara.json', 'r')
        #rootPara = json.load(fd)
        #fd.close()
        formStr = ""
        vin = self.getVin(vehicle)
        if vin is not None:
            formStr += boundary + "\r\n" + vin
        formStr += boundary + "\r\n" + self.getZimu(externalSpec)
        formStr += boundary + "\r\n" + self.getSpecV('brand', externalSpec['brand']['spell'])
        formStr += boundary + "\r\n" + self.getSpecV('chexi', externalSpec['series']['key'])

        # 车辆类型
        object_type = '1'
        if externalSpec['series'].get('object_type', None) is not None:
            if externalSpec['series']['object_type'].get("v", None) is not None:
                object_type = externalSpec['series']['object_type']['v']
        formStr += boundary + "\r\n" + self.getSpecV('ObjectType', object_type)
        
        # 58有没有model的 key = 0
        if externalSpec['model']['key'] == '0':
            pass
        else:
            formStr += boundary + "\r\n" + self.getSpecV('carchexing', externalSpec['model']['key'])
            formStr += boundary + "\r\n" + self.getSpecV('displacement', self.getDisplacementV(externalSpec, carInfo))
            formStr += boundary + "\r\n" + self.getSpecV('gearbox', externalSpec['summary']['gearbox']['v'])
            ##formStr += boundary + "\r\n" + self.getSpecV('kucheid', externalSpec['model']['kucheid']['v'])
            #formStr += boundary + "\r\n" + self.getSpecV('shangshishijian', externalSpec['model']['shangshishijian']['v'])
            formStr += boundary + "\r\n" + self.getShangshishijian(externalSpec, 'v')
            #formStr += boundary + "\r\n" + self.getSpecV('yczb_cheling', externalSpec['summary']['yczb_cheling']['v'])
            formStr += boundary + "\r\n" + self.getYczb_cheling(externalSpec, 'v')
            #formStr += boundary + "\r\n" + self.getSpecV('yczb_licheng', externalSpec['summary']['yczb_licheng']['v'])
            formStr += boundary + "\r\n" + self.getYczb_licheng(externalSpec, 'v')
        formStr += boundary + "\r\n" + self.getSpecV('madein', externalSpec['vendor']['v'])
        if externalSpec['series']['chexibieming'].get('v', None) is not None:
            formStr += boundary + "\r\n" + self.getChexibieming(externalSpec)
        formStr += boundary + "\r\n" + self.getErscpinpai(externalSpec)
        formStr += boundary + "\r\n" + self.getRundistanceqj(carInfo)
        formStr += boundary + "\r\n" + self.getChelingqj()
        formStr += boundary + "\r\n" + self.getBuytime(carInfo)
        formStr += boundary + "\r\n" + self.getShangpaiyuefen(vehicle_date)
        formStr += boundary + "\r\n" + self.getEmpty('buyfrom')
        formStr += boundary + "\r\n" + self.getString('baoyang', '515673')
        formStr += boundary + "\r\n" + self.getEmpty('yunying')
        formStr += boundary + "\r\n" + self.getString('shiguqk', '515713')
        formStr += boundary + "\r\n" + self.getEmpty('neishi')
        formStr += boundary + "\r\n" + self.getEmpty('syxian')
        formStr += boundary + "\r\n" + self.getEmpty('shouxu')
        formStr += boundary + "\r\n" + self.getCheshenyanse(carInfo)
        formStr += boundary + "\r\n" + self.getChexingyanse(carInfo)
        formStr += boundary + "\r\n" + self.getZbjcfanwei(carInfo)
        formStr += boundary + "\r\n" + self.getPic(photoList)
        formStr += boundary + "\r\n" + self.getPicTag(photoList)
        formStr += boundary + "\r\n" + self.getEmpty('picdesc1')
        formStr += boundary + "\r\n" + self.getEmpty('picdesc2')
        formStr += boundary + "\r\n" + self.getEmpty('picdesc3')
        formStr += boundary + "\r\n" + self.getEmpty('picdesc4')
        formStr += boundary + "\r\n" + self.getEmpty('picdesc5')
        formStr += boundary + "\r\n" + self.getEmpty('picdesc6')
        formStr += boundary + "\r\n" + self.getEmpty('picdesc7')
        formStr += boundary + "\r\n" + self.getEmpty('picdesc8')
        formStr += boundary + "\r\n" + self.getImageLoad()
        formStr += boundary + "\r\n" + self.getRundistance(carInfo)
        formStr += boundary + "\r\n" + self.getMinPrice(carInfo)
        formStr += boundary + "\r\n" + self.getMinPricej(carInfo)
        formStr += boundary + "\r\n" + self.getInstallment(carInfo)

        # 保障车源 - 消费保障等 - 改价
        merchantSubstituteConfig = carInfo.get("merchant_substitute_config", None)

        '''
        if merchantSubstituteConfig is not None:
            consumerGuarantee = self.getConsumerGuarantee(merchantSubstituteConfig)
            if consumerGuarantee is 1:
                formStr += boundary + "\r\n" + self.getDefault('mfghProxy', '1')  #免费过户
                formStr += boundary + "\r\n" + self.getDefault('qtktProxy', '1')  #7天可退
                formStr += boundary + "\r\n" + self.getDefault('qtkt', '1')  #7天可退
        '''
        formStr += boundary + "\r\n" + self.getDefault('mfghProxy', '1')  #免费过户
        formStr += boundary + "\r\n" + self.getDefault('qtktProxy', '1')  #7天可退
        if self.is_integrity_merchant(vehicle, username):
            qtkt = '1'
        else:
            qtkt = '0'
        formStr += boundary + "\r\n" + self.getDefault('qtkt', qtkt)  #7天可退

        formStr += boundary + "\r\n" + self.getTitle(externalSpec, carInfo, vehicle)
        formStr += boundary + "\r\n" + self.getContent(shareJob)
        formStr += boundary + "\r\n" + self.getGoblianxiren(carInfo)
        #formStr += boundary + "\r\n" + self.getFaburen()
        formStr += boundary + "\r\n" + self.getPhone(carInfo)
        formStr += boundary + "\r\n" + self.getIM(carInfo.get("merchant_substitute_config", {}))
        formStr += boundary + "\r\n" + self.getQitadianhua(carInfo.get("merchant_substitute_config", {}))
        formStr += boundary + "\r\n" + self.getCaraddress(merchantSubstituteConfig, vehicle.get("merchant", {}))
        formStr += boundary + "\r\n" + self.getType()
        if externalSpec['model']['key'] == '0':
            pass
        else:
            formStr += boundary + "\r\n" + self.getCspailiang(externalSpec, carInfo)
            formStr += boundary + "\r\n" + self.getBiansuqi(externalSpec, carInfo)
        formStr += boundary + "\r\n" + self.getEmpty('shigumiaoshu')
        '''
        cjshijian   2016|1
        qxshijian   2016|1
        syshijian   2016|1
        '''
        #getTypeDate(name, vehicle_date) edit by yjy (改价)
        formStr += boundary + "\r\n" + self.getTypeDate('cjshijian', vehicle_date)
        formStr += boundary + "\r\n" + self.getTypeDate('qxshijian', vehicle_date)
        formStr += boundary + "\r\n" + self.getTypeDate('syshijian', vehicle_date)

        formStr += boundary + "\r\n" + self.getXinxibianhao(bianhao)
        # 默认行驶证
        formStr += boundary + "\r\n" + drivingLicensePicture
        formStr += boundary + "\r\n" + self.getYczhibao(externalSpec)
        formStr += boundary + "\r\n" + self.getDefault('xbsx', '1')

        #vinstate - 改价
        formStr += boundary + "\r\n" + self.getDefault('vinstate', '1')

        formStr += boundary + "\r\n" + self.getIncludeTransferFee(vehicle, username)
        formStr += boundary + "\r\n" + self.getShangpainianyue(carInfo)
        formStr += boundary + "\r\n" + self.getCateapplyed()
        formStr += boundary + "\r\n" + self.getLocalapplyed(code)
        formStr += boundary + "\r\n" + self.getShifoufufeifabu()
        formStr += boundary + "\r\n" + self.getShifouyishou()
        formStr += boundary + "\r\n" + self.getEscwltv2()
        formStr += boundary + "\r\n" + self.getPaifangbiaozhun()
        formStr += boundary + "\r\n" + self.getWanglintongbieming()
        formStr += boundary + "\r\n" + self.getCanjiapaimai()
        formStr += boundary + "\r\n" + self.getIqasMcresult("")
        formStr += boundary + "\r\n" + self.getCubePostJsonkey()
        formStr += boundary + "\r\n" + self.getHiddenForPara()
        formStr += boundary + "\r\n" + self.getGobquzhi(externalSpec, carInfo, code)
        formStr += boundary + "\r\n" + self.getGobalsokey(externalSpec, carInfo, code)
        formStr += boundary + "\r\n" + self.getFcookie(fcookie)
        formStr += boundary + "\r\n" + self.getHiddenTextBoxJoinValue(externalSpec, carInfo, vehicle)
        formStr += boundary + "\r\n" + self.getXiaobaoOption()
        formStr += boundary + "--"
        if type(formStr == type(u'')):
            formStr = formStr.encode('utf-8')
        #print formStr
        logger.debug("formStr=" + str(formStr))
        conn = httplib.HTTPConnection("post.58.com", timeout=10)
        headers = copy.copy(self.headers)
        headers['Host'] = 'post.58.com'
        headers['Referer'] = 'http://post.58.com/' + url_code + '/29/s5/'
        headers['Content-Type'] = 'multipart/form-data; boundary=' + boundaryHeader
        headers['Content-Length'] = len(formStr)
        headers['Host'] = 'post.58.com'
        headers['Origin'] = 'http://post.58.com'
        postUrl = "/vupdate/" + queryId + "/submit?source=car&rand="+str(random.random())
        #print postUrl
        #print str(headers)
        #return


        conn.request("POST", postUrl, formStr, headers = headers)
        res = conn.getresponse()
        #print json.dumps(headers)
        #print url_code
        print res.status, res.reason
        logger.debug("headers="+json.dumps(headers))
        resHeaders = res.getheaders()
        self.setCookies(resHeaders, encode = True)
        #print resHeaders
        logger.debug("resHeaders=" + str(resHeaders))
        html = self.decodeBody(resHeaders, res.read())
        #zlib.decompress(res.read(), 16+zlib.MAX_WBITS)
        html = html.decode('utf-8')
        conn.close()
        #print "---html---"
        #print html
        logger.debug("---html---\n" + html)
        if html.count('postsuccess') == 0:
            return errorcode.SITE_ERROR, errormsg.SITE_OTHER_ERROR

        # 如果检测是否有跳转
        # if html.count('location.href') > 0:
        #     jumpLocationRe = re.search("location.href = \'(?P<href>.*)\'", html)
        #     locationHref = jumpLocationRe.group('href')
        #     conn = httplib.HTTPConnection("post.58.com", timeout=10)

        #conn = None
        #postsuccess = ""
        headers = copy.copy(self.headers)
        #if not url_code.startswith('v'):
        postsuccessRe = re.search('top\.location\.href = \'(?P<postsuccess>.*)\';', html)
        if postsuccessRe is not None:
            postsuccess = postsuccessRe.group('postsuccess')
            carIdRe = re.search('0/(?P<carId>.*)/\?', postsuccess)
            carId = carIdRe.group('carId')
            logger.debug("postsuccess = " + postsuccess)
            conn = httplib.HTTPConnection("post.58.com", timeout=10)
            headers['Host'] = 'post.58.com'
            headers['Referer'] = 'http://post.58.com/' + url_code + '/29/s5'
        else:
            postsuccessRe = re.search('vip_postsuccess\((?P<postsuccessJson>.*)\)<', html)
            if postsuccessRe is not None:
                postsuccessJson = postsuccessRe.group('postsuccessJson')
                logger.debug("postsuccessJson=" + postsuccessJson)
                postsuccessObj = json.loads(postsuccessJson)
                carId = postsuccessObj['infoid']
                jz_key = postsuccessObj['jz_key']
                postsuccess = "/cheyuanreceiver?infoid=%s&type=1&jzKey=%s&money=0.0&infoState=1"%(carId, jz_key)
                conn = httplib.HTTPConnection("info.vip.58.com", timeout=timeout_58)
                headers['Referer'] = 'http://info.vip.58.com/postcheyuan/?masteriframe=true&displocalid=%s&dispcateid=29&r=0.4967958819988352'%code
            else:
                postsuccessRe = re.search('postsuccess/'+url_code+"/(?P<carId>.*)/\?", html)
                if postsuccessRe is not None:
                # if html.count("postsuccess/" + url_code + "/") > 0:
                #     logger.debug("postsuccess without url return")
                #     print html
                    carId = postsuccessRe.group('carId')
                    cityName = self.city582.getName(cityCode)
                    url = 'http://'+cityName+'.58.com/ershouche/'+carId+"x.shtml"
                    logger.debug("---url---\n" + url)
                    return errorcode.SUCCESS, url
                else:
                    postsuccessRe = re.search('parent\.location\.href = \'(?P<postsuccess>.*)\';', html)
                    if postsuccessRe is not None:
                        postsuccess = postsuccessRe.group('postsuccess')
                        #get html from postSuccessUrl
                        conn = httplib.HTTPConnection("post.58.com", timeout=timeout_58)
                        headers['Host'] = 'post.58.com'
                        headers['Referer'] = 'http://post.58.com/' + url_code + '/29/s5'
                        carId = None
                    else:
                        return errorcode.SITE_ERROR, "url跳转错误"
        conn.request("GET", postsuccess, headers=headers)

        res = conn.getresponse()
        logger.debug("headers=" + json.dumps(headers))
        resHeaders = res.getheaders()
        logger.debug("resHeaders=" + str(resHeaders))
        html = zlib.decompress(res.read(), 16+zlib.MAX_WBITS)
        # html = res.read()
        html = html.decode('utf-8')
        logger.debug("---html---\n" + html)
        cityName = self.city582.getName(cityCode)
        if carId is None:
            carIdRe = re.search('ershouche\/(?P<carId>.*)x.shtml', html)
            carId = carIdRe.group('carId')
        url = 'http://'+cityName+'.58.com/ershouche/'+carId+"x.shtml"
        logger.debug("---url---\n" + url)
        return errorcode.SUCCESS, url

    def getContentVal_finance_58(self, shareJob, Symbol="\r\n", lateral="——"*23):
        externalSpec = shareJob['external_vehicle_spec']
        share_account = shareJob.get("share_account", None)
        model = externalSpec.get('model', None)
        key = model.get('key', None)
        content = ''
        vehicle = shareJob.get('vehicle', None)
        desc = vehicle.get('desc', None)
        detail = desc.get('detail', "")
        website = shareJob.get('share_account').get('website')

        startStyle_RedBigBold = '<span id="comp-paste-div-7602" style="color: red; font-size: 13.5pt; font-weight: bold">'
        startStyle_ReSmallBold = '<span id="comp-paste-div-7602" style="color: red; font-size: 10pt;font-weight: bold">'
        startStyle_ReSmallNormal = '<span id="comp-paste-div-7602" style="color: red; font-size: 10pt;">'
        startStyle_BlackSmallBold = '<span id="comp-paste-div-7602" style="font-size: 10pt; font-weight: bold">'
        startStyle_BlackSmallNormal = '<span id="comp-paste-div-7602" style="font-size: 10pt;">'
        endRedStyle = '</span>'

        merchantDisable = True  # 默认不填写
        vehicleDisable = False  # 默认填写
        globalDisable = False   # 默认填写
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

        content += startStyle_RedBigBold
        content += "可贷款  申请快  利率低"
        content += Symbol + "看车网发现二手好车，大量优质车源，车况靠谱，价格透明"
        content += Symbol + "1张身份证，秒速贷款。"
        content += endRedStyle

        content += startStyle_BlackSmallBold
        content += Symbol*2 + "车辆概况："
        content += endRedStyle

        # 采用商家说明 追加
        if merchantDisable is False:
            description = ""
            description_list = merchant_substitute_config.get('description_list', None)
            if description_list is not None:
                for i in description_list:
                    site = i.get('site', None)
                    if site == 'che168.com':
                        description = i.get('description', None)
                        description = string.replace(description, '\n', Symbol)
            content += Symbol + description

        if vehicleDisable is False:
            # 车况说明，来自bss模板
            if detail != "":
                content += Symbol + detail


        # 统一说明 追加
        if globalDisable is False:
            if share_account.get("account_type", None) == "substitute":
                content += startStyle_BlackSmallBold
                content += Symbol*2 + '值得信赖的专业二手车顾问'
                content += endRedStyle

                content += Symbol + startStyle_ReSmallBold + '[贷款] 月息低至6厘8，只需身份证，超低门槛，秒速贷款。' + endRedStyle
                content += Symbol + '[车况] 208项售前检测，绝无事故车，泡水、火烧车。'
                content += Symbol + '[服务] 免费过户，包办手续，有质保。'

                content += startStyle_ReSmallNormal
                content += Symbol*2 + '我是白户，可以申请车贷么？'
                content += Symbol + '想买个便宜车，贷款怎么办？'
                content += Symbol + '中意的车龄长达八年怎么办？'
                content += Symbol + '我资质非常好，想多多贷款？'
                content += Symbol + '没关系，只要您符合条件，只需一张身份证，其他的我们来做。'
                content += endRedStyle

                content += startStyle_ReSmallBold
                content += Symbol*2 + '不满意？没关系，登陆[看车网] ！更多优质车源供您挑选！'
                content += endRedStyle

                content += Symbol + '或致电看车网，根据您的需求，为您推荐最好最适合的车辆'

                content += Symbol*2 + '在看车网，买车从未如此简单，专业买车顾问全程1对1服务，交易透明，不赚差价'

                content += Symbol*2 + '看车网向您承诺：'
                content += Symbol + '选车：大量优质车源，根据您的需求，推荐最好最适合的车辆。'
                content += Symbol + '车况：208项售前检测，专业评估师把关，呈现真实车况。'
                content += Symbol + '车价：专业买车顾问全程1对1服务，交易透明，不赚差价。'
                content += Symbol + '过户：免费过户，包办手续。'
                content += Symbol + '质保：为8年及15万公里以内的车辆提供超低价格的1年或2万公里保修服务。'
                
                content += startStyle_ReSmallBold
                content += Symbol + '贷款：可分期付款，只需身份证，即可申请，超低月供, 超低月息。'
                content += endRedStyle

        content += startStyle_BlackSmallBold
        content += Symbol + "更多选择，尽在看车网。"
        content += endRedStyle
        content += Symbol*2 + str(vehicle.get('series_number', '')) + "#"
        content += str(vehicle['_id'])

        if "" == content:
            content = u"无车辆说明，请添加至10个字以上"
        return content





