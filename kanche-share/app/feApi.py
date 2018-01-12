# -*- coding: UTF-8 -*-

import requests, re, hashlib, datetime, calendar, urllib, httplib, copy
from bson.json_util import loads
from decimal import Decimal
from dt8601 import IsoDate
from urlparse import urlparse
from lxml import etree
import string

from base import BaseSharer
from city582 import City852
import errormsg
import errorcode
import zimu
import tz
import utils
import logger
import config


import session

timeout_58 = 30
publicAccount = {
    #"username": u"18610205279",
    #"password": u"mengqian2"
    "username": u"看车二手车石家庄2014",
    "password": u"kankanqwe123"
    #"username":u"18005819169",
    #"password":"110110"
}
# 单日上限50条	: 福州、广州、杭州、合肥、武汉、郑州、长沙、南宁、无锡、东莞、上海、
fiftyCityLimitList = ['350100', '440100', '330100', '340100', '420100', '410100', '430100', '450100', '320200', '441900', '310100']
# 单日上限100条	北京、厦门、成都、重庆/ 深圳、苏州、南京、沈阳/ 哈尔滨、西安、大连、昆明 /温州、呼和浩特、包头、济南 /长春、佛山、天津、宁波/ 石家庄、青岛
hundCityLimitList = ['110100', '350200', '510100', '500100',
                     '440300', '320500', '320100', '210100',
                     '230100', '610100', '210200', '530100',
                     '330300', '150100', '150200', '370100',
                     '220100', '440600', '120100', '330200',
                     '130100', '370200']

def get34(pVal):
    s = '0123456789abcdefghijklmnopqrstuvwx'
    m = pVal % 34
    if pVal > 34:
        return get34(int(pVal/34)) + s[m]
    else:
        return s[m]

