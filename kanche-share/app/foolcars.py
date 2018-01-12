#!/usr/bin/python
# -*- coding: UTF-8 -*-
from base import BaseSharer
import requests
import logger
import errormsg
import errorcode
import urllib2
import urllib
import lxml.html
import utils
import datetime
import cityfoolcar
import re
__author__ = 'qinying'
#username = u'18301080830'
#password = u'asasas123'
Host = 'www.foolcars.com'

#颜色映射
color_mapping = {
    'black': 1, #黑色
    'white': 4,#白色
    'silver':12,#银灰色
    'gray': 11,#深灰色
    'champagne': 15,#香槟色
    'res': 3,#红色
    'blue': 2,#蓝色
    'green': 7,#绿色
    'yellow': 8,#黄色
    'orange': 17,#橙色
    'brown': 14,#咖啡色
    'purple': 10,#紫色
    'multi': 15,#多彩色
    'silver': 5,#银色
    "other": 99,#其他
    #无金色 6 粉色 9 奶白色 13 墨绿色 16 米色20 黑米色 21
}

gear_pp = {

    u"手动":1,
    u"自动":2,
    u"手自一体":3,
    u"无级变速":4,
    u"双离合":5,
    u"其它":6,

}
fuel_op ={
    u"汽油":1,
    u"天然气":3,
    u"油电混合":4,
    u"柴油":5,
    u"多燃料":6,
    u"纯电动":7,
    u"油气混合":8,
    u"石油气":9,
    u"其他":10,
}
drii = {
    u"前驱":1,
    u"后驱":2,
    u"前置四驱":4,
    u"全时四驱":5,
    u"其它":6,

}
class FoolcarsSharer(BaseSharer):

    def __init__(self, sessionServer, specServer):
        super(FoolcarsSharer, self).__init__(sessionServer, specServer)
        self.headers["Referer"] = "http://www.foolcars.com"
        self.session = requests.session()

    #登录入口
    def doLogin(self, username, password):
        url = "http://www.foolcars.com/user/login.aspx?action=addcar"

        headers = {
            "Accept":"text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Encoding":"gzip, deflate",
            "Accept-Language":"zh-CN,zh;q=0.8,en;q=0.6",
            "Cache-Control":"max-age=0",
            "Connection":"keep-alive",
            "Content-Length":"795",
            "Content-Type":"application/x-www-form-urlencoded",
            "Host":"www.foolcars.com",
            "Origin":"http://www.foolcars.com",
            "Referer":"http://www.foolcars.com/user/login.aspx?action=addcar",
            "Upgrade-Insecure-Requests":"1",
            "User-Agent":"Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/46.0.2490.86 Safari/537.36",
        }

        data = {
            'username': username,
            'password': password,
            'ctype': 2,
            'ckey': u'请输入关键字',
            'ctl00$ContentPlaceHolder1$txtUsername': username,
            'ctl00$ContentPlaceHolder1$txtPass': password,
            'ctl00$ContentPlaceHolder1$cbkrempwd': 'on',
            'ctl00$ContentPlaceHolder1$Button1': '',
            'ctl00$ContentPlaceHolder1$rdgetpwd': 'phone',
            'ctl00$ContentPlaceHolder1$txtgetusername': '',
            'ctl00$ContentPlaceHolder1$txtcode': '',
            'ctl00$ContentPlaceHolder1$txtsetpwd': '',
            'ctl00$ContentPlaceHolder1$txtresetpwd': '',
        }

        tg = self.session.get("http://www.foolcars.com/user/login.aspx?action=addcar")
        uuf = tg.text.replace("gb2312","utf-8")
        deem = lxml.html.fromstring(uuf)
        ff = deem.xpath(u'//form[@id="aspnetForm"]/div/input[@id="__VIEWSTATE"]/@value')
        data['__VIEWSTATE'] = ff[0]
        print(data['__VIEWSTATE'])
        ii = deem.xpath(u'//form[@id="aspnetForm"]/div/input[@id="__VIEWSTATEGENERATOR"]/@value')
        data['__VIEWSTATEGENERATOR'] = ii[0]
        print(data['__VIEWSTATEGENERATOR'])
        r = self.session.post(url, data=data, headers=headers)
        #self.session.get("http://www.foolcars.com/ershouche/mchushou.aspx")
        eg = r.status_code
        if eg == 200:
            return True
        else:
            return False


    #发车入口
    def shareVehicle(self, shareJob):

        url = "http://www.foolcars.com/ershouche/mchushou.aspx"
        logger.debug("foolcars shareVehicle")
        account = shareJob.get("share_account", None)

        if account is None:
            logger.error("login fail")
            return errorcode.AUTH_ERROR, errormsg.LOGIN_FAIL

        username = account["username"]
        password = account["password"]

        successful = self.doLogin(username, password)
        if not successful:
            return errorcode.AUTH_ERROR, errormsg.LOGIN_FAIL
        #车辆基本信息
        external_vehicle_spec  = shareJob.get('external_vehicle_spec', None)
        series = external_vehicle_spec.get('series', None)
        brand = external_vehicle_spec.get('brand', None)
        model = external_vehicle_spec.get('model', None)
        pbid = brand.get('id', None)
        mdl = model.get('id', None)
        ser = series.get('id', None)
        series_name = series.get('name', None)
        model_name  = model.get('name', None)
        oo = str(series_name)+str(model_name)
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

        #行驶里程
        vehicle = shareJob.get('vehicle', None)
        summary = vehicle.get('summary',None)
        mileage = summary.get('mileage',None)
        if mileage is not None:
            mileage = (mileage /10000.0)

        #排量
        vehicle_spec_detail = shareJob.get('vehicle_spec_detail', None)
        details = vehicle_spec_detail.get('details', None)
        y =details[23]

        #车辆颜色
        vehicle = shareJob.get('vehicle', None)
        summary = vehicle.get('summary',None)
        color = summary.get('color',None)
        color = color_mapping.get(color, "其他")
        color = int(color)
        #
        #  #车辆内饰
        # vehicle = shareJob.get('vehicle', None)
        # summary = vehicle.get('summary', None)
        # interior = summary.get('interior', None)
        # interior = interior_mapply[interior]
        # interior = int(interior)
        #四驱
        vehicle_spec_detail = shareJob.get('vehicle_spec_detail', None)
        details = vehicle_spec_detail.get('details', None)
        dri = details[55]
        drir = drii[dri]

        #汽油
        vehicle_spec_detail = shareJob.get('vehicle_spec_detail', None)
        details = vehicle_spec_detail.get('details', None)
        fuel = details[25]
        fuell = fuel_op[fuel]

        #手动
        vehicle_spec_detail = shareJob.get('vehicle_spec_detail', None)
        details = vehicle_spec_detail.get('details', None)
        ddl_gear = details[42]
        gear = gear_pp[ddl_gear]

        #车辆信息
        vehicle = shareJob.get('vehicle', None)
        desc = vehicle.get('desc', None)
        desc = self.getContentVal(shareJob,'\n','')[:500]

        #首次上牌时间
        vehicle = shareJob.get('vehicle', None)
        vehicle_date = vehicle.get('vehicle_date', None)
        registration_date = vehicle_date.get('registration_date', None)
        year = registration_date.year
        month = registration_date.month

        #年险有效日期
        vehicle = shareJob.get('vehicle', None)
        vehicle_date = vehicle.get('vehicle_date', None)
        inspection_date = vehicle_date.get('inspection_date', None)
        years = inspection_date.year
        months = inspection_date.month

        #保险有效期
        vehicle = shareJob.get('vehicle', None)
        vehicle_date = vehicle.get('vehicle_date', None)
        manufacture_date = vehicle_date.get('manufacture_date', None)
        man_year = manufacture_date.year
        man_month = manufacture_date.month

        #城区
        vehicle = shareJob.get('vehicle', None)
        merchant = vehicle.get('merchant', None)
        address = merchant.get('address', None)
        province_name = address.get('province_name', None)
        city_name = address.get('city_code', None)

        #表城市
        city_txt = cityfoolcar.Cityfoolcar()
        city_id = city_txt.getName(city_name.encode('utf-8'))



        headers = {
            "Accept":"*/*",
            "Accept-Encoding":"gzip, deflate",
            "Accept-Language":"zh-CN,zh;q=0.8,en;q=0.6",
            "Connection":"keep-alive",
            "Content-Length":"17332",
            "Content-Type":"application/x-www-form-urlencoded; charset=UTF-8",
            "Host":"www.foolcars.com",
            "Origin":"http://www.foolcars.com",
            "Referer":"http://www.foolcars.com/ershouche/mchushou.aspx",
            "User-Agent":"Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/46.0.2490.86 Safari/537.36",
            "X-Requested-With":"XMLHttpRequest",
        }

        data ={
            'CBL3$2':'on',
            'ctl00$ContentPlaceHolder1$txtshopname':'',
            'cartype':1,
            'ctl00$ContentPlaceHolder1$txtcartype':1,
            'ctl00$ContentPlaceHolder1$txtchar02':'',
            'ctl00$ContentPlaceHolder1$txtcarname':oo, #u'奥迪A4L 2015款 30 TFSI 手动 舒适型',
            'ctl00$ContentPlaceHolder1$txtbrand':pbid,
            'ctl00$ContentPlaceHolder1$txtseries':ser,
            'ctl00$ContentPlaceHolder1$txtmodel': mdl,
            'ctl00$ContentPlaceHolder1$txtroadmaintain':u'便宜,手续齐全可过户',
            'ctl00$ContentPlaceHolder1$txtchepaihao1':u'请输入前两位',
            'ctl00$ContentPlaceHolder1$txtchepaihao2':u'请输入后五位',
            'ctl00$ContentPlaceHolder1$txtchejiahao':u'请输入车架号',
            'ctl00$ContentPlaceHolder1$txtfadongjihao':u'请输入发动机号',
            'ctl00$ContentPlaceHolder1$ddl_dict_cityinfo': city_id ,
            'ctl00$ContentPlaceHolder1$ddl_citydistrict': 13,
            'ctl00$ContentPlaceHolder1$txtchar03':u'昌平区',
            'ctl00$ContentPlaceHolder1$txtchar04':'',
            'ctl00$ContentPlaceHolder1$ddl_int1': 2012,
            'ctl00$ContentPlaceHolder1$ddl_int2': 3,
            'ctl00$ContentPlaceHolder1$ddl_yesr': year,
            'ctl00$ContentPlaceHolder1$ddl_month': month,
            'ctl00$ContentPlaceHolder1$ddl_pricememo':u'不包含过户费',
            'ctl00$ContentPlaceHolder1$txtprice': quoted_price,
            'ctl00$ContentPlaceHolder1$rbl_boxcount':0,
            'ctl00$ContentPlaceHolder1$txtdisplacement': y,
            'ctl00$ContentPlaceHolder1$txtmileage': mileage,
            'ctl00$ContentPlaceHolder1$ddl_color': color,
            'ctl00$ContentPlaceHolder1$dllsafeequip':1,
            'ctl00$ContentPlaceHolder1$ddl_gear': gear,
            'ctl00$ContentPlaceHolder1$txtgear':'',
            'ctl00$ContentPlaceHolder1$ddl_usertype':1,
            'ctl00$ContentPlaceHolder1$ddl_drive': drir,
            'ctl00$ContentPlaceHolder1$ddl_fuel': fuell,
            'ctl00$ContentPlaceHolder1$txtdoorcount':'',
            'ctl00$ContentPlaceHolder1$txtseatcount':'',
            'ctl00$ContentPlaceHolder1$txtloadweight':'',
            'ctl00$ContentPlaceHolder1$txtchar01':'',
            'ctl00$ContentPlaceHolder1$txtmotortype':'',
            'ctl00$ContentPlaceHolder1$txthorsepower':'',
            'ctl00$ContentPlaceHolder1$ddl_zhihuan':0,
            'ctl00$ContentPlaceHolder1$ddl_guohu':0,
            'ctl00$ContentPlaceHolder1$ddlisyishou':0,
            'ctl00$ContentPlaceHolder1$txtfapiaojia':'',
            'ctl00$ContentPlaceHolder1$ddlnjyear': years,
            'ctl00$ContentPlaceHolder1$ddlnjmonth': months,
            'ctl00$ContentPlaceHolder1$ddlbasicequip':u'商业',
            'ctl00$ContentPlaceHolder1$ddlbxyear': man_year,
            'ctl00$ContentPlaceHolder1$ddlbxmonth': man_month,
            'ctl00$ContentPlaceHolder1$txtinsideequip':u'保险注视',
            'ctl00$ContentPlaceHolder1$txtpeizhi':u'全景天窗',
            'ctl00$ContentPlaceHolder1$txtmemo': desc,
            'ctl00$ContentPlaceHolder1$rbl_jiance':0,
            'ctl00$ContentPlaceHolder1$rbl_zhihuan':0,
            'ctl00$ContentPlaceHolder1$rbl_fx':1,
            'ctl00$ContentPlaceHolder1$rbl_releaseday':60,
            'ctl00$ContentPlaceHolder1$txt_maijia':'',
            'ctl00$ContentPlaceHolder1$txt_maijiaphone':'',
            'ctl00$ContentPlaceHolder1$txt_xiaohao':'',
         }

        rt = self.session.get("http://www.foolcars.com/ershouche/mchushou.aspx")
        lo = rt.text.replace("gb2312","utf-8")
        dem = lxml.html.fromstring(lo)
        view_state = dem.xpath(u'//form[@id="aspnetForm"]/div/input[@id="__VIEWSTATE"]/@value')
        data['__VIEWSTATE'] = view_state[0]
        t1 = data['__VIEWSTATE']
        print t1
        view_sge = dem.xpath(u'//form[@id="aspnetForm"]/div/input[@id="__VIEWSTATEGENERATOR"]/@value')
        data['__VIEWSTATEGENERATOR'] = view_sge[0]
        t2 = data['__VIEWSTATEGENERATOR']
        print t2
        d = self.session.post(url, data=data, headers=headers)
        #图片
        vehicle = shareJob.get('vehicle', None)
        gallery = vehicle.get('gallery', None)
        photos = gallery.get('photos')
        urls = [photo["url"] for photo in photos]
        self.upload_pic(urls,d.text)
        self.session.get("http://www.foolcars.com/ershouche/mchushoupicflash.aspx?carid="+d.text)

        if d.status_code == 200:
            return errorcode.SUCCESS, "http://www.foolcars.com/usedcar/"+d.text +'.html'
        else:
            return errorcode.DATA_ERROR,''

    #改价入口
    def updateVehicle(self, shareJob):

        account = shareJob.get("share_account", None)
        if account is None:
            logger.error("login fail")
            return errorcode.AUTH_ERROR, errormsg.LOGIN_FAIL

        username = account["username"]
        password = account["password"]

        successful = self.doLogin(username, password)
        if not successful:
            return errorcode.AUTH_ERROR, errormsg.LOGIN_FAIL

        urls = shareJob.get('url', None)
        url_id = re.findall('http://www.foolcars.com/usedcar/([^.]+).html',urls)
        url_id = url_id[0]
        url = "http://www.foolcars.com/ershouche/mchushou.aspx?carid=" + url_id

        #车辆基本信息
        external_vehicle_spec  = shareJob.get('external_vehicle_spec', None)
        series = external_vehicle_spec.get('series', None)
        brand = external_vehicle_spec.get('brand', None)
        model = external_vehicle_spec.get('model', None)
        pbid = brand.get('id', None)
        mdl = model.get('id', None)
        ser = series.get('id', None)
        series_name = series.get('name', None)
        model_name  = model.get('name', None)
        oo = str(series_name)+str(model_name)
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

        #排量
        vehicle_spec_detail = shareJob.get('vehicle_spec_detail', None)
        details = vehicle_spec_detail.get('details', None)
        y =details[23]

        #车辆颜色
        vehicle = shareJob.get('vehicle', None)
        summary = vehicle.get('summary',None)
        color = summary.get('color',None)
        color = color_mapping.get(color, "其他")
        color = int(color)
        #
        #  #车辆内饰
        # vehicle = shareJob.get('vehicle', None)
        # summary = vehicle.get('summary', None)
        # interior = summary.get('interior', None)
        # interior = interior_mapply[interior]
        # interior = int(interior)
        #四驱
        vehicle_spec_detail = shareJob.get('vehicle_spec_detail', None)
        details = vehicle_spec_detail.get('details', None)
        dri = details[55]
        drir = drii[dri]

        #汽油
        vehicle_spec_detail = shareJob.get('vehicle_spec_detail', None)
        details = vehicle_spec_detail.get('details', None)
        fuel = details[25]
        fuell = fuel_op[fuel]

        #手动
        vehicle_spec_detail = shareJob.get('vehicle_spec_detail', None)
        details = vehicle_spec_detail.get('details', None)
        ddl_gear = details[42]
        gear = gear_pp[ddl_gear]

        #车辆信息
        vehicle = shareJob.get('vehicle', None)
        desc = vehicle.get('desc', None)
        desc = self.getContentVal(shareJob,'\n','')[:500]

        #首次上牌时间
        vehicle = shareJob.get('vehicle', None)
        vehicle_date = vehicle.get('vehicle_date', None)
        registration_date = vehicle_date.get('registration_date', None)
        year = registration_date.year
        month = registration_date.month

        #年险有效日期
        vehicle = shareJob.get('vehicle', None)
        vehicle_date = vehicle.get('vehicle_date', None)
        inspection_date = vehicle_date.get('inspection_date', None)
        years = inspection_date.year
        months = inspection_date.month

        #保险有效期
        vehicle = shareJob.get('vehicle', None)
        vehicle_date = vehicle.get('vehicle_date', None)
        manufacture_date = vehicle_date.get('manufacture_date', None)
        man_year = manufacture_date.year
        man_month = manufacture_date.month

        #城区
        vehicle = shareJob.get('vehicle', None)
        merchant = vehicle.get('merchant', None)
        address = merchant.get('address', None)
        province_name = address.get('province_name', None)
        city_name = address.get('city_code', None)

        #表城市
        city_txt = cityfoolcar.Cityfoolcar()
        city_id = city_txt.getName(city_name.encode('utf-8'))


        headers = {
            "Accept":"*/*",
            "Accept-Encoding":"gzip, deflate",
            "Accept-Language":"zh-CN,zh;q=0.8,en;q=0.6",
            "Connection":"keep-alive",
            "Content-Length":"19041",
            "Content-Type":"application/x-www-form-urlencoded; charset=UTF-8",
            "Cookie":"ASP.NET_SessionId=u1b5lfrb1cw1lrmgtyg2lpd0; foolcars_com_login_info=18301080830|asasas123; foolcars_com_login_userid=100231; 60m_auth=f662Qt6jPMGbk3pxWX1vxheZwbQTguqaGjJk4CV+7BXCCusNIukxbMLtLdcHrhgK; forums=C9970105059947FDEDAE85E92C42E913B6CBECAEA21284FFAD0968D05AFD3D4EC61F1D49E0524D6CA42F25402B4D8A5513FF47886F8E8DF64E149C4E9ED713784A0D4519BE99AD20DE234F10AFCF471B1AE5ED94F7419AACEC60EE3E5906CBC4AAE777941118EB7E33D5C75344969072D095FDC092DC7F261764C53D8917399535DF292E9DC9194FFE3C3B9D8088B293; CNZZDATA2098552=cnzz_eid%3D1857197056-1449314096-null%26ntime%3D1451280747; Hm_lvt_f95c1784f72c5aa618d60923d55f9e73=1450405477,1450662625,1450835588,1451274381; Hm_lpvt_f95c1784f72c5aa618d60923d55f9e73=1451280748; AJSTAT_ok_pages=15; AJSTAT_ok_times=41",
            "Host":"www.foolcars.com",
            "Origin":"http://www.foolcars.com",
            "Referer":"http://www.foolcars.com/ershouche/mchushou.aspx?carid=" + url_id,
            "User-Agent":"Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/46.0.2490.86 Safari/537.36",
            "X-Requested-With":"XMLHttpRequest",
        }

        data = {

            'ctl00$ContentPlaceHolder1$txtshopname':'',
            'cartype':1,
            'ctl00$ContentPlaceHolder1$txtcartype':1,
            'ctl00$ContentPlaceHolder1$txtchar02':'',
            'ctl00$ContentPlaceHolder1$txtcarname':oo, #u'奥迪A4L 2015款 30 TFSI 手动 舒适型',
            'ctl00$ContentPlaceHolder1$txtbrand':pbid,
            'ctl00$ContentPlaceHolder1$txtseries':ser,
            'ctl00$ContentPlaceHolder1$txtmodel': mdl,
            'ctl00$ContentPlaceHolder1$txtroadmaintain':u'便宜,手续齐全可过户',
            'ctl00$ContentPlaceHolder1$txtchepaihao1':u'请输入前两位',
            'ctl00$ContentPlaceHolder1$txtchepaihao2':u'请输入后五位',
            'ctl00$ContentPlaceHolder1$txtchejiahao':u'请输入车架号',
            'ctl00$ContentPlaceHolder1$txtfadongjihao':u'请输入发动机号',
            'ctl00$ContentPlaceHolder1$ddl_dict_cityinfo': city_id ,
            'ctl00$ContentPlaceHolder1$ddl_citydistrict': 13,
            'ctl00$ContentPlaceHolder1$txtchar03':u'昌平区',
            'ctl00$ContentPlaceHolder1$txtchar04':'',
            'ctl00$ContentPlaceHolder1$ddl_int1': 2012,
            'ctl00$ContentPlaceHolder1$ddl_int2': 3,
            'ctl00$ContentPlaceHolder1$ddl_yesr': year,
            'ctl00$ContentPlaceHolder1$ddl_month': month,
            'ctl00$ContentPlaceHolder1$ddl_pricememo':u'不包含过户费',
            'ctl00$ContentPlaceHolder1$txtprice': quoted_price,
            'ctl00$ContentPlaceHolder1$rbl_boxcount':0,
            'ctl00$ContentPlaceHolder1$txtdisplacement': y,
            'ctl00$ContentPlaceHolder1$txtmileage': mileage,
            'ctl00$ContentPlaceHolder1$ddl_color': color,
            'ctl00$ContentPlaceHolder1$dllsafeequip':1,
            'ctl00$ContentPlaceHolder1$ddl_gear': gear,
            'ctl00$ContentPlaceHolder1$txtgear':'',
            'ctl00$ContentPlaceHolder1$ddl_usertype':1,
            'ctl00$ContentPlaceHolder1$ddl_drive': drir,
            'ctl00$ContentPlaceHolder1$ddl_fuel': fuell,
            'ctl00$ContentPlaceHolder1$txtdoorcount':'',
            'ctl00$ContentPlaceHolder1$txtseatcount':'',
            'ctl00$ContentPlaceHolder1$txtloadweight':'',
            'ctl00$ContentPlaceHolder1$txtchar01':'',
            'ctl00$ContentPlaceHolder1$txtmotortype':'',
            'ctl00$ContentPlaceHolder1$txthorsepower':'',
            'ctl00$ContentPlaceHolder1$ddl_zhihuan':0,
            'ctl00$ContentPlaceHolder1$ddl_guohu':0,
            'ctl00$ContentPlaceHolder1$ddlisyishou':0,
            'ctl00$ContentPlaceHolder1$txtfapiaojia':'',
            'ctl00$ContentPlaceHolder1$ddlnjyear': years,
            'ctl00$ContentPlaceHolder1$ddlnjmonth': months,
            'ctl00$ContentPlaceHolder1$ddlbasicequip':u'商业',
            'ctl00$ContentPlaceHolder1$ddlbxyear': man_year,
            'ctl00$ContentPlaceHolder1$ddlbxmonth': man_month,
            'ctl00$ContentPlaceHolder1$txtinsideequip':u'保险注视',
            'ctl00$ContentPlaceHolder1$txtpeizhi':u'全景天窗',
            'ctl00$ContentPlaceHolder1$txtmemo': desc,
            'ctl00$ContentPlaceHolder1$rbl_jiance':0,
            'ctl00$ContentPlaceHolder1$rbl_zhihuan':0,
            'ctl00$ContentPlaceHolder1$rbl_fx':1,
            'ctl00$ContentPlaceHolder1$rbl_releaseday':60,
            'ctl00$ContentPlaceHolder1$txt_maijia':'',
            'ctl00$ContentPlaceHolder1$txt_maijiaphone':'',
            'ctl00$ContentPlaceHolder1$txt_xiaohao':'',


        }
        v = self.session.get("http://www.foolcars.com/ershouche/mchushou.aspx?carid=" + url_id)
        lo = v.text.replace("gb2312","utf-8")
        dem = lxml.html.fromstring(lo)
        view_state = dem.xpath(u'//form[@id="aspnetForm"]/div/input[@id="__VIEWSTATE"]/@value')
        data['__VIEWSTATE'] = view_state[0]
        t3 = data['__VIEWSTATE']
        print t3
        view_sge = dem.xpath(u'//form[@id="aspnetForm"]/div/input[@id="__VIEWSTATEGENERATOR"]/@value')
        data['__VIEWSTATEGENERATOR'] = view_sge[0]
        t4 = data['__VIEWSTATEGENERATOR']
        print t4
        ll = self.session.post('http://www.foolcars.com/ershouche/mchushou.aspx?carid='+ url_id,data=data,headers=headers)
        self.session.get('http://www.foolcars.com/ershouche/mchushoupicflash.aspx?carid='+ url_id)
        self.session.post('http://www.foolcars.com/ershouche/mchushoupicflash.aspx?carid='+url_id)
        self.session.get('http://www.foolcars.com/ershouche/succ.aspx?infoid='+url_id)
        # #图片
        # vehicle = shareJob.get('vehicle', None)
        # gallery = vehicle.get('gallery', None)
        # photos = gallery.get('photos')
        # urls = [photo["url"] for photo in photos]
        # self.upload_pic(urls,url_id)

        if ll.status_code == 200:
            return errorcode.SUCCESS, 'http://www.foolcars.com/usedcar/%s.html'%url_id
        else:
            return errorcode.DATA_ERROR, errormsg.SITE_OTHER_ERROR

    #下架入口
    def removeVehicle(self, shareJob):

        account = shareJob.get("share_account", None)
        if account is None:
            logger.error("login fail")
            return errorcode.AUTH_ERROR, errormsg.LOGIN_FAIL

        username = account["username"]
        password = account["password"]

        successful = self.doLogin(username, password)
        if not successful:
            return errorcode.AUTH_ERROR, errormsg.LOGIN_FAIL

        urls = shareJob.get('url', None)
        url_d = re.findall('http://www.foolcars.com/usedcar/([^.]+).html',urls)
        url_d = url_d[0]
        url = "http://www.foolcars.com/ershouche/ajaxsubmit.aspx?type=offline&ids=%s&_=1451356167384"%url_d

        headers = {
            "Accept":"*/*",
            "Accept-Encoding":"gzip,deflate, sdch",
            "Accept-Language":"zh-CN,zh;q=0.8,en;q=0.6",
            "Connection":"keep-alive",
            "Cookie":"ASP.NET_SessionId=u1b5lfrb1cw1lrmgtyg2lpd0; foolcars_com_login_info=18301080830|asasas123; foolcars_com_login_userid=100231; 60m_auth=3c689MUwiDrs99ryBpzSAX7KLPZU2wwxUaZhawObyCinkv7Wu0BqLmraBmZeKjiB; forums=9E3E3AB523028BA330A65D88B33209900D684DBF727EDA39E26B5533297B1C57703209C9EF237B97247F286CBB65357671B35D7DC686C9FCCCA17DE016F710DCB8FD606AA1269E53825A260DAA9407E4E61E9CC4A2F881E590828E7347B268D6A2A6EB3AE54C1D8105B95B1959A7136C9C2FE0CF7E728319DAB429EC5A27DAA507ED430CD6DCDFE584883A97E8FB9279; CNZZDATA2098552=cnzz_eid%3D1857197056-1449314096-null%26ntime%3D1451353283; Hm_lvt_f95c1784f72c5aa618d60923d55f9e73=1450405477,1450662625,1450835588,1451274381; Hm_lpvt_f95c1784f72c5aa618d60923d55f9e73=1451356167; AJSTAT_ok_pages=7; AJSTAT_ok_times=42",
            "Host":"www.foolcars.com",
            "Referer":"http://www.foolcars.com/ershouche/mchushoulist.aspx?type=2",
            "User-Agent":"Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/46.0.2490.86 Safari/537.36",
            "X-Requested-With":"XMLHttpRequest",
        }
        l = self.session.get(url,headers=headers)

        if l.status_code ==200:
            return errorcode.SUCCESS, '删除成功'
        else:
            return False,errormsg.SITE_OTHER_ERROR
        # 图片上传
    def upload_pic(self, urls,pid):
        gurl = "http://www.foolcars.com/ershouche/mchushoupicflash.aspx?carid="+pid
        arr = self.session.get(gurl)
        upload_url = "http://www.foolcars.com/ershouche/mchushoupicupload.aspx?carid="+pid
        for url in urls:

            files = {
                "Filename":(None, "02150vlt15.jpg"),
                "Upload":(None, "Submit Query"),
                "Filedata":("02150vlt15.jpg",urllib2.urlopen(url)),
            }
            t = self.session.post(upload_url, files=files)

        data = arr.text
        dom = lxml.html.fromstring(data)
        src = dom.xpath(u'//form//input')
        iData ={}
        for iItem in src:
            iData[iItem.attrib['name']] = iItem.attrib['value']

        self.session.post('http://www.foolcars.com/ershouche/mchushoupicflash.aspx?carid='+pid, data=iData)