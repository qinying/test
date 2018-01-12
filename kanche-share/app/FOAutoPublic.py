#!/usr/bin/python
# -*- coding: UTF-8 -*-

import json
import re
import errorcode
import logger
import suds
from base import BaseSharer

publicAccount = {
    "username": u"sykkc",
    "password": u"123456"
}

HOST = "v.51auto.com"
CODEC = "GBK"
MAX_PIC = 15
timeout = 60


# 通用接口地址
common = "http://www.51auto.com/services/CommonService?wsdl"

# 操作借口地址
url = "http://www.51auto.com/services/OpenCarService?wsdl"

# 用户名密码
# username = u"beijingesc01"
# username = u"sykkc"
# password = u"123123"
# password = u"asasas123"

#commcli = suds.client.Client(common)
#cli = suds.client.Client(url)

# 颜色映射
color_mapping = {
    "black": u"黑色",
    "res": u"红色",
    "yellow": u"黄色",
    "white": u"白色",
    "blue": u"蓝色",
    "green": u"绿色",
    "gray": u"灰色",
    "orange": u"橙色",
    "silver": u"银色",
    "champagne": u"香槟色",
    "brown": u"咖啡色",
    "purple": u"紫色",
    "multi": u"多彩色",
    "other": u"其他"
}

# 用法映射
purpose_mapping = {
    "personal": 0,
    "business": 1,
    "lease": 4,
}

# 错误提示
errormsg_mapping = {
    1:  u"更新成功",
    2:  u"数据格式有错误",
    4:  u"51汽车车型vehic1key为空",
    5:  u"51汽车车型不匹配",
    6:  u"经销商ID为空或没有找到匹配经销商",
    7:  u"行驶里程为空或格式错误",
    8:  u"价格为空或错误",
    9:  u"登记日期为空或格式错误",
    10:	u"年审日期格式错误",
    11:	u"保险到期日期格式错误",
    12:	u"车船税格式错误",
    13:	u"购车日期有误",
    14:	u"图片为空或地址错误",
    15:	u"价格类别格式错误",
    16:	u"行驶证格式错误",
    17:	u"购车发票格式错误",
    18:	u"购置税格式错误",
    19:	u"维修记录格式错误",
    20:	u"过户次数格式错误",
    21:	u"车源不属于该经销商",
    22:	u"卖点格式不正确",
    23:	u"含过户费格式不正确",
    24:	u"新车价格格式不正确",
    25:	u"销售代表不属于此经销商",
    26:	u"销售代表不存在或已删除",
    27:	u"您没有权限",
    28:	u"您的IP没有被授权",
    29:	u"上个请求正在处理",
    30:	u"限制相同经销商的同一车源只能一天更新一次",
    31:	u"限制相同经销商的同一辆车源不能重复推送",
    -1: u"其他错误"
}