class FEApiSharer(BaseSharer):
    def __init__(self, sessionServer, specServer):
        super(FEApiSharer, self).__init__(sessionServer, specServer)
        
        self.client_id = 38193754447361
        self.client_secret = 'wYbkICOLafqHneenxrXJ'
        self.call_back_url = 'http://saerp.kanche.com/callback.apsx'
        self.cate_id = 29
        self.citys = City852()
        self.Symbol = u"\n"
        self.lateral = u"——"*20
        
        self.headers = {
            'Accept':'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Encoding':'gzip, deflate',
            'Accept-Language':'zh-CN,zh;q=0.8,en;q=0.6',
            'Cache-Control':'max-age=0',
            'Connection':'keep-alive',
            'User-Agent':'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/49.0.2623.87 Safari/537.36'
        }
    
    @staticmethod
    def getMd5(msg):
        m = hashlib.md5()
        m.update(msg)
        return m.hexdigest()
    
    @staticmethod
    def getTimeSign():
        iTimeSign = datetime.datetime.utcnow()
        iTimeSign = float('%s.%s'%(calendar.timegm(iTimeSign.timetuple()), ('000000'+str(iTimeSign.microsecond))[-6:]))
        iTimeSign = int(iTimeSign*1000)
        return iTimeSign
    
    @staticmethod
    def dict2str(pDict):
        iList = []
        for k, v in pDict.items():
            iList.append('%s=%s'%(k.encode('utf8'), urllib.quote(v.encode('utf8'))))
        return '&'.join(iList)

    def promotionWords_58(self, vehicle, isSelectedBDwords=False):
        # defaultPromotionWords = u'【首付低 利率低 提车快】'
        defaultPromotionWords = u'首付低 利率低 提车快'
        promotionWords = u'准好车'
        promotable = self.loanable(vehicle)
        if promotable:
            promotionWords = defaultPromotionWords
        else:
            # promotionWords = u'【手续全 过户快】'
            promotionWords = u'手续全 过户快'
        '''
        #如果选择bd的推广话语
        if isSelectedBDwords:
            brief = vehicle.get('desc', None).get('brief', '')
            if brief == '' or brief is None:
                promotionWords = defaultPromotionWords
            else:
                promotionWords = brief.strip('\n')

        else:
            if promotable:
                promotionWords = defaultPromotionWords
            else:
                promotionWords = '【手续全 过户快】'
        '''
        return promotionWords
    
    def getTitleVal(self, externalSpec, carInfo, vehicle):
        promotionWords = self.promotionWords_58(vehicle, False)
        title = ''
        # if externalSpec['model']['key'] == '0':
        #     vehicleSpec = carInfo['vehicle']['spec']
        #     title = (externalSpec['brand']['name'] + externalSpec['series']['name'] + u' ' + vehicleSpec['sale_name'] + u' ' + vehicleSpec['year_group'])
        # else:
        #     title = (externalSpec['brand']['name'] + externalSpec['series']['name'] + u' ' + externalSpec['model']['name'])
        # title = title.replace(u'Ⅲ', 'III').replace(u'Ⅳ', 'IV').replace(u'Ⅴ', 'V')
        return promotionWords
    
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

        '''
        车辆信息：
        限时活动：可分期、超低首付、超低利率、包过户、有质保、快速提车
        车辆名称：捷达 2010款 1.6L 伙伴
        车辆颜色： 黑色外观 | 浅色内饰
        车辆报价：4.5万
        上牌时间：2011-11-01 | 行驶里程：5.2万公里
        年检到期：2017-11 | 交强险到期：2016-11
        用途性质：非运营
        车辆证件：
        是否有事故： 否
        '''
        # 首付低 利率低 提车快
        content += startStyle_RedBigBold
        content += u"可分期  申请快  利率低"
        content += Symbol + u"1张身份证，秒速办理。"
        content += endRedStyle

        content += startStyle_BlackSmallBold
        content += Symbol*2 + u"车辆信息："
        content += endRedStyle

        content += startStyle_ReSmallNormal
        content += Symbol + u"限时活动：可分期、超低首付、超低利率、包过户、有质保、快速提车"
        content += endRedStyle

        # 车辆说明
        if not (model is None) and not (key is None):
            content += startStyle_BlackSmallNormal
            content += Symbol + u"车辆名称: "
            if externalSpec['model']['key'] == '0':
                vehicleSpec = shareJob['vehicle']['spec']
                vehicle_dis = (externalSpec['brand']['name'] + externalSpec['series']['name'] + u' ' + vehicleSpec['sale_name'] + u'' + vehicleSpec['year_group'])
            else:
                vehicle_dis = (externalSpec['brand']['name'] + externalSpec['series']['name'] + u' ' + externalSpec['model']['name'])
            content += vehicle_dis

        # 车辆颜色： 黑色外观 | 浅色内饰
        (color_code, color_name) = self.getCheshenyanseVal(shareJob)
        interior = vehicle.get('summary').get('interior')
        interior_dict = {
            "light": u"浅色内饰",
            "dark": u"深色内饰"
        }
        content += Symbol + u"车辆颜色: "
        content += color_name + u"外观 | " + interior_dict[interior]

        # 价格: 万元
        price = self.getMinProceVal(shareJob)
        content += Symbol + u"车辆报价: " + str(price) + u"万"

        # 上牌时间：2011-11-01 | 行驶里程：5.2万公里
        registration_date = self.getDate(shareJob)
        mileage = self.getRundistanceVal(shareJob)  # 万
        content += Symbol + u"上牌时间: " + str(registration_date.year) + '|' + str(registration_date.month) + ' - '
        content += u"行驶里程: " + str(mileage) + '万公里'

        # 年检到期：2017-11 | 交强险到期：2016-11
        inspect_date = self.getTypeDate_58('cjshijian', vehicle.get('vehicle_date', {}))
        commercial_insurance_expire_date = self.getTypeDate_58('cjshijian', vehicle.get('vehicle_date', {}))
        content += Symbol + u"年检到期: " + str(inspect_date) + ' - '
        content += u"交强险到期: " + str(commercial_insurance_expire_date)

        # 用途性质：非运营
        content += Symbol + u"用途性质: 非运营"

        # 车辆证件:
        document_dict = {
            "property": u"产权证",
            "instruction": u"说明书",
            "transfer_ticket": u"过户票",
            "road_maintenance": u"养路费",
            "vehicle_tax": u"车船税",
            "maintenance_manual": u"保养手册",
            "purchase_tax": u"购置税",
            "registration_certificate": u"登记证"}
        document_str = ''
        vehicle_document = vehicle.get('document')
        for key in document_dict.keys():
            item = vehicle_document.get(key)
            if item is None or item is False or '' == item :
                continue
            document_str += document_dict[key] + '、'
        content += Symbol + u"车辆证件: " + document_str

        # 是否有事故： 否
        content += Symbol + u"是否有事故: 否"
        content += endRedStyle
        # end of all

        # 车辆概况:
        content += startStyle_BlackSmallBold
        content += Symbol*2 + u"车辆概况："
        content += endRedStyle


        # 车况说明，来自bss模板
        if vehicleDisable is False:
            if detail != "":
                content += Symbol + detail

        # 统一说明 追加
        '''
        外观：漆面保持较好，车身结构无修复，无重大事故。前脸完好。左右对称性正常。
        内饰：车身内饰干净整洁。座椅几乎无磨损。安全指示灯正常，气囊等被动安全项正常，车辆内电子器件使用良好，车内静态动态设备完善。
        驾驶：经短途试驾体验，车辆点火、起步、提速、过弯、减速、制动均无问题，加速迅猛，动力输出平稳舒适，无怠速抖动。
        整体：整体车况良好。车体骨架结构无变形扭曲、无火烧泡水痕迹。车身有喷漆痕迹，整体漆面良好，排除大事故车辆。适合家庭代步用车，动力强劲视野宽阔，练手最佳选择，空间宽敞明亮通风性较好，适合家庭代步用车。
        '''
        content += Symbol + u"外观: "
        content += u'漆面保持较好，车身结构无修复，无重大事故。前脸完好。左右对称性正常。'
        content += Symbol + u"内饰: "
        content += u'车身内饰干净整洁。座椅几乎无磨损。安全指示灯正常，气囊等被动安全项正常，车辆内电子器件使用良好，车内静态动态设备完善。'

        content += Symbol + u"驾驶: "
        content += u'经短途试驾体验，车辆点火、起步、提速、过弯、减速、制动均无问题，加速迅猛，动力输出平稳舒适，无怠速抖动。'

        content += Symbol + u"整体: "
        content += u'整体车况良好。车体骨架结构无变形扭曲、无火烧泡水痕迹。车身有喷漆痕迹，整体漆面良好，排除大事故车辆。适合家庭代步用车，动力强劲视野宽阔，练手最佳选择，空间宽敞明亮通风性较好，适合家庭代步用车。'
        content += endRedStyle

        if globalDisable is False:
            if share_account.get("account_type", None) == "substitute":
                content += startStyle_BlackSmallNormal
                content += Symbol*2 + u'看车网向您承诺：'
                content += Symbol + u'选车：大量优质车源，根据您的需求，推荐最好最适合的车辆。'
                content += Symbol + u'车况：208项售前检测，专业评估师把关，呈现真实车况。'
                content += Symbol + u'过户：免费过户，包办手续。'
                content += Symbol + u'质保：为8年及15万公里以内的车辆提供超低价格的1年或2万公里保修服务。'
                content += endRedStyle
                
                content += startStyle_ReSmallBold
                content += Symbol + u'付款：可分期付款，只需身份证，即可申请，超低月供, 超低月息。'
                content += endRedStyle

        content += Symbol*2 + str(vehicle.get('series_number', '')) + "#"
        content += str(vehicle['_id'])
        # logger.debug("content:" + str(content)[:1900])

        if "" == content:
            content = u"无车辆说明，请添加至10个字以上"
        return content[:1900]

    def getContentVal_normal_58(self, shareJob, Symbol="\r\n", lateral="——"*23):
        externalSpec = shareJob['external_vehicle_spec']
        share_account = shareJob.get("share_account", None)
        model = externalSpec.get('model', None)
        key = model.get('key', None)
        content = ''
        vehicle = shareJob.get('vehicle', None)
        desc = vehicle.get('desc', None)
        detail = desc.get('detail', "")
        website = shareJob.get('share_account').get('website')

        if type(lateral) != unicode:
            lateral = lateral.decode('utf8')

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
                    highlight_str += name + u"、"

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
                    content += u'更多选择，尽在看看车。' + Symbol
                # 
                # content += u'我们向您承诺：' + Symbol
                # content += u'车况：大量优质车源，208项售前检测，专业评估师把关，呈现真实车况。' + Symbol
                # content += u'车价：专业买车顾问全程1对1服务，交易透明，不赚差价。' + Symbol
                # content += u'过户：免费过户，包办手续。' + Symbol
                # content += u'质保：为8年及15万公里以内的车辆提供超低价格的1年或2万公里保修服务。' + Symbol
                # content += u'贷款：可分期付款，只需身份证，即可申请，超低月供, 超低月息。' + Symbol*2

        content += str(vehicle.get('series_number', '')) + "#"
        content += str(vehicle['_id'])

        if "" == content:
            content = u"无车辆说明，请添加至10个字以上"
        return content[:1900]
    
    def getIMVal(self, merchantSubstituteConfig):
       social = merchantSubstituteConfig.get("social", {})
       qq = social.get("qq", '')
       return qq
    
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
    
    @staticmethod
    def getCheshenyanseVal(carInfo):
        colorTable = {"black": "1", "white": "2", "silver":"3", "grey":"4", 
            "brown":"11", "red":"6", "blue":"7", "green":"8", "yellow": "9", 
            "orange": "10", "purple": "12", "champagne":"13", "multi":"14", "other": "14"}
        
        colorNameTable = {"black": "黑色", "white": "白色", "silver":"银色", "grey":"灰色",
                      "brown":"棕色", "red":"红色", "blue":"蓝色", "green":"绿色", "yellow": "黄色",
                      "orange": "橙色", "purple": "紫色", "champagne":"金色", "multi":"其它", "other": "其它"}
        
        cheshencode = "1"
        colorName = '黑色'
        vehicle = carInfo.get("vehicle", None)
        if vehicle is not None:
            summary = vehicle.get("summary", None)
            if summary is not None:
                color = summary.get("color", None)
                cheshencode = colorTable.get(color, "1")
                colorName = colorNameTable.get(color, "黑色")
        return cheshencode, colorName.decode('utf8')
    
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
    
    @staticmethod
    def getDate(carInfo):
        d = IsoDate.from_iso_string('2016-01-01T00:00:00.000+08:00')
        vehicle = carInfo.get("vehicle", None)
        if vehicle is not None:
            vehicleDate = vehicle.get('vehicle_date', None)
            if vehicleDate is not None:
                registrationDate = vehicleDate.get('registration_date', None)
                if registrationDate is not None:
                    d = registrationDate.astimezone(tz.HKT)
        return d
    
    @staticmethod
    def getTypeDate_58(name, vehicle_date):
        '''
        cjshijian   2016|1
        qxshijian   2016|1 交强险到期时间
        syshijian   2016|1
        '''
        iNow = datetime.datetime.now()
        iNow = iNow.replace(day=1,hour=0,minute=0,second=0,microsecond=0,tzinfo=tz.HKT)
        if name == 'syshijian':
            iDate = vehicle_date.get('commercial_insurance_expire_date', None)
            if iDate is not None:
                if iDate < iNow:
                    return u'无商业险'
        elif name == 'qxshijian':
            iDate = vehicle_date.get('compulsory_insurance_expire_date', None)
            if iDate is not None:
                iDate.astimezone(tz.HKT)
                if iDate < iNow:
                    return u'过保'
            
        typeDict = {
            "cjshijian": "inspection_date",
            #cjshijian暂不知什么意义
            "qxshijian": "compulsory_insurance_expire_date",
            "syshijian": "commercial_insurance_expire_date",
            "inspection": "inspection_date"
        }
        value = ""
        date = vehicle_date.get(typeDict[name], None)
        if date is None:
            date = vehicle_date.get(typeDict["inspection"], None)
            
        else:
            date = date.astimezone(tz.HKT)
        limit_year = iNow.year + 1
        year = date.year
        year = limit_year if (int(year) > limit_year) else year
        month = date.month
        if month == 0:
            month = 1
        value = (str(year) + "|" + str(month)).encode('utf-8')
        return value

    # 58诚信车商
    @staticmethod
    def is_integrity_merchant(vehicle):
        try:
            city_code = str(vehicle.get('merchant').get('address').get('city_code'))
        except:
            city_code = 0
        not_integrity_merchant_city_list = config.fe_not_integrity_merchant_city_list
        if city_code in not_integrity_merchant_city_list:
            return False
        return True
    
    @staticmethod
    def getShangpainianyue(carInfo):
        shangpainianyue = "201006"
        vehicle_date = carInfo['vehicle']['vehicle_date']
        registration_date = vehicle_date.get("registration_date", None).astimezone(tz.HKT)
        if registration_date is not None:
            shangpainianyue = "%d%2.2d"%(registration_date.year, registration_date.month)
        return shangpainianyue
    
    def getPostPage(self, code):
        logger.debug('wait for check 58vip')
        conn = httplib.HTTPConnection("post.58.com", timeout=timeout_58)
        headers = copy.copy(self.headers)
        headers['Host'] = 'post.58.com'
        #headers['Referer'] = 'http://post.58.com/' + code
        conn.request("GET", "/v" + code + "/29/s5", headers = headers)
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
        code = self.citys.getCode(cityCode)

        (url_code, html) = self.getPostPage(code)
        if not url_code.startswith('v'):
            return True
        return False
    
    def getQitadianhuaVal(self, merchantSubstituteConfig):
        extraContact = merchantSubstituteConfig.get("extra_contact", {})
        phone = extraContact.get("phone", '')
        if phone is None:
            phone = ''
        return phone
    
    
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
    
    def getParam(self, shareJob, pLocalId):
        default_iObjectType = '1'
        iMonth = ['515681','515682','515683','515684','515685','515686','515687','515688','515689','515690','515691','515692']
        iResult = {
            u"zimu":u"408788", u"brand":u"412596", u"chexi":u"412660", u"ObjectType":u"1", 
            u"chexibieming":u"583091",
            u"cheshenyanse":u"3", u"erscpinpai":u"2008款 2.5V 豪华版", u"rundistance":u"15", u"gobquzhi":u"",
            u"MinPrice":u"13.98", u"buytime":u"2008", u"shangpaiyuefen":u"515686",
            u"yczhibao":u"525379", 
            u"shangpainianyue":u"200806", u"shifoufufeifabu":u"1", u"shifouyishou":u"0",
            u"guohufeiyong":u"553663", u"xinxibianhao":u"O3yxwt",
            u"goblianxiren":u"刘先生", u"apilaiyuan":u"1", u"apiedit":u"1", u"type":u"0"
        }

        vehicle = shareJob.get("vehicle", {})
        externalSpec = shareJob.get("external_vehicle_spec", {})
        iBuyTime = self.getDate(shareJob)
        iColor = self.getCheshenyanseVal(shareJob)
        iObjectType = externalSpec['series'].get('object_type',{}).get('v')
        iResult['zimu'] = str(zimu.getZimuCode(externalSpec['brand']['name']))
        iResult['brand'] = externalSpec['brand']['spell']
        iResult['chexi'] = externalSpec['series']['key']
        iResult['ObjectType'] = iObjectType if (iObjectType is not None) else default_iObjectType
        iResult['chexibieming'] = externalSpec['series'].get('chexibieming', {}).get('v', '')
        iResult['cheshenyanse'] = iColor[0]
        iResult['erscpinpai'] = externalSpec['brand']['name'] + externalSpec['series']['name']
        iResult['rundistance'] = self.getRundistanceVal(shareJob)
        iResult['MinPrice'] = self.getMinProceVal(shareJob)
        iResult['buytime'] = str(iBuyTime.year)
        iResult['shangpaiyuefen'] = iMonth[iBuyTime.month - 1]
        iResult['shangpainianyue'] = self.getShangpainianyue(shareJob)
        iResult['guohufeiyong'] = '553663' if self.is_integrity_merchant(vehicle) else '553664'
        iResult['xinxibianhao'] = get34(int(self.getTimeSign()/34))
        iResult['goblianxiren'] = self.getContact(shareJob)[0]
        
        if self.isVIP(shareJob):
            iResult['escwltv2'] = '0'
            if self.is_integrity_merchant(vehicle):
                iResult['cylb'] = '525376'
                iResult['qtkt'] = '1'
                iResult['mianfeiguohu'] = '1'
            else:
                iResult['qtkt'] = '0'
                iResult['mianfeiguohu'] = '0'
            iResult['qitadianhua'] = self.getQitadianhuaVal(shareJob.get("merchant_substitute_config", {}))
            iResult['wanglintongbieming'] = u'北京看看车科技有限公司'
        
        
        iResult['cjshijian'] = self.getTypeDate_58('cjshijian', vehicle.get('vehicle_date', {}))
        iResult['qxshijian'] = self.getTypeDate_58('qxshijian', vehicle.get('vehicle_date', {}))
        iResult['syshijian'] = self.getTypeDate_58('syshijian', vehicle.get('vehicle_date', {}))
        iResult['baoyang'] = '515673'
        iResult['shiguqk'] = '515713'
        #iResult['yczhibao'] = '525379'
        #iResult['shifoufufeifabu'] = '1'
        #iResult['shifouyishou'] = '0'
        
        #iResult['apilaiyuan'] = '1'
        #iResult['apiedit'] = '1'
        #iResult['type'] = '0'

        vin = vehicle.get('vin', None)
        if vin is not None:
           iResult['Vin'] = vin

