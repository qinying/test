#!/usr/bin/python
# -*- coding: UTF-8 -*-

import logger
import errormsg
import execjs
import json
import errorcode
import lxml.html
import requests
import urllib2
import re

from base import BaseSharer
from data_model import DataModelUtil

username = u"bjkkc889@sohu.com"
password = u"asasas123"

HOST = '2sc.sohu.com'

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


class SohuSharer(BaseSharer):

    def __init__(self, sessionServer, specServer):
        super(SohuSharer, self).__init__(sessionServer, specServer)
        self.s = requests.session()
        self.util = DataModelUtil()

    def doLogin(self, usr, pwd):
        """
        登录搜狐二手车
        :param usr:
        :param pwd:
        :return: 登录成功 True, 登录失败 False
        """
        url = "http://2sc.sohu.com/ctb/dealer-doLogin.do?"
        url += "isRemember=1"
        url += "&passport=" + usr
        url += "&password=" + pwd
        r = self.s.get(url)
        data = r.content.replace("var data=", "")
        data = data.decode("gbk")
        engine = execjs.get()
        data = engine.eval(data)
        success = data.get(u'isLogin', None)
        if success != '0':
            return False
        return True

    ################################
    ## 发车
    ################################
    def shareVehicle(self, shareJob):
        """
        模拟发车
        :param shareJob:
        :return: 发车是否成功状态码与提示信息
        """
        # 表单提交地址
        url = "http://2sc.sohu.com/ctb/uscar-carInsert.do"

        logger.debug("sohu shareVehicle")
        account = shareJob.get("share_account", None)
        if account is None:
            logger.error("login fail")
            return errorcode.AUTH_ERROR, errormsg.LOGIN_FAIL
        if account.get('account_type', None) == 'public':
            account['username'] = username
            account['password'] = password

        successful = self.doLogin(username, password)
        if not successful:
            return errorcode.AUTH_ERROR, errormsg.LOGIN_FAIL

        self.upload_pic(shareJob)
        self.set_header()
        param = self.post_form(shareJob)
        r = self.s.post(url, param)
        ret = json.loads("%s" % r.text)
        status = ret.get("STATUS", -1)
        carid = ret.get("key1", None)
        if status == '0':
            return errorcode.SUCCESS, "http://2sc.sohu.com/buycar/carinfo_sohu_%s.shtml" % carid
        else:
            msg = ret.get('ERRORMSG', None)
            return errorcode.DATA_ERROR, "%s" % msg

    def set_header(self, method="POST"):
        """
        设置请求头信息,暂时只有POST
        :param method:
        :return:
        """
        if method == "GET":
            pass
        if method == "POST":
            self.s.headers["Origin"] = "http://2sc.sohu.com"
            self.s.headers["X-Requested-With"] = "XMLHttpRequest"
            self.s.headers["User-Agent"] = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_4) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/45.0.2454.93 Safari/537.36"
            self.s.headers["Content-Type"] = "application/x-www-form-urlencoded; charset=UTF-8"
            self.s.headers["Referer"] = "http://2sc.sohu.com/ctb/uscar-carAdd.do?t=3.2155478508470936"

    def post_form(self, share_car):
        """
        模拟表单提交数据
        :param share_car:
        :return:
        """
        # 车型库相关
        model_id = self.util.get_ext_model_id(share_car)
        brand_id = self.util.get_car_brand_id(share_car)
        serie_id = self.util.get_car_serie_id(share_car)

        (license_privince, license_city) = self.util.get_license_code(share_car)
        if license_privince == '110000':
            license_city = '-1'

        # 颜色
        color = self.util.get_vehicle_color(share_car)
        color = color_mapping.get(color, "其他")

        # 价格
        price = self.util.get_price(share_car).get("quoted_price", None)
        if price is not None:
            price = (price / 10000.0)

        # 排量
        engine = self.util.get_engine(share_car)
        engine = engine[:len(engine)-1]

        # 变速箱
        geal = self.util.get_geal(share_car)

        # 用途
        usage = self.util.get_vehicle_purpose(share_car)
        usage = purpose_mapping.get(usage, None)

        # 描述(最多500字)
        vehicle = self.util.get_vehicle(share_car)
        # title = self.get_title(vehicle)
        title = self.promotionWords(vehicle, isSelectedBDwords=False)
        desc = self.getContentVal(share_car, '', '')[:500]

        # 模型年份
        model_year = self.util.get_ext_model_year(share_car)

        # vin
        vin = self.util.get_vin(share_car)

        # 注册时间
        reg_date = self.util.get_vehicle_date_reg(share_car)
        reg_year = reg_date.year
        reg_month = reg_date.month

        # 行程
        mileage = self.util.get_vehicle_summary(share_car).get("mileage", 0)

        # 店铺id
        shopid = self.get_shop_id(share_car)

        # 年检有效期
        insp_date = self.util.get_vehicle_date_insp(share_car)
        insp_year = insp_date.year
        insp_month = insp_date.month

        # 商业险有效期
        bus_date = self.util.get_vehicle_date_commercial(share_car)
        if bus_date is None:
            bus_year = insp_year
            bus_month = insp_month
        else:
            bus_year = bus_date.year
            bus_month = bus_date.month

        # 交强险有效期
        insurance_date = self.util.get_vehicle_date_compulsory(share_car)
        if insurance_date is None:
            insurance_year = insp_year
            insurance_month = insp_month
        else:
            insurance_year = insurance_date.year
            insurance_month = insurance_date.month

        # 联系人
        (_, _phone) = self.getContact(share_car)

        # 销售id
        (_, _, sale_id) = self.get_contact_info(_phone)

        # 图片相关,封面,图片个数,路径
        (power, count, img_str) = self.upload_pic(share_car)

        param = {
            "typeflage": u"0",
            "is_user_enter": u"0",
            "scCarVo.infor_integrity": u"64",
            "scCarVo.relocation": u"1",
            "scCarVo.car_source": u"2",
            "scCarVo.flag_source": u"1",
            "scCarVo.cid": u"0",
            "scCarVo.flag1": u"1",
            "scCarVo.flag2": u"0",
            "scCarVo.flag3": u"-1",
            "scCarVo.flag4": u"0",
            "scCarVo.flag5": u"0",
            "scCarVo.flag6": u"0",
            "addyes": u"0",
            "configArr": u"{259:0,263:0,224:0,233:0,234:0,236:0,248:0,321:0,177:1,178:1,179:0,180:0,173:0,175:0,189:0,196:0,201:0,202:0,203:0,207:0,211:0,218:0,251:0,255:0,257:0,284:0,285:0,249:0}",
            "scCarVo.vin": vin,
            "scCarVo.brand_id": brand_id,
            "scCarVo.model_id": serie_id,
            "scCarVo.model_year": model_year,
            "scCarVo.trimm_id": model_id,  # mdoel_id
            "scCarVo.color": color,
            "scCarVo.engine_size": engine,
            "scCarVo.trans_drv": geal,
            "carConfig": u"177",
            "scCarVo.license_province": license_privince,
            "scCarVo.license_city": license_city,
            "scCarVo.first_license_date_year": reg_year,
            "scCarVo.first_license_date_month": reg_month,
            "scCarVo.mileage": mileage,
            "scCarVo.car_user_type": usage,
            "type": u"5",
            "scCarVo.car_use_nature": u"0",
            "scCarVo.annual_inspection_year": insp_year,
            "scCarVo.annual_inspection_month": insp_month,
            "scCarVo.insurance_date_year": insurance_year,
            "scCarVo.insurance_date_month": insurance_month,
            "scCarVo.syx_date_year": bus_year,
            "scCarVo.syx_date_month": bus_month,
            "power": power,
            "img": img_str,
            "imglist": count,
            "scCarVo.sale_price": price,
            "scCarVo.bargain": u"1",
            "scCarVo.remark": desc,
            "tbScCarExtends.title": title,
            "scCarVo.shop_id": shopid,
            "scCarVo.inspection_address": u"on",
            "scCarVo.salesman_id": sale_id,
        }
        return param

    def upload_pic(self, share_car):
        """
        模拟上传图片
        :param share_car:
        :return: (封面图片, 图片总数, 表单提交的路径)
        """
        # 获取待上传图片url
        upload_url = "http://2sc.sohu.com/ctb/uscar-photoUpload.do"
        res = []
        photos = self.util.get_car_photos(share_car)
        urls = [photo["url"] for photo in photos]

        for url in urls:
            # 读取kanche服务器图片,上传到sohu
            files = {
                "Filename": (None, "333.jpg"),
                "spinfo": (None, "c29odXxiamtrYzg4OUBzb2h1LmNvbXwyODk5NTkzMzM"),
                "vjuids": (None, "a95116d7.14fef2e3619.0.9d31be6e"),
                "Hm_lvt_de2ee7d6016b57f5be02a56e96256609": (None, "1442816457"),
                "Hm_lvt_d211ce3553e372caa3edbe8cec623079": (None, "1442908719,1442975664,1442976333,1442998346"),
                "ppinf": (None, "2|1442998354|1444207954|bG9naW5pZDowOnx1c2VyaWQ6MTc6Ympra2M4ODlAc29odS5jb218c2VydmljZXVzZTozMDowMDAwMDAwMDAwMDAwMDAwMDAwMDAwMDAwMDAwMDB8Y3J0OjA6fGVtdDoxOjB8YXBwaWQ6NDoxMDY2fHRydXN0OjE6MXxwYXJ0bmVyaWQ6MTowfHJlbGF0aW9uOjA6fHV1aWQ6MTY6c2M0MWQ1MjliN2JlNzQ1MXx1aWQ6MTY6c2M0MWQ1MjliN2JlNzQ1MXx1bmlxbmFtZTowOnw"),
                "lastdomain": (None, "1444207954|Ympra2M4ODlAc29odS5jb218|sohu.com|1"),
                "SMAPUVID": (None, "1442816473715674"),
                "SUV": (None, "1509141432064119"),
                "Hm_lpvt_d211ce3553e372caa3edbe8cec623079": (None, "1443000865"),
                "JSESSIONID": (None, "abcYZBho04lDO5MKwJU-u"),
                "CITYCODE": (None, "110000"),
                "vjlast":(None, "1442826827.1442890718.13"),
                "Hm_lpvt_de2ee7d6016b57f5be02a56e96256609": (None, "1443001012"),
                "ppsmu": (None, "1|1442998354|1444207954|dXNlcmlkOjE3OmJqa2tjODg5QHNvaHUuY29tfHVpZDowOnx1dWlkOjA6|Y_7Bj0dRXmVMagZ16tSbRP-tTmE1F192_arjyoMKqNvYJ24H_OhPRKkmVGYVXxqGwms0v-xPQB4jUQDBd7LO9g"),
                "_swfupload_": (None, "1"),
                "IPLOC": (None, "CN1100"),
                "Upload": (None, "Submit Query"),
                "filedata": ('111.jpg', urllib2.urlopen(url))
            }
            r = requests.post(upload_url, files=files)
            data = json.loads(r.text)
            code = data.get("code", None)
            if code == 'success':
                photo = data.get("data", None)
                if photo is not None:
                    pid = photo.get("photo_id", None)
                    if pid is not None:
                        p_info = dict()
                        p_info["id"] = pid
                        res.append(p_info)
        # 最多上传21张
        return res[0]["id"], len(res[:21]), json.dumps(res[:21])

    def get_contact_info(self, phone):
        """
        获取联系人的(电话,姓名,销售id)
        :param phone:
        :return:
        """
        r = self.s.get("http://2sc.sohu.com/ctb/saler-list.do?type=1")
        root = lxml.html.fromstring(r.text)
        ids = root.xpath(u'//ul[@class="yglist"]/li/@id')
        names = root.xpath(u'//ul[@class="yglist"]/li/p[@class="pl salesman_qq"]/span/text()')
        phones = root.xpath(u'//ul[@class="yglist"]/li/p[@class="pl"]/span/text()')
        phones = [phones[i] for i in range(len(phones)) if i % 2 == 0]
        contacts = [(phones[i], names[i], ids[i]) for i in range(len(ids))]
        for contact in contacts:
            (_phone, _name, _id) = contact
            if phone.strip() == _phone.strip():
                return _phone.strip(), _name.strip(), _id.strip()

    @staticmethod
    def get_shop_id(share_car):
        """
        获取店铺地址id
        :return:
        """
        # r = self.s.get("http://2sc.sohu.com/ctb/uscar-carAdd.do")
        # root = lxml.html.fromstring(r.text)
        # 店铺id
        # shops = root.xpath(u"//p[@class='ptb']/input[@name='scCarVo.inspection_address']")
        # if len(shops) > 0:
        #     shop = shops[0]
        #     shopid = shop.attrib.get('onclick', None)
        #     shopid = re.findall('javascript:getshopid\((.+)\)', shopid)[0]
        #     return shopid
        shopid = share_car["share_account"]["username"]
        return shopid

    @staticmethod
    def get_title(vehicle):
        line = u'手续全 包过户'
        brief = vehicle.get('desc', None).get('brief', '')
        if brief != '':
            line = brief.strip('\n')
        return line
