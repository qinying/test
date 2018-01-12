#!/usr/bin/python
# -*- coding: UTF-8 -*-
import requests
import lxml.html
import utils
import urllib2
import logger
import errorcode
import errormsg
import re
import city_xcar
import time

from base import BaseSharer

#username = u"18958795236"
#password = u"asasas123/"

Host = 'used.xcar.com.cn'
#颜色映射
color_mapping = {
    'black': 1, #黑色
    'white': 2,#白色
    'silver':3,#银灰色
    'gray': 4,#深灰色
    'champagne': 5,#香槟色
    'res': 6,#红色
    'blue': 7,#蓝色
    'green': 8,#绿色
    'yellow': 9,#黄色
    'orange': 10,#橙色
    'brown': 11,#咖啡色
    'purple': 12,#紫色
    'multi': 13,#多彩色
    "other":  14# u"其他"
}

#车辆内饰
interior_mapply = {
    'light': 2, #浅内饰
    'dark': 1,#深内饰
}
#车辆所在的省份
province_meppy = {
    u"北京市": 1,
    u"上海市": 2,
    u"天津市": 3,
    u"重庆市": 4,
    u"黑龙江省": 5,
    u"吉林省": 7,
    u"辽宁省": 6,
    u"内蒙古": 9,
    u"新疆省": 14,
    u"甘肃省": 12,
    u"宁夏省": 13,
    u"山西省": 11,
    u"陕西省": 10,
    u"河南省": 22,
    u"河北省": 8,
    u"山东省": 23,
    u"西藏省": 15,
    u"四川省": 17,
    u"青海省": 16,
    u"湖南省": 20,
    u"湖北省": 21,
    u"江西省": 32,
    u"安徽省": 24,
    u"江苏省": 25,
    u"浙江省": 26,
    u"福建省": 33,
    u"云南省": 18,
    u"贵州省": 19,
    u"广西省": 31,
    u"广东省": 30,
    u"海南省": 34,
}

#用途替换
purpose_his = {
    "personal": 1,
    "business": 3 ,
    "lease": 3,
}
#4S定期保养
maintenance_car = {
    True: 1,#有
    False: 0,#无
}
#性别
gender_male = {
    "male": 1,#男性
    "female": 0,#女性
}


__author__ = 'jesse'