#        iResult['apixinxiid'] = ''
#        iResult['shifougaodang'] = ''
#        iResult['paifangbiaozhun'] = '408'
#        iResult['xbsx'] = '1'
#        iResult['shigumiaoshu'] = ''

        # 行驶证照片
        vin_pic_url = vehicle.get('summary', None).get('vin_picture')
        vin_pic_url = '' if vin_pic_url is None else vin_pic_url
        iResult['yczbpic'] = vin_pic_url

#        iResult['MinPriceqj'] = self.getPriceRange(shareJob)
#        iResult['chelingqj'] = ''
#        iResult['rundistanceqj'] = ''
#        iResult['displacement'] = externalSpec['summary'].get('displacement', {}).get('v', '')
#        iResult['gearbox'] = externalSpec['summary'].get('gearbox', {}).get('v', '')
#        iResult['kucheid'] = externalSpec['model'].get('kucheid', {}).get('v', '')
#        iResult['shangshishijian'] = externalSpec['model'].get('shangshishijian', {}).get('v', '')
        iResult['carchexing'] = externalSpec['model'].get('key', '')
#        iResult['madein'] = externalSpec['vendor']['v']

        iGobquzhi = {
            u'zimu':u'F', u'brand':u'丰田', u'chexi':u'锐志', u'objecttype':u'轿车', u'chexibieming':u'丰田锐志', u'buytime':u'2008年',
            u'shangpaiyuefen':u'6月', u'cheshenyanse':u'银色', u'cateapplyed':u'29', u'localapplyed':u'4'
        }
        iGobquzhi['zimu'] = zimu.getFirstChar(externalSpec['brand']['name'])
        iGobquzhi['brand'] = externalSpec['brand']['name']
        iGobquzhi['chexi'] = externalSpec['series']['name']
        iGobquzhi['ObjectType'] = iObjectType if (iObjectType is not None) else default_iObjectType
        # if iObjectType is not None:
        #     iGobquzhi['objecttype'] = externalSpec['series']['object_type']['t']
        iGobquzhi['localapplyed'] = pLocalId
        iGobquzhi['chexibieming'] = externalSpec['series'].get('chexibieming', {}).get('t', '')
        iGobquzhi['buytime'] = u'%s年'%iBuyTime.year
        iGobquzhi['shangpaiyuefen'] = u'%s月'%iBuyTime.month
        iGobquzhi['cheshenyanse'] = iColor[1]
        iGobquzhi['baoyang'] = '是'
        iGobquzhi['shiguqk'] = '无'
        
        iGobquzhi['kucheid'] = '0'
        iResult['kucheid'] = ''
        
