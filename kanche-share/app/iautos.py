# !/usr/bin/python
# -*- coding: UTF-8 -*-

import tz
import httplib
import urllib
import string
import random
import json
import copy
from StringIO import StringIO
from decimal import *
from urlparse import urlparse
import lxml.html
import logger
import resize
import errorcode
import errormsg
from base import BaseSharer
from dt8601 import IsoDate

import re


publicAccount = {
    "username": u"看车二手车",
    "password": u"2wsx1qazkdycwc1"
}

class IautosSharer(BaseSharer):
    def __init__(self, sessionServer, specServer):
        super(IautosSharer, self).__init__(sessionServer, specServer)
        self.citys = IautosCity()

    def doLogin(self, username, password):
        conn = httplib.HTTPConnection("www.iautos.cn", timeout=10)
        conn.request("GET", "/user/login/", headers=self.headers)
        res1 = conn.getresponse()
        self.setCookies(res1.getheaders())
        conn.close()

        conn = httplib.HTTPConnection("www.iautos.cn", timeout=10)
        conn.request("GET", "/index.php?c=usedcar&a=get_captcha&key=login", headers=self.headers)
        res2 = conn.getresponse()
        headers2 = res2.getheaders()
        imageData = res2.read()
        conn.close()

        imageData = self.decodeBody(headers2, imageData)
        image = StringIO(imageData)
        captcha = self.getCaptcha(image, imageData)
        # print(captcha)

        conn = httplib.HTTPConnection("www.iautos.cn", timeout=10)
        validcode = captcha["text"]
        form = "username=" + urllib.quote(username.encode('utf-8')).upper()
        form += "&password=" + str(password)
        form += "&validatecode=" + str(validcode)
        form += "&btnSubmit=%E7%99%BB%E5%BD%95&backurl="

        headers3 = copy.copy(self.headers)
        headers3['Content-Length'] = len(form)
        headers3['Content-Type'] = 'application/x-www-form-urlencoded'

        conn.request("POST", "/user/login/", form, headers3)
        res = conn.getresponse()
        conn.close()
        if not res.status == 302:
            logger.debug(res.status)
            logger.debug(res.getheaders())
            logger.debug(res.msg)
            return False

        self.setCookies(res.getheaders())
        logger.debug(str(self.cookies))
        return True

    def shareVehicle(self, shareJob):
        shareAccount = shareJob.get("share_account", None)
        if shareAccount is None:
            return errorcode.AUTH_ERROR, errormsg.LOGIN_FAIL
        if shareAccount.get('account_type', None) == 'public':
            shareAccount['username'] = publicAccount['username']
            shareAccount['password'] = publicAccount['password']

        logger.debug("iautos shareVehicle")
        cookies = self.sessionServer.getSession('iautos', shareAccount['username'])
        if cookies is None:
            res = self.doLogin(shareAccount['username'], shareAccount['password'])
            if not res:
                logger.debug("login error")
                return errorcode.AUTH_ERROR, errormsg.LOGIN_FAIL
            self.sessionServer.setSession('iautos', shareAccount['username'], self.cookies)
        else:
            self.cookies = cookies
            ks = self.cookies.keys()
            cookie_list = []
            for k in ks:
                cookie_list.append(k + '=' + self.cookies[k])
            self.headers['Cookie'] = string.join(cookie_list, '; ')
        logger.debug("self.cookies" + str(self.cookies))

        vehicle = shareJob.get("vehicle", None)
        if vehicle is None:
            logger.error("vehicle missing")
            return errorcode.LOGIC_ERROR, errormsg.VEHICLE_EMPTY

        user = vehicle.get("user", None)
        if user is None:
            return errorcode.LOGIC_ERROR, errormsg.USER_EMPTY

        merchant = vehicle.get('merchant', None)
        address = merchant.get('address', None)
        if address is None:
            # return False
            return errorcode.LOGIC_ERROR, errormsg.ADDRESS_EMPTY

        mobile = user.get("mobile", None)
        if mobile is None:
            return errorcode.LOGIC_ERROR, errormsg.MOBILE_EMPTY

        (contactExistCode, contacts_user_id, contacts_name) = self.getContactAndKucun(shareJob)
        if contactExistCode == 1:
            logger.error("contact not found")
            return errorcode.SITE_ERROR, "第一车网缺少联系人,请手动添加联系人"
        if contactExistCode == 2:
            logger.error("Inventory was full, can't publish more cars")
            return errorcode.SITE_ERROR, "第一车网库存已满,已达第一车网发车数量上限"
        if contactExistCode == 3:
            logger.error("can't create contact")
            return errorcode.SITE_ERROR, "第一车网无法创建默认联系人"
        if contactExistCode == 4:
            logger.error("can't create contact")
            return errorcode.SITE_ERROR, "第一车网看车帮暂不支持个人账号免费发车"

        spec = vehicle.get("spec", None)
        if spec is None:
            logger.error("spec missing")
            return errorcode.SPEC_ERROR, errormsg.VEHICLE_SPEC_EMPTY

        externalVehicleSpec = shareJob.get("external_vehicle_spec", None)
        if externalVehicleSpec is None:
            logger.error("externalVehicleSpec missing")
            return errorcode.DATA_ERROR, errormsg.EXTERNAL_SPEC_EMPTY
        logger.debug(externalVehicleSpec)

        gallery = vehicle.get("gallery", None)
        if gallery is None:
            logger.error("gallery missing")
            return errorcode.DATA_ERROR, errormsg.PHOTO_NOT_ENOUGH

        photoList = self.uploadPics(gallery.get("photos", []))
        logger.debug(json.dumps(photoList))

        (success, msg) = self.postVehicle(shareJob,
                                          user,
                                          vehicle,
                                          externalVehicleSpec,
                                          contacts_user_id,
                                          contacts_name,
                                          photoList,
                                          ''
        )
        if success:
            return errorcode.SUCCESS, msg
        return errorcode.SITE_ERROR, msg

    def uploadLicensePic(self, licensePicUrl):
        photo_list = []
        o = urlparse(licensePicUrl)
        host = o.netloc
        uri = o.path

        # print content
        upload = self.sessionServer.getUpload('iautos', uri)
        if upload is not None:
            try:
                res = json.loads(str(upload))
            except Exception as e:
                logger.debug(str(e))
                logger.debug(urllib.quote(upload))
                res = None
        else:
            if host == 'pic.kanche.com':
                host = 'kanche-pic.qiniudn.com'
            conn = httplib.HTTPConnection(host, timeout=10)
            headersTemp = copy.copy(self.headers)
            del headersTemp['Cookie']
            headersTemp['Referer'] = "www.kanche.com"
            conn.request("GET", uri, headers=headersTemp)
            res = conn.getresponse()
            content = res.read()
            conn.close()
            res = self.uploadPicContent(content)
            if res is not None:
                jsonString = json.dumps(res)
                self.sessionServer.setUpload('iautos', uri, jsonString)
        if res is not None:
            # r = """
            # {
            # "url": "http:\/\/photo.iautos.cn\/carupload\/photo\/2014\/0829\/11\/20140829112227506158.jpg",
            # "pic": "20140829112227506158.jpg",
            # "extension": "jpg",
            # "mime": "image\/jpeg",
            # "size": 34128,
            #   "hash": "ae6012d93e5ee083ddcd334f407c70376ac49179"
            # }
            # """
            photo_list.append(res)
        return photo_list

    def uploadPics(self, photos):
        photo_list = []
        # 最多20张图片
        photos = photos[:19]
        for photo in photos:
            url = photo.get("url", None)
            if url is None:
                continue
            o = urlparse(url)
            host = o.netloc
            uri = o.path

            # print content
            upload = self.sessionServer.getUpload('iautos', uri)
            if upload is not None:
                try:
                    res = json.loads(str(upload))
                except Exception as e:
                    logger.debug(str(e))
                    logger.debug(urllib.quote(upload))
                    res = None
            else:
                if host == 'pic.kanche.com':
                    host = 'kanche-pic.qiniudn.com'
                conn = httplib.HTTPConnection(host)
                headersTemp = copy.copy(self.headers)
                del headersTemp['Cookie']
                headersTemp['Referer'] = "www.kanche.com"
                conn.request("GET", uri, headers=headersTemp)
                res = conn.getresponse()
                content = res.read()
                conn.close()
                res = self.uploadPicContent(content)
                if res is not None:
                    jsonString = json.dumps(res)
                    self.sessionServer.setUpload('iautos', uri, jsonString)
            if res is not None:
                # r = """
                # {
                # "url": "http:\/\/photo.iautos.cn\/carupload\/photo\/2014\/0829\/11\/20140829112227506158.jpg",
                # "pic": "20140829112227506158.jpg",
                # "extension": "jpg",
                # "mime": "image\/jpeg",
                # "size": 34128,
                #   "hash": "ae6012d93e5ee083ddcd334f407c70376ac49179"
                # }
                # """
                photo_list.append(res)
        return photo_list

    def uploadPicContent(self, content):

        conn = httplib.HTTPConnection("www.iautos.cn")
        headers = copy.copy(self.headers)

        img = StringIO(content)
        smallImg = StringIO()
        resize.resize(img, (800, 600), False, smallImg)
        content = smallImg.getvalue()

        boundaryHeader = '----WebKitFormBoundary' + str(random.random())
        boundary = '--' + boundaryHeader

        formStr = ""
        formStr += boundary + "\r\n" + 'Content-Disposition: form-data; name="userid"\r\n\r\n' + "114841" + "\r\n"
        formStr += boundary + "\r\n" + 'Content-Disposition: form-data; name="photoCount"\r\n\r\n' + "20" + "\r\n"
        formStr += boundary + "\r\n" + 'Content-Disposition: form-data; name="uploadurl"\r\n\r\n' + "/shopadmin/uploadimg/simple/" + "\r\n"
        formStr += boundary + "\r\n" + 'Content-Disposition: form-data; name="shopid"\r\n\r\n' + "0" + "\r\n"
        formStr += boundary + "\r\n" + 'Content-Disposition: form-data; name="btnUrl"\r\n\r\n' + "http://www.iautos.cn/static2013/images/shopadmin/car_photo_hover.jpg" + "\r\n"
        formStr += boundary + "\r\n" + 'Content-Disposition: form-data; name="maxSize"\r\n\r\n' + "8388608" + "\r\n"
        formStr += boundary + "\r\n" + 'Content-Disposition: form-data; name="is_add_watermark"\r\n\r\n' + "0" + "\r\n"
        formStr += boundary + "\r\n" + 'Content-Disposition: form-data; name="brand_id"\r\n\r\n' + "0" + "\r\n"
        formStr += boundary + "\r\n" + 'Content-Disposition: form-data; name="DropSelect"\r\n\r\n' + "1" + "\r\n"
        formStr += boundary + "\r\n" + 'Content-Disposition: form-data; name="Filename"\r\n\r\n' + "aa.jpg" + "\r\n"
        formStr += boundary + "\r\n" + 'Content-Disposition: form-data; name="flashId"\r\n\r\n' + "flash1" + "\r\n"
        formStr += boundary + "\r\n" + 'Content-Disposition: form-data; name="cid"\r\n\r\n' + "1" + "\r\n"

        formStr += boundary + '\r\n' + 'Content-Disposition: form-data; name="Filedata"; filename="aa.jpg"\r\nContent-Type: application/octet-stream\r\n\r\n'
        formStr += str(content) + "\r\n"
        formStr += boundary + "--"

        headers['Host'] = 'www.iautos.cn'
        headers['Content-Length'] = len(formStr)
        headers["Content-Type"] = "multipart/form-data; boundary=" + boundaryHeader

        logger.debug("picUpload headers=" + str(headers))

        conn.request("POST", "/shopadmin/uploadimg/simple/", formStr, headers=headers)
        res = conn.getresponse()
        resHeaders = res.getheaders()
        logger.debug(str(resHeaders))
        photoRes = self.decodeBody(resHeaders, res.read())
        # print photoRes#.decode("GB18030")
        conn.close()
        try:
            ret = json.loads(photoRes)
        except Exception as e:
            logger.debug(str(e))
            logger.debug(urllib.quote(photoRes))
            ret = None
        return ret

    #车辆说明
    def getContentVal_iautos(self, shareJob):
        Symbol = "\r\n"
        lateral = "——"*25
        externalSpec = shareJob['external_vehicle_spec']
        share_account = shareJob.get("share_account", None)
        model = externalSpec.get('model', None)
        key = model.get('key', None)
        content = ''
        vehicle = shareJob.get('vehicle', None)
        desc = vehicle.get('desc', None)

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
                    if site == 'iautos.cn':
                        description = i.get('description', None)
                        description = string.replace(description, '\n', Symbol)
            content += description
            content += Symbol + str(vehicle['_id'])

        # 统一说明 追加
        if globalDisable == False:
            if share_account.get("account_type", None) == "substitute":
                content += Symbol*2 + '看车网，发现二手好车。提供专业的咨询和购车指导，保证车源信息真实准确。二手车质量我们保证 !' + Symbol
                content += '（更多信息请来电咨询400-895-0101）' + Symbol*2

        # 每辆车说明 追加
        if vehicleDisable == False:
            content += lateral + Symbol*2
            content += '看车网车辆编号: '+str(shareJob.get('series_number', None)) + Symbol*2

            if not (model is None) and not (key is None):
                content += "[ 车辆名称 ]" + Symbol
                if externalSpec['model']['key'] == '0':
                    vehicleSpec = shareJob['vehicle']['spec']
                    content += (externalSpec['brand']['name'] + externalSpec['series']['name'] + u' ' + vehicleSpec['sale_name'] + u'' + vehicleSpec['year_group']) + Symbol*2
                else:
                    content += (externalSpec['brand']['name'] + externalSpec['series']['name'] + u' ' + externalSpec['model']['name']) + Symbol*2

            #车况说明
            condition =  "乘坐空间宽敞，储物空间充足;"
            condition = condition + "转向清晰，指向精准;" + Symbol
            condition = condition + "提速表现优秀，动力源源不断;" + Symbol
            condition = condition +"车身有少量、轻微划痕或者局部补漆的情况，不超过3处;" + Symbol
            condition = condition + "车辆内部后备箱内干净整洁，内饰及座椅无磨损、污渍;" + Symbol
            condition = condition + "油耗低，节能环保；座椅舒适度上乘，车内无噪音;"


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

            if len(highlight_show_name_list):
                content += "[ 亮点配置 ] " + Symbol + highlight_str + Symbol*2 + "[ 车况说明 ] " + condition + Symbol*2
            else:
                content += "[ 车况说明 ] " + Symbol + condition + Symbol*2

            content +=  lateral
            content +=  Symbol*4

        content += str(vehicle['_id'])
        if "" == content:
            content = u"无车辆说明，请添加至10个字以上"
        return content


    def postVehicle(self, shareJob, user, vehicle, externalVehicleSpec, contacts_user_id, contacts_name, photoList, queryId):
        vehicleSummary = vehicle.get("summary", None)
        summary = vehicle['summary']
        address = user.get('address', None)
        user = vehicle['user']
        company_address = user.get('company_address', None)

        merchant = vehicle.get('merchant', None)
        address = merchant.get('address', None)
        if address is not None:
            region = address["district_code"]
            detail = address['detail']

        (isReg, firstRegDate) = self.getReg(vehicle)
        (isCompulsoryInsuranceExpire, compulsoryInsuranceExpireDate) = self.getCompulsoryInsuranceExpireDate(vehicle)
        (usedcar_photo_url, usedcar_photo_hash) = self.getUsedcarPhotoFromPhotoList(photoList)
        (province_id, city_id, city_proper_id) = self.citys.getCode(str(region))

        form = "m=shopadmin"
        form += "&c=usedcar"

        if queryId.decode('utf8').isnumeric():
            form += "&a=updateUsedcar"
        else:
            form += "&a=createUsedcar"

        #更具id判断是发车还是改价
        form += "&Car[id]=" + queryId

        form += "&Car[province_id]=" + str(province_id)
        form += "&Car[city_id]=" + str(city_id)
        form += "&Car[city_proper_id]=" + str(city_proper_id)

        #vin码
        vin = vehicle.get('vin', None)
        if vin is None:
            vin = ""
        form += "&Car[vin]=" + str(vin)

        form += "&Car[brand_id]=" + str(externalVehicleSpec["brand"]["id"])
        form += "&Car[series_id]=" + str(externalVehicleSpec["series"]["id"])
        form += "&Car[mfrs_id]=" + str(externalVehicleSpec["vendor"]["id"])
        form += "&Car[purchase_year]=" + str(self.getPurchaseYear(vehicle))
        form += "&Car[model_simple_id]=" + str(externalVehicleSpec["model"]["id"])

        #标题
        title = ""
        title += externalVehicleSpec['brand']['name']
        #title += externalVehicleSpec['vendor']['name']
        title += externalVehicleSpec['series']['name']
        title += externalVehicleSpec["model"]["name"]
        form += "&Car[title]=" + urllib.quote(title.encode('utf-8'))

        # 车辆配置
        # 加热座椅1
        # 安全气囊(13) str(self.getHighlight(vehicle))
        #大灯清洗装置（22）
        # TODO 车辆配置
        form += "&Car[highlight]=1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22"
        # 可议价
        form += "&Car[isbid]=0"
        # 燃油类型 汽油11
        # TODO 燃油类型
        form += "&Car[fuel_type]=11"

        #初等时间
        form += "&Car[is_reg]=" + str(isReg)
        form += "&Car[first_reg_date]=" + str(firstRegDate)

        form += "&Car[price]=" + str(Decimal(self.getPrice(shareJob)) / Decimal(10000))
        form += "&Car[km]=" + str(Decimal(vehicle['summary']['mileage']) / Decimal(10000))
        #非营运
        form += "&Car[operation_type]=2"
        #？？
        form += "&Car[auth_brand_id]="
        #颜色
        form += "&Car[color]=" + str(self.getColorCode(shareJob))
        #内饰
        form += "&Car[interior_id]=" + str(self.getInterior(vehicleSummary))
        #保养记录:1齐全
        form += "&Car[service_record]=1"

        #车牌号
        license_number = summary.get('license_number', None)
        if license_number is None:
            license_number = ""
        form += "&Car[license_number]=" + urllib.quote(license_number.encode('utf-8'))
        #过户次数
        transferTimes = self.getTradeTimes(vehicleSummary)
        form += "&Car[transfer_count]=" + str(int(transferTimes))

        #一句话标题
        desc = vehicle.get('desc', None)
        brief = None
        if desc is not None:
            brief = desc.get('brief', None)
        if brief is None:
            brief = ""
        form += "&Car[subtitle]=" + urllib.quote(brief.encode('utf-8'))
        #车主附言
        form += "&Car[remark]=" + urllib.quote(self.getContentVal_iautos(shareJob).encode('utf-8'))

        #强险
        vehicle_date = vehicle.get('vehicle_date', None)
        compulsory_insurance_expire_date = vehicle_date.get('compulsory_insurance_expire_date', None)
        if compulsory_insurance_expire_date is None:
            compulsory_insurance_expire_date = '2016-06'
        else:
            compulsory_insurance_expire_date = str(compulsory_insurance_expire_date)[0:7]
        form += "&Car[road_maintance_fee_date]=" + str(compulsory_insurance_expire_date)
        form += "&Car[is_road_maintance_expired]=1"

        #商业险
        form += "&Car[insurance_date]=" + str(compulsoryInsuranceExpireDate)
        form += "&Car[is_insurance_expired]=" + str(isCompulsoryInsuranceExpire)

        #驾驶证是否齐全
        form += "&Car[driving_license]=1"
        #登记证是否齐全
        form += "&Car[registration]=1"
        #购车发票是否齐全
        form += "&Car[invoice]=1"

        #TODO:待测试：驾驶证照片
        license_url = ""
        reLicense_url = ""
        summary = vehicle.get('summary', None)
        if summary is not None:
            license_url = summary.get('driving_license_picture', None)
            if license_url is None:
                license_url = ""
        if "" != license_url:
            license_list = self.uploadLicensePic(license_url)
            (reLicense_url, license_hash) = self.getUsedcarPhotoFromPhotoList(license_list)
        form += "&Car[driving_license_pic]=" + str(reLicense_url)

        #登记照照片
        form += "&Car[registration_pic]="
        #购车发票照片
        form += "&Car[invoice_pic]=1"
        #特色服务#TODO:待验证，可能导致发车失败；
        form += "&Car[special_service]=1,2,3,4,5,6,7,8,9,10"
        #信息有效期：天
        form += "&Car[expiry_days]=30"

        #form += "&Car[car_location]=%E5%8C%97%E4%BA%AC%E5%B8%82%E4%B8%B0%E5%8F%B0%E5%8C%BA"
        #看车地址 set by yjy on 20150324
        if detail is None:
            detail = ""
        form += "&Car[car_location]=" + urllib.quote(detail.encode('utf-8'))
        #联系人id
        form += "&Car[contacts_user_id]=" + str(contacts_user_id)
        #TODO:联系电话,待修改
        form += "&Car[contacts_phone]="
        #联系人姓名
        form += "&Car[contacts_name]=" + urllib.quote(contacts_name.encode("utf-8"))

        form += "&Car[auditing]=1"
        form += "&Car[auditing_remark]="
        form += "&Car[car_photo_url]="
        #******上传车辆照片
        form += "&Car[usedcar_photo_url]=" + str(usedcar_photo_url)
        form += "&Car[usedcar_photo_hash]=" + str(usedcar_photo_hash)
        # 车辆信息完整度
        form += "&Car[integrity]=99"
        form += "&Car[transmission_type_id]=" + str(self.getTransmissionTypeId(vehicleSummary))

        logger.debug(form)

        headers = copy.copy(self.headers)
        headers['Content-Length'] = len(form)
        headers['Content-Type'] = 'application/x-www-form-urlencoded; charset=UTF-8'
        conn = httplib.HTTPConnection("www.iautos.cn", timeout=10)
        conn.request("POST", "/", form, headers)
        logger.debug(headers)

        res = conn.getresponse()
        idRes = res.read()
        carId = self.decodeBody(res.getheaders(), idRes)
        logger.debug(res.status)
        logger.debug(carId)

        try:
            jsonResult = json.loads(carId)
        except Exception as e:
            logger.debug(str(e))
            logger.debug(urllib.quote(carId))
            jsonResult = None

        logger.debug(jsonResult)

        if res.status == 200 and jsonResult is not None:
            if jsonResult.__contains__("error_code"):
                return False, str(jsonResult)
            if jsonResult.has_key('id'):
                url = "http://www.iautos.cn/usedcar/" + str(jsonResult["id"]) + ".html"
                return True, str(url)
            if jsonResult.has_key('status'):
                if '2' == jsonResult['status']:
                    logger.debug(jsonResult)
                    return False, u'重复车源!'

        return False, "a big bug"

    @staticmethod
    def getSpecV(specDetail, name, vname):
        v = specDetail[vname]
        return 'Content-Disposition: form-data; name="' + name + '"\r\n\r\n' + str(v) + '\r\n'

    @staticmethod
    def getPostForm(name, value):
        return 'Content-Disposition: form-data; name="' + name + '"\r\n\r\n' + str(value) + '\r\n'

    # 个人用户发车时字段
    def getShopId(self):
        conn = httplib.HTTPConnection("www.iautos.cn", timeout=10)
        headers = copy.copy(self.headers)
        conn.request("GET", "/shopadmin/usedcar/addusedcar/", headers=headers)
        res = conn.getresponse()
        html = res.read()
        dom = lxml.html.fromstring(html)
        conn.close()
        # <input value="119650" type="hidden" name="" id="shop_id">
        shop_id = dom.xpath('//*[@id="shop_id"]/@value')
        return str(shop_id)

    def getContactAndKucun(self, shareJob):
        conn = httplib.HTTPConnection("www.iautos.cn", timeout=10)
        headers = copy.copy(self.headers)
        conn.request("GET", "/shopadmin/usedcar/addusedcar/", headers=headers)
        res = conn.getresponse()
        resHeaders = res.getheaders()
        htmlgzip = res.read()
        html = self.decodeBody(resHeaders, htmlgzip)
        #小账号不支持
        if html == '':
            return 4, "", ""
        dom = lxml.html.fromstring(html)
        conn.close()

        # <input type="radio" value="121064" contact_name="任兵" contact_phone="" name="lxfs">
        #TODO:需要增加联系人电话号码
        contacts_user_id = dom.xpath('//*[@id="contact_ul"]/li/label/input/@value')
        contacts_name = dom.xpath('//*[@id="contact_ul"]/li/label/input/@contact_name')
        contacts_checked = dom.xpath('//*[@id="contact_ul"]/li/label/input/@checked')
        kucunStatus = dom.xpath('//*[@id="kucun"]')

        if len(kucunStatus) > 0:
            #库存数量已满
            return 2, "", ""

        (defaultUsername, defaultMobile) = self.getContact(shareJob)

        if len(contacts_user_id) == 3:
            i = 0
            for length in xrange(len(contacts_user_id)):
                if contacts_checked[length] == 'checked':
                    i = length
                    break
            for length in xrange(len(contacts_user_id)):
                if contacts_name[length] == defaultUsername:
                    i = length
                    break
            contactsUserId = contacts_user_id[i]
            contactsName = contacts_name[i]
            return 0, contactsUserId, contactsName
        else:
            for length in xrange(len(contacts_user_id)):
                if contacts_name[length] == defaultUsername:
                    i = length
                    contactsUserId = contacts_user_id[i]
                    contactsName = contacts_name[i]
                    return 0, contactsUserId, contactsName

            form = "name=" + defaultUsername
            form += "&phone=" + defaultMobile
            form += "&tel=&phone_400="

            logger.debug(form)

            headers = copy.copy(self.headers)
            headers['Content-Length'] = len(form)
            headers['Content-Type'] = 'application/x-www-form-urlencoded; charset=UTF-8'
            conn = httplib.HTTPConnection("www.iautos.cn", timeout=10)
            conn.request("POST", "/index.php?m=shopadmin&c=usedcar&a=addContact", form, headers)
            logger.debug(headers)

            res = conn.getresponse()
            jsonRes = res.read()
            josnResponse = self.decodeBody(res.getheaders(), jsonRes)
            logger.debug(res.status)
            logger.debug(josnResponse)

            jsonResult = json.loads(josnResponse)
            # jsonString = json.dumps(josnResponse)
            info = jsonResult.get("info", None)
            if info is not None:
                user_id = info.get("user_id", None)
                phone = info.get("phone", None)
                if user_id is not None and phone is not None:
                    return 0, user_id, phone
                else:
                    return 3, "", ""
            else:
                return 3, "", ""

        return 1, "", ""

    # ==========================================
    # remove Vehicle from management desk
    # ==========================================
    def removeVehicle(self,shareJob):
        print '\tgo into removeVehicle'
        shareAccount = shareJob.get("share_account", None)
        if shareAccount is None:
            return errorcode.AUTH_ERROR, ""
        if shareAccount.get('account_type', None) == 'public':
            shareAccount['username'] = publicAccount['username']
            shareAccount['password'] = publicAccount['password']

        cookies = self.sessionServer.getSession('iauots', shareAccount['username'])
        if cookies is None:
            result = self.doLogin(shareAccount['username'], shareAccount['password'])
            if not result:
                return errorcode.AUTH_ERROR, errormsg.LOGIN_FAIL
            self.sessionServer.setSession('iautos', shareAccount['username'], self.cookies)
        else:
            self.cookies = cookies
            ks = self.cookies.keys()
            cookie_list = []
            for k in ks:
                cookie_list.append(k + '=' + self.cookies[k])
            self.headers['Cookie'] = str(string.join(cookie_list, '; '))

        urlForApp = shareJob.get("url", None)
        #if urlForApp is None:
        if urlForApp is None or len(urlForApp) == 0:
            return errorcode.DATA_ERROR, errormsg.VEHICLE_URL_EMPTY
        print '\turlForApp:',urlForApp
        #http://www.iautos.cn/usedcar/4231080.html
        pRule = r'([0-9]{7})'
        pageList = re.compile(pRule).findall(urlForApp)
        if len(pageList):
            pageId = pageList[0]
        else:
            logger.debug("error:get pageId failed!")
            pageId = ""

        #1. POST http://www.iautos.cn/index.php?m=shopadmin&c=usedcar&a=CarUpdate
        url = "/index.php?m=shopadmin&c=usedcar&a=CarUpdate"
        headers = copy.copy(self.headers)
        headers["Content-Length"] = "29"
        headers["Connection"] = "keep-alive"
        headers["Host"] = "www.iautos.cn"
        headers["origin"] = "http://www.iautos.cn"
        headers["Referer"] = "http://www.iautos.cn/shopadmin/usedcar/manage/?type=0"
        headers ["Content-Type"]= "application/x-www-form-urlencoded; charset=UTF-8"
        print "\theaders:",headers

        formData = "Car[id]=" + pageId.encode('utf-8')
        formData += "&Car[status]=" + '1'
        print "\tformData:",formData

        conn = httplib.HTTPConnection("www.iautos.cn", timeout=10)
        conn.request("POST", url,formData, headers=headers)
        res1 = conn.getresponse()
        print '\tQequest cookies:',self.headers['Cookie']
        self.setCookies(res1.getheaders())
        #res1 = conn.getresponse()
        resStatus = res1.status
        result = self.decodeBody(res1.getheaders(), res1.read())
        conn.close()
        print 'end...'
        if resStatus == 200 and (result.count('"id":') > 0):
            logger.debug("remove success")
            return errorcode.SUCCESS, ""
        else:
            return errorcode.SITE_ERROR, errormsg.VEHICLE_REMOVE_FAIL

        logger.debug("taoche remove failed \ngotoApp=" + result)


    def getPageHtml(self, host, uri):
        print host, uri
        conn = httplib.HTTPConnection(host, timeout=10)
        conn.request("GET", uri, headers=self.headers)
        getResponse = conn.getresponse()
        getHeaders = getResponse.getheaders()
        strhtml = self.decodeBody(getHeaders, getResponse.read())
        conn.close()
        print host, uri
        return strhtml, getHeaders

    # ==========================================
    # update Vehicle
    # ==========================================
    def updateVehicle(self, shareJob):
        shareAccount = shareJob.get("share_account", None)
        if shareAccount is None:
            return errorcode.AUTH_ERROR, errormsg.LOGIN_FAIL
        if shareAccount.get('account_type', None) == 'public':
            shareAccount['username'] = publicAccount['username']
            shareAccount['password'] = publicAccount['password']

        logger.debug("iautos shareVehicle")
        cookies = self.sessionServer.getSession('iautos', shareAccount['username'])
        if cookies is None:
            res = self.doLogin(shareAccount['username'], shareAccount['password'])
            if not res:
                logger.debug("login error")
                return errorcode.AUTH_ERROR, errormsg.LOGIN_FAIL
            self.sessionServer.setSession('iautos', shareAccount['username'], self.cookies)
        else:
            self.cookies = cookies
            ks = self.cookies.keys()
            cookie_list = []
            for k in ks:
                cookie_list.append(k + '=' + self.cookies[k])
            self.headers['Cookie'] = string.join(cookie_list, '; ')
        logger.debug("self.cookies --updateVehicle-- : " + str(self.cookies))

        vehicle = shareJob.get("vehicle", None)
        if vehicle is None:
            logger.error("vehicle missing")
            return errorcode.LOGIC_ERROR, errormsg.VEHICLE_EMPTY

        user = vehicle.get("user", None)
        if user is None:
            return errorcode.LOGIC_ERROR, errormsg.USER_EMPTY

        merchant = vehicle.get('merchant', None)
        address = merchant.get('address', None)
        if address is None:
            # return False
            return errorcode.LOGIC_ERROR, errormsg.ADDRESS_EMPTY

        mobile = user.get("mobile", None)
        if mobile is None:
            return errorcode.LOGIC_ERROR, errormsg.MOBILE_EMPTY

        '''(contactExistCode, contacts_user_id, contacts_name) = self.getContactAndKucun(shareJob)
        if contactExistCode == 1:
            logger.error("contact not found")
            return errorcode.SITE_ERROR, "第一车网缺少联系人,请手动添加联系人"
        if contactExistCode == 2:
            logger.error("Inventory was full, can't publish more cars")
            return errorcode.SITE_ERROR, "第一车网库存已满,已达第一车网发车数量上限"
        if contactExistCode == 3:
            logger.error("can't create contact")
            return errorcode.SITE_ERROR, "第一车网无法创建默认联系人"'''

        spec = vehicle.get("spec", None)
        if spec is None:
            logger.error("spec missing")
            return errorcode.SPEC_ERROR, errormsg.VEHICLE_SPEC_EMPTY

        externalVehicleSpec = shareJob.get("external_vehicle_spec", None)
        if externalVehicleSpec is None:
            logger.error("externalVehicleSpec missing")
            return errorcode.DATA_ERROR, errormsg.EXTERNAL_SPEC_EMPTY
        logger.debug(externalVehicleSpec)

        urlForApp = shareJob.get("url", None)
        if urlForApp is None or urlForApp=='':
            return errorcode.DATA_ERROR, '车辆url为空'

        queryId = re.findall('(\d+)\.html', urlForApp)
        if queryId is None:
            return errorcode.DATA_ERROR, "车辆ID为空"
        elif len(queryId) <1:
            return errorcode.DATA_ERROR, "车辆ID为空"
        else:
            queryId = queryId[-1]

        html, heads = self.getPageHtml('www.iautos.cn', '/shopadmin/usedcar/update/?id='+queryId)
        hxs = lxml.html.fromstring(html)

        photoList = []
        iList = hxs.xpath("//div[input/@name = 'usedcar_photo_hash[]']")
        for iItem in iList:
            photoList.append({
                'url':iItem.xpath('img/@src')[0].replace('/small/','/'),
                'hash':iItem.xpath('input/@value')[0]
            })


        logger.debug(json.dumps(photoList))
        #return errorcode.SUCCESS, 'debug'

        #contacts_user_id, contacts_name
        contacts_input = hxs.xpath("//input[@name='lxfs' and checked]")
        if len(contacts_input):
            contacts_input = contacts_input[0]
            contacts_user_id = contacts_input.get('value')
            contacts_name = contacts_input.get('contact_name')
        else:
            (contactExistCode, contacts_user_id, contacts_name) = self.getContactAndKucun(shareJob)

        (success, msg) = self.postVehicle(shareJob,
                                          address,
                                          vehicle,
                                          externalVehicleSpec,
                                          contacts_user_id,
                                          contacts_name,
                                          photoList,
                                          queryId.encode('utf8')
        )
        if success:
            return errorcode.SUCCESS, msg
        return errorcode.SITE_ERROR, errormsg.SITE_OTHER_ERROR

    @staticmethod
    def getVin(vehicle):
        vin = vehicle.get("vin", None)
        if vin is not None:
            return vin
        return ""

    @staticmethod
    def getPurchaseYear(vehicle):
        vehicleDate = vehicle.get("vehicle_date", None)
        if vehicleDate is not None:
            registrationDate = vehicleDate.get("registration_date", None)
            if registrationDate is not None:
                registrationDate = registrationDate.astimezone(tz.HKT)
                purchaseYear = registrationDate.year
                return purchaseYear
        return ""

    @staticmethod
    def getExternalVehicleSpecFromVehicle(self):
        pass

    @staticmethod
    def getHighlight(vehicle):
        pass

    #初等时间
    @staticmethod
    def getReg(vehicle):
        vehicleDate = vehicle.get("vehicle_date", None)
        if vehicleDate is not None:
            registrationDate = vehicleDate.get("registration_date", None)
            if registrationDate is not None:
                d = registrationDate.astimezone(tz.HKT)
                regDate = str(d.year) + "-" + str(d.month)
                return 1, regDate
        return 0, ""

    @staticmethod
    def getCompulsoryInsuranceExpireDate(vehicle):
        vehicleDate = vehicle.get("vehicle_date", None)
        if vehicleDate is not None:
            compulsoryInsuranceExpireDate = vehicleDate.get("compulsory_insurance_expire_date", None)
            if compulsoryInsuranceExpireDate is not None:
                d = compulsoryInsuranceExpireDate
                regDate = str(d.year) + "-" + str(d.month)
                return 1, regDate
            else:
                compulsoryInsuranceExpireDate = vehicleDate.get("inspection_date", None)
                compulsoryInsuranceExpireDate = compulsoryInsuranceExpireDate.astimezone(tz.HKT)
                regDate = str(compulsoryInsuranceExpireDate.year) + "-" + str(compulsoryInsuranceExpireDate.month)
                return 1, regDate
        return 0, ""


    @staticmethod
    def getColorCode(shareJob):
        colorCode = "2"
        colorTable = {"black": "2",
                      "silver": "1",
                      "white": "3",
                      "red": "8",
                      "blue": "4",
                      "grey": "6",
                      "champagne": "9",
                      "green": "5",
                      "yellow": "7",
                      "orange": "10",
                      "brown": "12",
                      "purple": "13",
                      "multi": "11",
                      "other": "11"}

        vehicle = shareJob.get("vehicle", None)
        if vehicle is not None:
            summary = vehicle.get("summary", None)
            if summary is not None:
                color = summary.get("color", None)
                colorCode = colorTable.get(color, "2")
        return colorCode

    @staticmethod
    # TODO 变速器
    def getTransmissionTypeId(vehicleSummary):
        if vehicleSummary is not None:
            engine = vehicleSummary.get("engine", None)
            if engine is not None:
                if engine.count(u"自") > 0:
                    # 自动
                    return 28
        # 手动
        return 27

    @staticmethod
    def getUsedcarPhotoFromPhotoList(photoList):
        usedcar_photo_url_list = []
        usedcar_photo_hash_list = []
        for i in photoList:
            usedcar_photo_url_list.append(str(i["url"]))
            usedcar_photo_hash_list.append(str(i["hash"]))
        usedcar_photo_url = ",".join(usedcar_photo_url_list)
        usedcar_photo_hash = ",".join(usedcar_photo_hash_list)
        return usedcar_photo_url, usedcar_photo_hash

    @staticmethod
    def getInterior(vehicleSummary):
        interior = vehicleSummary.get("interior", None)
        if interior is not None:
            if interior.count(u"浅") > 0:
                # 浅内饰
                return 2
        # 深内饰
        return 1

    @staticmethod
    def getTradeTimes(vehicleSummary):
        times = vehicleSummary.get("trade_times", None)
        if times is not None:
            return times
        return "undefined"


class Singleton(type):
    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(Singleton, cls).__call__(*args, **kwargs)
        return cls._instances[cls]


class IautosCity(object):
    __metaclass__ = Singleton

    def __init__(self):
        self.regionCodeTable = {}

        fd = open('data/iautos_city.txt', 'r')
        for line in fd.readlines():
            params = line.split('\t')
            if len(params) == 14:
                self.regionCodeTable[params[4]] = [params[7], params[9], params[12]]
        fd.close()

    def getCode(self, regionCode):
        region = self.regionCodeTable.get(regionCode, None)
        if region is not None:
            return region[0], region[1], region[2]
        # 默认北京丰台
        return 1, 828, 186

