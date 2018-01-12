#!python-env/bin/python
# -*- coding: UTF-8 -*-

__author__ = 'jesse'

import re
import json
import errorcode
import errormsg
from cityTaoche import CityTaoche
import logger
from base import BaseSharer
from suds.client import Client
import string
import time
import urllib2

import sys

reload(sys)
if sys.stdout.encoding is None:
    import codecs

    writer = codecs.getwriter("utf-8")
    sys.stdout = writer(sys.stdout)

#看车帮api账号
ApiAccount = {
    'userName': 'kanchePlatForm',
    'secretkey': '5987E9595699774F338A'
}

webServiceUrl = 'http://svc.taoche.cn/PlatformCarSourceService.asmx?WSDL'

# 保障车源城市
ensured_city_list = ['510100', '420100']

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

    def md5(self, str):
        import hashlib
        import types
        if type(str) is types.StringType:
            m = hashlib.md5()
            m.update(str)
            return m.hexdigest()
        else:
            return ''

    def getColor(self, color):
        colorCode = u"黑色"
        colorTable = {"black": u"黑色", "white": u"白色", "red": u"红色", "yellow": u"黄色", "multi": u"多彩色", "orange": u"橙色",
                      "brown": u"咖啡色", "blue": u"蓝色", "green": u"绿色", "purple": u"紫色", "silver": u"银灰色", "grey": u"深灰色",
                      "champagne": u"香槟色", "other": u"其它"}
        colorCode = colorTable.get(color, u"黑色")
        return colorCode

    def getInterior(self, vehicle):
        interior = vehicle.get("summary").get("interior", None)
        interiorString = u'深'
        if interior is None:
            logger.error("interior missing")
            return interiorString
            # return errorcode.DATA_ERROR, ""
        else:
            if interior.count(u'浅') or interior.count(u'light'):
                interiorString = u'浅'
            elif interior.count(u'深') or interior.count(u'dark'):
                interiorString = u'深'
            else:
                interiorString = u'深'

        logger.debug("interior=" + interiorString)
        return interiorString

    def getPicList(self, vehicle):
        picList = []
        Separator = '|,|'
        photos = vehicle.get('gallery', None).get('photos', None)
        for photo in photos:
            if len(picList) == 20:
                continue
            url = photo.get('url', '')
            picList.append(url)

        picListStr = Separator.join(picList)
        return picListStr

    def getChkImageList(self):
        Separator = '|,|'
        checkImgList = ['http://kanche.oss-cn-qingdao.aliyuncs.com/%E5%8F%91%E8%BD%A6%E6%9C%8D%E5%8A%A1/%E5%B1%8F%E5%B9%95%E5%BF%AB%E7%85%A7%202015-11-09%2019.34.53.png',
                       'http://kanche.oss-cn-qingdao.aliyuncs.com/%E5%8F%91%E8%BD%A6%E6%9C%8D%E5%8A%A1/%E5%B1%8F%E5%B9%95%E5%BF%AB%E7%85%A7%202015-11-09%2019.35.14.png',
                       'http://kanche.oss-cn-qingdao.aliyuncs.com/%E5%8F%91%E8%BD%A6%E6%9C%8D%E5%8A%A1/%E5%B1%8F%E5%B9%95%E5%BF%AB%E7%85%A7%202015-11-09%2019.35.30.png',
                       'http://kanche.oss-cn-qingdao.aliyuncs.com/%E5%8F%91%E8%BD%A6%E6%9C%8D%E5%8A%A1/%E5%B1%8F%E5%B9%95%E5%BF%AB%E7%85%A7%202015-11-09%2019.35.30.png',
                       'http://kanche.oss-cn-qingdao.aliyuncs.com/%E5%8F%91%E8%BD%A6%E6%9C%8D%E5%8A%A1/%E5%B1%8F%E5%B9%95%E5%BF%AB%E7%85%A7%202015-11-09%2019.35.30.png']
        checkImgListStr = Separator.join(checkImgList)
        return checkImgListStr

    def ShowCarSourceV2(self, shareJob, dealerCode, carSourceID):
        logger.debug('ShowCarSourceV2')
        userName = ApiAccount['userName']
        _secretkey = ApiAccount['secretkey']
        #密码为carSourceID加淘车提供的secretkey所组成字符串的MD5值
        pwd = self.md5(carSourceID + _secretkey)

        externalVehicleSpec = shareJob.get('external_vehicle_spec', None)
        CarTypeID = str(externalVehicleSpec.get('model', None).get('id', None))

        vehicleSpecDetail = shareJob.get('vehicle_spec_detail', None)
        details = vehicleSpecDetail.get('details', None)
        Exhaust = str(details[23])

        GearBoxType = externalVehicleSpec.get('summary', None).get('gear', None)
        if GearBoxType is None:
            GearBoxType = vehicleSpecDetail.get('details', None)[42]

        vehicle = shareJob.get('vehicle', None)
        vehicleSummary = vehicle.get('summary', None)
        DrivingMileage = str(int(vehicleSummary.get('mileage', '')))

        color = vehicleSummary.get('color', None)
        Color = self.getColor(color)

        FirstCardTime = vehicle.get('vehicle_date', None).get('registration_date', None)
        FirstCardDate = str(FirstCardTime)[:10]

        InsuranceExpireTime = vehicle.get('vehicle_date').get('inspection_date', None)
        InsuranceExpireDate = str(InsuranceExpireTime)[:10]

        merchantCity = vehicle.get('merchant', None).get('address', None).get('city_name', None)

        MaintainRecord = '1'
        ifMaintenance = vehicleSummary.get('maintenance', True)
        if ifMaintenance:
            MaintainRecord = '1'
        else:
            MaintainRecord = '0'

        vin = vehicle.get('vin', None)
        if vin is None:
            vinCode = ''
        else:
            VinCode = str(vin)

        # Symbol = "\r\n"
        Symbol = "<br>"
        lateral = "——"*23
        if self.loanable(vehicle):
            content_val = self.getContentVal_finance(shareJob, Symbol, lateral)
        else:
            content_val = self.getContentVal(shareJob, Symbol, lateral)
        StateDescription = content_val[:1000]

        price = vehicle.get('price', None).get('quoted_price', None)
        DisplayPrice = str(round(float(price)/10000, 2))

        IsIncTransfer = '1'
        ifIncTransfer = vehicle.get('price', None).get('quoted_price_include_transfer_fee', True)
        if not ifIncTransfer:
            IsIncTransfer = '0'

        InnerColor = self.getInterior(vehicle)

        (ContactName, ContactTel) = self.getContact(shareJob)

        #taoche
        if str(ContactTel).startswith('400'):
            ContactTel = ''

        #行驶证图片：没有就用vin照片
        DriveLicensePic = vehicleSummary.get('driving_license_picture', '')

        #vin图片
        summary = vehicle.get('summary', None)
        vin_picture = summary.get('vin_picture', '')
        if DriveLicensePic == '' or DriveLicensePic is None:
            DriveLicensePic = str(vin_picture)
        else:
            DriveLicensePic = str(DriveLicensePic)

        merchantCityCode = vehicle.get('merchant', None).get('address', None).get('city_code', None)
        if str(merchantCityCode) in ensured_city_list and self.isEnsuredVehicle(shareJob):
            logger.debug('ensured vehicle')
            #是否保障车源:是
            IsWarranty = '1'
            #保障车质检报告图片
            chkImageList = (self.getChkImageList()).encode('utf-8')

        else:
            logger.debug('not ensured vehicle')
            #是否保障车源:否
            IsWarranty = '0'
            chkImageList = ''

        #车源JSON信息
        carSource = {
            "CarTypeID": CarTypeID,
            "CarTypeName": u"车型名称",
            "Exhaust": Exhaust,
            "GearBoxType": GearBoxType.encode('utf-8'),
            "DrivingMileage": DrivingMileage,
            "Color": Color.encode('utf-8'),
            "FirstCardDate": FirstCardDate,
            "LicenseLocation": merchantCity.encode('utf-8'),
            "UcarLocation": merchantCity.encode('utf-8'),
            "CarType": "0",
            "MaintainRecord": MaintainRecord,
            "InsuranceExpireDate": InsuranceExpireDate,
            "ExamineExpireDate": InsuranceExpireDate,
            "VinCode": VinCode,
            "CardCode": "",
            "StateDescription": StateDescription.encode('utf-8'),
            "DisplayPrice": DisplayPrice,
            "IsIncTransfer": IsIncTransfer,
            "InnerColor": InnerColor.encode('utf-8'),
            "IsCard": "1",
            "IsChangePrice": "1",
            "ContactName": ContactName.encode('utf-8'),
            "ContactTel": str(ContactTel),
            "IsWarranty": IsWarranty,
            "DriveLicensePic": DriveLicensePic,
            "WarrantyServiceTypes": "2",
            "ManuSvrDate": "2016-07"
        }
        cs = json.dumps(carSource)

        # pictureList = "http://img8.taoche.cn/1d/02150cm9e4.jpg|,|http://img8.taoche.cn/1d/02150cm9e4.jpg"
        pictureList = (self.getPicList(vehicle)).encode('utf-8')


        client = Client(webServiceUrl, faults=False)
        result = client.service.ShowCarSourceV2(userName, pwd, dealerCode, carSourceID, cs, pictureList, chkImageList)
        status = result[0]
        info = result[1]
        logger.debug(result)
        if str(status) == '200':
            # url = 'http://www.taoche.com/buycar/b-DealerKCW1337575T.html'
            uri = 'http://www.taoche.com/buycar/b-'
            infoDict = json.loads(info)
            code = infoDict['code']
            message = infoDict['message']
            if str(code) == '1':
                return errorcode.SUCCESS, uri + message + '.html'
            elif message == 'Api call exceeded limit':
                return errorcode.SUCCESS, 'www.kanche.com'
            else:
                return errorcode.DATA_ERROR, message
        return errorcode.DATA_ERROR, info

    def HideCarSource(self, shareJob, dealerCode, carSourceID):
        userName = ApiAccount['userName']
        _secretkey = ApiAccount['secretkey']
        #密码为carSourceID加淘车提供的secretkey所组成字符串的MD5值
        pwd = self.md5(carSourceID + _secretkey)

        client = Client(webServiceUrl, faults=False)
        result = client.service.HideCarSource(userName, pwd, dealerCode, carSourceID)
        status = result[0]
        info = result[1]
        logger.debug(result)
        if str(status) == '200':
            # url = 'http://taoche.com/' + dealerCode + '/' + carSourceID + '.html'
            infoDict = json.loads(info)
            code = infoDict['code']
            message = infoDict['message']
            if str(code) == '1':
                return errorcode.SUCCESS, u'success, 删除成功'
            else:
                return errorcode.DATA_ERROR, message
        return errorcode.DATA_ERROR, info

    def isEnsuredVehicle(self, shareJob):
        '''
        VIN码必填
        VIN码格式：长度只能是17位
        上牌的车源行驶证图片必填
        车龄小于5年
        行驶里程小于10万公里
        检测报告图片必填  不超过15张
        延长质保和原厂质保请至少选择1项
        如果是原厂质保：截止日期必填  并且不能早于当前时间
        :param shareJob:
        :return: True/False
        '''
        vehicle = shareJob.get('vehicle', None)
        vin = vehicle.get('vin', None)
        if vin is None or vin == '':
            return False

        if len(vin) != 17:
            return False

        #行驶证图片：没有就用vin照片
        vehicleSummary = vehicle.get('summary', None)
        DriveLicensePic = vehicleSummary.get('driving_license_picture', None)

        #vin图片
        vin_picture = vehicleSummary.get('vin_picture', None)
        if DriveLicensePic is None or DriveLicensePic == '':
            if vin_picture is None or vin_picture == '':
                return False

        vehicle_date = vehicle.get('vehicle_date', None)
        registration_date = vehicle_date.get('registration_date', None)
        rDate = str(registration_date)[:10]
        rYear = int(rDate[:4])
        rMonth = int(rDate[5:7])
        rDay = int(rDate[8:10])

        #车龄:
        standardDays = 5 * 365
        mDate = time.strftime("%Y-%m-%d", time.localtime())
        mYear = int(mDate[:4])
        mMonth = int(mDate[5:7])
        mDay = int(mDate[8:10])

        if (mYear*365 + mMonth*30 + mDay) - (rYear*365 + rMonth*30 + rDay) >= standardDays:
            return False

        #行驶里程
        DrivingMileage = int(vehicleSummary.get('mileage', ''))
        if DrivingMileage >= 100000:
            return False
        #延长质保，默认ok

        return True

    # ==========================================
    # shareVehicle 发车入口
    # ==========================================
    def shareVehicle(self, shareJob):
        username = shareJob.get('share_account', None).get('username', None)
        # password = shareJob.get('share_account', None).get('password', None)
        dealerCode = str(re.compile(r'\d+').findall(username)[0])
        logger.debug('dealerCode:'+dealerCode)

        vehicle_id = shareJob.get('vehicle', None).get('_id', None)
        carSourceID = str(vehicle_id)
        logger.debug('carSourceID:' + str(carSourceID))

        #TODO:修改
        # dealerCode = '100074344' #username
        (success, reInfo) = self.ShowCarSourceV2(shareJob, dealerCode, carSourceID)
        return success, reInfo

    # ==========================================
    # removeVehicle 下架入口
    # ==========================================
    def removeVehicle(self, shareJob):
        username = shareJob.get('share_account', None).get('username', None)
        # password = shareJob.get('share_account', None).get('password', None)
        dealerCode = str(re.compile(r'\d+').findall(username)[0])
        logger.debug('dealerCode:'+dealerCode)

        vehicle_id = shareJob.get('vehicle', None).get('_id', None)
        carSourceID = str(vehicle_id)
        logger.debug('carSourceID:' + str(carSourceID))

        #TODO:修改
        # dealerCode = '100074344' #username
        (success, reInfo) = self.HideCarSource(shareJob, dealerCode, carSourceID)
        return success, reInfo


    # ==========================================
    # updateVehicle 改价入口
    # ==========================================
    def updateVehicle(self, shareJob):
        (success, info) = self.shareVehicle(shareJob)
        return success, info