#        iGobquzhi['kucheid'] = externalSpec['model'].get('kucheid', {}).get('t', '')
#        iGobquzhi['displacement'] = externalSpec['summary'].get('displacement', {}).get('t', '')
#        iGobquzhi['gearbox'] = externalSpec['summary'].get('gearbox', {}).get('t', '')
#        iGobquzhi['shangshishijian'] = externalSpec['model'].get('shangshishijian', {}).get('t', '')
#        iGobquzhi['tingshoushijian'] = externalSpec['model'].get('tingshoushijian', {}).get('t', '')
#        iGobquzhi['zbjcfanwei'] = '1'
#        iGobquzhi['yczb_cheling'] = externalSpec['summary'].get('yczb_cheling', {}).get('t', '')
#        iGobquzhi['yczb_licheng'] = externalSpec['summary'].get('yczb_licheng', {}).get('t', '')
#        iGobquzhi['madein'] = externalSpec['vendor']['name']
#        iGobquzhi['rundistanceqj'] = ''
#        iGobquzhi['chelingqj'] = ''

#        iGobquzhi['minpriceqj'] = ''
        iGobquzhi['carchexing'] = externalSpec['model'].get('name', '')
        #iResult['syshijian'] = u'无商业险'
        iResult['gobquzhi'] = self.dict2str(iGobquzhi)
