#!/usr/bin/python
# -*- coding: UTF-8 -*-

#####################################
## 在用;
## 按照技术文档来ｐｏｓｔ发车
#####################################


from base import BaseSharer
import errorcode
import errormsg
import httplib
import urllib
import logger
import json
import re
import tz
import time
from urlparse import urlparse
import copy
from StringIO import StringIO
import resize
from decimal import *
from dt8601 import IsoDate
import string

HOST = "open.api.che168.com"

class Che168Sharer(BaseSharer):
    def __init__(self, sessionServer, specServer):
        super(Che168Sharer, self).__init__(sessionServer, specServer)
        self.headers["Referer"] = "http://dealer.che168.com"

    def shareVehicle(self, shareJob):
        publicAccount = self.getAccount(shareJob)
        if len(publicAccount) == 0:
            return errorcode.AUTH_ERROR, errormsg.LOGIN_FAIL

        externalSpec = shareJob.get("external_vehicle_spec", None)
        if externalSpec is None:
            logger.error("external spec missing")
            return errorcode.SPEC_ERROR, errormsg.EXTERNAL_SPEC_EMPTY

        vehicle = shareJob.get("vehicle", None)
        if vehicle is None:
            logger.error("vehicle missing")
            return errorcode.DATA_ERROR, errormsg.VEHICLE_EMPTY

        price =vehicle.get('price', None)
        if price is None:
            logger.error('price missing')
            return errorcode.DATA_ERROR, errormsg.PRICE_EMPTY

        user = vehicle.get("user", None)
        if user is None:
            logger.error("user missing")
            return errorcode.DATA_ERROR, errormsg.USER_EMPTY

        '''
        address = user.get("address", None)
        if address is None:
            logger.error("address missing")
            return errorcode.DATA_ERROR, errormsg.ADDRESS_EMPTY
        '''
        merchant = vehicle.get('merchant', None)
        address = merchant.get('address', None)

        ##组合发车字段
        carinfo = {}
        #车辆唯一标识码(发车时为0): "carid":0,
        carinfo['carid'] = 0

        #品牌id: "brandid": 33,
        brandid = externalSpec['brand']['id']
        carinfo['brandid'] = int(brandid)

        #车系id: "seriesid": 2951,
        seriesid = externalSpec['series']['id']
        carinfo['seriesid'] = int(seriesid)

        #车型id: "productid": 14411,
        productid = externalSpec['model']['id']
        carinfo['productid'] = int(productid)

        #车辆自定义名称: "carname":""
        carname = externalSpec['series']['name'] + ' ' + externalSpec['model']['name']
        carinfo['carname'] = urllib.quote(urllib.quote(carname.encode('utf-8')))

        #TODO:没有排量接口,有车型id会自动识别;没有车型id就需要手填;
        #排量，单位：L，数值字符串，如：1.2: "displacement":"",
        #carinfo['displacement'] = "1.4"

        #变速箱(手动、自动): "gearbox":"",
        spec_details = shareJob['vehicle_spec_detail']['details']
        gearbox = "手动"
        if spec_details[42].count(u"自") > 0 :
            gearbox = "自动"
        carinfo['gearbox'] = urllib.quote(gearbox.encode('utf-8'))

        #是否包含过户费用:"isincludetransferfee":true,
        quoted_price_include_transfer_fee = price.get('quoted_price_include_transfer_fee', True)
        carinfo['isincludetransferfee'] = quoted_price_include_transfer_fee

        #预售价格(单位: 万元):"bookprice":15.5,
        bookprice = 0.0
        price = vehicle.get("price", None)
        if price is not None:
            quotedPrice = price.get("quoted_price", None)
            if quotedPrice is not None:
                bookprice = int(quotedPrice)*1.0/10000
        carinfo['bookprice'] = bookprice

        #是否一口价: "isfixprice":false,
        carinfo['isfixprice'] = False

        #省id: "provinceid":1,
        provinceid = 1
        provinceid = address.get("province_code", None)
        if provinceid is None:
            return errorcode.DATA_ERROR, errormsg.PROVINCE_EMPTY
        carinfo['provinceid'] = int(provinceid)

        #市id "cityid":1,
        cityid = 1
        cityid = address.get("city_code", None)
        if cityid is None:
            return errorcode.DATA_ERROR, errormsg.CITY_EMPTY
        carinfo['cityid'] = int(cityid)

        #行驶里程(单位: 万公里): "drivemileage":3.5,
        drivemileage = 0.1
        summary = vehicle.get("summary",None)
        if summary is None:
            return errorcode.DATA_ERROR, errormsg.VEHICLE_SUMMARY_EMPTY
        drivemileage = summary.get("mileage",None)
        if drivemileage is None:
            return errorcode.DATA_ERROR, errormsg.VEHICLE_SUMMARY_EMPTY
        carinfo['drivemileage'] = int(drivemileage)*1.0/10000

        #车辆用途id: "purposeid":1,
        purpose = summary.get("purpose", None)
        carinfo['purposeid'] = int(self.getPurposeID(purpose))

        #车辆颜色id: "colorid":0,
        color = summary.get("color", None)
        carinfo['colorid'] = int(self.getColorID(color))

        #首次上牌时间: "firstregtime":"2012-1",
        carinfo['firstregtime'] = str(self.getDate("registration_date", shareJob).year) + "-" + str(self.getDate("registration_date", shareJob).month)

        #车辆年审时间: "verifytime":"2012-2",
        carinfo['verifytime'] = str(self.getDate("inspection_date", shareJob).year) + "-" + str(self.getDate("inspection_date", shareJob).month)

        #车船使用税有效时间: "veticaltaxtime":"2012-3",
        carinfo['veticaltaxtime'] = carinfo['verifytime']

        #交强险日期: "insurancedate":"2012-4"
        carinfo['insurancedate'] = carinfo['firstregtime']
        '''
        vehicle_date = vehicle.get("vehicle_date", None)
        if vehicle_date is not None:
            compulsory_insurance_expire_date = vehicle_date.get("compulsory_insurance_expire_date", None)
            if compulsory_insurance_expire_date is not None:
                carinfo['insurancedate'] = compulsory_insurance_expire_date
        '''
        QualityAssDate = 0
        QualityAssMile = 0
        MerchantSubstituteConfig = shareJob.get('merchant_substitute_config', None)
        if MerchantSubstituteConfig is not None:
            merchant_summary = MerchantSubstituteConfig.get('summary', None)
            if merchant_summary is not None:
                QualityAssDate = MerchantSubstituteConfig.get('quality_assurance_time', 6)
                QualityAssMile = MerchantSubstituteConfig.get('quality_assurance_mile', 20000.0)
        #延长质保日期: "qualityassdate": 0 ;月,
        carinfo['qualityassdate'] = int(QualityAssDate)
        #延长质保里程: "qualityassmile ":0;万公里,
        carinfo['qualityassmile'] = QualityAssMile/10000.0

        #TODO:注意：vin码和行驶证照片链接同时有或者同时无 -> 行驶证照片用vin照片替换
        #车源行驶证的图片，1张: "driverlicenseimage":" http://www.autoimg.cn/2scimg/2013/8/19/u_505895724323298.jpg”,
        # summary = externalSpec.get("summary", None)
        # drivingLicenseUrl = summary.get('drivingLicensePicture', None)
        vin_picture_url = vehicle.get("summary").get("vin_picture", None)

        #"vincode": "aaaacxadfadf11334"
        vincode = vehicle.get("vin", None)
        print "vin_picture:", vin_picture_url
        print 'vin:', vincode
        if (vin_picture_url is None) or (vincode is None):
            carinfo['vincode'] = ""
            carinfo['driverlicenseimage'] = ""
        else:
            carinfo['vincode'] = str(vincode)
            carinfo['driverlicenseimage'] = self.uploadLicensePic(vin_picture_url, publicAccount)



        #图片地址, 以英文逗号分割: http://www.autoimg.cn/2scimg/2013/8/19/u_50589572323423174598.jpg ",
        #方法一： 上传图片流

        #方法二：上传地址[待改正，先要上传图片]
        '''
        #存放图片及地址信息session.py
        imgurls = self.getUrlList(vehicle, publicAccount)
        if imgurls is None:
            return errorcode.DATA_ERROR, u"上传图片url出错，请重试"
        carinfo['imgurls'] = imgurls
        #carinfo['imgurls'] = "http://www.autoimg.cn/2scimg/2013/8/19/u_505895724323298.jpg,http://www.autoimg.cn/2scimg/2013/8/19/u_50589572323423174598.jpg "
        '''
        gallery = vehicle.get("gallery", None)
        if gallery is None:
            logger.error("gallery missing")
            return errorcode.DATA_ERROR, errormsg.PHOTO_NOT_ENOUGH
        photoList = self.uploadPics(gallery.get("photos", []), publicAccount)
        carinfo['imgurls'] = photoList

        #商家附言: "usercomment":"测试的数据"
        Symbol="\r\n"
        lateral="——"*23
        carinfo['usercomment'] = urllib.quote(self.getContentVal(shareJob, Symbol, lateral).encode('utf-8'))

        '''
        salesperson = {}
        salesperson['salesid'] = 77789
        salesperson['salesname'] = urllib.quote("销售代表".encode('utf-8'))
        salesperson['salesphone'] = "13711592683"
        salesperson['salesqq'] = "535124082"
        carinfo['salesperson'] = salesperson
        '''
        #销售人员实体类: salesperson
        salesperson = self.getSiteContact(publicAccount)
        if salesperson is None:
            return errorcode.SPEC_ERROR, errormsg.SALEID_EMPTY
        carinfo['salesperson'] = salesperson

        carinfoJson = json.dumps(carinfo)
        logger.debug("carinfoJson:" + str(carinfoJson))

        publicAccount = self.getAccount(shareJob)
        #form = {"_appid": publicAccount["_appid"], "dealerid": publicAccount["dealerid"], "key": publicAccount["key"], "carinfo": carinfo}
        form = "_appid="+publicAccount["_appid"]+"&dealerid=%d"%(publicAccount["dealerid"])+"&key="+publicAccount["key"]+"&carinfo="+str(carinfoJson)

        #开始发车
        (success, msg) = self.postVehicle(form, publicAccount)
        if success:
            logger.debug("post success for che168public")
            return errorcode.SUCCESS, msg
        return errorcode.SITE_ERROR, msg


    ########################################
    #发车
    ########################################
    def postVehicle(self, form, publicAccount):
        #post url='http://open.api.che168.com/v1/car/release.ashx'
        #form = urllib.urlencode(form)
        headers = {"Content-type": "application/x-www-form-urlencoded", "Accept": "text/plain"}
        conn = httplib.HTTPConnection(HOST, timeout=10)
        conn.request("POST", "/v1/car/release.ashx", form, headers)
        res = conn.getresponse()
        status = res.status
        reason = res.reason
        logger.debug("status: " + str(status) + " reason: " + str(reason))
        msg = res.read()
        logger.debug("msg:\t"+str(msg))

        #response msg:
        logger.debug("response msg: "+str(msg))
        pRule = r'^(<!DOCTYPE html>)'
        typeJudge = re.compile(pRule).findall(msg)
        if len(typeJudge) and 200 == status:
            url = ""
            #TODO: get url
            #return True, url
            return True, msg

        if len(typeJudge):
            if 500 == status:
                return False, u"内部服务器错误"

        if msg.count('returncode=500'):
            logger.debug('error:' + str(msg))
            return False, u'500错误'

        msgJson = json.JSONDecoder().decode(msg)
        returnCode = msgJson.get("returncode", "1")
        returnMsg = msgJson.get("message", "noMsg")
        result = msgJson.get("result", "noMsg")
        if 0 == returnCode:
            carid = result.get("carid", None)
            url = ""
            if carid is not None:
                url = "http://www.che168.com/dealer/" + str(publicAccount["dealerid"]) + "/" + str(carid) + ".html"
            return True, url
        if 1 == returnCode:
            logger.debug("post error!!! msg" + str(returnMsg))
        else:
            logger.debug("post vehicle error!!!" + str(returnCode) + ":" + str(returnMsg))
        logger.debug('error:' + str(msg))
        return False, returnMsg


    ########################################
    #已售【下架】
    ########################################
    '''
    对于che168，目前的下架功能是设置为已售，且已售价格为显示时的价格
    '''
    #post http://open.api.che168.com/v1/car/setsaled.ashx
    def removeVehicle(self, shareJob):
        #get url: www.che168.com/dealer/85822/4355371.html
        #对于有两个url的，取extra
        publicAccount = self.getAccount(shareJob)
        if len(publicAccount) == 0:
            return errorcode.AUTH_ERROR, errormsg.LOGIN_FAIL

        share_job_url = shareJob.get("extra", '')
        if str(share_job_url)  == '':
            share_job_url = shareJob.get("url", None)
            if share_job_url is None:
                share_job_url = ""
        #数据库中有列表型url
        if type(share_job_url) == type([]):
            if len(share_job_url) == 0:
                share_job_url = ""
            else:
                share_job_url = share_job_url[0]

        if share_job_url == "":
            return errorcode.DATA_ERROR, errormsg.VEHICLE_URL_EMPTY

        pRule = r'\d{7,}'
        carid = re.compile(pRule).findall(share_job_url)
        if len(carid) == 0:
            logger.debug("get url failed in removeVehicle!")
            return errorcode.DATA_ERROR, errormsg.VEHICLE_REMOVE_FAIL
        carid = int(carid[0])
        #end of get url!

        #get selledprice
        vehicle = shareJob.get("vehicle", None)
        if vehicle is None:
            return errorcode.LOGIC_ERROR, errormsg.VEHICLE_EMPTY
        price = vehicle.get("price", None)
        if price is None:
            return errorcode.DATA_ERROR, errormsg.VEHICLE_REMOVE_FAIL
        quoted_price = price.get("quoted_price", None)
        if quoted_price is None:
            return errorcode.DATA_ERROR, errormsg.VEHICLE_REMOVE_FAIL

        selledprice = int(quoted_price)*1.0/10000
        #end of get selledprice!

        form = "_appid="+publicAccount["_appid"]+"&dealerid=%d"%(publicAccount["dealerid"])+"&key="+publicAccount["key"]
        form += "&carid=%d"%(carid)
        form += "&selledprice=%f"%(selledprice)

        headers = {"Content-type": "application/x-www-form-urlencoded", "Accept": "text/plain"}
        conn = httplib.HTTPConnection(HOST, timeout=10)
        conn.request("POST", "/v1/car/setsaled.ashx", form, headers)
        res = conn.getresponse()
        status = res.status
        reason = res.reason
        logger.debug("status: " + str(status) + " reason: " + str(reason))
        msg = res.read()
        logger.debug("msg:\t"+str(msg))

        #response msg:
        msgJson = json.JSONDecoder().decode(msg)
        returnCode = msgJson.get("returncode", "1")
        returnMsg = msgJson.get("message", "noMsg")
        if 0 == returnCode:
            return errorcode.SUCCESS, share_job_url
        if 1 == returnCode:
            logger.debug("post error!!! msg" + str(returnMsg))
        else:
            logger.debug("post vehicle error!!!" + str(returnCode) + ":" + str(returnMsg))
        return errorcode.SITE_ERROR, returnMsg


    ########################################
    #改价
    ########################################
    def updateVehicle(self, shareJob):
        publicAccount = self.getAccount(shareJob)
        if len(publicAccount) == 0:
            return errorcode.AUTH_ERROR, errormsg.LOGIN_FAIL

        externalSpec = shareJob.get("external_vehicle_spec", None)
        if externalSpec is None:
            logger.error("external spec missing")
            return errorcode.SPEC_ERROR, errormsg.EXTERNAL_SPEC_EMPTY

        vehicle = shareJob.get("vehicle", None)
        if vehicle is None:
            logger.error("vehicle missing")
            return errorcode.DATA_ERROR, errormsg.VEHICLE_EMPTY

        price =vehicle.get('price', None)
        if price is None:
            logger.error('price missing')
            return errorcode.DATA_ERROR, errormsg.PRICE_EMPTY

        user = vehicle.get("user", None)
        if user is None:
            logger.error("user missing")
            return errorcode.DATA_ERROR, errormsg.USER_EMPTY

        '''
        address = user.get("address", None)
        if address is None:
            logger.error("address missing")
            return errorcode.DATA_ERROR, errormsg.ADDRESS_EMPTY
        '''
        merchant = vehicle.get('merchant', None)
        address = merchant.get('address', None)

        url = shareJob.get("url", None)
        if url is None:
            logger.error("url missing")
            return errorcode.DATA_ERROR, errormsg.VEHICLE_URL_EMPTY

        ##组合发车字段
        carinfo = {}
        #车辆唯一标识码(发车时为0): "carid":0,
        pRule = r'\d{7,}'
        carid = re.compile(pRule).findall(url)
        if len(carid) == 0:
            return errorcode.DATA_ERROR, errormsg.VEHICLE_URL_EMPTY
        carinfo['carid'] = int(carid[0])

        carinfo['view'] = 0

        #品牌id: "brandid": 33,
        brandid = externalSpec['brand']['id']
        carinfo['brandid'] = int(brandid)

        #车系id: "seriesid": 2951,
        seriesid = externalSpec['series']['id']
        carinfo['seriesid'] = int(seriesid)

        #车型id: "productid": 14411,
        productid = externalSpec['model']['id']
        carinfo['productid'] = int(productid)

        #车辆自定义名称: "carname":""
        carname = externalSpec['series']['name'] + ' ' + externalSpec['model']['name']
        carinfo['carname'] = urllib.quote(urllib.quote(carname.encode('utf-8')))

        #TODO:没有排量接口,有车型id会自动识别;没有车型id就需要手填;
        #排量，单位：L，数值字符串，如：1.2: "displacement":"",
        carinfo['displacement'] = "1.4"

        #变速箱(手动、自动): "gearbox":"",
        spec_details = shareJob['vehicle_spec_detail']['details']
        gearbox = "手动"
        if spec_details[42].count(u"自") > 0 :
            gearbox = "自动"
        carinfo['gearbox'] = urllib.quote(gearbox.encode('utf-8'))

        #是否包含过户费用:"isincludetransferfee":true,
        quoted_price_include_transfer_fee = price.get('quoted_price_include_transfer_fee', True)
        carinfo['isincludetransferfee'] = quoted_price_include_transfer_fee

        #预售价格(单位: 万元):"bookprice":15.5,
        bookprice = 0.0
        price = vehicle.get("price", None)
        if price is not None:
            quotedPrice = price.get("quoted_price", None)
            if quotedPrice is not None:
                bookprice = int(quotedPrice)*1.0/10000
        carinfo['bookprice'] = bookprice

        #是否一口价: "isfixprice":false,
        carinfo['isfixprice'] = False

        #省id: "provinceid":1,
        provinceid = 1
        provinceid = address.get("province_code", None)
        if provinceid is None:
            return errorcode.DATA_ERROR, errormsg.PROVINCE_EMPTY
        carinfo['provinceid'] = int(provinceid)

        #市id "cityid":1,
        cityid = 1
        cityid = address.get("city_code", None)
        if cityid is None:
            return errorcode.DATA_ERROR, errormsg.CITY_EMPTY
        carinfo['cityid'] = int(cityid)

        #行驶里程(单位: 万公里): "drivemileage":3.5,
        drivemileage = 0.1
        summary = vehicle.get("summary",None)
        if summary is None:
            return errorcode.DATA_ERROR, errormsg.VEHICLE_SUMMARY_EMPTY
        drivemileage = summary.get("mileage",None)
        if drivemileage is None:
            return errorcode.DATA_ERROR, errormsg.VEHICLE_SUMMARY_EMPTY
        carinfo['drivemileage'] = int(drivemileage)*1.0/10000

        #车辆用途id: "purposeid":1,
        purpose = summary.get("purpose", None)
        carinfo['purposeid'] = int(self.getPurposeID(purpose))

        #车辆颜色id: "colorid":0,
        color = summary.get("color", None)
        carinfo['colorid'] = int(self.getColorID(color))

        #首次上牌时间: "firstregtime":"2012-1",
        carinfo['firstregtime'] = str(self.getDate("registration_date", shareJob).year) + "-" + str(self.getDate("registration_date", shareJob).month)

        #车辆年审时间: "verifytime":"2012-2",
        carinfo['verifytime'] = str(self.getDate("inspection_date", shareJob).year) + "-" + str(self.getDate("inspection_date", shareJob).month)

        #车船使用税有效时间: "veticaltaxtime":"2012-3",
        carinfo['veticaltaxtime'] = carinfo['verifytime']

        #交强险日期: "insurancedate":"2012-4"
        carinfo['insurancedate'] = carinfo['firstregtime']
        '''
        vehicle_date = vehicle.get("vehicle_date", None)
        if vehicle_date is not None:
            compulsory_insurance_expire_date = vehicle_date.get("compulsory_insurance_expire_date", None)
            if compulsory_insurance_expire_date is not None:
                carinfo['insurancedate'] = compulsory_insurance_expire_date
        '''
        QualityAssDate = 0
        QualityAssMile = 0
        MerchantSubstituteConfig = shareJob.get('merchant_substitute_config', None)
        if MerchantSubstituteConfig is not None:
            merchant_summary = MerchantSubstituteConfig.get('summary', None)
            if merchant_summary is not None:
                QualityAssDate = MerchantSubstituteConfig.get('quality_assurance_time', 6)
                QualityAssMile = MerchantSubstituteConfig.get('quality_assurance_mile', 20000.0)
        #延长质保日期: "qualityassdate": 0 ;月,
        carinfo['qualityassdate'] = int(QualityAssDate)
        #延长质保里程: "qualityassmile ":0;万公里,
        carinfo['qualityassmile'] = QualityAssMile/10000.0


        #TODO:注意：vin码和行驶证照片链接同时有或者同时无 -> 行驶证照片用vin照片替换
        #车源行驶证的图片，1张: "driverlicenseimage":" http://www.autoimg.cn/2scimg/2013/8/19/u_505895724323298.jpg”,
        # summary = externalSpec.get("summary", None)
        # drivingLicenseUrl = summary.get('drivingLicensePicture', None)
        vin_picture_url = vehicle.get("summary").get("vin_picture", None)

        #"vincode": "aaaacxadfadf11334"
        vincode = vehicle.get("vin", None)
        print "vin_picture:", vin_picture_url
        print 'vin:', vincode
        if (vin_picture_url is None) or (vincode is None):
            carinfo['vincode'] = ""
            carinfo['driverlicenseimage'] = ""
        else:
            carinfo['vincode'] = str(vincode)
            carinfo['driverlicenseimage'] = self.uploadLicensePic(vin_picture_url, publicAccount)


        #图片地址, 以英文逗号分割: http://www.autoimg.cn/2scimg/2013/8/19/u_50589572323423174598.jpg ",
        #方法一： 上传图片流


        #方法二：上传地址[待改正，先要上传图片]
        '''
        #存放图片及地址信息session.py
        imgurls = self.getUrlList(vehicle, publicAccount)
        if imgurls is None:
            return errorcode.DATA_ERROR, u"上传图片url出错，请重试"
        carinfo['imgurls'] = imgurls
        #carinfo['imgurls'] = "http://www.autoimg.cn/2scimg/2013/8/19/u_505895724323298.jpg,http://www.autoimg.cn/2scimg/2013/8/19/u_50589572323423174598.jpg "
        '''
        gallery = vehicle.get("gallery", None)
        if gallery is None:
            logger.error("gallery missing")
            return errorcode.DATA_ERROR, errormsg.PHOTO_NOT_ENOUGH
        photoList = self.uploadPics(gallery.get("photos", []), publicAccount)
        carinfo['imgurls'] = photoList

        #商家附言: "usercomment":"测试的数据"
        Symbol="\r\n"
        lateral="——"*23
        carinfo['usercomment'] = urllib.quote(self.getContentVal(shareJob, Symbol, lateral).encode('utf-8'))

        #销售人员实体类: salesperson
        salesperson = self.getSiteContact(publicAccount)
        if salesperson is None:
            return errorcode.SPEC_ERROR, errormsg.SALEID_EMPTY
        carinfo['salesperson'] = salesperson

        carinfoJson = json.dumps(carinfo)
        logger.debug("carinfoJson:" + str(carinfoJson))

        #form = {"_appid": publicAccount["_appid"], "dealerid": publicAccount["dealerid"], "key": publicAccount["key"], "carinfo": carinfo}
        form = "_appid="+publicAccount["_appid"]+"&dealerid=%d"%(publicAccount["dealerid"])+"&key="+publicAccount["key"]+"&carinfo="+str(carinfoJson)

        #开始改价
        (success, msg) = self.postUpdateVehicle(form, publicAccount)
        if success:
            logger.debug("post success for che168public")
            return errorcode.SUCCESS, msg
        return errorcode.SITE_ERROR, msg

    def postUpdateVehicle(self, form, publicAccount):
        #post url='http://open.api.che168.com/v1/car/release.ashx'
        #form = urllib.urlencode(form)
        headers = {"Content-type": "application/x-www-form-urlencoded", "Accept": "text/plain"}
        conn = httplib.HTTPConnection(HOST, timeout=10)
        conn.request("POST", "/v1/car/edit.ashx", form, headers)
        res = conn.getresponse()
        status = res.status
        reason = res.reason
        logger.debug("status: " + str(status) + " reason: " + str(reason))
        msg = res.read()
        logger.debug("msg:\t"+str(msg))

        pRule = r'^(<!DOCTYPE html>)'
        typeJudge = re.compile(pRule).findall(msg)
        if len(typeJudge) and 200 == status:
            url = ""
            #TODO: get url
            #return True, url
            return True, msg

        if len(typeJudge):
            if 500 == status:
                return False, u"内部服务器错误"

        msgJson = json.JSONDecoder().decode(msg)
        returnCode = msgJson.get("returncode", "1")
        returnMsg = msgJson.get("message", "noMsg")
        result = msgJson.get("result", "noMsg")
        if 0 == returnCode:
            carid = result.get("carid", None)
            url = ""
            if carid is not None:
                url = "http://www.che168.com/dealer/" + str(publicAccount["dealerid"]) + "/" + str(carid) + ".html"
            return True, url
        if 1 == returnCode:
            logger.debug("post error!!! msg" + str(returnMsg))
        else:
            logger.debug("post vehicle error!!!" + str(returnCode) + ":" + str(returnMsg))
        return False, returnMsg


    @staticmethod
    def getAccount(sharejob):
        publicAccount = {}
        share_account = sharejob.get("share_account", None)
        if share_account is None:
            return publicAccount

        username = share_account.get("username", None)
        if username is None:
            return username

        account_dict = {
            # 北京110100、石家庄130100、成都510100、佛山440600、南京320100
            "110100": [147591, "gJx1qlcPW/J6heXOEGg06+S8QXUZVgWNNEl5CH7rjeX9ioTBXED+iXyyqtcWc1GG"],
            "130100": [183830, "FoitwdBs6fpnjthqYIPfzvYDr7THM0wefS57Bekjl6vLxW7Ahm5tQSBnU/LYuUij"],
            "510100": [216812, "qMxTVtR3DKqLPKuSHG5QGC9kGD/+unv1ZFbWHRGN062h9hlkrf3nx6LJzNjuq7oX"],
            "440600": [216822, "bnBBRbOM8WFg4mRK0BNEomGxpujdpof4XEPj3qEF9rrjpxdpqArZKZWfkqX9LPqx"],
            "320100": [216816, "frWN+LGGz1k9GHR/x/fEQVP/DdHgaJmSv+Dq05vKkVqnXOLDdfps6QGsK41qSbRY"],
            # 深圳440300、苏州320500、武汉420100、西安610100、郑州410100
            "440300": [216820, "V+5qUT0F3QnGtS8+ji7tpUGQMY+1GB+dd8kmuO24XgFqoYqqegjveaY+BdEZ+3ma"],
            "320500": [216814, "TxALZkwOdNOaEsrDdwwNQeFyN05Niyhi9vy6tnE5VovwvoIVmaYRNrpR96pkrwwm"],
            "420100": [216823, "Dc6SA0rpTL9pperxn46RP66vmNGWZJ+0NcgITFgPDGftaaIieWRAPkxmkKn9mVJs"],
            "610100": [216818, "TnxwhZEaDQTmDdRzweJQ8TM2+99PifaokrbBoL90QaiWNLxYZiw4sZilEsE/t8KC"],
            "410100": [216824, "AIr0w0foApXoTfWyi8lA2F5EdzI7N5fRzeCOAPwKn9zHZtLFy09gkI7C0MriKr3p"],
            # 重庆500100、长沙430100、南宁450100、福州350100、济南370100
            "500100": [216813, "RwGiiBN3bYKmzHjV1yL9vcfAcdmFkwr2pqvnfq87UbDkuUBVjsJe0KRKs03FJamp"],
            "430100": [231288, "PwYKjBsOellcpblfjuHfEOjvuGTasBx26LLgWCWuc6S+jDdwhjeTn6ATDFeRUfTI"],
            "450100": [231286, "hTgkhBW9TB6PE8X1E5S8NhFak/0xZ6OruO50OqbY9PZcZQfo9lN7dthsur1WKMR+"],
            "350100": [231283, "Uo1CVpzwX6dNUOyw2TGgoZD2DjzahcemjJlLMwBRCrHUCQqiUy1Gyd/EXA1Tfgg3"],
            "370100": [231285, "F6Vs8igo4CsXpBHFtsxuoIk+jyYOHsWwZ0ZiKgCA8MSQhqV6Zr2c+yV6VU6AoojO"],
            # 合肥340100、天津120100、东莞441900、哈尔滨230100、杭州330100
            "340100": [231566, "sbdMlUb76bWkAAFlkR4ZWTktjREodLjYap4K00yJLaZ1VUu46X4hbjrSUpHXqSfI"],
            "120100": [232343, "tR3fdXFnK9BzW+YyIOYCNJobAi3EE4+jkNLGmxzy5qpNNrpQOwQxhQ/ykVILlDTS"],
            "441900": [233157, "iqy42MTIcTMqhhSNG1XRYnHWmrMKju5ud+hMqaYVX+UD5G9ApgpleEwP2A0CXNDv"],
            "230100": [233964, "uGnAti1KBbn7SjgIUnnNOuskHe2wIvctMJweGXV0JPZMS1Z+GasetlXgh3GcHYU9"],
            "330100": [233966, "fkdLW9eSXbmXW9BVVDPnr5fFBMh1MVO+7RfVy0PDtnmb7klezgPFETO6FPLbby4u"],
            # 长春220100、温州330300、大连210200、沈阳210200、无锡320200
            "220100": [233968, "qToJP/NADvck6gcqvKYbe7X/rrPm2FdyZ0Tq+Aoj8Y9sEciKPCAP6d577udcAKBt"],
            "330300": [233969, "6N6CvXB+E41t7OGxgRD61ZVyJ4x0UB7zXEq8WMIc4hGAy51e2TNykB1JoV6bTYBE"],
            "210200": [233967, "1u65LjOWZPaBAa8mugxPtAf4cGsu1eR8X5n1kgWngRL5Tv0p1DqzjfdPO8ty5e61"],
            "210100": [233963, "usFSkDKc1j4qj9wpWqO0kvIMg+by+yvDX4aIKtXdJgCRd37srWX1Sl4rB33Hcl/3"],
            "320200": [233962, "PfaHKokf6FmVW0zkyykXWbAphJiIoJbimO4vQ59F3RlUwhP/4uAPubcNg20SLp0U"],
        }

        try:
            city_code = sharejob.get('vehicle', None).get('merchant', None).get('address', None).get('city_code', None)
        except:
            return {}

        if city_code is None:
            return {}

        publicAccount = {
                "_appid": urllib.quote("kkc"),
                "dealerid": account_dict[str(city_code)][0],
                "key": urllib.quote(account_dict[str(city_code)][1])
        }

        return publicAccount

    #id":1,"use":"家用"},{"id":2,"use":"运营转私人"},{"id":3,"use":"单位用车"
    @staticmethod
    def getPurposeID(purpose):
        purposeid = 1
        if purpose == "非运营" :
            purposeid = 1
        if purpose == "非运营租赁" :
            purposeid = 1
        if purpose == "运营" :
            purposeid = 1
        return purposeid

    '''
    "result":{"colorlist":[{"id":1,"color":"黑色"},{"id":2,"color":"白色"},
    {"id":3,"color":"银灰色"},{"id":4,"color":"深灰色"},{"id":5,"color":"红色"},{"id":6,"color":"蓝色"},{"id":7,"color":"绿色"},
    {"id":8,"color":"黄色"},{"id":9,"color":"香槟色"},{"id":10,"color":"紫色"},{"id":11,"color":"其他"}]}}
    '''
    @staticmethod
    def getColorID(color):
        colorCode = 11
        colorTable = {"black": 1, "white": 2, "red": 5, "yellow": 8,
                      "blue": 6, "green": 7, "purple": 10, "silver": 3, "grey": 4,
                      "champagne": 9, "other": 11}
        colorCode = colorTable.get(color, 11)
        return colorCode

    @staticmethod
    def getDate(dateType, shareJob):
        d = IsoDate.from_iso_string('2014-06-01T00:00:00.000+08:00')
        vehicle = shareJob.get("vehicle", None)
        if vehicle is not None:
            vehicleDate = vehicle.get('vehicle_date', None)
            if vehicleDate is not None:
                if "registration_date" == dateType:
                    returnDate = vehicleDate.get('registration_date', None)
                    if returnDate is not None:
                        # d = IsoDate.from_iso_string(registrationDate)
                        d = returnDate.astimezone(tz.HKT)
                if "inspection_date" == dateType:
                    returnDate = vehicleDate.get('inspection_date', None)
                    if returnDate is not None:
                        d = returnDate.astimezone(tz.HKT)
                    else:
                        returnDate = vehicleDate.get('registration_date', None)
                        d = returnDate.astimezone(tz.HKT)
        return d

    @staticmethod
    def getSiteContact(publicAccount):
        form = "_appid="+publicAccount["_appid"]+"&dealerid="+str(publicAccount["dealerid"])+"&key="+publicAccount["key"]
        # http://open.api.che168.com/v1/dealer/getsales.ashx
        headers = {"Content-type": "application/x-www-form-urlencoded", "Accept": "text/plain"}
        conn = httplib.HTTPConnection(HOST, timeout=10)
        conn.request("GET", "/v1/dealer/getsales.ashx", form, headers)
        res = conn.getresponse()
        status = res.status
        msg = res.read()
        logger.debug("msg:\t"+str(msg))

        #debug msg
        logger.debug("type:"+str(type(msg)))
        if msg is None:
            logger.debug("get salelist error!")
            return None
        if 200 == status:
            salesDict = json.loads(msg)
            if salesDict.has_key('result'):
                result = salesDict['result']
                saleperson = result['saleslist'][0]         #str
                if saleperson is not None:
                    return saleperson
            elif salesDict.has_key('message'):
                return None

        return None

    def uploadLicensePic(self, drivingLicenseUrl, publicAccount):
        photo_list = []
        o = urlparse(drivingLicenseUrl)
        host = o.netloc
        uri = o.path

        upload = self.sessionServer.getUpload('che168', uri)
        logger.debug('--upload-- \n' + str(upload))

        img = ""
        if upload is not None:
            #convert string from unicode to dict:
            #str
            uploadStr = json.dumps(upload)
            #delete /
            uploadStr_1 = uploadStr.replace("\\", "")
            #delete " for head and tail
            uploadStr_2 = uploadStr_1.strip("\"")
            #todo: unicode 怎么转 string
            res = json.loads(uploadStr_2)
            img = res['result']['img']
        else:
            #上传行驶证
            (img, res) = self.uploadPicContent(drivingLicenseUrl, photo_list, publicAccount, 30)
            if (res != "") and (res is not None):
                logger.debug(str(res))
                self.sessionServer.setUpload('che168', uri, json.dumps(res))

        if (res != "") and (res is not None):
            photo_list.append(img)
        photoStr = ",".join(photo_list)
        return photoStr


    def uploadPics(self, photos, publicAccount):
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

            img = ""
            if upload is not None:
                #convert string from unicode to dict:
                #str
                uploadStr = json.dumps(upload)
                #delete /
                uploadStr_1 = uploadStr.replace("\\", "")
                #delete " for head and tail
                uploadStr_2 = uploadStr_1.strip("\"")
                #todo: unicode 怎么转 string
                res = json.loads(uploadStr_2)
                img = res['result']['img']
            else:
                (img, res) = self.uploadPicContent(url, photo_list, publicAccount, 1)
                if (res != "") and (res is not None):
                    logger.debug(str(res))
                    self.sessionServer.setUpload('che168', uri, json.dumps(res))

            if (res != "") and (res is not None):
                photo_list.append(img)
        photoStr = ",".join(photo_list)
        return photoStr

    def uploadPicContent(self, url, photo_list, publicAccount, picType):
        #上传照片：
        form = "apiURL=http://"+HOST+"/V1/car/uploadimagebyurl.ashx"
        form += "&_appid="+publicAccount["_appid"]
        form += "&dealerid="+str(publicAccount["dealerid"])
        form += "&key="+publicAccount["key"]
        #picType 1,为车辆图片；30,为行驶证图片
        if 1 == picType:
            if 0 == len(photo_list):
                form += "&imgurl="+url+"&imgtype="+str(1)
            else:
                form += "&imgurl="+url+"&imgtype="+str(2)
        else:
            form += "&imgurl="+url+"&imgtype="+str(30)

        headers = {"Content-type": "application/x-www-form-urlencoded", "Accept": "text/plain"}
        time.sleep(0.5)
        conn = httplib.HTTPConnection(HOST, timeout=10)
        conn.request("POST", "/v1/car/uploadimagebyurl.ashx", form, headers)
        res = conn.getresponse()
        status = res.status
        msg = res.read()
        if 200 == status:
            msgDict = json.loads(msg)
            if msgDict is None:
                return None
            returncode = msgDict["returncode"]
            if returncode != 0:
                returnmsg = msgDict["message"]
                logger.debug(u"网站错误:\t"+returnmsg)
                return "", ""
            else:
                img = msgDict['result']['img']
            logger.debug("url:"+str(img))
            return img, msg
        return "", ""
