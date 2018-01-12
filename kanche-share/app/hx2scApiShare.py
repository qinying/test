#!/usr/bin/python
# -*- coding: UTF-8 -*-

import requests
import json
import urllib2
import hashlib
import pprint
import data_model
import errorcode
import errormsg
import re
import logging as log
from base import BaseSharer
import logger

__author__ = 'zhuonima'

# 颜色映射
color_mapping = {
    "black": 1,
    "red": 2,
    "yellow": 6,
    "white": 4,
    "blue": 3,
    "green": 5,
    "gray": 8,
    "orange": 9,
    "silver": 7,
    "champagne": 11,
    "other": 10
}

# 用户名-秘钥
username_mapping = {
    "shenyangkankanche": "b09651f80b2d2c9156c5e4d6ed364528be15cae43da8359d",
    "shanghaikankanche": "ca22854ded101b6556c5e4d6ed364528be15cae43da8359d",
    "wuxikankanche": "a808edd15a5bb715c608881dfc4e12d1",
    "hefeikankanche": "6de8f97e80cead40ba401180d8de1b61",
    "suzhoukankanche": "5f75ff9bd4d67ecae576b6c2215bed8b",
    "dongguankankanche": "ca223d61c5c24e3156c5e4d6ed364528be15cae43da8359d",
    "hangzhoukankanche": "dcc0c2ce735b31b156c5e4d6ed364528be15cae43da8359d",
    "nanningkankanche": "cdb5cc85f07033090b224d42e0a8771bd9bed9339d701aa5",
    "nanjingkankanche": "9eb00865f85ad0210b224d42e0a8771bd9bed9339d701aa5",
    "jinankankanche": "6b9fd13735d2f414ba401180d8de1b61",
    "wuhankankanche": "816c802a3ee13ee7ba401180d8de1b61",
    "changshakankanche": "d65f77a31d55d51e56c5e4d6ed364528be15cae43da8359d",
    "wenzhoukankanche": "14a154f7e925bdf50b224d42e0a8771bd9bed9339d701aa5",
    "hushikankanche": "ec2ecb922809909fba401180d8de1b61",
    "Bjkankanche": "9bef6a0b509ba97c83391b3c0baa6836",
    "baotoukankanche": "d2319c5704d8fd89e576b6c2215bed8b",
    "sjzkankanche": "0cb53936db2d5b7fe89c4ac52a73d789",
    "zhengzhoukankanche": "114191d40b3fdfba06555aaa2a5353f177a0ffb9080d21c5",
    "fuzhoukankanche": "ae73cd587feba2c1e576b6c2215bed8b",
    "guangzhoukankanche": "1123fa6a3aca49a806555aaa2a5353f177a0ffb9080d21c5",
    "foshankankanche": "fba5dd449f6791c8e576b6c2215bed8b",
    "haerbinkankanche": "1a42331af663cd490b224d42e0a8771bd9bed9339d701aa5",
    "XAkankanche": "bae9bc17646ec88c83391b3c0baa6836",
    "Dlkankanche": "5e004f37ac35134183391b3c0baa6836",
    "TJkankanche": "b6284f485848ca7483391b3c0baa6836",
    "chengdukankanche": "f7405122dd96305d0b224d42e0a8771bd9bed9339d701aa5",
    "chongqingkankanche": "ac6a08785f0b9840223b32befd82d6b577a0ffb9080d21c5",
    "changchunkankanche": "70d6f1d3e3c1c1ba4a135f3b6c3c338c77a0ffb9080d21c5",
}

# 手动自动
gear_mapping = {
    u'手动': 2,
}