#        print iResult['gobquzhi']
        iRoot = etree.Element("x")
        for k, v in iResult.items():
            iItem = etree.Element('para')
            iItem.attrib['name'] = k
            if v is None:
                v = ''
            iItem.attrib['value'] = v
            iRoot.append(iItem)
            
        return etree.tostring(iRoot)[3:-4]
    
    def setPics(self, shareJob):
        iResult = []
        iIndex = 0
        iList = shareJob.get("vehicle", {}).get("gallery", {}).get('photos', [])
        watermark = shareJob.get("merchant_substitute_config", {}).get("watermark", None)
        #iList.reverse()
        for iItem in iList[:16]:
            iUrl = iItem['url']
            o = urlparse(iUrl)
            if (watermark is not None) and (watermark.get("enable_sites", []).count("58.com")):
                uri = utils.pic_with_watermark_ali(o.path,
                       watermark.get("image", ""),
                       watermark.get("gravity", "NorthWest"))
                iUrl = 'http://pic.kanche.com%s'%uri
            logger.debug(iUrl)
            r = requests.get(iUrl)
            iResult.append(('pic%s'%iIndex, ('pic%s.jpg'%iIndex, r.content, 'application/octet-stream', {'Content-Length': len(r.content)})))
            #iResult.append(('pic%s'%iIndex, ('pic%s.jpg'%iIndex, str(iIndex))))
            iIndex += 1
            #break
        #logger.debug(iResult)
        return iResult
    
    def doLogin(self, username, passport):
        iCookies = self.sessionServer.getSession('openapi.58.com', username)
        if iCookies is None:
            return self.getUserInfo(username, passport)
        elif (datetime.datetime.now() - iCookies['create_at']).days + 14 < int(iCookies['expires_in']):
            return True, iCookies
        else:
            return self.refreshToken(iCookies, username, passport)

    def getCode(self, username, passport):
        s = requests.session()
        r_get = s.get('http://openapi.58.com/oauth2/authorize?response_type=code&client_id=%s'%self.client_id, headers=self.headers)
        content = r_get.text


        iData = {
            'domain':'58.com', 'callback':'handleLoginResult', 'sysIndex':1,
            'pptusername':username.encode('utf8'), 'pptpassword':passport
        }
        iHeaders = {
            'Accept-Language' : 'zh-CN,zh;q=0.8,en;q=0.6',
            'Accept-Encoding' : 'gzip, deflate',
            'Accept' : 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'User-Agent' : 'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/49.0.2623.87 Safari/537.36',
            'Connection' : 'keep-alive',
            'Cache-Control' : 'max-age=0',
            'Upgrade-Insecure-Requests' : '1',
            'Referer' : 'http://openapi.58.com/oauth2/authorize?response_type=code&client_id=%s' % self.client_id
        }
        r = s.post(url='https://passport.58.com/douilogin', data=iData, headers=iHeaders)

