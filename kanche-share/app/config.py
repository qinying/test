#!/usr/bin/python
# -*- coding: UTF-8 -*-

__author__ = 'jesse'

# mongoServer = "mongodb://localhost:27017"
mongoServer = "mongodb://10.163.171.62:27017"


#TODO: to change!
# accountLimitMongoServer = "mongodb://localhost:27017"
accountLimitMongoServer = "mongodb://10.45.201.13:27017"

CaptchaByPassKey = ''

che168VIPAccountList = [u'武汉看看车二手车', u'成都看看车二手车', u'重庆看看车二手车',
                        u'西安看看车二手车', u'郑州看看车二手车', u'佛山看看车二手车',
                        u'南京看看车二手车', u'苏州看看车二手车']

publicAccount_che168 =[u'北京看看车二手车', u'成都看看车二手车', u'佛山看看车二手车',
                       u'南京看看车二手车', u'深圳看看车二手车', u'石家庄看看车二手车',
                       u'苏州看看车二手车', u'武汉看看车二手车', u'西安看看车二手车',
                       u'郑州看看车二手车', u'重庆看看车二手车', u'长沙看看车二手车',
                       u'南宁看看车二手车', u'福州看看车二手车', u'济南看看车二手车',
                       u'包头看看车二手车', u'天津看看车二手车', u'东莞看看车二手车',
                       u'哈尔滨看看车二手车', u'杭州看看车二手车', u'长春看看车二手车',
                       u'温州看看车二手车', u'大连看看车二手车', u'沈阳看看车二手车',
                       u'无锡看看车二手车', u'合肥看看车二手车']


# 58非诚信车商账号的城市
# 合肥、长沙、佛山、杭州、沈阳、温州、武汉、南宁、昆明
# 大连、重庆、成都、石家庄、长春、哈尔滨、西安、郑州
fe_not_integrity_merchant_city_list = ['340100', '430100', '440600', '330100', '210100', '330300', '420100', '450100', '530100',
                                       '210200', '500100', '510100', '130100', '220100', '230100', '610100', '410100']


ganjiUsername2UseridDict = {
    u"北京看车二手车":     363275351,
    u"成都看车网":   473457661,
    u"大连看车网":   482734182,
    u"德州看看车":	454680832,
    u"佛山看车网":	472391026,
    u"福州看车网":	472385128,
    u"广州看车网":	492638440,
    u"哈尔滨看车网":	492638934,
    u"合肥看车网":	493710769,
    u"杭州看车网":	493707919,
    u"呼和浩特看车网":	493717423,
    u"南京看车网":	493710425,
    u"青岛看车网":	447609171,
    u"厦门看车网":	483803243,
    u"深圳看车网":	493711199,
    u"沈阳看车网":	493712083,
    u"石家庄看车网":	416885100,
    u"苏州看车网":	492635256,
    u"武汉看车网":	493711605,
    u"西安看车网":	492637906,
    u"长春看车网":	493711745,
    u"郑州看车网":	492634454,
    u"重庆看车网":	473457485,
    u"上海看车网":	500505932,
    u"无锡看车网":	493710207,
    u"宁波看车网":	501549899,
    u"南宁看车网":	500480588,
    u"温州看车网":	500479158,
    u"昆明看车网":	501547237,
    u"东莞看车网":	500505608,
    u"长沙看车网":	501546655,
    u"天津看车网":	501546209,
    u"济南看车网":	532847664
}