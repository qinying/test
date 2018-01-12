#!/usr/bin/python
# -*- coding: UTF-8 -*-

import zlib
import string
import logger
import urllib
import pymongo
import config
import deathbycaptcha
import bypass_api
from decimal import *
from cookies import Cookie
import time
import base64
import datetime
import tz


class BaseSharer(object):
    def __init__(self, sessionServer, specServer):
        self.sessionServer = sessionServer
        self.specServer = specServer
        self.cookies = {}
        self.headers = {
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Encoding": "gzip,deflate,sdch",
            "Accept-Language": "en-US,en;q=0.8,zh-CN;q=0.6,zh-TW;q=0.4",
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_8_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/35.0.1916.114 Safari/537.36"
        }

    @staticmethod
    def getCaptcha(image, image_data):
        # 通过DeathByCaptcha 方式获取验证码
        client = deathbycaptcha.SocketClient('', '')
        try:
            captcha = client.decode(image, 60)
            if captcha:
                logger.debug("CAPTCHA %s solved: %s" % (captcha["captcha"], captcha["text"]))
                logger.debug(str(captcha["text"]))
                if 'no clear' == str(captcha["text"]):
                    raise Exception("cannot captcha this picture")
                return captcha
        except Exception as e:
            logger.error("DEATH BY CAPTCHA exception:" + str(e))

            # 通过CaptchaByPass 方式获取验证码
            bypass_key = config.CaptchaByPassKey
            con = base64.b64encode(image_data)
            logger.debug("Decoding.")
            try:
                ret = bypass_api.bc_submit_captcha(bypass_key, con)
                logger.debug("Using the decoded %s : %s." % (ret['TaskId'], ret['Value']))
                logger.debug("There are " + bypass_api.bc_get_left(bypass_key) + " credits left on this key.")
                captcha = dict()
                captcha['text'] = ret['Value']
                if 'test' == str(captcha['text']):
                    raise Exception('captcha error')
                return captcha
            except Exception as e:
                logger.debug("BYPASS exception:" + str(e))
        return None

    @staticmethod
    def decodeBody(headers, body):
        for header in headers:
            if header[0].lower() == 'content-encoding':
                if header[1].lower().count('gzip') > 0:
                    return zlib.decompress(body, 16+zlib.MAX_WBITS)
        return body

    def setCookies(self, headers, encode=False):
        def next_token_is_not_semi(s):
            for i in  xrange(len(s)):
                if s[i] == ';':
                    return False
                if s[i] == '=':
                    return True
            return True

        def parse_one_cookie(set_cookie_str):
            state = 0
            for i in xrange(len(set_cookies_str)):
                if state == 0 and set_cookies_str[i] == '=':
                    state = 1
                elif state == 1 and set_cookies_str[i] == ';':
                    state = 0
                if state == 0 and set_cookies_str[i] == ',':
                    return  set_cookies_str[:i], set_cookies_str[i+1:].strip()
                if state == 1 and set_cookies_str[i] == ',' and next_token_is_not_semi(set_cookies_str[i+1:]):
                    return  set_cookies_str[:i], set_cookies_str[i+1:].strip()
                else:
                    continue
            return set_cookie_str, ""

        for header in headers:
            if header[0].lower() == 'set-cookie':
                #logger.debug(str(header))
                #set_cookies = header[1].split('; Path=/; ')
                set_cookies_str = header[1]
                #print set_cookies_str
                while len(set_cookies_str) > 0:
                    (one_cookie_str,set_cookies_str) = parse_one_cookie(set_cookies_str)
                    #print one_cookie_str
                    #print set_cookies_str
                    cookie = Cookie.from_string(one_cookie_str)
                    #print "cookie.name=%s,cookie.value=%s"%(cookie.name, cookie.value)
                    #self.cookies[cookie.name] = cookie.value
                    if encode:
                        self.cookies[cookie.name] = urllib.quote(cookie.value.encode('utf8'))
                    else:
                        self.cookies[cookie.name] = cookie.value.encode('utf8')
                #for set_cookie in set_cookies:
                #    cookie = Cookie.from_string(set_cookie)
                #    self.cookies[cookie.name] = cookie.value
        ks = self.cookies.keys()
        cookie_list = []
        for k in ks:
            cookie_list.append(k + '=' + self.cookies[k])
        self.headers['Cookie'] = string.join(cookie_list, '; ')
        logger.debug(str(self.headers))

    @staticmethod
    def getPrice(shareJob):
        vehicle = shareJob.get("vehicle", None)
        if vehicle is not None:
            price = vehicle.get("price", None)
            if price is not None:
                quotedPrice = price.get("quoted_price", None)
                if quotedPrice is not None:
                    return int(round(Decimal(quotedPrice) / 100) * 100)
        return None

    def getSubstituteContact(self, share_account):
        substitute_account = share_account.get("substitute_account", None)
        if substitute_account is None:
            return None, None
        contact = substitute_account.get("contact", None)
        if contact is None:
            return None, None
        name = contact.get("name", None)
        phone = contact.get("phone", None)
        if name is None or phone is None:
            return None, None
        return name, phone

    def getPublicContact(self, shareJob):
        share_account = shareJob['share_account']
        # FIXME
        name, phone = self.getSubstituteContact(share_account)
        if name is not None and phone is not None:
            return name, phone

        # TODO: 保底联系人
        default_name = u'乔女士'
        default_phone = u'15300066914'

        return default_name, default_phone

    def getUserName(self, user):
        name = user.get('name', u'乔女士')
        return name
        '''
        gender = user.get("gender", "male")
        firstName = user.get("name", u"看")[:1]
        if gender == "male":
            return firstName + u"先生"
        else:
            return firstName + u"女士"
        '''

    def getIVRContact(self, user):
        conn = pymongo.Connection(config.mongoServer, tz_aware=True)
        db = conn['kanche']
        ivr_number_collection = db['ivr_number']
        ivr_number = ivr_number_collection.find_one({"user_id": user.get("_id", None)})
        if ivr_number is None:
            conn.close()
            return None
        else:
            conn.close()
            return self.getUserName(user), ivr_number.get("display_number", None)

    def getContact(self, shareJob):
        vehicle = shareJob.get("vehicle", None)
        if vehicle is None:
            logger.error("vehicle missing")
            return None, None
        merchant = vehicle.get("merchant", None)
        if merchant is not None:
            ownership = merchant.get("ownership", None)
            if ownership is not None and len(ownership) != 0:
                occupied = ownership[0].get("occupied", None)
                if occupied is True:
                    owner = ownership[0].get("owner", None)
                    if owner is not None:
                        res = self.getIVRContact(owner)
                        if res is not None:
                            return res
        #contracted = vehicle.get("contracted", False)
        #if contracted is True:
        #    return u'詹先生', u'15300066914'
        share_account = shareJob.get("share_account")
        if share_account is None:
            return None, None
        if share_account.get("account_type", None) == "public":
            return self.getPublicContact(shareJob)
        user = vehicle.get("user", None)
        if user is None:
            return None, None
        if share_account.get("account_type", None) == "substitute":
            return self.getPublicContact(shareJob)

        mobile = user.get("mobile", None)
        if mobile is None:
            return None, None
        public_phone = user.get("public_phone", None)
        if public_phone is not None:
            if len(public_phone) > 10:
                mobile = public_phone
        return user['name'], mobile

    def getContentVal(self, shareJob, Symbol="\r\n", lateral="——"*23):
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

                content += u'我们向您承诺：' + Symbol
                content += u'车况：大量优质车源，208项售前检测，专业评估师把关，呈现真实车况。' + Symbol
                content += u'车价：专业买车顾问全程1对1服务，交易透明，不赚差价。' + Symbol
                content += u'过户：免费过户，包办手续。' + Symbol
                content += u'质保：为8年及15万公里以内的车辆提供超低价格的1年或2万公里保修服务。' + Symbol
                content += u'贷款：可分期付款，只需身份证，即可申请，超低月供, 超低月息。' + Symbol*2

        content += str(vehicle.get('series_number', '')) + "#"
        content += str(vehicle['_id'])

        if "" == content:
            content = u"无车辆说明，请添加至10个字以上"
        return content

    def getContentVal_finance(self, shareJob, Symbol="\r\n", lateral="——"*23):
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

        content += u"可贷款 申请快 利率低"
        content += Symbol + u"看车网发现二手好车，大量优质有效车源，车况靠谱，价格透明"
        content += Symbol*2 + u"1张身份证，秒速贷款。"

        content += Symbol*2 + u"车辆概况："
        # 采用商家说明 追加
        if merchantDisable is False:
            description = ""
            description_list = merchant_substitute_config.get('description_list', None)
            if description_list is not None:
                for i in description_list:
                    site = i.get('site', None)
                    if site == 'che168.com':
                        description = i.get('description', None)
                        description = string.replace(description, '\n', Symbol)
            content += Symbol + description

        if vehicleDisable is False:
            # 车况说明，来自bss模板
            if detail != "":
                content += Symbol + detail


        # 统一说明 追加
        if globalDisable is False:
            if share_account.get("account_type", None) == "substitute":
                content += Symbol*3 + u'值得信赖的专业二手车顾问'
                content += Symbol + u'[ 贷款 ] 月息低至6厘8，只需身份证，超低门槛，秒速贷款。'
                content += Symbol + u'[ 车况 ] 208项售前检测，绝无事故车，泡水、火烧车。'
                content += Symbol + u'[ 服务 ] 免费过户，包办手续，有质保。'

                content += Symbol*2 + u'我是白户，可以申请车贷么？'
                content += Symbol + u'想买个便宜车，贷款怎么办？'
                content += Symbol + u'中意的车龄长达八年怎么办？'
                content += Symbol + u'我资质非常好，想多多贷款？'
                content += Symbol + u'没关系，只要您符合条件，只需一张身份证，其他的我们来做。'

                content += Symbol*2 + u'不满意？没关系，登陆[ 看车网 ] ！更多优质车源供您挑选！'
                content += Symbol + u'或致电看车网，根据您的需求，为您推荐最好最适合的车辆'

                content += Symbol*2 + u'在看车网，买车从未如此简单，专业买车顾问全程1对1服务，交易透明，不赚差价'

                content += Symbol*2 + u'看车网向您承诺：'
                content += Symbol + u'选车：大量优质车源，根据您的需求，推荐最好最适合的车辆。'
                content += Symbol + u'车况：208项售前检测，专业评估师把关，呈现真实车况。'
                content += Symbol + u'车价：专业买车顾问全程1对1服务，交易透明，不赚差价。'
                content += Symbol + u'过户：免费过户，包办手续。'
                content += Symbol + u'质保：为8年及15万公里以内的车辆提供超低价格的1年或2万公里保修服务。'
                content += Symbol + u'贷款：可分期付款，只需身份证，即可申请，超低月供, 超低月息。'

        content += Symbol*2 + u"更多选择，尽在看看车。"
        content += Symbol*2 + str(vehicle.get('series_number', '')) + "#"
        content += str(vehicle['_id'])

        if "" == content:
            content = u"无车辆说明，请添加至10个字以上"
        return content


    def promotionWords(self, vehicle, isSelectedBDwords=False):
        defaultPromotionWords = u'[此车可贷款,只需身份证]'
        promotionWords = ''
        promotable = self.loanable(vehicle)
        if promotable:
            promotionWords = defaultPromotionWords
        else:
            promotionWords = u'[手续全 过户快]'
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

    # 是否可贷款
    def loanable(self, vehicle):
        vehicle_date = vehicle.get('vehicle_date', None)
        registration_date = vehicle_date.get('registration_date', None)
        registration_year = int(str(registration_date)[:4])
        price = vehicle.get("price", None)
        quoted_price = price.get("quoted_price", 0)

        # 南京：所有08以后的车，全是可贷款。
        if registration_year >= 2008 and quoted_price >= 30000:
            promotable = True
        else:
            promotable = False
        return promotable

    ####
    #判断账号是否超出限制的函数
    #website、username 、date：'2015-01-01'、num: int
    #####
    def isInnerAccountLimit(self, website, username, limit, deadline="day"):
        conn = pymongo.Connection(config.accountLimitMongoServer, tz_aware=True)
        db = conn['kanche']
        col = db['send_count']
        col.ensure_index(
            [("website", pymongo.ASCENDING), ("username", pymongo.ASCENDING), ("date", pymongo.ASCENDING)])

        mDate = time.strftime("%Y-%m-%d", time.localtime())
        if deadline == 'day':
            date = mDate
        elif deadline == 'week':
            #TODO date
            pass
        elif deadline == 'month':
            #TODO date
            pass

        query = {
            "website": website,
            "username": username,
            "date": date
        }
        item = col.find_one(query)
        conn.close()

        if item is None:
            return True

        num = item.get('num', None)
        if num is None:
            return True

        if num < limit:
            return True

        return False


    ##########
    #添加或者更改发车的数量值
    ##########
    def upsertAccountNum(self, website, username, limit, deadline):
        conn = pymongo.Connection(config.accountLimitMongoServer, tz_aware=True)
        db = conn['kanche']
        col = db['send_count']
        col.ensure_index(
            [("website", pymongo.ASCENDING), ("username", pymongo.ASCENDING), ("date", pymongo.ASCENDING)])

        mDate = time.strftime("%Y-%m-%d", time.localtime())
        if deadline == 'day':
            date = mDate
        elif deadline == 'week':
            #TODO date
            pass
        elif deadline == 'month':
            #TODO date
            pass

        query = {
            "website": website,
            "username": username,
            "date": date
        }

        item = col.find_one(query)
        if item is None:
            value = {
                "website": website,
                "username": username,
                "date": date,
                "num": 1
            }
            col.update(query, {"$set": value}, upsert=True)
            conn.close()
            return


        num = item.get('num', None)
        if num is None or num == limit:
            logger.debug("upsert num error - " + str(website))
            conn.close()
            return

        if num < limit:
            value = {
                "website": website,
                "username": username,
                "date": date,
                "num": num+1
            }
            col.update(query, {"$set": value}, upsert=True)
            conn.close()
            return

    def getCheshenyanseVal(self, carInfo):
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

    def getMinProceVal(self, carInfo):
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

    def getRundistanceVal(self, carInfo):
        rundistance = '1'
        vehicle = carInfo.get("vehicle", None)
        if vehicle is not None:
            summary = vehicle.get("summary", None)
            if summary is not None:
                mileage = summary.get("mileage", None)
                if mileage is not None:
                    rundistance = str(Decimal(mileage) / Decimal(10000))
        return rundistance

    def getTypeDate(self, name, vehicle_date):
        '''
        cjshijian   2016|1
        qxshijian   2016|1
        syshijian   2016|1
        '''
        iNow = datetime.datetime.now()
        iNow = iNow.replace(day=1, hour=0, minute=0, second=0, microsecond=0, tzinfo=tz.HKT)
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
            # cjshijian暂不知什么意义
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
        year = date.year
        month = date.month
        if month == 0:
            month = 1
        value = (str(year) + "|" + str(month)).encode('utf-8')
        return value


    def doLogin(self, username, password):
        raise NotImplementedError()

    def shareVehicle(self, shareJob):
        raise NotImplementedError()

    def updateVehicle(self, shareJob):
        raise NotImplementedError()

    def removeVehicle(self, shareJob):
        raise NotImplementedError()