class FOAutoSharer(BaseSharer):
    def __init__(self, session_server, spec_server):
        super(FOAutoSharer, self).__init__(session_server, spec_server)
        self.commcli = suds.client.Client(common)
        self.cli = suds.client.Client(url)

    # =======================================================
    #  发车 for 51auto by yjy on 2015-09-16
    # =======================================================
    def shareVehicle(self, shareJob):
        """
        发车
        :param shareJob: mongo中读取的share_job
        :return:
        """
        vehicle = self.build_vehicle(shareJob)
        (username, password) = self.get_account(shareJob)
        code = self.insert_vehicle(username, password, vehicle)
        if code > 1000000:
            logger.debug("publish success")
            return errorcode.SUCCESS, "http://www.51auto.com/buycar/%s.html" % code
        else:
            logger.error("publish failed")
            logger.debug("****************error code: " + str(code))
            return errorcode.DATA_ERROR, errormsg_mapping.get(code, "其他错误")

    # =======================================================
    # 下架 for 51auto by yjy on 2015-09-16
    # =======================================================
    def removeVehicle(self, shareJob):
        """
        下架车源,对应51auto接口中的车源状态改为已售
        :param shareJob: mongo中读取的share_job
        :return: 提示信息
        """
        carid = self.get_carid(shareJob)
        (username, password) = self.get_account(shareJob)
        code = self.delete_vehicle(username, password, carid)
        if code == 1:
            logger.debug("remove success")
            return errorcode.SUCCESS, "reomve success for 51auto-Public"
        else:
            logger.debug("****************error code: " + str(code))
            logger.error("remove faild, error msg = %s" % (errormsg_mapping.get(code, "其他错误")))
            return errorcode.DATA_ERROR, errormsg_mapping.get(code, "其他错误")

    # =======================================================
    # 改价 for 51auto by yjy on 2015-09-16
    # =======================================================
    def updateVehicle(self, shareJob):
        """
        改价
        :param shareJob: mongo中读取的share_job
        :return:
        """
        car_id = self.get_carid(shareJob)
        vehicle = self.build_vehicle(shareJob, car_id)
        (username, password) = self.get_account(shareJob)
        code = self.insert_vehicle(username, password, vehicle)
        if code == 1:
            logger.debug("update success")
            return errorcode.SUCCESS, "http://www.51auto.com/buycar/%s.html" % car_id
        else:
            logger.debug("****************error code: " + str(code))
            logger.error("update error, error code = %s" % code)
            return errorcode.OTHER, errormsg_mapping.get(code, "其他错误")

    def get_account(self, shareJob):
        account = shareJob.get("share_account", {})
        usr = account.get("username", "")
        pwd = account.get("password", "")
        return usr, pwd

    def get_brands(self, usr, pwd):
        """
        获取51汽车所有品牌信息
        :param usr: 用户名
        :param pwd: 密码
        :return:
        """
        data = self.commcli.service.getBrandList(usr, pwd)
        return data

    def get_familys(self, usr, pwd, brand):
        """
        获取指定品牌下的车系
        :param usr: 用户名
        :param pwd: 密码
        :param brand:    品牌名称
        :return:
        """
        data = self.commcli.service.getFamilyByBrand(usr, pwd, brand)
        return data

    def get_made_year(self, usr, pwd, code, family):
        """
        获取指定车系的制造年份
        :param usr: 用户名
        :param pwd: 密码
        :param code:     产商代码
        :param family:   车系代码
        :return:
        """
        data = self.commcli.service.getYearList(usr, pwd, code, family)
        return data

    def get_styles(self, usr, pwd, code, family, year):
        """
        获取车型
        :param usr: 用户名
        :param pwd: 密码
        :param code:     产商代码
        :param family:   车系代码
        :param year:     制造年份
        :return:
        """
        data = self.commcli.service.getFileList(usr, pwd, code, family, year)
        return data

    def insert_vehicle(self, usr, pwd, vehicle):
        """
        新增车源接口
        :param usr: 用户名
        :param pwd: 密码
        :param vehicle:  车源数据信息,详细见51-看看车接口文档
        :return: 新增成功返回车源id,其余返回错误代码
        """
        vehicle_id = self.cli.service.setVehicle(usr, pwd, vehicle)
        return vehicle_id

    def update_vehicle(self, usr, pwd, vehicle):
        """
        修改车源接口
        :param usr: 用户名
        :param pwd: 密码
        :param vehicle:  车源数据信息,必须带车源id,详细见51-看看车接口文档
        :return: 更新成功返回1,其余返回错误代码
        """
        code = self.cli.service.setVehicle(usr, pwd, vehicle)
        return code

    def delete_vehicle(self, usr, pwd, vehicle_id):
        """
        将车源状态改为已售,即下架
        :param usr: 用户名
        :param pwd: 密码
        :param vehicle_id: 车型id(51网站上的车型id)
        :return:
        """
        code = self.cli.service.rmVehicle(usr, pwd, vehicle_id)
        return code

    def get_carid(self, job):
        """
        匹配出下架的url,拿到车源id
        :param job:
        :return: carid
        """
        vehicle_url = job.get("url", None)
        if vehicle_url is None or len(vehicle_url) == 0:
            return -1
        carid = re.findall("\d{7}", job.get("url", None))
        if len(carid) > 0:
            return carid[0]
        return carid

    def build_vehicle(self, job, carid=""):
        """
        构建发车json对象
        :param job:
        :param carid:
        :return: vehicle
        """
        vehicle_obj = job.get("vehicle", {})
        vehicle_date = vehicle_obj.get("vehicle_date", {})
        summary = vehicle_obj.get("summary", "")
        gallery = vehicle_obj.get("gallery", {})
        photos = gallery.get("photos", {})
        document = vehicle_obj.get("document", {})

        # 注册时间
        register_date = vehicle_date.get("registration_date", "")
        reg_year = register_date.year
        reg_month = register_date.month

        # 检查时间
        inspection_date = vehicle_date.get("inspection_date", "")
        inspection_year = inspection_date.year
        inspection_month = inspection_date.month

        # 购买税
        has_purchase_tax = document.get("purchase_tax", True)
        surtax = 1
        if not has_purchase_tax:
            surtax = -1

        # 过户发票
        invoice = 1
        has_tranfer_ticket = document.get("transfer_ticket", True)
        if not has_tranfer_ticket:
            invoice = -1

        # 过户次数,规则具体参照文档,99为1手车
        transfer = summary.get("trade_times", 99)
        if transfer == 0:
            transfer = 99
        if transfer > 5 and transfer is not 99:
            transfer = 10

        # 图片
        picture_urls = ",".join(map(lambda obj: obj.get("url", ""), photos))

        # 颜色
        color = color_mapping.get(summary.get("color", {}), "其他")

        # 用途
        usage = purpose_mapping.get(summary.get("purpose", None), 0)

        # 价格类型,一口价
        price_type = 2

        # 行程
        mileage = int(summary.get("mileage", 1))

        # 是否有驾驶证
        has_licenese = -1
        licenese_num = summary.get("license_number", None)
        if licenese_num is not None:
            has_licenese = 1

        vehiclekey = job["external_vehicle_spec"]["model"]["id"]
        price = job["vehicle"]["price"]["quoted_price"]
        # description = job["vehicle"]["desc"]["detail"]

        description = self.getContentVal(shareJob=job)

        temp = {
            "car_id": carid,
            "vehiclekey": vehiclekey,
            "picture_urls": picture_urls,
            "usages": usage,
            "color": color,
            "distance": mileage,
            "price": price,
            "price_type": price_type,
            "reg_year": reg_year,
            "reg_month": reg_month,
            "description": description,
            "driving_license": has_licenese,
            "invoice": invoice,
            "surtax": surtax,
            "insurance_year": inspection_year,
            "insurance_month": inspection_month,
            "usetax_year": inspection_year,
            "usetax_month": inspection_month,
            "mot_year": inspection_year,
            "mot_month": inspection_month,
            "transfer": transfer,
            "repair_recorder": 1
        }

        vehicle = json.dumps(temp)
        return vehicle
