#!/usr/bin/python
# -*- coding: UTF-8 -*-

import json
from urlparse import urlparse

import httplib
import string
import copy
from decimal import *
import errormsg
from cityBaixing import CityBaixing
import time
import hashlib
import base64
import urllib2
import errorcode
import logger
from base import BaseSharer
import pymongo
import config
from datetime import datetime
import random


'''
publicAccount = {
    "username": u"15300067246",
    "password": u"111206bai"
}
'''

BASE_URL = "api.baixing.com.cn"

publicAccount = {
    # ('2252', '883BDFF2F85BD69169F5DAB2BBBDE63856692F1D'),#18610205279,mengqian
    ('3264', '3E092DC2551D3D81B67358A791546D26C1E2608A'),#13681210639
    ('3266', 'B2803C00D1DBEEEDEBB08345EF89DADF9C8C212C'),#18730634308
    ('3267', '0D958F7719EA50E58BF149CC27AD0ABFB2C8180E'),#13810790418
    ('3268', '5C00B9933D40F4C561D95C585F8461F9CA5FE0AC'),#18610842384
    ('3468', '8377456CBA9568D321C3231E71C12CDF0602E42A'),#18610842384
    ('3474', '789BB8FCE7C6F88367F206100BB691F338061580'),#18610842384
    ('3470', '2EB88EC925F4D974541DE6ABB9BBFBCBBAD8A25F'),#18610842384
    ('3475', 'F160D577679454D0B33ABCD60FB92C72DFA79234'),#18610842384
    ('3471', '89780B67D0E7E3709958E1C29AEBD270F6B299C7'),#18610842384
    ('3617', 'C8C115C2AFA97A9ED66111C9F137115ABFA920D7'),
}

# mongoServer = "mongodb://localhost:27017"
mongoServer = config.mongoServer
conn = pymongo.Connection(mongoServer)
db = conn.kanche
col = db.baixing_api_key