#        print r.status_code, '++++++++++++++', r.url, r.request.headers
#        print '|%s|'%r.text

        iResult = loads(re.findall('(\{[^\}]+\})', r.text)[0].replace("'", '"'))
        if int(iResult['code']) != 0:
            return False, r.text

        # https://passport.58.com/validcode/captcha


#        iTxt = re.findall('''\(['"]([^'"]+)''', r.text)[0]
#        iList = iTxt.split('?')[-1].split('&')
#        iResult = {}
#        for iItem in iList:
#            iKeyVal = iItem.split('=')
#            iResult[iKeyVal[0]] = iKeyVal[1]
#        if iResult['type'] != 'success':
#            return False, r.text
#        
#        r = s.get('http://openapi.58.com/backscript?domain=58.com&type=success&callback=handleLoginResult&isweak=${isweak}&uid=0')
#        iTxt = re.findall('\(([^\)]+)', r.text)
#        #print iTxt[0]
#        iResult = loads(iTxt[0].replace("'", '"'))
#        if int(iResult['code']) != 0:
#            return False, r.text
            
        r = s.get('http://openapi.58.com/oauth2/authorize?response_type=code&client_id=%s&confirm=1'%self.client_id, allow_redirects=False)
        if r.status_code != 302:
            #logger.debug(r.headers)
            return False, r.text
        iTxt = r.headers['Location']
        iTxt = re.findall('code=([^&]+)', iTxt)
        
        return True, iTxt[0]
        
    def getUserInfo(self, username, passport):
        iFlag, iCode = self.getCode(username, passport)
        if not iFlag:
            return iFlag, iCode
            
        iTimeSign = self.getTimeSign()
        iData = {
            'code': iCode,
            'grant_type':'authorization_code',
            'redirect_uri':self.call_back_url,
            'time_sign':iTimeSign,
            'client_id':self.client_id,
            'client_secret':self.getMd5('%s%s%s'%(self.client_secret, 'openapi.58.com', iTimeSign))
        }
        r = requests.post('http://openapi.58.com/oauth2/access_token', iData)
        iResult = loads(r.text)
        if 'error' in iResult.keys():
            return False, r.text
        iResult['create_at'] = datetime.datetime.now()
        self.sessionServer.setSession('openapi.58.com', username, iResult)
        return True, iResult
        
    def refreshToken(self, pToken, username, passport):
        iTimeSign = self.getTimeSign()
        iData = {
            'refresh_token':pToken['refresh_token'],
            'grant_type':'refresh_token',
            'redirect_uri':self.call_back_url,
            
            'time_sign':iTimeSign,
            'client_id':self.client_id,
            'client_secret':self.getMd5('%s%s%s'%(self.client_secret, 'openapi.58.com', iTimeSign)),
            '58user_id':pToken['uid'],
            'access_token':pToken['access_token']
        }
        r = requests.post('http://openapi.58.com/oauth2/refresh_token', iData)
        iResult = loads(r.text)
        if 'error' in iResult.keys():
            return False, r.text
        iResult['create_at'] = datetime.datetime.now()
        self.sessionServer.setSession('openapi.58.com', username, iResult)
        return True, iResult

    def callApi(self, pData, pToken, pAction = '/postservice/send', pFiles = None):
        iData = pData.copy()
        iTimeSign = self.getTimeSign()
        iData['time_sign'] = iTimeSign
        iData['client_id'] = self.client_id
        iData['client_secret'] = self.getMd5('%s%s%s'%(self.client_secret, 'openapi.58.com', iTimeSign))
        iData['58user_id'] = pToken['uid']
        iData['access_token'] = pToken['access_token']

        try:
            r = requests.post(url = 'http://openapi.58.com/oauth2/gateway%s'%pAction, data = iData, files = pFiles)
        except:
            logger.debug('post error,retry')
            try:
                r = requests.post(url = 'http://openapi.58.com/oauth2/gateway%s'%pAction, data = iData, files = pFiles)
            except:
                logger.debug('post error,retry again')
                r = requests.post(url = 'http://openapi.58.com/oauth2/gateway%s'%pAction, data = iData, files = pFiles)
