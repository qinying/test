#!/usr/bin/python
# -*- coding: UTF-8 -*-

from base import BaseSharer
import errorcode
import errormsg
import requests
import json
import logger

__author__ = 'jesse'


class JZGSharer(BaseSharer):

    def __init__(self, sessionServer, specServer):
        super(JZGSharer, self).__init__(sessionServer, specServer)
        # 授权码：83cd1ab1-7dcf-42ea-97c0-8f4c42e77e7a
        self.Sign = '83cd1ab1-7dcf-42ea-97c0-8f4c42e77e7a'
        self.headers = {
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Encoding': 'gzip, deflate',
            'Accept-Language': 'zh-CN,zh;q=0.8,en;q=0.6',
            'Cache-Control': 'max-age=0',
            'Connection': 'keep-alive',
            'Content-Type': 'application/x-www-form-urlencoded',
            'Host': 'api.jingzhengu.com',
            'Origin': 'http://api.jingzhengu.com',
            'User-Agent':'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/46.0.2490.86 Safari/537.36',
        }

    @staticmethod
    def get_color(color):
        color_mapping = {
            'black': u'黑色', #黑色
            'white': u'白色',#白色
            'silver': u'银灰色',#银灰色
            'gray': u'香槟色',#深灰色
            'champagne': u'香槟色',#香槟色
            'red': u'红色',#红色
            'blue': u'蓝色',#蓝色
            'green': u'绿色',#绿色
            'yellow': u'黄色',#黄色
            'orange': u'橙色',#橙色
            'brown': u'咖啡色',#咖啡色
            'purple': u'紫色',#紫色
            'multi': u'多彩色',#多彩色
            "other":  u"其他"# u"其他"
        }
        return color_mapping[color]

    @staticmethod
    def get_str_date(date):
        if(date is None) or (len(str(date)) < 10):
            return '2016-06-01'
        return str(date)[:10]

    @staticmethod
    def get_photos_url_list(photos):
        url_list = []
        for photo in photos:
            url = photo.get('url', '')
            url_list.append(url)
        return url_list

    ######################
    # 发车接口
    ######################
    def shareVehicle(self, shareJob):
        post_url = 'http://api.jingzhengu.com/CarSource/JZGCarSources.ashx'
        spec = shareJob.get('vehicle', None).get('spec')
        summary = shareJob.get('vehicle', None).get('summary', None)
        address = shareJob.get('vehicle', None).get('merchant', None).get('address', None)
        vehicle_date = shareJob.get('vehicle', None).get('vehicle_date', None)

        CarSourceID = str(shareJob.get('vehicle', None).get('_id', '111222'))
        JzgStyleID = '105026'
        # CarSourceType = u'个人'
        # 品牌名称[必填]
        MakeName = spec.get('brand', None)
        # 厂商名称[必填]
        ManufacturerName = spec.get('maker', None)
        # 车系名称[必填]
        ModelName = spec.get('series', None)
        # 车型名称[必填]
        StyleName = spec.get('sale_name', None)
        # 车型年款[必填]
        StyleYear = spec.get('year_group', None)
        # 车辆级别
        # CarLevel = u'轿车'
        Mileage = int(summary.get('mileage', None))

        LicenseProvinceName = address.get('province_name')
        LicenseCityName = address.get('city_name')

        BodyColor = self.get_color(summary.get('color'))
        # 行驶证时间
        LicenseTime = '2010-1-1'
        # ImageUrl = ['http://pic.kanche.com/9a20ed0d-f059-4f8d-8e5d-3afcf7f3db19.jpg',
        #             'http://pic.kanche.com/94338e67-40df-4831-92af-1ac44539d69d.jpg']
        photos = shareJob.get('vehicle', None).get('gallery', None).get('photos')
        ImageUrl = self.get_photos_url_list(photos)

        # 车源发布时间
        PublishTime = self.get_str_date(shareJob.get('create_at', None))
        # 保险到期时间
        InsuranceExpireDate = self.get_str_date(vehicle_date.get('compulsory_insurance_expire_date', None))
        # 年检到期时间
        InspectionExpireDate = self.get_str_date(vehicle_date.get('inspection_date', None))
        SellPrice = int(shareJob.get('vehicle', None).get('price', None).get('quoted_price', 10000))/10000.0
        # ContactsName = u'张小姐'
        # ContactsPhone = u'13312345678'
        (ContactsName, ContactsPhone) = self.getContact(shareJob)
        # Status = u'上架'
        # 车辆来源URL
        Url = 'http://www.kanche.com/vehicle/' + CarSourceID
        # 厂商指导价
        NowMsrp = ''
        # 成交价格(单位：万元)
        TransactionPrice = ''

        CarSourceData = {
            "Sign": self.Sign,
            "CarSourceID": CarSourceID,
            "JzgStyleID": JzgStyleID,
            "CarSourceType": u'个人',
            "MakeName": MakeName,
            "ManufacturerName": ManufacturerName,
            "ModelName": ModelName,
            "StyleName": StyleName,
            "StyleYear": StyleYear,
            "CarLevel": u'轿车',
            "Mileage": Mileage,
            "LicenseProvinceName": LicenseProvinceName,
            "LicenseCityName": LicenseCityName,
            "BodyColor": BodyColor,
            "LicenseTime": LicenseTime,
            "ImageUrl": ImageUrl,
            "PublishTime": PublishTime,
            "InsuranceExpireDate": InsuranceExpireDate,
            "InspectionExpireDate": InspectionExpireDate,
            "SellPrice": SellPrice,
            "ContactsName": ContactsName,
            "ContactsPhone": ContactsPhone,
            "Status": u'上架',
            "Url": Url,
            "NowMsrp": NowMsrp,
            "TransactionPrice": TransactionPrice
        }

        data = 'CarSourceData=' + json.dumps(CarSourceData)
        res = requests.post(url=post_url, data=data, headers=self.headers)
        res_content = json.loads(res.content)
        res_status = res_content['status']
        res_msg = res_content['msg']

        logger.debug("res_status: " + str(res_status))
        print res_msg

        if 100 == int(res_status):
            return errorcode.SUCCESS, ''
        return errorcode.SITE_ERROR, res_msg

    def updateVehicle(self, shareJob):
        raise errorcode.SITE_ERROR, errormsg.FUNCTION_NOT_FINISHED

    def removeVehicle(self, shareJob):
        raise errorcode.SITE_ERROR, errormsg.FUNCTION_NOT_FINISHED