class BaixingApiSharer(BaseSharer):
    def __init__(self, sessionServer, specServer):
        super(BaixingApiSharer, self).__init__(sessionServer, specServer)
        self.cityBaixing = CityBaixing()


    def postVehicle(self,shareJob, parseResult, queryId):
        #init data
        shareAccount = shareJob.get("share_account", None)
        APP_KEY = shareAccount.get('username', None)
        APP_SECRET = shareAccount.get('password', None)

        vehicle = shareJob.get("vehicle", None)
        user = vehicle.get('user', None)
        substitute_account = shareAccount.get('substitute_account', None)
        address = substitute_account.get('address', None)
        city_code = address.get('city_code', None)
        userMobile = self.getUserMobile(APP_KEY, city_code)

        address = user.get('address', None)
        spec = vehicle.get("spec", None)
        specDetail = shareJob.get("vehicle_spec_detail", None)
        externalVehicleSpec = shareJob.get('external_vehicle_spec')
        iQueryId = queryId.encode('utf8') if type(queryId) == unicode else queryId
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
        if shareAccount.get('account_type', None) == 'public':
            (contactName, mobile) = self.getContact(shareJob)
        else:
            (contactName, mobile) = self.getContact(shareJob)

        Symbol = "\r\n"
        lateral = "——"*20

        formData = {
            'userMobile': userMobile,
            'categoryId':'ershouqiche',
            'cityEnglishName': parseResult['cityName'],
            'wanted': '0',
            'title': str(spec['brand']) + str(spec['series']) + str(spec['sale_name']),
            '车品牌': brand,
            '车系列': str(spec['brand']) + str(spec['series']),
            '车型': str(spec['series']) + str(spec['sale_name']),
            '类型': 'm177927',
            '年份': str(registrationDate.year)+ '年' + str(registrationDate.month)+'月',
            '行驶里程': str(Decimal(vehicle['summary']['mileage']) / Decimal(10000)),
            '价格': str(Decimal(self.getPrice(shareJob)) / Decimal(10000)),
            'content': str(self.getContentVal_baixing(shareJob, Symbol, lateral)),
            '地区': parseResult['cityCode'],
            'contact': mobile,
            '车辆颜色': str(self.getColor(vehicle)),
            '排量': str(specDetail['details'][23]),
            '变速箱': str(specDetail['details'][42]),
            '燃油类型':str('汽油'),
            '排放标准':str(specDetail['details'][10]),
            '车辆用途':str('家用'),
            '年检':str(inspectionDate.year)+'年'+str(inspectionDate.month)+'月',
            '交强险':str(compulsoryInsuranceExpireDateYear)+'年'+str(compulsoryInsuranceExpireDateMonth)+'月',
            '商业险':str(commercialInsuranceExpireDateYear)+'年'+str(commercialInsuranceExpireDateMonth)+'月',
            '登记证':str('齐全'),
            '能否过户':str('能'),
            '能否按揭':str('能'),
            '购置税': str(self.getBooleanText(vehicle, "document", "purchase_tax")),
            '行驶证': str(self.getBooleanText(vehicle, "document", "registration_certificate")),
            '购车发票': str('齐全'), # document.property
            '维修记录': str(self.getBooleanText(vehicle, "document", "maintenance_manual")),
            '重大事故': str(self.getBooleanText(vehicle, "summary", "accident")),
            '承担过户费': transferFee
        }
        #photoList
        gallery = vehicle.get("gallery", None)
        if gallery is None:
            logger.error("gallery missing")
            return errorcode.LOGIC_ERROR, errormsg.PHOTO_NOT_ENOUGH
        photoList = gallery.get("photos", [])
        imgs = []
        logger.debug('--baixing image upload start-- ')
        for photo in photoList:
            # photo.pop("name", None)
            base = self.b64(photo["url"])
            if base is None:
                return errorcode.LOGIC_ERROR, errormsg.PHOTO_NOT_ENOUGH
            else:
                imgs.append({"jpg":base})
        formData['upload_images'] = imgs
        logger.debug('--baixing image upload end-- ')


        formJson = json.dumps(formData)
        sApiHash = hashlib.md5('post' + formJson + APP_SECRET).hexdigest()
        conn = httplib.HTTPConnection(BASE_URL)
        headers = {
            "Bapi-App-Key": APP_KEY,
            "Bapi-Hash": sApiHash,
            "Content-Type": "application/json; charset=utf-8"
        }
        conn.request("POST", "/v2/post", formJson, headers=headers)
        response = conn.getresponse().read()
        logger.debug('response:' + str(response))
        parseRes = json.loads(response)
        conn.close()
        print response
        if parseRes["status"] == "success":
            url = parseRes["data"]["link"]
            return errorcode.SUCCESS, url
        elif parseRes["status"] == "fail":
            if parseRes['message'].count('Api call exceeded limit'):
                return errorcode.SUCCESS, 'www.kanche.com'
            elif parseRes['message'].count('Inconsistent hash value'):
                return errorcode.SITE_ERROR, u'发车数据不符合规范'
            return errorcode.SITE_ERROR, parseRes['message']
        else:
            return errorcode.SITE_ERROR, errormsg.VEHICLE_DUPLICATED

    def getUserMobile(self, username, city_code):
        cityDict = {
            "500100": "18080033280",#重庆
            "410100": "18503837262",#郑州
            "430100": "13142006358",#长沙
            "220100": "18684315610",#长春
            "420100": "17786121549",#武汉	18682286880  420100
            "320200": "18915520044",#无锡	18915520044  320200
            "120100": "18522706530",#天津	18522706530  120100
            "320500": "18879174552",#苏州	18879174552  320500
            "130100": "15383933832",#石家庄	18631188363   130100
            # "450100": "15077182512",#南宁	15077182512  450100
            "370100": "18560142766",#济南	18560142766  370100
            # "150100": "15174916941",#呼和浩特	  15174916941   150100
            "340100": "18256029061",#合肥	18256029061  340100
            # "330100": "15869183833",#杭州	15869183833  330100
            "230100": "15043096668",#哈尔滨	15043096668   230100
            "440100": "18565590602",#广州	18620568096  440100
            # "350100": "15080453882",#福州	15080453882  350100
            "440600": "18928966535",#佛山	18928966535  440600
            "210200": "13234066887",#大连	15142456235  210200
            "510100": "18180792349",#成都	13982284603  510100
            "110100": "18514293607",#北京	18514293607  110100
            "150200": "13722123171",#包头	13722123171  150200
            "320100": "15606900245",
            "330300": "13860440368",
            "210100": "15209244666",#沈阳
            "441900": "13681759194", #东莞
            "310100": "13614764743" #上海default
        }
        # duplicateList = ['320100', '320200', '330300', '210100', '210200', '450100', '310100']
        duplicateList = ['320100', '320200', '310100']
        duplicateCollection = [('320100', ('15606900245', '18001442722')),#南京
                               ('320200', ('18915520044', '18610842384')),#无锡
                                ('330300', ('13860440368')),#温州
                                ('210100', ('15209244666')),#沈阳
                                #('210200', ('15142456235', '15080453882')),#大连
                                ('450100', ('15174916941')), #南宁)
                               ('310100', ('13614764743', '15590929141', '15011154188'))#上海
                               ]

        userDict = {
            "2252": "18256029061",
            "3264": "13681210639",
            "3266": "18730634308",
            "3267": "13810790418",
            "3268": "18610842384",
            "3468": "17751450018",
            "3474": "18651646635",
            "3470": "15995758077",
            "3475": "13394116728",
            # "3471": "13665567570",
            "3617": "15043096668",#default 15043096668
        }

        if username == '3617' and city_code in cityDict.keys():
            if city_code in duplicateList:
                for item in duplicateCollection:
                    if city_code == item[0]:
                        return random.choice(item[1])
            else:
                return cityDict[city_code]
        else:
            return userDict[username]

    def b64(self, url):
        if url:
            try:
                f = urllib2.urlopen(url.encode('utf-8'), timeout=10).read()
                return base64.encodestring(f)

            except urllib2.URLError, e:
                print e.reason
                return None

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

    def initShareJob(self, shareJob):
        shareAccount = shareJob.get("share_account", None)
        if shareAccount is None:
            return errorcode.AUTH_ERROR, ""
        if shareAccount.get('account_type', None) == 'public':
            shareAccount['username'] = publicAccount['username']
            shareAccount['password'] = publicAccount['password']

        vehicle = shareJob.get("vehicle", None)
        if vehicle is None:
            logger.error("vehicle missing")
            return errorcode.LOGIC_ERROR, errormsg.VEHICLE_EMPTY

        merchant = vehicle.get('merchant', None)
        merchant_address = merchant.get('address', None)
        # districtCode = merchant_address.get('district_code', None)
        cityCode = merchant_address.get('city_code', None)
        if cityCode is None:
            #return
            return errorcode.DATA_ERROR, errormsg.CITY_EMPTY

        user = vehicle.get('user', None)
        if user is None:
            # return False
            return errorcode.DATA_ERROR, errormsg.USER_EMPTY

        cityName = self.cityBaixing.getName(cityCode)
        baixingCityCode = self.cityBaixing.getCode(cityCode)
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
        return errorcode.SUCCESS, parseResult

    def doLogin(self, username, password):
        pass

    #############
    # 改价
    #############
    def updateVehicle(self, shareJob):
        shareAccount = shareJob.get("share_account", None)
        APP_KEY = shareAccount.get('username', None)
        APP_SECRET = shareAccount.get('password', None)

        if shareAccount is None:
            return errorcode.AUTH_ERROR, ""
        if shareAccount.get('account_type', None) == 'public':
            (contactName, mobile) = self.getContact(shareJob)
        urlForApp = shareJob.get("url", None)
        if urlForApp is None or urlForApp == '':
            return errorcode.DATA_ERROR, '车辆url为空'

        adID = urlForApp.split("/")[-1].replace(".html", "")
        if adID is None:
            return errorcode.DATA_ERROR, "车辆ID为空"
        vehicle = shareJob.get("vehicle", None)
        user = vehicle.get('user', None)
        substitute_account = shareAccount.get('substitute_account', None)
        address = substitute_account.get('address', None)
        city_code = address.get('city_code', None)
        userMobile = self.getUserMobile(APP_KEY, city_code)

        formData = {
            'userMobile': userMobile,
            'id': str(adID),
            '价格': str(Decimal(self.getPrice(shareJob)) / Decimal(10000))
        }
        formJson = json.dumps(formData)
        sApiHash = hashlib.md5('update' + formJson + APP_SECRET).hexdigest()
        conn = httplib.HTTPConnection(BASE_URL, timeout=10)
        headers = {
            "Bapi-App-Key": APP_KEY,
            "Bapi-Hash": sApiHash,
            "Content-Type": "application/json; charset=utf-8"
        }
        conn.request("POST", "/v2/update", formJson, headers=headers)
        response = conn.getresponse().read()
        parseRes = json.loads(response)
        conn.close()
        print response
        if parseRes["status"] == "success":
            url = parseRes["data"]["link"]
            return errorcode.SUCCESS, url
        else:
            return errorcode.SITE_ERROR, parseRes['message']

    def removeVehicle(self, shareJob):
        shareAccount = shareJob.get("share_account", None)
        APP_KEY = shareAccount.get('username', None)
        APP_SECRET = shareAccount.get('password', None)
        vehicle = shareJob.get("vehicle", None)
        user = vehicle.get('user', None)
        substitute_account = shareAccount.get('substitute_account', None)
        address = substitute_account.get('address', None)
        city_code = address.get('city_code', None)
        userMobile = self.getUserMobile(APP_KEY, city_code)

        if shareAccount is None:
            return errorcode.AUTH_ERROR, ""
        if shareAccount.get('account_type', None) == 'public':
            (contactName, mobile) = self.getContact(shareJob)

        urlForApp = shareJob.get("url", None)
        if urlForApp is not None and len(urlForApp) > 0:
            print urlForApp
            adID = urlForApp.split("/")[-1].replace(".html","")
            formData = {
                'userMobile' : userMobile,
                'id': str(adID)
            }
            formJson = json.dumps(formData)
            sApiHash = hashlib.md5('delete' + formJson + APP_SECRET).hexdigest()
            conn = httplib.HTTPConnection(BASE_URL, timeout=10)
            headers = {
                "Bapi-App-Key": APP_KEY,
                "Bapi-Hash": sApiHash,
                "Content-Type": "application/json; charset=utf-8"
            }
            conn.request("POST", "/v2/delete", formJson, headers=headers)
            res = conn.getresponse().read()
            parseRes = json.loads(res)
            conn.close()
            print res
            if parseRes["status"] == "success":
                return errorcode.SUCCESS, "success"
            else:
                return errorcode.SITE_ERROR, parseRes['message']
        else:
            return errorcode.DATA_ERROR, errormsg.VEHICLE_URL_EMPTY

    def shareVehicle(self, shareJob):
        (success, parseResult) = self.initShareJob(shareJob)
        if success == errorcode.SUCCESS:
            (shareSuccess, url) = self.postVehicle(shareJob, parseResult, 'ershouqiche')
            return shareSuccess, url
        else:
            return True, parseResult

    def getContentVal_baixing(self, shareJob, Symbol="\r\n", lateral="——"*23):
        externalSpec = shareJob['external_vehicle_spec']
        share_account = shareJob.get("share_account", None)
        model = externalSpec.get('model', None)
        key = model.get('key', None)
        content = ''
        vehicle = shareJob.get('vehicle', None)
        desc = vehicle.get('desc', None)
        detail = desc.get('detail', "")
        website = shareJob.get('share_account').get('website')

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
                    if site == 'che168.com':
                        description = i.get('description', None)
                        description = string.replace(description, '\n', Symbol)
            content += description
            content += Symbol + str(vehicle['_id'])

        # 每辆车说明 追加
        if vehicleDisable == False:

            #因为che168问题，不需要填写车辆名称
            # if not (model is None) and not (key is None):
            #     content += "[ 车辆名称 ]" + Symbol
            #     if externalSpec['model']['key'] == '0':
            #         vehicleSpec = shareJob['vehicle']['spec']
            #         content += (externalSpec['brand']['name'] + externalSpec['series']['name'] + u' ' + vehicleSpec['sale_name'] + u'' + vehicleSpec['year_group']) + Symbol*2
            #     else:
            #         content += (externalSpec['brand']['name'] + externalSpec['series']['name'] + u' ' + externalSpec['model']['name']) + Symbol*2

            # #车况说明
            # condition = "乘坐空间宽敞，储物空间充足;"
            # condition = condition + "转向清晰，指向精准;" + Symbol
            # condition = condition + "提速表现优秀，动力源源不断;" + Symbol
            # condition = condition +"车身有少量、轻微划痕或者局部补漆的情况，不超过3处;" + Symbol
            # condition = condition + "车辆内部后备箱内干净整洁，内饰及座椅无磨损、污渍;" + Symbol
            # condition = condition + "油耗低，节能环保；座椅舒适度上乘，车内无噪音;"


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

            # if len(highlight_show_name_list):
            #     content += "[ 亮点配置 ] " + Symbol + highlight_str + Symbol*2
            # else:
            #     pass
            #
            # if "" == detail:
            #     content += "[ 车况说明 ] " + Symbol + condition + Symbol*2
            # else:
            #     content += "[ 车况说明 ] " + Symbol + detail + Symbol*2

            #车况说明，来自bss模板
            if detail != "":
                content += detail + Symbol*2

        # 统一说明 追加
        if globalDisable == False:
            if share_account.get("account_type", None) == "substitute":
                if website != 'che168.com':
                    content += '更多选择，尽在看看车。' + Symbol

                content += '我们向您承诺：' + Symbol
                content += '车况：大量优质车源，208项售前检测，专业评估师把关，呈现真实车况。' + Symbol
                content += '车价：专业买车顾问全程1对1服务，交易透明，不赚差价。' + Symbol
                content += '过户：免费过户，包办手续。' + Symbol
                content += '质保：为8年及15万公里以内的车辆提供超低价格的1年或2万公里保修服务。' + Symbol*2

        content += str(vehicle.get('series_number', '')) + "#"
        content += str(vehicle['_id'])

        if "" == content:
            content = u"无车辆说明，请添加至 10个字以上"
        return content