#        r = requests.post(url = 'http://127.0.0.1:60088/?act=%s'%pAction, data = iData, files = pFiles)
        print r.text
        return r

    def shareVehicle(self, shareJob, infoid = None):
        shareAccount = shareJob.get("share_account", None)
        if shareAccount is None:
            return errorcode.DATA_ERROR, "缺少帐号"
        if shareAccount.get('account_type', None) == 'public':
            shareAccount['username'] = publicAccount['username']
            shareAccount['password'] = publicAccount['password']
        
#        print shareAccount['username'], shareAccount['password']
        iFlag, iCookies = self.doLogin(shareAccount['username'], shareAccount['password'])
        if not iFlag:
            return errorcode.AUTH_ERROR, iCookies
        
        vehicle = shareJob.get("vehicle", None)
        merchant = vehicle.get('merchant', None)
        address = merchant.get('address', None)
        externalSpec = shareJob.get("external_vehicle_spec", None)
        
        if address is None:
            return errorcode.DATA_ERROR, errormsg.ADDRESS_EMPTY
        cityCode = address.get('city_code', None)

        website = '58.com'
        limit = 1000 #default
        if cityCode in fiftyCityLimitList:
            limit = 50
        if cityCode in hundCityLimitList:
            limit = 100

        if infoid is None:
            check = self.isInnerAccountLimit(website, shareAccount['username'], limit, deadline="day")
            if not check:
                return errorcode.DATA_ERROR, errormsg.OUTER_ACCOUNT_LIMIT
        
        if externalSpec is None:
            logger.error("external spec missing")
            return errorcode.SPEC_ERROR, errormsg.EXTERNAL_SPEC_EMPTY
        
        iLocalId = self.citys.getCode(cityCode)
        iTitle = self.getTitleVal(externalSpec, shareJob, vehicle)
        iTmp, iPhone = self.getContact(shareJob)
        iQQ = self.getIMVal(shareJob.get("merchant_substitute_config", {}))
        
        if self.loanable(vehicle=vehicle):
            iContent = self.getContentVal_finance_58(shareJob, self.Symbol, self.lateral)
        else:
            iContent = self.getContentVal_normal_58(shareJob, self.Symbol, self.lateral)
        
        iFiles = self.setPics(shareJob)
        iData = {}
        
        iAction = '/postservice/send'
        if infoid is not None:
            iData['infoid'] = infoid
            iAction = '/postservice/update'

        iParas = self.getParam(shareJob, iLocalId)