class XcarSharer(BaseSharer):
    def __init__(self, sessionServer, specServer):
        super(XcarSharer, self).__init__(sessionServer, specServer)
        self.headers["Referer"] = "http://xcar.com.cn"
        self.session = requests.session()

    ##########
    #登陆入口
    ##########
    def doLogin(self, username, password):

        url = "http://my.xcar.com.cn/logging.php?action=login"
        password = utils.md5(password)
        r = self.session.get('http://my.xcar.com.cn/logging.php?action=login')
        root = lxml.html.fromstring(r.text)

        headers = {
            "Accept":"text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Encoding":"gzip, deflate",
            "Accept-Language":"zh-CN,zh;q=0.8,en;q=0.6",
            "Cache-Control":"max-age=0",
            "Connection":"keep-alive",
            "Content-Length":"273",
            "Content-Type":"application/x-www-form-urlencoded",
            # "Cookie":"_Xdwuv=5636dad33a396; _Xdwnewuv=1; mlti=@10~144643557218378819@; newcar_last_views=3%7C5897%7C%E5%A5%A5%E8%BF%AATT%E5%8F%8C%E9%97%A8%231590%7C6972%7C%E6%96%B0%E7%A6%8F%E5%85%8B%E6%96%AF%E4%B8%A4%E5%8E%A2; bbs_visitedfid=91; cooperation_referer=http%253A%252F%252Fused.xcar.com.cn%252Freg%252F; _locationInfo_=%7Burl%3A%22http%3A%2F%2Fbj.xcar.com.cn%2F%22%2Ccity_id%3A%22475%22%2Cprovince_id%3A%221%22%2C%20city_name%3A%22%25E5%258C%2597%25E4%25BA%25AC%22%7D; mlts=@10~5@; _xcar_name_utf8=%E7%A7%A6%E8%8E%B9; ad__city=475; place_prid=1; place_crid=475; place_ip=111.204.156.30_1; uv_firstv_refer=%28%2420%29/personal/3797474.htm; uv_firstv_refers=http%3A//my.xcar.com.cn/car/usedcar.php; bbs_cookietime=31536000; __isshowad=no; _Xdwstime=1448505283; xgame_ly=http%3A%2F%2Fmy.xcar.com.cn%2F; xgame_currweb=http%3A%2F%2Fmy.xcar.com.cn%2Flogging.php%3Faction%3Dlogin%26referer%3D%252F; Hm_lvt_53eb54d089f7b5dd4ae2927686b183e0=1448344486,1448421873,1448462448,1448502949; Hm_lpvt_53eb54d089f7b5dd4ae2927686b183e0=1448505283; mltn=@10~6189429155027616965>41>1448505280370>41>1448505280370>6189427038034355491>1448344485574@",
            "Host":"my.xcar.com.cn",
            "Origin":"http://my.xcar.com.cn",
            "Referer":"http://my.xcar.com.cn/logging.php?action=login&referer=%2Fcar%2Fusedcar.php",
            "Upgrade-Insecure-Requests":"1",
            "User-Agent":"Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/46.0.2490.86 Safari/537.36",


        }
        chash = root.xpath(u'//input[@id="chash"]//@value').pop(0)
        dhash = root.xpath(u'//input[@id="dhash"]//@value').pop(0)
        ehash = root.xpath(u'//input[@id="ehash"]//@value').pop(0)
        formhash = root.xpath(u'//input[@name="formhash"]//@value').pop(0)

        data = {
            'username': username,
            'password': password,
            'formhash': formhash,
            'referer': '/car/usedcar.php',
            'loginsubmit': u'提交',
            'chash': chash,
            'dhash': dhash,
            'ehash': ehash,
            'cookietime': '2592000',
        }

        req = self.session.post(url, data=data, headers=headers)
        # self.mycookie = r.cookies
        # tt = requests.utils.dict_from_cookiejar(r.cookies)

        # code = r.history[0].status_code
        # code = req.status_code
        # print 'code: ', code
        content = req.content
        if content.decode('gb2312').encode('utf8').count(u'退　　出'):
            return True
        else:
            return False

    ##########
    #发车入口
    ##########
    def shareVehicle(self, shareJob):
        #表单提交地址
        temp_url = "http://used.xcar.com.cn/post.htm?entrance=7"
        post_url = 'http://used.xcar.com.cn/Car/createvalidate'

        # self.mycookie = p.cookies
        logger.debug("xcar shareVehicle")
        account = shareJob.get("share_account", None)

        if account is None:
            logger.error("login fail")
            return errorcode.AUTH_ERROR, errormsg.LOGIN_FAIL

        username = account['username']
        password = account['password']

        successful = self.doLogin(username, password)
        if not successful:
            return errorcode.AUTH_ERROR, errormsg.LOGIN_FAIL

        # p = self.session.get(url,headers = {'Cookie':self.mycookie})
        # iCookie = requests.utils.dict_from_cookiejar(self.mycookie)
        # iCookie.update(requests.utils.dict_from_cookiejar(p.cookies))

        headers = {
            "Accept":"text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Encoding":"gzip, deflate",
            "Accept-Language":"zh-CN,zh;q=0.8,en;q=0.6",
            "Cache-Control":"max-age=0",
            "Connection":"keep-alive",
            "Content-Length":"1002",
            "Content-Type":"application/x-www-form-urlencoded",
            "Cookie":"_Xdwuv=5636dad33a396; _Xdwnewuv=1; mlti=@10~144643557218378819@; LDCLGFbrowser=ab5c48ce-f78d-411b-85dc-67d1e2924106; newcar_last_views=3%7C5897%7C%E5%A5%A5%E8%BF%AATT%E5%8F%8C%E9%97%A8%231590%7C6972%7C%E6%96%B0%E7%A6%8F%E5%85%8B%E6%96%AF%E4%B8%A4%E5%8E%A2; bbs_visitedfid=91; cooperation_referer=http%253A%252F%252Fused.xcar.com.cn%252Freg%252F; _locationInfo_=%7Burl%3A%22http%3A%2F%2Fbj.xcar.com.cn%2F%22%2Ccity_id%3A%22475%22%2Cprovince_id%3A%221%22%2C%20city_name%3A%22%25E5%258C%2597%25E4%25BA%25AC%22%7D; mlts=@10~5@; _xcar_name_utf8=%E7%A7%A6%E8%8E%B9; cms_H_news=OK; ad__city=475; uv_firstv_refer=%28%243%29; place_prid=1; place_crid=475; place_ip=111.204.156.30_1; uv_firstv_refers=http%3A//www.xcar.com.cn/; PHPSESSID=sghjma9urvtl8ssk4gc91gcfq5; _discuz_uid=9827697; _discuz_pw=708f3864bab83c0dde1fdf8b73a7a842; _xcar_name=xuser9927697; _discuz_vip=5; weibo_referer=http%3A%2F%2Fmy.xcar.com.cn%2Flogging.php%3Faction%3Dlogin%26errlog%3D1; bbs_cookietime=31536000; bbs_auth=BEyztFV6qEUNZC8i759DsF5gtiWJvRq7aHbb7ZOOWXpfiGen57JbrIbRIkqkbVxNCA; bbs_sid=Q7MvrJ; xgame_ly=http%3A%2F%2Fmy.xcar.com.cn%2F; xgame_currweb=http%3A%2F%2Fmy.xcar.com.cn%2Fcar%2Findex.php; _Xdwstime=1448504216; Hm_lvt_53eb54d089f7b5dd4ae2927686b183e0=1448344486,1448421873,1448462448,1448502949; Hm_lpvt_53eb54d089f7b5dd4ae2927686b183e0=1448504217; mltn=@10~6189429155027616965>26>1448504214536>26>1448504214536>6189427038034355491>1448344485574@",
            "Host":"used.xcar.com.cn",
            "Origin":"http://used.xcar.com.cn",
            "Referer":"http://used.xcar.com.cn/post.htm?entrance=7",
            "Upgrade-Insecure-Requests":"1",
            "User-Agent":"Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/46.0.2490.86 Safari/537.36",

        }
        #车型信息
        external_vehicle_spec = shareJob.get('external_vehicle_spec', None)
        series = external_vehicle_spec.get('series', None)
        brand = external_vehicle_spec.get('brand', None)
        model = external_vehicle_spec.get('model', None)
        pbid = brand.get('id', None)
        mdl = model.get('id', None)
        ser = series.get('id', None)
        if pbid is None:
            pbid = 0
        else:
            pbid = int(pbid)

        if ser is None:
            ser = 0
        else:
            ser = int(ser)

        if mdl is None:
            mdl = 0
        else:
            mdl = int(mdl)

        #车型价格
        vehicle = shareJob.get('vehicle', None)
        price = vehicle.get('price', None)
        quoted_price = price.get('quoted_price', None)

        if quoted_price is not None:
            quoted_price = str(round(float(quoted_price)/10000, 2))

        # 行驶里程
        vehicle = shareJob.get('vehicle', None)
        summary = vehicle.get('summary' ,None)
        mileage = summary.get('mileage', None)
        if mileage is not None:
            mileage = int(mileage /10000)

        # 车辆颜色
        vehicle = shareJob.get('vehicle', None)
        summary = vehicle.get('summary', None)
        color = summary.get('color', None)
        color = color_mapping.get(color, 14)
        color = int(color)

        # 车辆内饰
        vehicle = shareJob.get('vehicle', None)
        summary = vehicle.get('summary', None)
        interior = summary.get('interior', None)
        interior = interior_mapply[interior]
        interior = int(interior)

        #首次上牌日期
        vehicle = shareJob.get('vehicle', None)
        vehicle_date = vehicle.get('vehicle_date', None)
        registration_date = vehicle_date.get('registration_date', None)
        registration_date_str = '2014-05-27'
        if registration_date is not None:
            registration_date_str = str(registration_date)[:10]

        #车辆所在地
        vehicle = shareJob.get('vehicle', None)
        merchant = vehicle.get('merchant', None)
        address = merchant.get('address', None)
        province_name = address.get('province_name', None)
        city_code = address.get('city_code' , None)
        if province_name == u'台湾省':
            return errorcode.DATA_ERROR, errormsg.PROVINCE_FORBIDDEN
        province_op = province_meppy[province_name]

        #用途性质
        vehicle = shareJob.get('vehicle', None)
        summary = vehicle.get('summary', None)
        purpose = summary.get('purpose', None)
        purpose_name = purpose_his[purpose]
        purpose_name = int(purpose_name)

        #4s保养次数
        vehicle = shareJob.get('vehicle', None)
        summary = vehicle.get('summary', None)
        maintenance = summary.get('maintenance', None)
        maintenance_id = maintenance_car[maintenance]
        maintenance_id = int(maintenance_id)

        #年险有效日期
        vehicle = shareJob.get('vehicle', None)
        vehicle_date = vehicle.get('vehicle_date', None)
        inspection_date = vehicle_date.get('inspection_date', None)
        if inspection_date is None:
            inspection_date_str = '2016-12-01'
        else:
            inspection_date_str = str(inspection_date)[:10]

        # 保险有效期
        vehicle = shareJob.get('vehicle', None)
        vehicle_date = vehicle.get('vehicle_date', None)
        manufacture_date = vehicle_date.get('manufacture_date', None)

        if manufacture_date is None:
            manufacture_date_str = inspection_date
        else:
            manufacture_date_str = str(manufacture_date)[:10]

        # 车辆信息
        vehicle = shareJob.get('vehicle', None)
        desc = vehicle.get('desc', None)
        desc = self.getContentVal(shareJob, '\n', '')[:500]

        # 联系人
        vehicle = shareJob.get('vehicle', None)
        user = vehicle.get('user', None)
        name, mobile = self.getContact(shareJob=shareJob)

        # 性别
        vehicle = shareJob.get('vehicle', None)
        merchant = vehicle.get('merchant', None)
        user = merchant.get('user', None)
        gender = user.get('gender', None)
        gender_id = gender_male[gender]
        gender_id = int (gender_id)

        # 城区
        vehicle = shareJob.get('vehicle', None)
        merchant = vehicle.get('merchant', None)
        address = merchant.get('address', None)
        province_name = address.get('province_name', None)
        city_name = address.get('city_name', None)
        if city_name is None:
            city_name = ''

        # 表中读取数据
        city_txt = city_xcar.Cityxcar()
        city_id = city_txt.getName(city_name.encode('utf-8'))
        saleAddr = str(province_name) + str(city_name)

        # 图片
        vehicle = shareJob.get('vehicle', None)
        gallery = vehicle.get('gallery', None)
        photos = gallery.get('photos')
        urls = [photo["url"] for photo in photos]
        temp = self.upload_pic(urls)

        data = {
            'CarForm[pbid]': pbid,
            'CarForm[pserid]': ser,
            'CarForm[mid]': mdl,
            'CarForm[salePrice]': quoted_price,
            'CarForm[mileage]': mileage,
            'CarForm[color]': color,
            'CarForm[inColor]': interior,
            'CarForm[cardTime]': registration_date_str,
            'CarForm[provinceId]': province_op,
            'CarForm[cityId]': city_id,
            'CarForm[nature]': purpose_name,
            'CarForm[mainTenance]': maintenance_id,
            'CarForm[insuranceTime]': manufacture_date_str,
            'CarForm[inspectionTime]': inspection_date_str,
            'CarForm[introduction]': desc,
            'CarForm[infoPercentage]': 99,
            'CarForm[linkUser]': name,
            'CarForm[linkUserSex]': gender_id,
            'CarForm[phone]': mobile,
            'CarForm[cTime]': 1,
            'CarForm[购置税]': 1,
            'CarForm[行驶证]': 1,
            'CarForm[发票]': 1,
            'CarForm[saleAddr]': saleAddr,
            'img': temp[0],
            'carimg[]': temp[1:],
            'CarForm[xid]': 9846056,
            # 'yt0': u'确认发布',
        }

        c = self.session.get(temp_url)
        d = self.session.post(post_url, data=data, headers=headers, allow_redirects=False)
        data['yt0'] = u'确认发布'
        e = self.session.post(temp_url, data=data, headers=headers, allow_redirects=False)
        f = self.session.get(temp_url)
        # file_object = open('./xcar1.html', 'w+')
        # file_object.write(d.content)
        # file_object.close()
        #
        # file_object = open('./xcar2.html', 'w+')
        # file_object.write(e.content)
        # file_object.close()
        #
        # file_object = open('./xcar3.html', 'w+')
        # file_object.write(f.content)
        # file_object.close()

        # TODO: fixme
        # if e.history[0].status_code == 301:
        if e.status_code == 301:
            # a = requests.get(url, headers = {'Cookie':cookie})
            # headers = {"Content-type":"application/x-www-form-urlencoded", 'Referer':url, 'Cookie':cookie}
            # b = requests.post(url, data=data, headers = headers)
            # c = requests.get(url, headers = {'Referer':url, 'Cookie':cookie})
            time.sleep(3)
            return errorcode.SUCCESS, self.reUrl(shareJob)

        else:
            return errorcode.DATA_ERROR, errormsg.SITE_OTHER_ERROR

    def checkUrlId(self, url, jobId):
        o = self.session.get(url)
        return url,o.text.find(jobId)>0

    #获取url
    def reUrl(self, shareJob):
        url = 'http://my.xcar.com.cn/car/usedcar.php'
        g = self.session.get(url)
        exvehicle = shareJob['external_vehicle_spec']
        vehicle = shareJob.get('vehicle', None)
        strhtml = g.text
        hxs = lxml.html.fromstring(strhtml.decode('utf8'))
        htmlurl = hxs.xpath(u'//div[@class="used_lists"]/ul/li/p[@class="title"]/a/@href')
        for urlId in htmlurl:
            pageId,checkFlag = self.checkUrlId(urlId, str(vehicle['_id']))
           # print pageId,checkFlag,str(vehicle['_id'])
            if checkFlag:
                return pageId
        return ''
    ##########
    #下架入口
    ##########
    def removeVehicle(self, shareJob):
        urls = shareJob.get('url', None)
        url_id = re.findall('http://used.xcar.com.cn/personal/([^.]+).htm',urls)
        url_id = url_id[0]
        url = "http://my.xcar.com.cn/car/usedcar.php?action=del&carid="+url_id

        logger.debug("xcar shareVehicle")
        account = shareJob.get("share_account", None)

        if account is None:
            logger.error("login fail")
            return errorcode.AUTH_ERROR, errormsg.LOGIN_FAIL

        username = account['username']
        password = account['password']

        successful = self.doLogin(username, password)
        if not successful:
            return errorcode.AUTH_ERROR, errormsg.LOGIN_FAIL

        headers = {
            'Accept':'*/*',
            'Accept-Encoding':'gzip, deflate, sdch',
            'Accept-Language':'zh-CN,zh;q=0.8,en;q=0.6',
            'Connection':'keep-alive',
            'Cookie':'_Xdwuv=5636dad33a396; mlti=@10~144643557218378819@; newcar_last_views=3%7C5897%7C%E5%A5%A5%E8%BF%AATT%E5%8F%8C%E9%97%A8%231590%7C6972%7C%E6%96%B0%E7%A6%8F%E5%85%8B%E6%96%AF%E4%B8%A4%E5%8E%A2; cooperation_referer=http%253A%252F%252Fused.xcar.com.cn%252Freg%252F; mlts=@10~5@; _Xdwnewuv=1; _xcar_name_utf8=xuser9930341; ad__city=475; place_prid=1; place_crid=475; place_ip=111.204.156.30_1; _locationInfo_=%7Burl%3A%22http%3A%2F%2Fbj.xcar.com.cn%2F%22%2Ccity_id%3A%22475%22%2Cprovince_id%3A%221%22%2C%20city_name%3A%22%25E5%258C%2597%25E4%25BA%25AC%22%7D; _discuz_uid=9830341; _discuz_pw=28817f9a6f4f0dd209766dc2c23a3981; _xcar_name=xuser9930341; _discuz_vip=5; weibo_referer=http%3A%2F%2Fmy.xcar.com.cn%2Flogging.php%3Faction%3Dlogin%26referer%3D%252F; bbs_cookietime=31536000; bbs_auth=ABLn5gR7%2BEEIbC9168FM5Qpn4HuKuk7tPCrdvcGMAioLiTXxtbNXr4bRIkqlallADg; __isshowad=no; bbs_sid=079khn; _Xdwstime=1450945929; Hm_lvt_53eb54d089f7b5dd4ae2927686b183e0=1450319831,1450874236,1450922627,1450945945; Hm_lpvt_53eb54d089f7b5dd4ae2927686b183e0=1450945965; mltn=@10~6171417252059303305>21>1450945963917>21>1450945963917>6189427038034355491>1448344485574@',
            'Host':'my.xcar.com.cn',
            'Referer':'http://my.xcar.com.cn/car/usedcar.php',
            'User-Agent':'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/46.0.2490.86 Safari/537.36',
            'X-Requested-With':'XMLHttpRequest',
        }

        c = self.session.get(url,headers=headers)
        if c.status_code == 200:
            return errorcode.SUCCESS, '删除成功'
        else:
            return False,errormsg.SITE_OTHER_ERROR

    ##########
    #改价入口
    ##########
    def updateVehicle(self, shareJob):
        urls = shareJob.get('url', None)
        url_id = re.findall('http://used.xcar.com.cn/personal/([^.]+).htm',urls)
        url_id = url_id[0]
        url = "http://used.xcar.com.cn/index.php?r=car/Create/cid/"+ url_id
        y = self.session.get(url)
        to = lxml.html.fromstring(y.text)

        logger.debug("xcar shareVehicle")
        account = shareJob.get("share_account", None)

        if account is None:
            logger.error("login fail")
            return errorcode.AUTH_ERROR, errormsg.LOGIN_FAIL

        username = account['username']
        password = account['password']

        successful = self.doLogin(username, password)
        if not successful:
            return errorcode.AUTH_ERROR, errormsg.LOGIN_FAIL

        #车型信息
        external_vehicle_spec  = shareJob.get('external_vehicle_spec', None)
        series = external_vehicle_spec.get('series', None)
        brand = external_vehicle_spec.get('brand', None)
        model = external_vehicle_spec.get('model', None)
        pbid = brand.get('id', None)
        mdl = model.get('id', None)
        ser = series.get('id', None)
        if pbid is None:
            pbid = 0
        else:
            pbid = int(pbid)

        if ser is None:
            ser = 0
        else:
            ser = int (ser)

        if mdl is None:
            mdl = 0
        else:
            mdl = int(mdl)

        #车型价格
        vehicle = shareJob.get('vehicle', None)
        price = vehicle.get('price', None)
        quoted_price = price.get('quoted_price', None)

        if quoted_price is not None:
            quoted_price = str(round(float(quoted_price)/10000, 2))

        #行驶里程
        vehicle = shareJob.get('vehicle', None)
        summary = vehicle.get('summary',None)
        mileage = summary.get('mileage',None)
        if mileage is not None:
            mileage = (mileage /10000.0)

        #车辆颜色
        vehicle = shareJob.get('vehicle', None)
        summary = vehicle.get('summary',None)
        color = summary.get('color',None)
        color = color_mapping.get(color, "其他")
        color = int(color)

        #车辆内饰
        vehicle = shareJob.get('vehicle', None)
        summary = vehicle.get('summary', None)
        interior = summary.get('interior', None)
        interior = interior_mapply[interior]
        interior = int(interior)

        #首次上牌日期
        vehicle = shareJob.get('vehicle', None)
        vehicle_date = vehicle.get('vehicle_date', None)
        registration_date = vehicle_date.get('registration_date', None)
        if registration_date is not None:
            registration_date_str = str(registration_date)[:10]

        #车辆所在地
        vehicle = shareJob.get('vehicle', None)
        merchant = vehicle.get('merchant', None)
        address = merchant.get('address', None)
        province_name = address.get('province_name', None)
        city_code = address.get('city_code' , None)
        if province_name == u'台湾省':
            return errorcode.DATA_ERROR, errormsg.PROVINCE_FORBIDDEN
        province_op = province_meppy[province_name]

        #用途性质
        vehicle = shareJob.get('vehicle', None)
        summary = vehicle.get('summary', None)
        purpose = summary.get('purpose', None)
        purpose_name = purpose_his[purpose]
        purpose_name = int (purpose_name)

        #4s保养次数
        vehicle = shareJob.get('vehicle', None)
        summary = vehicle.get('summary', None)
        maintenance = summary.get('maintenance', None)
        maintenance_id= maintenance_car[maintenance]
        maintenance_id = int (maintenance_id)

        #年险有效日期
        vehicle = shareJob.get('vehicle', None)
        vehicle_date = vehicle.get('vehicle_date', None)
        inspection_date = vehicle_date.get('inspection_date', None)
        if inspection_date is None:
            inspection_date_str = '2016-12-01'
        else:
            inspection_date_str = str(inspection_date)[:10]

        #保险有效期
        vehicle = shareJob.get('vehicle', None)
        vehicle_date = vehicle.get('vehicle_date', None)
        manufacture_date = vehicle_date.get('manufacture_date', None)

        if manufacture_date is None:
            manufacture_date_str = inspection_date
        else:
            manufacture_date_str = str(manufacture_date)[:10]

        #车辆信息
        vehicle = shareJob.get('vehicle', None)
        desc = vehicle.get('desc', None)
        desc = self.getContentVal(shareJob,'\n','')[:500]

        #联系人
        vehicle = shareJob.get('vehicle', None)
        user = vehicle.get('user',None)
        name, mobile = self.getContact(shareJob=shareJob)

        #性别
        vehicle = shareJob.get('vehicle', None)
        merchant = vehicle.get('merchant', None)
        user = merchant.get('user', None)
        gender = user.get('gender', None)
        gender_id = gender_male[gender]
        gender_id = int (gender_id)

        #城区
        vehicle = shareJob.get('vehicle', None)
        merchant = vehicle.get('merchant', None)
        address = merchant.get('address', None)
        province_name = address.get('province_name', None)
        city_name = address.get('city_name', None)
        if city_name is None:
            city_name = ''

        # 表中读取数据
        city_txt = city_xcar.Cityxcar()
        city_id = city_txt.getName(city_name.encode('utf-8'))
        saleAddr = str(province_name) + str(city_name)

        #图片
        vehicle = shareJob.get('vehicle', None)
        gallery = vehicle.get('gallery', None)
        photos = gallery.get('photos')
        urls = [photo["url"] for photo in photos]
        temp = self.upload_pic(urls)

         #车型信息
        external_vehicle_spec  = shareJob.get('external_vehicle_spec', None)
        series = external_vehicle_spec.get('series', None)
        brand = external_vehicle_spec.get('brand', None)
        model = external_vehicle_spec.get('model', None)
        pbid = brand.get('id', None)
        mdl = model.get('id', None)
        ser = series.get('id', None)
        if pbid is None:
            pbid = 0
        else:
            pbid = int(pbid)

        if ser is None:
            ser = 0
        else:
            ser = int (ser)

        if mdl is None:
            mdl = 0
        else:
            mdl = int(mdl)

        #车型价格
        vehicle = shareJob.get('vehicle', None)
        price = vehicle.get('price', None)
        quoted_price = price.get('quoted_price', None)

        if quoted_price is not None:
            quoted_price = str(round(float(quoted_price)/10000, 2))

        #行驶里程
        vehicle = shareJob.get('vehicle', None)
        summary = vehicle.get('summary',None)
        mileage = summary.get('mileage',None)
        if mileage is not None:
            mileage = (mileage /10000.0)

        #车辆颜色
        vehicle = shareJob.get('vehicle', None)
        summary = vehicle.get('summary',None)
        color = summary.get('color',None)
        color = color_mapping.get(color, "其他")
        color = int(color)

        #车辆内饰
        vehicle = shareJob.get('vehicle', None)
        summary = vehicle.get('summary', None)
        interior = summary.get('interior', None)
        interior = interior_mapply[interior]
        interior = int(interior)

        #首次上牌日期
        vehicle = shareJob.get('vehicle', None)
        vehicle_date = vehicle.get('vehicle_date', None)
        registration_date = vehicle_date.get('registration_date', None)
        if registration_date is not None:
            registration_date_str = str(registration_date)[:10]

        #车辆所在地
        vehicle = shareJob.get('vehicle', None)
        merchant = vehicle.get('merchant', None)
        address = merchant.get('address', None)
        province_name = address.get('province_name', None)
        city_code = address.get('city_code' , None)
        if province_name == u'台湾省':
            return errorcode.DATA_ERROR, errormsg.PROVINCE_FORBIDDEN
        province_op = province_meppy[province_name]

        #用途性质
        vehicle = shareJob.get('vehicle', None)
        summary = vehicle.get('summary', None)
        purpose = summary.get('purpose', None)
        purpose_name = purpose_his[purpose]
        purpose_name = int (purpose_name)

        #4s保养次数
        vehicle = shareJob.get('vehicle', None)
        summary = vehicle.get('summary', None)
        maintenance = summary.get('maintenance', None)
        maintenance_id= maintenance_car[maintenance]
        maintenance_id = int (maintenance_id)

        #年险有效日期
        vehicle = shareJob.get('vehicle', None)
        vehicle_date = vehicle.get('vehicle_date', None)
        inspection_date = vehicle_date.get('inspection_date', None)
        if inspection_date is None:
            inspection_date_str = '2016-12-01'
        else:
            inspection_date_str = str(inspection_date)[:10]

        #保险有效期
        vehicle = shareJob.get('vehicle', None)
        vehicle_date = vehicle.get('vehicle_date', None)
        manufacture_date = vehicle_date.get('manufacture_date', None)

        if manufacture_date is None:
            manufacture_date_str = inspection_date
        else:
            manufacture_date_str = str(manufacture_date)[:10]

        #车辆信息
        vehicle = shareJob.get('vehicle', None)
        desc = vehicle.get('desc', None)
        desc = self.getContentVal(shareJob,'\n','')[:500]

        #联系人
        vehicle = shareJob.get('vehicle', None)
        user = vehicle.get('user',None)
        name, mobile = self.getContact(shareJob=shareJob)

        #性别
        vehicle = shareJob.get('vehicle', None)
        merchant = vehicle.get('merchant', None)
        user = merchant.get('user', None)
        gender = user.get('gender', None)
        gender_id = gender_male[gender]
        gender_id = int (gender_id)

        #城区
        vehicle = shareJob.get('vehicle', None)
        merchant = vehicle.get('merchant', None)
        address = merchant.get('address', None)
        province_name = address.get('province_name', None)
        city_name = address.get('city_name', None)
        if city_name is None:
            city_name = ''

        # 表中读取数据
        city_txt = city_xcar.Cityxcar()
        city_id = city_txt.getName(city_name.encode('utf-8'))
        saleAddr = str(province_name) + str(city_name)

        #图片
        vehicle = shareJob.get('vehicle', None)
        gallery = vehicle.get('gallery', None)
        photos = gallery.get('photos')
        urls = [photo["url"] for photo in photos]
        temp = self.upload_pic(urls)

        headers = {
            'Accept':'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Encoding':'gzip, deflate',
            'Accept-Language':'zh-CN,zh;q=0.8,en;q=0.6',
            'Cache-Control':'max-age=0',
            'Connection':'keep-alive',
            'Content-Length':'2653',
            'Content-Type':'application/x-www-form-urlencoded',
            'Cookie':'_Xdwuv=5636dad33a396; mlti=@10~144643557218378819@; LDCLGFbrowser=ab5c48ce-f78d-411b-85dc-67d1e2924106; newcar_last_views=3%7C5897%7C%E5%A5%A5%E8%BF%AATT%E5%8F%8C%E9%97%A8%231590%7C6972%7C%E6%96%B0%E7%A6%8F%E5%85%8B%E6%96%AF%E4%B8%A4%E5%8E%A2; cooperation_referer=http%253A%252F%252Fused.xcar.com.cn%252Freg%252F; mlts=@10~5@; _Xdwnewuv=1; _xcar_name_utf8=xuser9930341; cms_H_news=OK; _discuz_uid=9830341; _discuz_pw=28817f9a6f4f0dd209766dc2c23a3981; _xcar_name=xuser9930341; _discuz_vip=5; bbs_cookietime=31536000; bbs_auth=ABLn5gR7%2BEEIbC9168FM5Qpn4HuKuk7tPCrdvcGMAioLiTXxtbNXr4bRIkqlallADg; _locationInfo_=%7Burl%3A%22http%3A%2F%2Fbj.xcar.com.cn%2F%22%2Ccity_id%3A%22475%22%2Cprovince_id%3A%221%22%2C%20city_name%3A%22%25E5%258C%2597%25E4%25BA%25AC%22%7D; bbs_sid=yimroc; PHPSESSID=164k5kl11mvbrsbntvcusm47i5; cars=czoxNToiMzk2NTQzNSwzOTY1MjIxIjs%3D; _Xdwstime=1450929653; Hm_lvt_53eb54d089f7b5dd4ae2927686b183e0=1449543939,1450319831,1450874236,1450922627; Hm_lpvt_53eb54d089f7b5dd4ae2927686b183e0=1450929688; mltn=@10~6189431632778138222>29>1450929687756>29>1450929687756>6189427038034355491>1448344485574@',
            'Host':'used.xcar.com.cn',
            'Origin':'http://used.xcar.com.cn',
            'Referer':'http://used.xcar.com.cn/index.php?r=car/Create/cid/'+url_id,
            'Upgrade-Insecure-Requests':'1',
            'User-Agent':'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/46.0.2490.86 Safari/537.36',
        }

        data = {
            'CarForm[pbid]':pbid,
            'CarForm[pserid]':ser,
            'CarForm[mid]':mdl,
            'CarForm[salePrice]':quoted_price,
            'CarForm[mileage]':mileage,
            'CarForm[color]':color,
            'CarForm[inColor]':interior,
            'CarForm[cardTime]':registration_date_str,
            'CarForm[provinceId]':province_op,
            'CarForm[cityId]':city_id,
            'CarForm[nature]':purpose_name,
            'CarForm[mainTenance]':maintenance_id,
            'CarForm[insuranceTime]':manufacture_date_str,
            'CarForm[inspectionTime]':inspection_date_str,
            'CarForm[introduction]':desc,
            'CarForm[infoPercentage]':100,
            'CarForm[linkUser]':name,
            'CarForm[linkUserSex]':gender_id,
            'CarForm[phone]':mobile,
            'CarForm[cTime]':1,
            'CarForm[购置税]':1,
            'CarForm[行驶证]':1,
            'CarForm[发票]':1,
            'CarForm[saleAddr]': saleAddr,
            'img': temp[0],
            # 'carimg[]':22365636,
            'carimg[]':temp[1:],
            'CarForm[xid]':9830341,
            'yt0': u'保存修改',
        }

        e = requests.post(url, data=data, headers = headers)

        if e.status_code == 200:
            return errorcode.SUCCESS, self.reUrl(shareJob)
        else:
            return errorcode.DATA_ERROR,errormsg.SITE_OTHER_ERROR


    def upload_pic(self, urls):
        # 上传图片
        upload_url = "http://used.xcar.com.cn/public/file/upload"
        arr = []
        for url in urls:
            files = {
                "Filename":(None, "4953913_114138038732_2.jpg"),
                "token":(None, "2a8c416fc78be865300e5e99445c8932"),
                "timestamp":(None, "1446631643"),
                "session":(None, "10nrnnk6opon6lp1neqqpqqa50"),
                "Upload":(None, "Submit Query"),
                "Filedata":("4953913_114138038732_2.jpg",urllib2.urlopen(url)),
            }
            r = requests.post(upload_url, files=files)
            data = r.text
            imgUrl = "http://used.xcar.com.cn/index.php?r=public/load/CarImageObj.%d.liHtml" % int(data)
            r = requests.get(imgUrl)
            data = r.text
            dom = lxml.html.fromstring(data)
            src = dom.xpath(u'//input/@value').pop(0)
            arr.append(int(src))
        return arr