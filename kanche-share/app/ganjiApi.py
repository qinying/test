#!/usr/bin/python
# -*- coding: UTF-8 -*-

import requests
import data_model
import cityGanji
# import data.ganji_city_domain as ganji_city_domain
from data.ganji_city_domain import ganji_info
import re
import logger
import errorcode
import errormsg
from base import BaseSharer
import time
import json
import hashlib
import config
import urllib
from decimal import *
from dt8601 import IsoDate
import tz
import string

error_dict = {
    0: u"success-成功",
    1: u"not exsist-自定义错误,自定义消息",
    2: u"此方法后端服务暂时不可用",
    3: u"Open Api接口不支持",
    4: u"Open Api接口的调用请求数达到上限",
    5: u"客户端ip没有授权",
    6: u"appkey无效",
    7: u"token 签名出错",
    8: u"请求已过期了",
    100: u"参数无效",
    102: u"Open Api方法没有授权",
    103: u"类别没有授权",
    104: u'用户没有授权',
    10000: u"帖子参数无效"
}

class GanjiSharer(BaseSharer):
    def __init__(self, sessionServer, specServer):
        super(GanjiSharer, self).__init__(sessionServer, specServer)
        '''
        http://msapi.ganji.com/1.0/{method_name}?_msapi_key={appkey}a&_msapi_time={request_time}&_msapi_token=令牌?{method_specific_parameters}
        '''
        self.appkey = 'f70499870dcf66f744431cf8c6a83d1e'
        self.appsecret = '90e49f50c86e28f3c4d484d0ae8400b4'
        self.request_time = ''
        self._msapi_token = ''
        self.url = 'http://msapi.ganji.com/1.0/%s?'
        self.username_2_userid_dict = config.ganjiUsername2UseridDict
        self.domain = ''
        self.session = requests.session()
        self.util = data_model.DataModelUtil()

    def generate_token(self, params):
        '''
        msapi_token生成方式：
        把所有的请求参数按参数名从小到大排序后，用"key=value"拼接成参数字符串A。
        注意: value 必须是urlencode(value)之后的结果
        在请求字符串A之后拼接上appsceret，再md5, 即得到验证token
        '''
        if type(params) is not dict:
            return False, None
        # 不包括_msapi_token令牌本身
        if "_msapi_token" in params.keys():
            params.pop('_msapi_token')

        result = ""
        sorted_params = sorted(params.items(), key=lambda d: d[0], reverse=False)
        for param in sorted_params:
            # print param
            result += urllib.urlencode({param[0]: param[1]})

        result += self.appsecret
        logger.debug("result in token: " + str(result))
        m = hashlib.md5()
        m.update(result)
        token = m.hexdigest()
        logger.debug("token:" + str(token))
        self.set_token(token)
        return True, token

    def get_token(self):
        return self._msapi_token

    def set_token(self, token):
        self._msapi_token = token

    def update_request_time(self):
        self.request_time = int(time.time())

    def get_request_time(self):
        return self.request_time

    def set_domain(self, domain):
        self.domain = domain

    def get_domain(self):
        return self.domain

    '''构建url
    '''
    def generate_post_url(self, method_name, params):
        params_str = ''
        logger.debug("request params: " + str(params))
        for key in params:
            # print key, params[key]
            # print "="*10
            # params_str += str(key) + "=" + urllib.quote(str(params[key])) + '&'
            params_str += urllib.urlencode({key: str(params[key])}) + '&'

        # url = self.url % (method_name, appkey, request_time, token) + '&' + params_str
        url = self.url % method_name + '&' + params_str
        logger.debug("generate_post_url: " + str(url))
        return url

    '''登陆
    '''
    def doLogin(self, username, password):
        '''
        _msapi_key 申请的的appkey
        method_name GANJI OPEN API 所有开放的API 名称(使用需要授权), 示例:post.get, geo.citylist
        _msapi_time 时间戳,发起请求的系统时间的秒值, 超过5分钟,请求失效,用于防攻击
        _msapi_token 令牌, 参考令牌的生成和验证
        '''
        pass

    def test_token(self):
        self.update_request_time()
        post_data = {
            '_msapi_time': self.get_request_time(),
            '_msapi_key': self.appkey,
            'major_category_id': 14
        }
        (success, token) = self.generate_token(post_data)
        if not success:
            logger.debug("get token failed")
        post_data['_msapi_token'] = token
        method_name = 'category.children'
        url = self.generate_post_url(method_name, post_data)
        res = requests.post(url=url, data=post_data)
        result = res.content
        logger.debug("result:" + str(result))

    def get_account_msg(self, share_job):
        '''
        :param share_job:
        :return: 账号 & 用户id
        '''
        try:
            username = share_job.get("share_account").get("username")
            user_id = self.username_2_userid_dict[username]
            return username, user_id
        except Exception, e:
            logger.error("Expection: " + str(e))
            return None, None

    def get_title(self, share_job):
        '''
        帖子标题，6-30字，不能填写电话、特殊符号
        :param share_job:
        :return: 标题 + 一句话标题
        '''
        try:
            external_vehicle_spec = share_job.get('external_vehicle_spec')
            vehicle = share_job.get('vehicle')
            spec = vehicle.get('spec')
            if external_vehicle_spec['model']['key'] == '0':
                title = external_vehicle_spec['brand']['name'] + spec['year_group'] + ' ' + spec['sale_name']
            else:
                title = external_vehicle_spec['brand']['name'] + external_vehicle_spec['series']['name'] + external_vehicle_spec['model']['name']
            ad_title = self.promotionWords(vehicle)
            return (title + ad_title)[:30]
            # return (u'[测试]' + title + ad_title)[:30]

        except Exception, e:
            logger.error('Exception: ' + str(e))
            return None

    @staticmethod
    def get_brand_id(share_job):
        try:
            external_vehicle_spec = share_job.get('external_vehicle_spec')
            brand_id = external_vehicle_spec.get('brand').get('id')
            return brand_id
        except Exception, e:
            logger.error('Exception: ' + str(e))
            return None

    @staticmethod
    def get_series_id(share_job):
        try:
            external_vehicle_spec = share_job.get('external_vehicle_spec')
            series_id = external_vehicle_spec.get('series').get('id')
            return series_id
        except Exception, e:
            logger.error('Exception: ' + str(e))
            return None

    @staticmethod
    def get_model_id(share_job):
        try:
            external_vehicle_spec = share_job.get('external_vehicle_spec')
            model_id = external_vehicle_spec.get('model').get('id')
            return model_id
        except Exception, e:
            logger.error('Exception: ' + str(e))
            return None

    def get_area_msg(self, share_job):
        '''
        vehicle.merchant.address
        :param share_job:
        :return: 地区信息
        '''
        try:
            # 'city_id' => '12',                                //枚举值来自geo.citylist接口，例如12表示北京
            # 'district_id' => '174',                           //枚举值来自geo.children接口，例如174表示朝阳,看车地点
            # 'district_name' => '朝阳',
            address = share_job.get('vehicle').get('merchant').get('address')
            city_code = address.get('city_code')
            district_code = address.get('district_code')
            city = cityGanji.CityGanji()
            ganji_domain = city.get_domain(district_code)
            ganji_district_id = city.getCode(district_code)
            ganji_district_name = city.get_chName(district_code)
            # ganji_info = .ganji_info
            ganji_city_id = None
            for item in ganji_info:
                if ganji_domain == item['city_domain']:
                    ganji_city_id = item['city_id']
            self.set_domain(ganji_domain)
            return ganji_domain, ganji_city_id, ganji_district_id, ganji_district_name
        except Exception, e:
            logger.error('Exception: ' + str(e))
            return None, None, None, None
            # (ganji_domain, ganji_city_id, ganji_district_id, ganji_district_name)

    @staticmethod
    def get_color_code(share_job):
        vehicle = share_job.get("vehicle")
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
    def get_displacement(share_job):
        summary = share_job.get('vehicle').get('summary')
        displacement = summary.get('engine_displacement')
        default_displacement = 2
        if displacement is None or '' == displacement:
            displacement = default_displacement
        return displacement

    @staticmethod
    def get_license_date(share_job):
        '''
        :param share_job:
        :return: 初等时间
        '''
        d = IsoDate.from_iso_string('2014-05-09T00:00:00.000+08:00')
        vehicle = share_job.get("vehicle", None)
        if vehicle is not None:
            vehicleDate = vehicle.get('vehicle_date', None)
            if vehicleDate is not None:
                registrationDate = vehicleDate.get('registration_date', None)
                if registrationDate is not None:
                    # d = IsoDate.from_iso_string(registrationDate)
                    d = registrationDate.astimezone(tz.HKT)
        license_year = str(d.year)
        license_month = str(d.month)
        return license_year, license_month

    @staticmethod
    def get_inspection_date(share_job):
        '''
        :param share_job:
        :return: 年检到期
        '''
        d = IsoDate.from_iso_string('2018-05-09T00:00:00.000+08:00')
        vehicle = share_job.get("vehicle", None)
        if vehicle is not None:
            vehicleDate = vehicle.get('vehicle_date', None)
            if vehicleDate is not None:
                registrationDate = vehicleDate.get('inspection_date', None)
                if registrationDate is not None:
                    d = registrationDate.astimezone(tz.HKT)
        inspection_year = str(d.year)
        inspection_month = str(d.month)
        return inspection_year + '-' + inspection_month

    @staticmethod
    def get_compulsory_date(share_job):
        '''
        :param share_job:
        :return: 强险到期
        '''
        d = IsoDate.from_iso_string('2018-05-09T00:00:00.000+08:00')
        # 如果不存在，默认等于年检时间
        vehicle = share_job.get("vehicle", None)
        if vehicle is not None:
            vehicleDate = vehicle.get('vehicle_date', None)
            if vehicleDate is not None:
                registrationDate = vehicleDate.get('compulsory_insurance_expire_date', None)
                if registrationDate is not None:
                    # d = IsoDate.from_iso_string(registrationDate)
                    d = registrationDate.astimezone(tz.HKT)
        compulsory_year = str(d.year)
        compulsory_month = str(d.month)
        return compulsory_year + '-' + compulsory_month

    @staticmethod
    def get_mileage(share_job):
        '''
        :param share_job:
        :return: 返回公里数
        '''
        try:
            mileage = share_job['vehicle']['summary']['mileage']
            return str(Decimal(mileage) / Decimal(10000))
        except Exception, e:
            logger.error('Exception: ' + str(e))
            return None

    @staticmethod
    def get_transfer_fee(share_job):
        '''
        :param share_job:
        :return: 含过户费: 默认包含:1
        '''
        default_transfer_fee = '1'
        quoted_price_include_transfer_fee = share_job.get('vehicle').get('price').get('quoted_price_include_transfer_fee', None)
        if quoted_price_include_transfer_fee is None or '' == quoted_price_include_transfer_fee:
            transfer_fee = default_transfer_fee
        if quoted_price_include_transfer_fee:
            transfer_fee = '1'
        transfer_fee = '0'
        return transfer_fee

    @staticmethod
    def get_images(share_job):
        # json.dumps([{'image_remote_url': 'http://pic.kanche.com/e95375f2-8b7d-4b31-a234-f8047aa3d8cc.jpg'},
        #                {'image_remote_url': 'http://pic.kanche.com/ab048a93-1359-4632-93e7-dc7247ec329e.jpg'}])
        try:
            photos = share_job.get('vehicle').get('gallery').get('photos')
            photo_list = []
            for photo in photos:
                url = photo['url']
                photo_list.append({'image_remote_url': url})
            return photo_list
        except Exception, e:
            logger.error('Exception: ' + str(e))
            return None

    @staticmethod
    def get_puid(share_job):
        '''
        :param share_job:
        :return: 解析出url中id
        '''
        try:
            url = share_job.get('url')
            url_id = share_job.get('url_id')
            if url is None or '' == url:
                return None
            if url_id is None or '' == url_id:
                rule = r'(\d{6,})'
                url_id = re.compile(rule).findall(url)
                if len(url_id):
                    return url_id[-1]
                else:
                    return None
            return url_id

        except Exception, e:
            logger.error('Exception: ' + str(e))
            return None

    @staticmethod
    def replace_special_character(description):
        description = description.replace('【', '[')
        description = description.replace('】', ']')
        description = description.replace('，', ',')
        description = description.replace('。', '.')
        description = description.replace('；', ';')
        description = description.replace('？', '?')
        return description

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

    def generate_vehicle_dict(self, share_job):
        (account_name, account_id) = self.get_account_msg(share_job)
        if account_name is None or account_id is None:
            return errorcode.DATA_ERROR, errormsg.SHARE_ACCOUNT_EMPTY

        title = self.get_title(share_job)
        if title is None:
            return errorcode.DATA_ERROR, errormsg.VEHICLE_EMPTY

        description = self.getContentVal_finance_ganji(share_job, Symbol="\r\n", lateral="——" * 20)[:800]
        description = self.replace_special_character(description)

        brand_id = self.get_brand_id(share_job)
        if brand_id is None:
            return errorcode.DATA_ERROR, errormsg.VEHICLE_EMPTY

        series_id = self.get_series_id(share_job)
        if series_id is None:
            return errorcode.DATA_ERROR, errormsg.VEHICLE_EMPTY

        model_id = self.get_model_id(share_job)
        if model_id is None:
            return errorcode.DATA_ERROR, errormsg.VEHICLE_EMPTY

        (ganji_domain, ganji_city_id, ganji_district_id, ganji_district_name) = self.get_area_msg(share_job)
        if (ganji_domain is None) or (ganji_city_id is None) or (ganji_district_id is None) or (ganji_district_name is None):
            return errorcode.DATA_ERROR, errormsg.DISTRICT_EMPTY

        price = self.getPrice(share_job)
        if price is None:
            return errorcode.DATA_ERROR, errormsg.VEHICLE_EMPTY
        price = str(Decimal(price) / Decimal(10000))

        (user_name, user_phone) = self.getContact(share_job)
        color = self.get_color_code(share_job)
        displacement = self.get_displacement(share_job)
        transfer_fee = self.get_transfer_fee(share_job)

        (license_year, license_month) = self.get_license_date(share_job)
        inspection_date = self.get_inspection_date(share_job)
        compulsory_date = self.get_compulsory_date(share_job)

        mileage = self.get_mileage(share_job)
        if mileage is None:
            return errorcode.DATA_ERROR, errormsg.VEHICLE_EMPTY

        # fixme: 图片是固定的，不是我给定的
        photo_list = self.get_images(share_job)
        if photo_list is None or 0 == len(photo_list):
            return errorcode.DATA_ERROR, errormsg.VEHICLE_EMPTY

        self.update_request_time()
        post_data = {
            '_msapi_time': self.get_request_time(),
            '_msapi_key': self.appkey,
            'user_id': account_id,
            'username': account_name,
            'title': title,                                 # //帖子标题，6-30字，不能填写电话、特殊符号
            'description': description,                     #  帖子描述，10-800字，不能填写电话、特殊字符
            'category_id': 6,                               # 6 车辆
            'major_category_id': 14,                        # 14 二手车
            'minor_category': brand_id,                       # 品牌，枚举值见category.children接口
            'tag': series_id,                                  # 车系，枚举值见category.children接口
            'car_id': model_id,                               # 车型，枚举值vehicle.getCarsByTagId接口
            'user_defined_category': u'自定义车型',          # 自定义车型
            'city_id': ganji_city_id,                       # 枚举值来自geo.citylist接口，例如12表示北京
            'district_id': ganji_district_id,               # 枚举值来自geo.children接口，例如174表示朝阳
            'district_name': ganji_district_name,            # 同上
            # 其他属性
            'price': price,                                  # 价格，单位万元，最多3位整数，2位小数
            'person': user_name,                             # 2-15个汉字或字母
            'phone': user_phone,                         #联系电话，如87654321-001或400-1234-5678或138********
            'im': '',                                       #QQ号码
            'deal_type': 0,                                 #0转让
            'agent': 1,                                     #1商家
            'car_color': color,                              #颜色，枚举值见下面
            'gearbox': '2',                                 #变速箱， 1手动, 2自动
            'air_displacement': displacement,               #排气量，单位：升
            'license_date': license_year,                   #上牌年份，例如2009年
            'license_math': license_month,                  #上牌月份，例如11月
            'road_haul': mileage,                           #行驶里程，单位：万公里
            "accidents": 1,                                 #有无重大事故，事故记录，1无事故，2有轻微刮蹭，3有过大修
            "insurance_date": inspection_date,              #年检到期时间
            "strong_insurance_date": compulsory_date,       #交强险到期时间
            "transfer_fee": transfer_fee,                   #过户费，过户费，1包含，默认不包含
            #图片
            'images': json.dumps(photo_list)
        }
        return errorcode.SUCCESS, post_data

    '''发车
    '''
    def shareVehicle(self, share_job):
        # self.test_token()
        # logger.debug("="*20 + 'end of test')
        (generate_code, post_msg) = self.generate_vehicle_dict(share_job)
        if generate_code != errorcode.SUCCESS:
            return generate_code, post_msg

        post_data = post_msg
        (success, token) = self.generate_token(post_data)
        if not success:
            return errorcode.LOGIC_ERROR, 'get token failed'

        post_data['_msapi_token'] = token
        method_name = 'post.publish'
        url = self.generate_post_url(method_name, post_data)
        res = requests.post(url=url, data=post_data)
        result = res.content
        logger.debug("result:" + str(result))
        result = json.loads(result)
        err_code = result['errorCode']
        err_msg = result['errorMessge']
        result_data = result['data']
        if int(err_code) != 0:
            return errorcode.DATA_ERROR, err_msg
        puid = result_data['puid']  # 1938567873 # http://jn.ganji.com/ershouche/1938567873x.htm
        # FIXME: get city_en_code
        url = 'http://' + self.get_domain() + '.ganji.com/ershouche/' + str(puid) + 'x.htm'
        return errorcode.SUCCESS, url

    '''下架
    '''
    def removeVehicle(self, share_job):
        self.update_request_time()
        puid = self.get_puid(share_job)
        if puid is None:
            return errorcode.DATA_ERROR, 'vehicle not exist or removed'
        post_data = {
            '_msapi_time': self.get_request_time(),
            '_msapi_key': self.appkey,
            'puid': puid
        }
        (success, token) = self.generate_token(post_data)
        if not success:
            return errorcode.LOGIC_ERROR, 'get token failed'
        post_data['_msapi_token'] = token
        method_name = 'post.delete'
        url = self.generate_post_url(method_name, post_data)
        res = requests.post(url=url, data=post_data)
        result = res.content
        logger.debug("result:" + str(result))
        result = json.loads(result)
        err_code = result['errorCode']
        err_msg = result['errorMessge']
        # result_data = result['data']
        # 找不到车源，当做成功处理，防止多次重试
        if 1 == int(err_code):
            logger.debug('success-404')
            return errorcode.SUCCESS, err_msg
        if int(err_code) != 0:
            return errorcode.DATA_ERROR, err_msg
        return errorcode.SUCCESS, "remove success for ganji"

    '''改价
    '''
    def updateVehicle(self, share_job):
        (generate_code, post_msg) = self.generate_vehicle_dict(share_job)
        if generate_code != errorcode.SUCCESS:
            return generate_code, post_msg

        post_data = post_msg
        post_data['puid'] = '1960732203'
        (success, token) = self.generate_token(post_data)
        if not success:
            return errorcode.LOGIC_ERROR, 'get token failed'

        post_data['_msapi_token'] = token
        method_name = 'post.edit'
        url = self.generate_post_url(method_name, post_data)
        res = requests.post(url=url, data=post_data)
        result = res.content
        logger.debug("result:" + str(result))
        result = json.loads(result)
        err_code = result['errorCode']
        err_msg = result['errorMessge']
        # 找不到车源，当做成功处理，防止多次重试
        if 1 == int(err_code):
            logger.debug('success-404')
            return errorcode.SUCCESS, err_msg
        if int(err_code) != 0:
            return errorcode.DATA_ERROR, err_msg
        return errorcode.SUCCESS, "update success for ganji"

    def getContentVal_finance_ganji(self, shareJob, Symbol="\r\n", lateral="——"*23):
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
        content += u"可分期  申请快  利率低"
        content += Symbol + u"1张身份证，秒速办理。"

        content += Symbol*2 + u"车辆信息："
        content += Symbol + u"限时活动：可分期、超低首付、超低利率、包过户、有质保、快速提车"

        # 车辆说明
        if not (model is None) and not (key is None):
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
        inspect_date = self.getTypeDate('cjshijian', vehicle.get('vehicle_date', {}))
        commercial_insurance_expire_date = self.getTypeDate('cjshijian', vehicle.get('vehicle_date', {}))
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
        # end of all

        # 车辆概况:
        content += Symbol*2 + u"车辆概况："

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

        if globalDisable is False:
            if share_account.get("account_type", None) == "substitute":
                content += Symbol*2 + u'看车网向您承诺：'
                content += Symbol + u'选车：大量优质车源，根据您的需求，推荐最好最适合的车辆。'
                content += Symbol + u'车况：208项售前检测，专业评估师把关，呈现真实车况。'
                content += Symbol + u'过户：免费过户，包办手续。'
                content += Symbol + u'质保：为8年及15万公里以内的车辆提供超低价格的1年或2万公里保修服务。'

                content += Symbol + u'付款：可分期付款，只需身份证，即可申请，超低月供, 超低月息。'

        content += Symbol*2 + str(vehicle.get('series_number', '')) + "#"
        content += str(vehicle['_id'])
        # logger.debug("content:" + str(content)[:1900])

        if "" == content:
            content = u"无车辆说明，请添加至10个字以上"
        return content[:1900]

    def getContentVal_normal_ganji(self, shareJob, Symbol="\r\n", lateral="——"*23):
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
            # 亮点配置
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

            # 车况说明，来自bss模板
            if detail != "":
                content += detail + Symbol*2

        # 统一说明 追加
        if globalDisable is False:
            if share_account.get("account_type", None) == "substitute":
                if website != 'che168.com':
                    content += u'更多选择，尽在看看车。' + Symbol

        content += str(vehicle.get('series_number', '')) + "#"
        content += str(vehicle['_id'])

        if "" == content:
            content = u"无车辆说明，请添加至10个字以上"
        return content[:1900]