#        iTitle = u'长安长安之星 2009款 1.0L 手动 带空调(国Ⅲ)【手续全 过户快】'
#        print '+++++++++++++++++++\n%s\n+++++++++++++++++++++++'%iTitle
        iData['cate_id'] = self.cate_id
        iData['local_id'] = iLocalId
        iData['title'] = iTitle
        iData['content'] = iContent
        iData['phone'] = iPhone
        iData['email'] = ''
        iData['im'] = iQQ
        iData['paras'] = iParas

        try:
            r = self.callApi(pData = iData, pToken = iCookies, pAction = iAction, pFiles = iFiles)
        except Exception, e:
            logger.debug("Exception:" + str(e))
            return errorcode.NETWORK_ERROR, u'网络超时: Broken pipe'

        # print r.text
        iResult = loads(r.text)
        if 'infoid' in iResult.keys() and 'url' in iResult.keys():
            if int(iResult['status']) == 3:
                logger.debug('waiting for checked')
            if infoid is None:
                self.upsertAccountNum(website, shareAccount['username'], limit, deadline="day")
            return errorcode.SUCCESS, iResult['url']
        else:
            if r.text.count('rundistance'):
                return errorcode.SITE_ERROR, u'采集的车辆行驶里程异常'
            if r.text.count("openapi 未知异常"):
                return errorcode.SITE_ERROR, errormsg.THIRD_SERVICE_SERVER_ERROR
            return errorcode.SITE_ERROR, r.text

    def updateVehicle(self, shareJob):
        iUrl = shareJob.get('url')
        if iUrl is None or iUrl == '':
            return errorcode.DATA_ERROR, 'url is empty'

        iUrl = re.findall('/(\d+)x\.s?htm', iUrl)
        if len(iUrl) == 0:
            return errorcode.DATA_ERROR, 'url is bad'
        
        return self.shareVehicle(shareJob, iUrl[0])

    def removeVehicle(self, shareJob):
        iUrl = shareJob.get('url')
        if iUrl is None or iUrl == '':
            return errorcode.DATA_ERROR, 'url is empty'

        iUrl = re.findall('/(\d+)x\.s?htm', iUrl)
        if len(iUrl) == 0:
            return errorcode.DATA_ERROR, 'url is bad'
        
        iData = {'infoid':iUrl[0]}
        
        shareAccount = shareJob.get("share_account", None)
        if shareAccount is None:
            return errorcode.DATA_ERROR, "缺少帐号"
        if shareAccount.get('account_type', None) == 'public':
            shareAccount['username'] = publicAccount['username']
            shareAccount['password'] = publicAccount['password']
        
#        print shareAccount['username'], shareAccount['password']
        iFlag, iCookies = self.doLogin(shareAccount['username'], shareAccount['password'])
        if not iFlag:
            return errorcode.AUTH_ERROR, iCookies
            
        r = self.callApi(iData, iCookies, '/delservice/delete')
        
        iResult = loads(r.text)
        if int(iResult['gateway_success']) == 1:
            return errorcode.SUCCESS, iResult['infoid']
        else:
            return errorcode.SITE_ERROR, r.text