class Hx2scAPISharer(BaseSharer):
    """
    华夏api接口
    1.shareVehicle  -> 发车
    2.updateehicle  -> 改价
    3.removeVehicle -> 删除
    """

    def __init__(self, session_srv, spec_srv):
        super(Hx2scAPISharer, self).__init__(session_srv, spec_srv)
        self.post_headers = {
            "X-Requested-With": "XMLHttpRequest",
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_4) "
                          "AppleWebKit/537.36 (KHTML, like Gecko) "
                          "Chrome/45.0.2454.93 Safari/537.36",
            "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
        }

        ###############################
        #  prod=生产环境, test=测试环境  #
        #  部署时请修改为 prod           #
        ################################
        self.mode = 'prod'
        if self.mode == 'prod':
            self.baseurl = "http://www.hx2car.com"
            self.post_headers['Origin'] = "http://www.hx2car.com/"
        else:
            self.baseurl = "http://www.2schome.net"
            self.post_headers['Origin'] = "http://www.2schome.net"
        self.session = requests.session()
        self.util = data_model.DataModelUtil()

    def shareVehicle(self, job):
        """
        华夏api发车
        :param job:
        :return: 成功/错误码, 提示信息
        """
        website = 'hx2car.com'
        username = self.util.get_account(job)['username']
        limit = 50

        ##check share_account
        check = self.isInnerAccountLimit(website, username, limit, deadline="day")
        if not check:
            return errorcode.DATA_ERROR, errormsg.OUTER_ACCOUNT_LIMIT

        data = self.post_form(job)
        publish_url = self.baseurl + "/hx2car/savecar.htm"
        h = self.session.post(publish_url, data=data)
        ret = json.loads(h.text)
        (state, msg) = ret.get('state', None), ret.get('message', None)
        carid = ret.get('carid', '')

        # state = True
        # carid = '110'

        if state is True:
            #upsert account num for hx2car
            self.upsertAccountNum(website, username, limit, deadline="day")
            if self.mode is 'prod':
                return errorcode.SUCCESS, 'http://www.hx2car.com/details/%s' % carid
            else:
                return errorcode.SUCCESS, 'http://www.2schome.net/details/%s' % carid
        else:
            return errorcode.DATA_ERROR, errormsg.VEHICLE_EMPTY

    def updateVehicle(self, job):
        """
        华夏api改价接口
        :param job:
        :return:
        """
        carid = re.findall('\d{9}', job['url']).pop(0)
        data = self.post_form(job)
        data['id'] = carid
        update_url = self.baseurl + "/hx2car/savecar.htm"
        h = self.session.post(update_url, data=data)
        ret = json.loads(h.text)
        (state, msg) = ret.get('state', None), ret.get('message', None)
        if state is True:
            return errorcode.SUCCESS, errormsg.SUCCESS
        else:
            return errorcode.DATA_ERROR, errormsg.VEHICLE_URL_EMPTY

    def removeVehicle(self, job):
        """
        华夏api下架接口
        :param job:
        :return:
        """
        try:
            carid = re.findall('\d{9}', job['url']).pop(0)
        except TypeError:
            return errorcode.DATA_ERROR, errormsg.VEHICLE_URL_EMPTY
        remove_url = self.baseurl + '/hx2car/delcar.htm'
        if self.mode is 'prod':
            usr = self.util.get_account(job)['username']
            usr = username_mapping.get(usr, '')
            pwd = self.util.get_account(job)['password']
        else:
            usr = '4895b01bb97160cd'
            pwd = '123456'
        pwd = self.encode_pwd(pwd)
        data = {
            'loginname': usr,
            'password': pwd,
            'ids': carid
        }
        h = self.session.post(remove_url, data=data)
        ret = json.loads(h.text)
        (state, msg) = ret.get('state', False), ret.get('message', '')
        if state is True:
            return errorcode.SUCCESS, errormsg.SUCCESS
        else:
            return errorcode.DATA_ERROR, errormsg.VEHICLE_URL_EMPTY

    def doLogin(self, username, password):
        pass

    @staticmethod
    def encode_pwd(pwd):
        """
        按照华夏规则加密字符串
        :param pwd:
        :return:
        """
        m = hashlib.md5()
        m.update(pwd)
        password = m.hexdigest()
        password += 'HXPUBCARINTERFACE'
        m = hashlib.md5()
        m.update(password)
        return m.hexdigest()

    def post_form(self, job):
        """
        构造接口数据
        :param job:
        :return:
        """
        # 用户名密码
        if self.mode is 'prod':
            usr = self.util.get_account(job)['username']
            usr = username_mapping.get(usr, '')
            pwd = self.util.get_account(job)['password']
        else:
            usr = '4895b01bb97160cd'
            pwd = '123456'

        pwd = self.encode_pwd(pwd)

        # 上牌时间
        reg_date = self.util.get_vehicle_date_reg(job)
        use_year = reg_date.year
        use_month = reg_date.month

        # 车辆类型
        big_type = '1'

        # 车辆价格
        money = self.util.get_price(job).get("quoted_price", None)
        money /= 10000.0

        # 车辆id, 没有id时为新增
        vid = ''

        # 自动,手动(1:自动挡，2:手动档，3:手自一体)
        # 如果没有默认自动
        car_auto = gear_mapping.get(self.util.get_geal(job), 1)

        # 营运标志
        car_foruse = self.util.get_vehicle_purpose(job)
        if car_foruse is "personal":
            car_foruse = 1
        else:
            car_foruse = 2

        # 车辆型号
        car_type = self.util.get_ext_model_id(job)

        # 品牌相关(1级,2级,品牌型号)
        par_serial = self.util.get_car_brand_id(job)
        son_serial = self.util.get_car_series_id(job)
        brand_str = self.util.get_car_brand(job)["name"]

        # 颜色
        color = self.util.get_car_color(job)
        color = color_mapping.get(color, 10)

        # 公里数
        journey = self.util.get_vehicle_summary(job).get("mileage", 0)

        # 按揭,非按揭
        mortgage = 1

        # 燃油类型(以下其中一种)
        # (1, "汽油" 2, "柴油" 3, "电动" 4, "混合动力" 5, "燃气")
        oil_wear = 1

        # 座位数, 默认为4
        seats = 4

        # 能否过户(能, 不能)
        transfer = 1

        # 图片地址
        logger.debug('upload pictures')
        photos = self.util.get_car_photos(job)
        urls = [photo["url"] for photo in photos]

        # 这个是传递给华夏api的数据
        pic_urls = self.upload_pic(urls)

        # 描述
        memo = self.util.get_desc(job).get('detail', None)

        memo = '{"desc": "%s"}' % memo

        param = {
            "loginname": usr,
            "password": pwd,
            "useYear": use_year,
            "useMonth": use_month,
            "bigType": big_type,
            "money": money,
            "id": vid,
            "carAuto": car_auto,
            "carForuse": car_foruse,
            "carType": car_type,
            "sonSerial": son_serial,
            "parSerial": par_serial,
            "brandStr": brand_str,
            "color": color,
            "journey": journey,
            "mortgage": mortgage,
            "oilWear": oil_wear,
            "seats": seats,
            "transfer": transfer,
            "picUrls": pic_urls,
            "memo": memo,
        }
        if self.mode is 'test':
            pprint.pprint(param, indent=4)
        return param

    def upload_pic(self, photos):
        """
        华夏api上传图片
        :param photos:
        :return:
        """
        pic_urls = []
        upload_url = self.baseurl + '/car/upload.json'

        for photo in photos:
            try:
                log.debug('upload photo ing... url = [%s]' % photo)
                data = {
                    "file": ("2.jpg", urllib2.urlopen(photo)),
                }
                h = self.session.post(upload_url, files=data)
                tmp = json.loads(h.text)
                path = tmp['uploadobject']['relativePath']
                pic_urls.append(path)
            except Exception as e:
                log.error(e.message)
                continue
        return ",".join(pic_urls)
