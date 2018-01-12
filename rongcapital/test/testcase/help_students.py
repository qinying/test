#-*- coding: UTF-8 -*-
from datetime import date
import data
import datetime
import random
from jsondate import data
import time
import sys
import requests
reload(sys)
sys.setdefaultencoding('utf8')

a = data()
jsondata = a.json()
per_json = a.per()
yueshijue_json = a.yue()
fang_json = a.fangcangqiye()
d = random.randint(1000, 9999)
nub = random.randint(100, 1000)
# 企业用户ID
usrid = 201712345 + d
# 个人用户ID
guserid = 1990123 + d
# 机构号
constid = 'M000020'
# 交易流水
orderid = 10080 + d
# 产品号
productid = 'P000146'
# 身份证号
certificatenumber = 110228199007290030 + nub
# 税务登记号
taxregcard = 20179877 + d
# 企业名称
c = str(d)
today = date.today()
a = today.year
b = today.month
tt = today.day
daty = tt + 1
year = str(a)[2:]
date_today = year + "-" + str(b) + "-" + str(daty)
session = requests.session()
order_id = 2015876 + d

class shuju():
    session = requests.session()
    # 58测试环境rop企业接口
    method_url = "ruixue.wheatfield.enterprise.entityaccountopt"  # 机构开户
    Push_url = "ruixue.wheatfield.oprsystem.credit.company"  # 机构推送
    Credit_url = "ruixue.wheatfield.order.mixservice.creditapplication"  # 机构授信
    Agreement = "ruixue.wheatfield.order.service.agreementconfirm"  # 协议上传

    # 测试环境rop个人接口
    personal_method_url = "ruixue.wheatfield.person.accountopr"  # 个人开户
    personal_Push_url = "ruixue.wheatfield.oprsystem.credit.person"  # 个人授信推送
    personal_loan_url = "ruixue.wheatfield.order.service.newloanapply"  # 贷款申请

    # 58测试环境key secret url
    app_key = "33D9F33B-C932-451B-9200-676EF3C9AFED"
    app_secret = "DE8BA286-3A96-4FFF-B021-218602D5F4A8"
    ropurl = "https://api.open.ruixuesoft.com:30005/ropapi"

    def sessionApi(self):
        # 获取Session Key
        url = "http://open.ruixuesoft.com:30002/Common/HttpAdpter.ashx"
        headers = {
            "Accept": "text/plain, */*; q=0.01",
            "Accept-Encoding": "gzip, deflate",
            "Accept-Language": "zh-CN,zh;q=0.8",
            "Connection": "keep-alive",
            "Content-Length": "206",
            "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
            "Host": "open.ruixuesoft.com:30002",
            "Origin": "http://open.ruixuesoft.com:30002",
            "Referer": "http://open.ruixuesoft.com:30002/ApiTool/index?sign=",
            "User-Agent": "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/54.0.2840.99 Safari/537.36",
            "X-Requested-With": "XMLHttpRequest"
        }
        data = {
            'action': 'EXCUTEAPISESSION',
            'adpter': 'apiadpter',
            'format': 'xml',
            'ropurl': shuju.ropurl,
            'app_key': shuju.app_key,
            'app_secret': shuju.app_secret
        }

        cong_fig = self.session.post(url=url, data=data, headers=headers)
        congfig_text = cong_fig.text
        session_Key = congfig_text[4:]
        return session_Key
        print session_Key + 'sadddfff'


    # 调用API开户 帮帮

    def open_Account(self):
        shu = shuju()
        keys = shu.sessionApi()
        time = datetime.datetime.now()
        api_url = "http://open.ruixuesoft.com:30002/Common/HttpAdpter.ashx"
        session = requests.session()
        header = {
            "Accept": "text/plain, */*; q=0.01",
            "Accept-Encoding": "gzip, deflate",
            "Accept-Language": "zh-CN,zh;q=0.8",
            "Connection": "keep-alive",
            "Content-Length": "1203",
            "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
            "Host": "open.ruixuesoft.com:30002",
            "Origin": "http://open.ruixuesoft.com:30002",
            "Referer": "http://open.ruixuesoft.com:30002/ApiTool/index?sign=",
            "User-Agent": "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/54.0.2840.99 Safari/537.36X-Requested-With:XMLHttpRequest"
        }
        date = {
            'action': 'EXCUTEAPI',
            'adpter': 'apiadpter',
            'format': 'xml',
            'method': shuju.method_url,
            'ropurl': shuju.ropurl,
            'app_key': shuju.app_key,
            'app_secret': shuju.app_secret,
            'session': keys,
            'param_name_0': 'companyname',  # 企业名称
            'param_value_0': u'企业名称' + c,
            'param_name_1': 'shortname',
            'param_value_1': '',
            'param_name_2': 'mcc',
            'param_value_2': '',
            'param_name_3': 'post',
            'param_value_3': '',
            'param_name_4': 'connect',
            'param_value_4': '',
            'param_name_5': 'address',
            'param_value_5': '',
            'param_name_6': 'buslince',  # 营业执照号
            'param_value_6': 12546448484844 + d,
            'param_name_7': 'acuntopnlince',
            'param_value_7': '',
            'param_name_8': 'companycode',
            'param_value_8': '',
            'param_name_9': 'taxregcardf',
            'param_value_9': '',
            'param_name_10': 'taxregcards',
            'param_value_10': '',
            'param_name_11': 'organcertificate',
            'param_value_11': '',
            'param_name_12': 'corporatename',
            'param_value_12': '',
            'param_name_13': 'corporateidentity',
            'param_value_13': '',
            'param_name_14': 'busplacectf',
            'param_value_14': '',
            'param_name_15': 'loancard',
            'param_value_15': '',
            'param_name_16': 'remark',
            'param_value_16': '',
            'param_name_17': 'userid',  # 用户Id
            'param_value_17': usrid,
            'param_name_18': 'usertype',
            'param_value_18': 1,
            'param_name_19': 'constid',  # 机构号
            'param_value_19': constid,
            'param_name_20': 'productid',  # 产品号
            'param_value_20': productid,
            'param_name_21': 'role',
            'param_value_21': '',
            'param_name_22': 'username',  # 用户名称
            'param_value_22': u'帮帮助学',
            'param_count': 23
        }

        m = session.post(url=api_url, headers=header, data=date)
        adpter = m.text
        print adpter

        # 调用API推送
        Push_data = {
            'action': 'EXCUTEAPI',
            'adpter': 'apiadpter',
            'format': 'xml',
            'method': shuju.Push_url,
            'ropurl': shuju.ropurl,
            'app_key': shuju.app_key,
            'app_secret': shuju.app_secret,
            'session': keys,
            'param_name_0': 'userid',
            'param_value_0': usrid,
            'param_name_1': 'constid',
            'param_value_1': constid,
            'param_name_2': 'companyname',  # 法人姓名
            'param_value_2': u'法人姓名',
            'param_name_3': 'registrationorga',  # 企业登记号
            'param_value_3': u'企业登记号',
            'param_name_4': 'businesslicense',  # 营业执照号
            'param_value_4': 2016098 + d,
            'param_name_5': 'certificatestartdate',
            'param_value_5': time,
            'param_name_6': 'certificateexpiredate',
            'param_value_6': time,
            'param_name_7': 'companytype',
            'param_value_7': 1,
            'param_name_8': 'registfinance',  # 注册基本
            'param_value_8': 12000000,
            'param_name_9': 'address',  # 企业地址
            'param_value_9': u'企业地址',
            'param_name_10': 'taxregcard',  # 税务登记号
            'param_value_10': taxregcard,
            'param_name_11': 'organcertificate',  # 机构号
            'param_value_11': constid,
            'param_name_12': 'acuntopenlince',
            'param_value_12': 9,
            'param_name_13': 'corporatename',  # 企业名称
            'param_value_13': u'企业名称' + c,
            'param_name_14': 'certificatetype',
            'param_value_14': 1,
            'param_name_15': 'certificatenumber',  # 法人身份证号
            'param_value_15': 110228199007290021,
            'param_count': 16
        }
        Push_data_post = session.post(url=api_url, headers=header, data=Push_data)
        pust_test = Push_data_post.text
        print pust_test

        # 调用API授信
        Credit_data = {
            'action': 'EXCUTEAPI',
            'adpter': 'apiadpter',
            'format': 'xml',
            'method': shuju.Credit_url,
            'ropurl': shuju.ropurl,
            'app_key': shuju.app_key,
            'app_secret': shuju.app_secret,
            'session': keys,
            'param_name_0': 'userid',
            'param_value_0': usrid,
            'param_name_1': 'userorderid',
            'param_value_1': order_id,
            'param_name_2': 'amount',
            'param_value_2': 15500000,
            'param_name_3': 'productid',  # 产品ID
            'param_value_3': productid,
            'param_name_4': 'rootinstcd',
            'param_value_4': constid,
            'param_name_5': 'userrelateid',  # 关联ID
            'param_value_5': usrid,
            'param_name_6': 'reqesttime',  # 申请期限
            'param_value_6': 6,
            'param_name_7': 'orderplatformname',  # 申请单位名称
            'param_value_7': u'申请单位名称',
            'param_name_8': 'requestdate',  # 申请时间
            'param_value_8': time,
            'param_name_9': 'ratetemplrate',
            'param_value_9': 'RA201607151100005',
            'param_name_10': 'remark',  # 备注
            'param_value_10': u'备注',
            'param_name_11': 'jsondata',
            'param_value_11': jsondata,
            'param_name_12': 'urlkey',
            'param_value_12': '0eef33f2-6cc2-4a5f-9e23-512f9c348179',
            'param_name_13': 'creditype',
            'param_value_13': '',
            'param_count': 14,
        }
        Credit_post = session.post(url=api_url, headers=header, data=Credit_data)
        Credit_test = Credit_post.text
        print Credit_test
        return order_id

    # 待协议上传
    def Agr(self):
        shu = shuju()
        Agreement_keys = shu.sessionApi()
        Agreement_url = 'http://open.ruixuesoft.com:30002/Common/HttpAdpter.ashx'
        Agreement_header = {
            'Accept': 'text/plain, */*; q=0.01',
            'Accept-Encoding': 'gzip, deflate',
            'Accept-Language': 'zh-CN,zh;q=0.8',
            'Connection': 'keep-alive',
            'Content-Length': '712',
            'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
            'Host': 'open.ruixuesoft.com:30002',
            'Origin': 'http://open.ruixuesoft.com:30002',
            'RA-Sid': '4f353fa0-ccdc-11e6-82e6-e993dd9ab1c8',
            'RA-Ver': '6.1',
            'Referer': 'http://open.ruixuesoft.com:30002/ApiTool/index?sign=',
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_2) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/55.0.2883.95 Safari/537.36',
            'X-Requested-With': 'XMLHttpRequest'
        }
        Agreement_data = {
            'action': 'EXCUTEAPI',
            'adpter': 'apiadpter',
            'format': 'xml',
            'method': 'ruixue.wheatfield.order.service.agreementconfirm',
            'ropurl': shuju.ropurl,
            'app_key': shuju.app_key,
            'app_secret': shuju.app_secret,
            'session': Agreement_keys,
            'param_name_0': 'urlkeyd',
            'param_value_0': '',
            'param_name_1': 'userorderid',  # 订单ID
            'param_value_1': order_id,
            'param_name_2': 'rootinstcd',  # 机构号
            'param_value_2': constid,
            'param_name_3': 'urlkeya',
            'param_value_3': '',
            'param_name_4': 'urlkeyb',
            'param_value_4': '',
            'param_name_5': 'urlkeyc',
            'param_value_5': '',
            'param_name_6': 'userid',  # 用户ID
            'param_value_6': usrid,
            'param_name_7': 'merchanturlkey',
            'param_value_7': '8b2ffb6c-d1df-48d3-8b24-e398e5da7984',
            'param_name_8': 'murlkeya',
            'param_value_8': 'f0a59bc1-3e1d-4ceb-af87-b9b464742e11',
            'param_name_9': 'userflag',  # 2为企业 1为个人
            'param_value_9': 2,
            'param_count': 10,
        }
        Agreement_post = self.session.post(url=Agreement_url, headers=Agreement_header, data=Agreement_data)
        print Agreement_post.text
        time.sleep(20)

# 个人开户 授信 贷款
    def personal(self):
        per_data = datetime.datetime.now()
        shu = shuju()
        personal_keys = shu.sessionApi()
        personal_url = "http://open.ruixuesoft.com:30002/Common/HttpAdpter.ashx"
        personal_header = {
            'Accept': 'text/plain, */*; q=0.01',
            'Accept-Encoding': 'gzip, deflate',
            'Accept-Language': 'zh-CN,zh;q=0.8',
            'Connection': 'keep-alive',
            'Content-Length': '1067',
            'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
            'Host': 'open.ruixuesoft.com:30002',
            'Origin': 'http://open.ruixuesoft.com:30002',
            'RA-Sid': '4f353fa0-ccdc-11e6-82e6-e993dd9ab1c8',
            'RA-Ver': '6.1',
            'Referer': 'http://open.ruixuesoft.com:30002/ApiTool/index?sign=',
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_2) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/55.0.2883.95 Safari/537.36',
            'X-Requested-With': 'XMLHttpRequest'
        }
        personal_data = {
            'action': 'EXCUTEAPI',
            'adpter': 'apiadpter',
            'format': 'xml',
            'method': shuju.personal_method_url,
            'ropurl': shuju.ropurl,
            'app_key': shuju.app_key,
            'app_secret': shuju.app_secret,
            'session': personal_keys,
            'param_name_0': 'address',
            'param_value_0': '',
            'param_name_1': 'productid',  # 产品号
            'param_value_1': productid,
            'param_name_2': 'persontype',
            'param_value_2': '',
            'param_name_3': 'personchnname',  # 中文名字
            'param_value_3': 2,
            'param_name_4': 'constid',  # 机构号
            'param_value_4': constid,
            'param_name_5': 'remark',
            'param_value_5': '',
            'param_name_6': 'personsex',
            'param_value_6': '',
            'param_name_7': 'certificatetype',  # 证件类型  0 - 7
            'param_value_7': 0,
            'param_name_8': 'certificatenumber',  # 证件号
            'param_value_8': certificatenumber,
            'param_name_9': 'mobiletel',
            'param_value_9': '',
            'param_name_10': 'userid',  # 用户ID
            'param_value_10': guserid,
            'param_name_11': 'post',
            'param_value_11': '',
            'param_name_12': 'fixtel',
            'param_value_12': '',
            'param_name_13': 'referuserid',
            'param_value_13': '',
            'param_name_14': 'username',
            'param_value_14': '',
            'param_name_15': 'role',
            'param_value_15': '',
            'param_name_16': 'birthday',
            'param_value_16': '',
            'param_name_17': 'personengname',
            'param_value_17': '',
            'param_name_18': 'opertype',  # 操作类型
            'param_value_18': 1,
            'param_name_19': 'email',
            'param_value_19': '',
            'param_count': 20
        }
        personal_post = self.session.post(url=personal_url, headers=personal_header, data=personal_data)
        print personal_post.text

        kaihu_data = {
            'action': 'EXCUTEAPI',
            'adpter': 'apiadpter',
            'format': 'xml',
            'method': shuju.personal_Push_url,
            'ropurl': shuju.ropurl,
            'app_key': shuju.app_key,
            'app_secret': shuju.app_secret,
            'session': personal_keys,
            'param_name_0': 'userid',  # 申请人ID
            'param_value_0': guserid,
            'param_name_1': 'certificatestartdate',  # 身份生效
            'param_value_1': '1990-01-03 10:01:01',
            'param_name_2': 'certificateexpiredate',  # 身份失效期
            'param_value_2': '2020-01-03 10:01:01',
            'param_name_3': 'mobilephone',  # 手机号
            'param_value_3': 18301080830,
            'param_name_4': 'constid',  # 机构号
            'param_value_4': constid,
            'param_name_5': 'certificatenumber',  # 身份证号
            'param_value_5': certificatenumber,
            'param_name_6': 'username',  # 姓名
            'param_value_6': u'姓名',
            'param_name_7': 'occupation',  # 职业
            'param_value_7': u'程序员',
            'param_name_8': 'isauthor',  # 身份证验证结果
            'param_value_8': 1,
            'param_name_9': 'tcaccount',  # 银行卡
            'param_value_9': 6228480402564890018,
            'param_count': 10
        }
        kaihu_post = self.session.post(url=personal_url, headers=personal_header, data=kaihu_data)
        print kaihu_post.text

        daikuan_data = {
            'action': 'EXCUTEAPI',
            'adpter': 'apiadpter',
            'format': 'xml',
            'method': 'ruixue.wheatfield.order.service.newloanapply',
            'ropurl': shuju.ropurl,
            'app_key': shuju.app_key,
            'app_secret': shuju.app_secret,
            'session': personal_keys,
            'param_name_0': 'userid',  # 申请人ID
            'param_value_0': guserid,
            'param_name_1': 'userorderid',  # 交易流水
            'param_value_1': orderid,
            'param_name_2': 'amount',  # 申请金额
            'param_value_2': 1,
            'param_name_3': 'productid',  # 产品ID
            'param_value_3': productid,
            'param_name_4': 'rootinstcd',  # 机构号
            'param_value_4': constid,
            'param_name_5': 'userrelateid',  # 申请人机构
            'param_value_5': usrid,
            'param_name_6': 'reqesttime',  # 申请期限
            'param_value_6': 4,
            'param_name_7': 'username',
            'param_value_7': u'学生',
            'param_name_8': 'requestdate',  # 申请时间
            'param_value_8': per_data,
            'param_name_9': 'ratetemplate',  # 费率模版
            'param_value_9': 'RA201607151100001',
            'param_name_10': 'remark',  # 备注
            'param_value_10': u'备注',
            'param_name_11': 'jsondata',
            'param_value_11': per_json,
            'param_name_12': 'urlkey',  # 费率模版
            'param_value_12': '7461673f-2b54-4c61-8b58-cc9e4053e8a4',
            'param_count': 13
        }
        daikuan_post = self.session.post(url=personal_url, headers=personal_header, data=daikuan_data)
        print daikuan_post.text
#个人协议上传
    def individual(self):
        shu = shuju()
        individual_keys = shu.sessionApi()
        individual_url = 'http://open.ruixuesoft.com:30002/Common/HttpAdpter.ashx'
        individual_header = {
            'Accept': 'text/plain, */*; q=0.01',
            'Accept-Encoding': 'gzip, deflate',
            'Accept-Language': 'zh-CN,zh;q=0.8',
            'Connection': 'keep-alive',
            'Content-Length': '712',
            'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
            'Host': 'open.ruixuesoft.com:30002',
            'Origin': 'http://open.ruixuesoft.com:30002',
            'RA-Sid': '4f353fa0-ccdc-11e6-82e6-e993dd9ab1c8',
            'RA-Ver': '6.1',
            'Referer': 'http://open.ruixuesoft.com:30002/ApiTool/index?sign=',
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_2) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/55.0.2883.95 Safari/537.36',
            'X-Requested-With': 'XMLHttpRequest'
        }
        individual_data = {
            'action': 'EXCUTEAPI',
            'adpter': 'apiadpter',
            'format': 'xml',
            'method': 'ruixue.wheatfield.order.service.agreementconfirm',
            'ropurl': shuju.ropurl,
            'app_key': shuju.app_key,
            'app_secret': shuju.app_secret,
            'session': individual_keys,
            'param_name_0': 'urlkeyd',
            'param_value_0': 'c628a2b4-4416-4fb0-adef-ad3fa895cfd5',
            'param_name_1': 'userorderid',  # 订单ID
            'param_value_1': orderid,
            'param_name_2': 'rootinstcd',  # 机构号
            'param_value_2': constid,
            'param_name_3': 'urlkeya',
            'param_value_3': '47238c84-01e2-4ef7-b16e-aab12aec698e',
            'param_name_4': 'urlkeyb',
            'param_value_4': '33ccffd6-4697-40f6-ae49-dc8c57149cad',
            'param_name_5': 'urlkeyc',
            'param_value_5': 'aff0d815-deda-4d1f-8259-bdeb6264a877',
            'param_name_6': 'userid',  # 用户ID
            'param_value_6': guserid,
            'param_name_7': 'merchanturlkey',
            'param_value_7': '',
            'param_name_8': 'murlkeya',
            'param_value_8': '',
            'param_name_9': 'userflag',  # 2为企业 1为个人
            'param_value_9': 1,
            'param_count': 10,
        }
        individual_post = self.session.post(url=individual_url, headers=individual_header, data=individual_data)
        print individual_post.text
        time.sleep(20)

        '''
            以上为帮帮企业授信 帮帮个人授信等接口
                                       '''
#房仓企业授信
    def fang_Cart(self):
        shu = shuju()
        fang_key = shu.sessionApi()
        fang_url = 'http://open.ruixuesoft.com:30002/Common/HttpAdpter.ashx'
        fang_head = {
            'Accept':'text/plain, */*; q=0.01',
            'Accept-Encoding':'gzip, deflate',
            'Accept-Language':'zh-CN,zh;q=0.8',
            'Connection': 'keep-alive',
            'Content-Length':'1289',
            'Content-Type':'application/x-www-form-urlencoded; charset=UTF-8',
            'Host':'open.ruixuesoft.com:30002',
            'Origin':'http://open.ruixuesoft.com:30002',
            'RA-Sid':'fbd6b7gqpxe06f3d11e6a73f4548ae513cdf',
            'RA-Ver':'7.1',
            'Referer':'http://open.ruixuesoft.com:30002/apitool/index?sign=',
            'User-Agent':'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_2) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/59.0.3071.115 Safari/537.36 EXT/fbd6b7gqpxe06f3d11e6a73f4548ae513cdf/7.1',
            'X-Requested-With':'XMLHttpRequest'
        }
        date = {
            'action': 'EXCUTEAPI',
            'adpter': 'apiadpter',
            'format': 'xml',
            'method': 'ruixue.wheatfield.enterprise.entityaccountopt',
            'ropurl': 'https://api.open.ruixuesoft.com:30005/ropapi',
            'app_key':shuju.app_key ,
            'app_secret': shuju.app_secret,
            'session': fang_key,
            'param_name_0': 'address',
            'param_value_0': '',
            'param_name_1': 'organcertificate',
            'param_value_1': '',
            'param_name_2': 'constid',
            'param_value_2': 'M000016',
            'param_name_3': 'productid',
            'param_value_3': 'P000070',
            'param_name_4': 'taxregcardf',
            'param_value_4': '',
            'param_name_5': 'remark',
            'param_value_5': '',
            'param_name_6': 'connect',
            'param_value_6': '',
            'param_name_7': 'mcc',
            'param_value_7': '',
            'param_name_8': 'companycode',
            'param_value_8': '',
            'param_name_9': 'buslince',
            'param_value_9': taxregcard,
            'param_name_10': 'corporatename',
            'param_value_10': '',
            'param_name_11': 'role',
            'param_value_11': '',
            'param_name_12': 'corporateidentity',
            'param_value_12': '',
            'param_name_13': 'userid',
            'param_value_13': usrid,
            'param_name_14': 'username',
            'param_value_14': u'房仓业务',
            'param_name_15': 'loancard',
            'param_value_15':'',
            'param_name_16':'shortname',
            'param_value_16':'',
            'param_name_17':'busplacectf',
            'param_value_17':'',
            'param_name_18':'taxregcards',
            'param_value_18':'',
            'param_name_19':'acuntopnlince',
            'param_value_19':'',
            'param_name_20':'referuserid',
            'param_value_20':'',
            'param_name_21':'post',
            'param_value_21':'',
            'param_name_22':'companyname',
            'param_value_22':u'房仓python',
            'param_name_23':'usertype',
            'param_value_23':1,
            'param_count':24,
        }
        fang_post = self.session.post(url=fang_url,headers=fang_head,data=date)
        print fang_post.text

        tui_data = {
            'action': 'EXCUTEAPI',
            'adpter': 'apiadpter',
            'format': 'xml',
            'method': 'ruixue.wheatfield.oprsystem.credit.company',
            'ropurl': 'https://api.open.ruixuesoft.com:30005/ropapi',
            'app_key': shuju.app_key,
            'app_secret': shuju.app_secret,
            'session': fang_key,
            'param_name_0': 'certificatestartdate',
            'param_value_0': datetime.datetime.now(),
            'param_name_1': 'certificatetype',
            'param_value_1': 1,
            'param_name_2': 'registrationorga',
            'param_value_2': '',
            'param_name_3': 'certificatenumber',
            'param_value_3': certificatenumber,
            'param_name_4': 'address',
            'param_value_4': u'北京朝阳',
            'param_name_5': 'organcertificate',
            'param_value_5': '',
            'param_name_6': 'registfinance',
            'param_value_6': 120000,
            'param_name_7': 'taxregcard',
            'param_value_7': taxregcard,
            'param_name_8': 'companytype',
            'param_value_8': 1,
            'param_name_9': 'companyname',
            'param_value_9': 'fangcang',
            'param_name_10': 'businesslicense',
            'param_value_10': taxregcard,
            'param_name_11': 'userid',
            'param_value_11': usrid,
            'param_name_12': 'corporatename',
            'param_value_12': u'房产测试',
            'param_name_13': 'constid',
            'param_value_13':'M000016',
            'param_name_14': 'acuntopenlince',
            'param_value_14': '',
            'param_name_15': 'certificateexpiredate',
            'param_value_15': datetime.datetime.now(),
            'param_count': 16,
        }
        fang_ret = self.session.post(url=fang_url,headers=fang_head, data=tui_data)
        print fang_ret.text

        shou_data = {
            'action': 'EXCUTEAPI',
            'adpter': 'apiadpter',
            'format': 'xml',
            'method': 'ruixue.wheatfield.order.mixservice.creditapplication',
            'ropurl': 'https://api.open.ruixuesoft.com:30005/ropapi',
            'app_key': shuju.app_key,
            'app_secret': shuju.app_secret,
            'session': fang_key,
            'param_name_0': 'userid',
            'param_value_0': usrid,
            'param_name_1': 'userorderid',
            'param_value_1': orderid,
            'param_name_2': 'amount',
            'param_value_2': 1400000,
            'param_name_3': 'productid',
            'param_value_3': 'P000070',
            'param_name_4': 'rootinstcd',
            'param_value_4': 'M000016',
            'param_name_5': 'userrelateid',
            'param_value_5': usrid,
            'param_name_6': 'reqesttime',
            'param_value_6': 12,
            'param_name_7': 'orderplatformname',
            'param_value_7': u'房仓测试',
            'param_name_8': 'requestdate',
            'param_value_8': datetime.datetime.now(),
            'param_name_9': 'ratetemplrate',
            'param_value_9': 'RA201611011800001',
            'param_name_10': 'remark',
            'param_value_10': '',
            'param_name_11': 'jsondata',
            'param_value_11': fang_json,
            'param_name_12': 'urlkey',
            'param_value_12': '0eef33f2-6cc2-4a5f-9e23-512f9c348179',
            'param_name_13': 'creditype',
            'param_value_13': 1,
            'param_count': 14,
        }
        shouxin = self.session.post(url=fang_url, headers=fang_head, data=shou_data)
        print shouxin.text

#悦视觉授信
    def yueshiyue(self):
        shu = shuju()
        yue_keys = shu.sessionApi()

        yue_url = "http://open.ruixuesoft.com:30002/Common/HttpAdpter.ashx"
        yue_head = {
            "Accept":"text/plain, */*; q=0.01",
            "Accept-Encoding":'gzip, deflate',
            "Accept-Language":"zh-CN,zh;q=0.8",
            "Connection":"keep-alive",
            "Content-Length":"1102",
            "Content-Type":"application/x-www-form-urlencoded; charset=UTF-8",
            "Host":"open.ruixuesoft.com:30002",
            "Origin":"http://open.ruixuesoft.com:30002",
            "RA-Sid":"fbd6b7gqpxe06f3d11e6a73f4548ae513cdf",
            "RA-Ver":"7.1",
            "Referer":"http://open.ruixuesoft.com:30002/apitool/index?sign=",
            "User-Agent":"Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_2) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/59.0.3071.115 Safari/537.36 EXT/fbd6b7gqpxe06f3d11e6a73f4548ae513cdf/7.1",
            "X-Requested-With":"XMLHttpRequest"
        }
        yue_data = {
            'action': 'EXCUTEAPI',
            'adpter': 'apiadpter',
            'format': 'xml',
            'method': 'ruixue.wheatfield.person.accountopr',
            'ropurl': shuju.ropurl,
            'app_key': shuju.app_key,
            'app_secret': shuju.app_secret,
            'session': yue_keys,
            'param_name_0': 'address',
            'param_value_0': '',
            'param_name_1': 'productid',
            'param_value_1': 'P000218',
            'param_name_2': 'persontype',
            'param_value_2': '',
            'param_name_3': 'personchnname',
            'param_value_3': usrid,
            'param_name_4': 'constid',
            'param_value_4': 'M000025',
            'param_name_5': 'remark',
            'param_value_5': '',
            'param_name_6': 'personsex',
            'param_value_6': '',
            'param_name_7': 'certificatetype',
            'param_value_7': 0,
            'param_name_8': 'certificatenumber',
            'param_value_8': certificatenumber,
            'param_name_9': 'mobiletel',
            'param_value_9': '',
            'param_name_10': 'userid',
            'param_value_10': usrid,
            'param_name_11': 'post',
            'param_value_11': '',
            'param_name_12': 'fixtel',
            'param_value_12': '',
            'param_name_13': 'referuserid',
            'param_value_13': '',
            'param_name_14': 'username',
            'param_value_14': '',
            'param_name_15': 'role',
            'param_value_15': '',
            'param_name_16': 'birthday',
            'param_value_16':'',
            'param_name_17':'personengname',
            'param_value_17':'',
            'param_name_18':'opertype',
            'param_value_18':1,
            'param_name_19':'email',
            'param_value_19':'',
            'param_count':20,
        }
        yue_post = self.session.post(url=yue_url,headers=yue_head,data=yue_data)
        print yue_post.text

        bang_data = {
            'action': 'EXCUTEAPI',
            'adpter': 'apiadpter',
            'format': 'xml',
            'method': 'ruixue.wheatfield.bankaccount.binding',
            'ropurl': shuju.ropurl,
            'app_key': shuju.app_key,
            'app_secret': shuju.app_secret,
            'session': yue_keys,
            'param_name_0': 'userid',
            'param_value_0': usrid,
            'param_name_1': 'usertype',
            'param_value_1': 2,
            'param_name_2': 'constid',
            'param_value_2': 'M000025',
            'param_name_3': 'productid',
            'param_value_3': 'P000218',
            'param_name_4': 'role',
            'param_value_4': '',
            'param_name_5': 'accountnumber',
            'param_value_5': 622500020170508007,
            'param_name_6': 'accounttypeid',
            'param_value_6': 00,
            'param_name_7': 'bankbranchname',
            'param_value_7': '',
            'param_name_8': 'bankheadname',
            'param_value_8': u'上海浦发银行',
            'param_name_9': 'currency',
            'param_value_9': 'CNY',
            'param_name_10': 'openaccountdate',
            'param_value_10': '',
            'param_name_11': 'req_sn',
            'param_value_11': 00001,
            'param_name_12': 'submit_time',
            'param_value_12': 201700508144101,
            'param_name_13': 'openaccountdescription',
            'param_value_13': '',
            'param_name_14': 'accountpurpose',
            'param_value_14': 1,
            'param_name_15': 'bindid',
            'param_value_15': '',
            'param_name_16': 'accountproperty',
            'param_value_16': 1,
            'param_name_17': 'relatid',
            'param_value_17': '',
            'param_name_18': 'certificatetype',
            'param_value_18': 0,
            'param_name_19': 'certificatenumnumber',
            'param_value_19': 130911199005080007,
            'param_name_20': 'account_name',
            'param_value_20': u'悦视觉测试',
            'param_name_21': 'relatedcard',
            'param_value_21': '',
            'param_name_22': 'tel',
            'param_value_22': '',
            'param_name_23': 'merrem',
            'param_value_23': '',
            'param_name_24': 'remark',
            'param_value_24': '',
            'param_name_25': 'referuserid',
            'param_value_25': '',
            'param_name_26': 'bank_code',
            'param_value_26': 103,
            'param_name_27': 'bank_branch',
            'param_value_27': 103,
            'param_name_28': 'bank_province',
            'param_value_28': u'河北省',
            'param_name_29': 'bank_city',
            'param_value_29': u'黄骅市',
            'param_count': 30,
        }
        kaihu_post = self.session.post(url=yue_url,headers=yue_head,data=bang_data)
        print kaihu_post.text

        tui_data = {
            'action': 'EXCUTEAPI',
            'adpter': 'apiadpter',
            'format': 'xml',
            'method': 'ruixue.wheatfield.oprsystem.credit.person',
            'ropurl': shuju.ropurl,
            'app_key': shuju.app_key,
            'app_secret': shuju.app_secret,
            'session': yue_keys,
            'param_name_0': 'userid',
            'param_value_0': usrid,
            'param_name_1': 'certificatestartdate',
            'param_value_1': '2010-07-26 12:00:00',
            'param_name_2': 'certificateexpiredate',
            'param_value_2': '2018-07-26 12:00:00',
            'param_name_3': 'mobilephone',
            'param_value_3': 18301080830,
            'param_name_4': 'constid',
            'param_value_4': 'M000025',
            'param_name_5': 'certificatenumber',
            'param_value_5': certificatenumber,
            'param_name_6': 'username',
            'param_value_6': u'悦视觉测试',
            'param_name_7': 'occupation',
            'param_value_7': u'学生',
            'param_name_8': 'isauthor',
            'param_value_8': 1,
            'param_name_9': 'tcaccount',
            'param_value_9': 622500020170508008,
            'param_count': 10,
        }
        tui_post = self.session.post(url=yue_url,headers=yue_head,data=tui_data)
        print tui_post.text

        dai_data = {
            'action': 'EXCUTEAPI',
            'adpter': 'apiadpter',
            'format': 'xml',
            'method': 'ruixue.wheatfield.order.service.newloanapply',
            'ropurl': shuju.ropurl,
            'app_key': shuju.app_key,
            'app_secret': shuju.app_secret,
            'session': yue_keys,
            'param_name_0': 'userid',
            'param_value_0': usrid,
            'param_name_1': 'userorderid',
            'param_value_1': orderid,
            'param_name_2': 'amount',
            'param_value_2': 1000,
            'param_name_3': 'productid',
            'param_value_3': 'P000218',
            'param_name_4': 'rootinstcd',
            'param_value_4': 'M000025',
            'param_name_5': 'userrelateid',
            'param_value_5': 'btest_080305',
            'param_name_6': 'reqesttime',
            'param_value_6': '',
            'param_name_7': 'username',
            'param_value_7': u'悦视觉测试',
            'param_name_8': 'requestdate',
            'param_value_8': datetime.datetime.now(),
            'param_name_9': 'ratetemplate',
            'param_value_9': 'RA201608101600001',
            'param_name_10': 'remark',
            'param_value_10': u'备注',
            'param_name_11': 'jsondata',
            'param_value_11': yueshijue_json,
            'param_name_12': 'urlkey',
            'param_value_12':'470de6cb-1b4d-4d2c-9192-454cb3d6b8d7',
            'param_count': 13,
        }
        dai_post = self.session.post(url=yue_url,headers=yue_head,data=dai_data)
        print dai_post.text

#悦视觉协议上传
    def xieyi(self):
        shu = shuju()
        xie_keys = shu.sessionApi()
        xie_url = 'http://open.ruixuesoft.com:30002/Common/HttpAdpter.ashx'
        xie_header = {
            "Accept": "text/plain, */*; q=0.01",
            "Accept-Encoding": 'gzip, deflate',
            "Accept-Language": "zh-CN,zh;q=0.8",
            "Connection": "keep-alive",
            "Content-Length": "1102",
            "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
            "Host": "open.ruixuesoft.com:30002",
            "Origin": "http://open.ruixuesoft.com:30002",
            "RA-Sid": "fbd6b7gqpxe06f3d11e6a73f4548ae513cdf",
            "RA-Ver": "7.1",
            "Referer": "http://open.ruixuesoft.com:30002/apitool/index?sign=",
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_2) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/59.0.3071.115 Safari/537.36 EXT/fbd6b7gqpxe06f3d11e6a73f4548ae513cdf/7.1",
            "X-Requested-With": "XMLHttpRequest"
        }
        xie_data = {
            'action': 'EXCUTEAPI',
            'adpter': 'apiadpter',
            'format': 'xml',
            'method': 'ruixue.wheatfield.order.service.agreementconfirm',
            'ropurl': shuju.ropurl,
            'app_key': shuju.app_key,
            'app_secret': shuju.app_secret,
            'session': xie_keys,
            'param_name_0': 'urlkeyd',
            'param_value_0': '438ca24e-f07d-4d44-9a5a-bb7a9067e68f',
            'param_name_1': 'userorderid',
            'param_value_1': orderid,
            'param_name_2': 'rootinstcd',
            'param_value_2': 'M000025',
            'param_name_3': 'urlkeya',
            'param_value_3': '9ca61c8a-3b7c-4cf0-9d55-c81d31de1613',
            'param_name_4': 'urlkeyb',
            'param_value_4': 'ab6e05c1-dde4-491b-bd5b-659366e52105',
            'param_name_5': 'urlkeyc',
            'param_value_5': '001c4efd-6dfb-4561-9834-eecf04bedccc',
            'param_name_6': 'userid',
            'param_value_6': usrid,
            'param_name_7': 'merchanturlkey',
            'param_value_7': '5f1f3973-f578-4392-aef1-4405af5a6b3daa',
            'param_name_8': 'murlkeya',
            'param_value_8': 1,
            'param_name_9': 'userflag',
            'param_value_9': 1,
            'param_count': 10
        }
        xie_post = self.session.post(url=xie_url,headers=xie_header,data=xie_data)
        print xie_post.text

#美容分期

    def meirong(self):
        shu = shuju()
        mei_keys = shu.sessionApi()

        mei_url = "http://open.ruixuesoft.com:30002/Common/HttpAdpter.ashx"
        mei_head = {
            "Accept":"text/plain, */*; q=0.01",
            "Accept-Encoding":'gzip, deflate',
            "Accept-Language":"zh-CN,zh;q=0.8",
            "Connection":"keep-alive",
            "Content-Length":"1102",
            "Content-Type":"application/x-www-form-urlencoded; charset=UTF-8",
            "Host":"open.ruixuesoft.com:30002",
            "Origin":"http://open.ruixuesoft.com:30002",
            "RA-Sid":"fbd6b7gqpxe06f3d11e6a73f4548ae513cdf",
            "RA-Ver":"7.1",
            "Referer":"http://open.ruixuesoft.com:30002/apitool/index?sign=",
            "User-Agent":"Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_2) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/59.0.3071.115 Safari/537.36 EXT/fbd6b7gqpxe06f3d11e6a73f4548ae513cdf/7.1",
            "X-Requested-With":"XMLHttpRequest"
        }
        mei_data = {
            'action': 'EXCUTEAPI',
            'adpter': 'apiadpter',
            'format': 'xml',
            'method': 'ruixue.wheatfield.person.accountopr',
            'ropurl': shuju.ropurl,
            'app_key': shuju.app_key,
            'app_secret': shuju.app_secret,
            'session': mei_keys,
            'param_name_0': 'address',
            'param_value_0': '',
            'param_name_1': 'productid',
            'param_value_1': 'P000138',
            'param_name_2': 'persontype',
            'param_value_2': '',
            'param_name_3': 'personchnname',
            'param_value_3': usrid,
            'param_name_4': 'constid',
            'param_value_4': 'M000028',
            'param_name_5': 'remark',
            'param_value_5': '',
            'param_name_6': 'personsex',
            'param_value_6': '',
            'param_name_7': 'certificatetype',
            'param_value_7': 0,
            'param_name_8': 'certificatenumber',
            'param_value_8': certificatenumber,
            'param_name_9': 'mobiletel',
            'param_value_9': '',
            'param_name_10': 'userid',
            'param_value_10': usrid,
            'param_name_11': 'post',
            'param_value_11': '',
            'param_name_12': 'fixtel',
            'param_value_12': '',
            'param_name_13': 'referuserid',
            'param_value_13': '',
            'param_name_14': 'username',
            'param_value_14': '',
            'param_name_15': 'role',
            'param_value_15': '',
            'param_name_16': 'birthday',
            'param_value_16':'',
            'param_name_17':'personengname',
            'param_value_17':'',
            'param_name_18':'opertype',
            'param_value_18':1,
            'param_name_19':'email',
            'param_value_19':'',
            'param_count':20,
        }
        mei_post = self.session.post(url=mei_url,headers=mei_head,data=mei_data)
        print mei_post.text

        mr_data = {
            'action': 'EXCUTEAPI',
            'adpter': 'apiadpter',
            'format': 'xml',
            'method': 'ruixue.wheatfield.bankaccount.binding',
            'ropurl': shuju.ropurl,
            'app_key': shuju.app_key,
            'app_secret': shuju.app_secret,
            'session': mei_keys,
            'param_name_0': 'userid',
            'param_value_0': usrid,
            'param_name_1': 'usertype',
            'param_value_1': 2,
            'param_name_2': 'constid',
            'param_value_2': 'M000028',
            'param_name_3': 'productid',
            'param_value_3': 'P000138',
            'param_name_4': 'role',
            'param_value_4': '',
            'param_name_5': 'accountnumber',
            'param_value_5': 622500020170508007,
            'param_name_6': 'accounttypeid',
            'param_value_6': 00,
            'param_name_7': 'bankbranchname',
            'param_value_7': '',
            'param_name_8': 'bankheadname',
            'param_value_8': u'上海浦发银行',
            'param_name_9': 'currency',
            'param_value_9': 'CNY',
            'param_name_10': 'openaccountdate',
            'param_value_10': '',
            'param_name_11': 'req_sn',
            'param_value_11': 00001,
            'param_name_12': 'submit_time',
            'param_value_12': 201700508144101,
            'param_name_13': 'openaccountdescription',
            'param_value_13': '',
            'param_name_14': 'accountpurpose',
            'param_value_14': 1,
            'param_name_15': 'bindid',
            'param_value_15': '',
            'param_name_16': 'accountproperty',
            'param_value_16': 1,
            'param_name_17': 'relatid',
            'param_value_17': '',
            'param_name_18': 'certificatetype',
            'param_value_18': 0,
            'param_name_19': 'certificatenumnumber',
            'param_value_19': 130911199005080007,
            'param_name_20': 'account_name',
            'param_value_20': u'美容测试',
            'param_name_21': 'relatedcard',
            'param_value_21': '',
            'param_name_22': 'tel',
            'param_value_22': '',
            'param_name_23': 'merrem',
            'param_value_23': '',
            'param_name_24': 'remark',
            'param_value_24': '',
            'param_name_25': 'referuserid',
            'param_value_25': '',
            'param_name_26': 'bank_code',
            'param_value_26': 103,
            'param_name_27': 'bank_branch',
            'param_value_27': 103,
            'param_name_28': 'bank_province',
            'param_value_28': u'河北省',
            'param_name_29': 'bank_city',
            'param_value_29': u'黄骅市',
            'param_count': 30,
        }
        mrC_post = self.session.post(url=mei_url,headers=mei_head,data=mr_data)
        print mrC_post.text

        mrtui_data = {
            'action': 'EXCUTEAPI',
            'adpter': 'apiadpter',
            'format': 'xml',
            'method': 'ruixue.wheatfield.oprsystem.credit.person',
            'ropurl': shuju.ropurl,
            'app_key': shuju.app_key,
            'app_secret': shuju.app_secret,
            'session': mei_keys,
            'param_name_0': 'userid',
            'param_value_0': usrid,
            'param_name_1': 'certificatestartdate',
            'param_value_1': '2010-07-26 12:00:00',
            'param_name_2': 'certificateexpiredate',
            'param_value_2': '2018-07-26 12:00:00',
            'param_name_3': 'mobilephone',
            'param_value_3': 18301080830,
            'param_name_4': 'constid',
            'param_value_4': 'M000028',
            'param_name_5': 'certificatenumber',
            'param_value_5': certificatenumber,
            'param_name_6': 'username',
            'param_value_6': u'美容测试',
            'param_name_7': 'occupation',
            'param_value_7': u'学生',
            'param_name_8': 'isauthor',
            'param_value_8': 1,
            'param_name_9': 'tcaccount',
            'param_value_9': 622500020170508008,
            'param_count': 10,
        }
        mrtui_post = self.session.post(url=mei_url,headers=mei_head,data=mrtui_data)
        print mrtui_post.text

        mrrdai_data = {
            'action': 'EXCUTEAPI',
            'adpter': 'apiadpter',
            'format': 'xml',
            'method': 'ruixue.wheatfield.order.service.newloanapply',
            'ropurl': shuju.ropurl,
            'app_key': shuju.app_key,
            'app_secret': shuju.app_secret,
            'session': mei_keys,
            'param_name_0': 'userid',
            'param_value_0': usrid,
            'param_name_1': 'userorderid',
            'param_value_1': orderid,
            'param_name_2': 'amount',
            'param_value_2': 1000,
            'param_name_3': 'productid',
            'param_value_3': 'P000138',
            'param_name_4': 'rootinstcd',
            'param_value_4': 'M000028',
            'param_name_5': 'userrelateid',
            'param_value_5': 'btest_080305',
            'param_name_6': 'reqesttime',
            'param_value_6': '',
            'param_name_7': 'username',
            'param_value_7': u'美容测试',
            'param_name_8': 'requestdate',
            'param_value_8': datetime.datetime.now(),
            'param_name_9': 'ratetemplate',
            'param_value_9': 'RA201611141800001',
            'param_name_10': 'remark',
            'param_value_10': u'备注',
            'param_name_11': 'jsondata',
            'param_value_11': yueshijue_json,
            'param_name_12': 'urlkey',
            'param_value_12':'470de6cb-1b4d-4d2c-9192-454cb3d6b8d7',
            'param_count': 13,
        }
        mrdai_post = self.session.post(url=mei_url,headers=mei_head,data=mrrdai_data)
        print mrdai_post.text

#美容协议上传
    def mrxieyi(self):
        shu = shuju()
        meixie_keys = shu.sessionApi()
        mxie_url = 'http://open.ruixuesoft.com:30002/Common/HttpAdpter.ashx'
        mxie_header = {
            "Accept": "text/plain, */*; q=0.01",
            "Accept-Encoding": 'gzip, deflate',
            "Accept-Language": "zh-CN,zh;q=0.8",
            "Connection": "keep-alive",
            "Content-Length": "1102",
            "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
            "Host": "open.ruixuesoft.com:30002",
            "Origin": "http://open.ruixuesoft.com:30002",
            "RA-Sid": "fbd6b7gqpxe06f3d11e6a73f4548ae513cdf",
            "RA-Ver": "7.1",
            "Referer": "http://open.ruixuesoft.com:30002/apitool/index?sign=",
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_2) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/59.0.3071.115 Safari/537.36 EXT/fbd6b7gqpxe06f3d11e6a73f4548ae513cdf/7.1",
            "X-Requested-With": "XMLHttpRequest"
        }
        mxie_data = {
            'action': 'EXCUTEAPI',
            'adpter': 'apiadpter',
            'format': 'xml',
            'method': 'ruixue.wheatfield.order.service.agreementconfirm',
            'ropurl': shuju.ropurl,
            'app_key': shuju.app_key,
            'app_secret': shuju.app_secret,
            'session': meixie_keys,
            'param_name_0': 'urlkeyd',
            'param_value_0': '438ca24e-f07d-4d44-9a5a-bb7a9067e68f',
            'param_name_1': 'userorderid',
            'param_value_1': orderid,
            'param_name_2': 'rootinstcd',
            'param_value_2': 'M000028',
            'param_name_3': 'urlkeya',
            'param_value_3': '9ca61c8a-3b7c-4cf0-9d55-c81d31de1613',
            'param_name_4': 'urlkeyb',
            'param_value_4': 'ab6e05c1-dde4-491b-bd5b-659366e52105',
            'param_name_5': 'urlkeyc',
            'param_value_5': '001c4efd-6dfb-4561-9834-eecf04bedccc',
            'param_name_6': 'userid',
            'param_value_6': usrid,
            'param_name_7': 'merchanturlkey',
            'param_value_7': '5f1f3973-f578-4392-aef1-4405af5a6b3daa',
            'param_name_8': 'murlkeya',
            'param_value_8': 1,
            'param_name_9': 'userflag',
            'param_value_9': 1,
            'param_count': 10
        }
        mxie_post = self.session.post(url=mxie_url,headers=mxie_header,data=mxie_data)
        print mxie_post.text

    #客栈企业 个人
    def open_kezhan(self):
        shu = shuju()
        ke_keys = shu.sessionApi()
        time = datetime.datetime.now()
        api_url = "http://open.ruixuesoft.com:30002/Common/HttpAdpter.ashx"
        k_header = {
            "Accept": "text/plain, */*; q=0.01",
            "Accept-Encoding": "gzip, deflate",
            "Accept-Language": "zh-CN,zh;q=0.8",
            "Connection": "keep-alive",
            "Content-Length": "1203",
            "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
            "Host": "open.ruixuesoft.com:30002",
            "Origin": "http://open.ruixuesoft.com:30002",
            "Referer": "http://open.ruixuesoft.com:30002/ApiTool/index?sign=",
            "User-Agent": "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/54.0.2840.99 Safari/537.36X-Requested-With:XMLHttpRequest"
        }
        k_date = {
            'action': 'EXCUTEAPI',
            'adpter': 'apiadpter',
            'format': 'xml',
            'method': shuju.method_url,
            'ropurl': shuju.ropurl,
            'app_key': shuju.app_key,
            'app_secret': shuju.app_secret,
            'session': ke_keys,
            'param_name_0': 'companyname',  # 企业名称
            'param_value_0': u'企业名称' + c,
            'param_name_1': 'shortname',
            'param_value_1': '',
            'param_name_2': 'mcc',
            'param_value_2': '',
            'param_name_3': 'post',
            'param_value_3': '',
            'param_name_4': 'connect',
            'param_value_4': '',
            'param_name_5': 'address',
            'param_value_5': '',
            'param_name_6': 'buslince',  # 营业执照号
            'param_value_6': 12546448484844 + d,
            'param_name_7': 'acuntopnlince',
            'param_value_7': '',
            'param_name_8': 'companycode',
            'param_value_8': '',
            'param_name_9': 'taxregcardf',
            'param_value_9': '',
            'param_name_10': 'taxregcards',
            'param_value_10': '',
            'param_name_11': 'organcertificate',
            'param_value_11': '',
            'param_name_12': 'corporatename',
            'param_value_12': '',
            'param_name_13': 'corporateidentity',
            'param_value_13': '',
            'param_name_14': 'busplacectf',
            'param_value_14': '',
            'param_name_15': 'loancard',
            'param_value_15': '',
            'param_name_16': 'remark',
            'param_value_16': '',
            'param_name_17': 'userid',  # 用户Id
            'param_value_17': usrid,
            'param_name_18': 'usertype',
            'param_value_18': 1,
            'param_name_19': 'constid',  # 机构号
            'param_value_19': 'M000004',
            'param_name_20': 'productid',  # 产品号
            'param_value_20': 'P000008',
            'param_name_21': 'role',
            'param_value_21': '',
            'param_name_22': 'username',  # 用户名称
            'param_value_22': u'客栈',
            'param_count': 23
        }

        m = session.post(url=api_url, headers=k_header, data=k_date)
        adpter = m.text
        print adpter

        # 调用API推送
        Pushk_data = {
            'action': 'EXCUTEAPI',
            'adpter': 'apiadpter',
            'format': 'xml',
            'method': shuju.Push_url,
            'ropurl': shuju.ropurl,
            'app_key': shuju.app_key,
            'app_secret': shuju.app_secret,
            'session': ke_keys,
            'param_name_0': 'userid',
            'param_value_0': usrid,
            'param_name_1': 'constid',
            'param_value_1': 'M000004',
            'param_name_2': 'companyname',  # 法人姓名
            'param_value_2': u'法人姓名',
            'param_name_3': 'registrationorga',  # 企业登记号
            'param_value_3': u'企业登记号',
            'param_name_4': 'businesslicense',  # 营业执照号
            'param_value_4': 2016098 + d,
            'param_name_5': 'certificatestartdate',
            'param_value_5': time,
            'param_name_6': 'certificateexpiredate',
            'param_value_6': time,
            'param_name_7': 'companytype',
            'param_value_7': 1,
            'param_name_8': 'registfinance',  # 注册基本
            'param_value_8': 12000000,
            'param_name_9': 'address',  # 企业地址
            'param_value_9': u'企业地址',
            'param_name_10': 'taxregcard',  # 税务登记号
            'param_value_10': taxregcard,
            'param_name_11': 'organcertificate',  # 机构号
            'param_value_11': 'M000004',
            'param_name_12': 'acuntopenlince',
            'param_value_12': 9,
            'param_name_13': 'corporatename',  # 企业名称
            'param_value_13': u'企业名称' + c,
            'param_name_14': 'certificatetype',
            'param_value_14': 1,
            'param_name_15': 'certificatenumber',  # 法人身份证号
            'param_value_15': 110228199007290021,
            'param_count': 16
        }
        Push_data_post = session.post(url=api_url, headers=k_header, data=Pushk_data)
        pust_test = Push_data_post.text
        print pust_test

        # 调用API授信
        Creditk_data = {
            'action': 'EXCUTEAPI',
            'adpter': 'apiadpter',
            'format': 'xml',
            'method': shuju.Credit_url,
            'ropurl': shuju.ropurl,
            'app_key': shuju.app_key,
            'app_secret': shuju.app_secret,
            'session': ke_keys,
            'param_name_0': 'userid',
            'param_value_0': usrid,
            'param_name_1': 'userorderid',
            'param_value_1': order_id,
            'param_name_2': 'amount',
            'param_value_2': 15500000,
            'param_name_3': 'productid',  # 产品ID
            'param_value_3': 'P000008',
            'param_name_4': 'rootinstcd',
            'param_value_4': 'M000004',
            'param_name_5': 'userrelateid',  # 关联ID
            'param_value_5': usrid,
            'param_name_6': 'reqesttime',  # 申请期限
            'param_value_6': 6,
            'param_name_7': 'orderplatformname',  # 申请单位名称
            'param_value_7': u'申请单位名称',
            'param_name_8': 'requestdate',  # 申请时间
            'param_value_8': time,
            'param_name_9': 'ratetemplrate',
            'param_value_9': 'RA201506231814031',
            'param_name_10': 'remark',  # 备注
            'param_value_10': u'备注',
            'param_name_11': 'jsondata',
            'param_value_11': jsondata,
            'param_name_12': 'urlkey',
            'param_value_12': '0eef33f2-6cc2-4a5f-9e23-512f9c348179',
            'param_name_13': 'creditype',
            'param_value_13': '',
            'param_count': 14,
        }
        Credit_post = session.post(url=api_url, headers=k_header, data=Creditk_data)
        Credit_test = Credit_post.text
        print Credit_test
        return order_id

    # 待协议上传
    def ke_Agr(self):
        shu = shuju()
        Agreement_keys = shu.sessionApi()
        Agreement_url = 'http://open.ruixuesoft.com:30002/Common/HttpAdpter.ashx'
        Agreement_header = {
            'Accept': 'text/plain, */*; q=0.01',
            'Accept-Encoding': 'gzip, deflate',
            'Accept-Language': 'zh-CN,zh;q=0.8',
            'Connection': 'keep-alive',
            'Content-Length': '712',
            'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
            'Host': 'open.ruixuesoft.com:30002',
            'Origin': 'http://open.ruixuesoft.com:30002',
            'RA-Sid': '4f353fa0-ccdc-11e6-82e6-e993dd9ab1c8',
            'RA-Ver': '6.1',
            'Referer': 'http://open.ruixuesoft.com:30002/ApiTool/index?sign=',
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_2) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/55.0.2883.95 Safari/537.36',
            'X-Requested-With': 'XMLHttpRequest'
        }
        Agreement_data = {
            'action': 'EXCUTEAPI',
            'adpter': 'apiadpter',
            'format': 'xml',
            'method': 'ruixue.wheatfield.order.service.agreementconfirm',
            'ropurl': shuju.ropurl,
            'app_key': shuju.app_key,
            'app_secret': shuju.app_secret,
            'session': Agreement_keys,
            'param_name_0': 'urlkeyd',
            'param_value_0': '',
            'param_name_1': 'userorderid',  # 订单ID
            'param_value_1': order_id,
            'param_name_2': 'rootinstcd',  # 机构号
            'param_value_2': 'M000004',
            'param_name_3': 'urlkeya',
            'param_value_3': '',
            'param_name_4': 'urlkeyb',
            'param_value_4': '',
            'param_name_5': 'urlkeyc',
            'param_value_5': '',
            'param_name_6': 'userid',  # 用户ID
            'param_value_6': usrid,
            'param_name_7': 'merchanturlkey',
            'param_value_7': '8b2ffb6c-d1df-48d3-8b24-e398e5da7984',
            'param_name_8': 'murlkeya',
            'param_value_8': 'f0a59bc1-3e1d-4ceb-af87-b9b464742e11',
            'param_name_9': 'userflag',  # 2为企业 1为个人
            'param_value_9': 2,
            'param_count': 10,
        }
        Agreement_post = self.session.post(url=Agreement_url, headers=Agreement_header, data=Agreement_data)
        print Agreement_post.text
        time.sleep(20)

        # 个人开户 授信 贷款

    def k_personal(self):
        per_data = datetime.datetime.now()
        shu = shuju()
        personal_keys = shu.sessionApi()
        personal_url = "http://open.ruixuesoft.com:30002/Common/HttpAdpter.ashx"
        personalk_header = {
            'Accept': 'text/plain, */*; q=0.01',
            'Accept-Encoding': 'gzip, deflate',
            'Accept-Language': 'zh-CN,zh;q=0.8',
            'Connection': 'keep-alive',
            'Content-Length': '1067',
            'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
            'Host': 'open.ruixuesoft.com:30002',
            'Origin': 'http://open.ruixuesoft.com:30002',
            'RA-Sid': '4f353fa0-ccdc-11e6-82e6-e993dd9ab1c8',
            'RA-Ver': '6.1',
            'Referer': 'http://open.ruixuesoft.com:30002/ApiTool/index?sign=',
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_2) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/55.0.2883.95 Safari/537.36',
            'X-Requested-With': 'XMLHttpRequest'
        }
        personalk_data = {
            'action': 'EXCUTEAPI',
            'adpter': 'apiadpter',
            'format': 'xml',
            'method': shuju.personal_method_url,
            'ropurl': shuju.ropurl,
            'app_key': shuju.app_key,
            'app_secret': shuju.app_secret,
            'session': personal_keys,
            'param_name_0': 'address',
            'param_value_0': '',
            'param_name_1': 'productid',  # 产品号
            'param_value_1': 'P000009',
            'param_name_2': 'persontype',
            'param_value_2': '',
            'param_name_3': 'personchnname',  # 中文名字
            'param_value_3': 2,
            'param_name_4': 'constid',  # 机构号
            'param_value_4': 'M000004',
            'param_name_5': 'remark',
            'param_value_5': '',
            'param_name_6': 'personsex',
            'param_value_6': '',
            'param_name_7': 'certificatetype',  # 证件类型  0 - 7
            'param_value_7': 0,
            'param_name_8': 'certificatenumber',  # 证件号
            'param_value_8': certificatenumber,
            'param_name_9': 'mobiletel',
            'param_value_9': '',
            'param_name_10': 'userid',  # 用户ID
            'param_value_10': guserid,
            'param_name_11': 'post',
            'param_value_11': '',
            'param_name_12': 'fixtel',
            'param_value_12': '',
            'param_name_13': 'referuserid',
            'param_value_13': '',
            'param_name_14': 'username',
            'param_value_14': '',
            'param_name_15': 'role',
            'param_value_15': '',
            'param_name_16': 'birthday',
            'param_value_16': '',
            'param_name_17': 'personengname',
            'param_value_17': '',
            'param_name_18': 'opertype',  # 操作类型
            'param_value_18': 1,
            'param_name_19': 'email',
            'param_value_19': '',
            'param_count': 20
        }
        personal_post = self.session.post(url=personal_url, headers=personalk_header, data=personalk_data)
        print personal_post.text

        kaihuk_data = {
            'action': 'EXCUTEAPI',
            'adpter': 'apiadpter',
            'format': 'xml',
            'method': shuju.personal_Push_url,
            'ropurl': shuju.ropurl,
            'app_key': shuju.app_key,
            'app_secret': shuju.app_secret,
            'session': personal_keys,
            'param_name_0': 'userid',  # 申请人ID
            'param_value_0': guserid,
            'param_name_1': 'certificatestartdate',  # 身份生效
            'param_value_1': '1990-01-03 10:01:01',
            'param_name_2': 'certificateexpiredate',  # 身份失效期
            'param_value_2': '2020-01-03 10:01:01',
            'param_name_3': 'mobilephone',  # 手机号
            'param_value_3': 18301080830,
            'param_name_4': 'constid',  # 机构号
            'param_value_4': 'M000004',
            'param_name_5': 'certificatenumber',  # 身份证号
            'param_value_5': certificatenumber,
            'param_name_6': 'username',  # 姓名
            'param_value_6': u'姓名',
            'param_name_7': 'occupation',  # 职业
            'param_value_7': u'程序员',
            'param_name_8': 'isauthor',  # 身份证验证结果
            'param_value_8': 1,
            'param_name_9': 'tcaccount',  # 银行卡
            'param_value_9': 6228480402564890018,
            'param_count': 10
        }
        kaihu_post = self.session.post(url=personal_url, headers=personalk_header, data=kaihuk_data)
        print kaihu_post.text

        daikuank_data = {
            'action': 'EXCUTEAPI',
            'adpter': 'apiadpter',
            'format': 'xml',
            'method': 'ruixue.wheatfield.order.service.newloanapply',
            'ropurl': shuju.ropurl,
            'app_key': shuju.app_key,
            'app_secret': shuju.app_secret,
            'session': personal_keys,
            'param_name_0': 'userid',  # 申请人ID
            'param_value_0': guserid,
            'param_name_1': 'userorderid',  # 交易流水
            'param_value_1': orderid,
            'param_name_2': 'amount',  # 申请金额
            'param_value_2': 1,
            'param_name_3': 'productid',  # 产品ID
            'param_value_3': productid,
            'param_name_4': 'rootinstcd',  # 机构号
            'param_value_4': 'M000004',
            'param_name_5': 'userrelateid',  # 申请人机构
            'param_value_5': usrid,
            'param_name_6': 'reqesttime',  # 申请期限
            'param_value_6': 4,
            'param_name_7': 'username',
            'param_value_7': u'学生',
            'param_name_8': 'requestdate',  # 申请时间
            'param_value_8': per_data,
            'param_name_9': 'ratetemplate',  # 费率模版
            'param_value_9': 'RA201607151100001',
            'param_name_10': 'remark',  # 备注
            'param_value_10': u'备注',
            'param_name_11': 'jsondata',
            'param_value_11': per_json,
            'param_name_12': 'urlkey',  # 费率模版
            'param_value_12': '7461673f-2b54-4c61-8b58-cc9e4053e8a4',
            'param_count': 13
        }
        daikuan_post = self.session.post(url=personal_url, headers=personalk_header, data=daikuank_data)
        print daikuan_post.text
        # 个人协议上传

    def ke_individual(self):
        shu = shuju()
        individual_keys = shu.sessionApi()
        individual_url = 'http://open.ruixuesoft.com:30002/Common/HttpAdpter.ashx'
        individualk_header = {
            'Accept': 'text/plain, */*; q=0.01',
            'Accept-Encoding': 'gzip, deflate',
            'Accept-Language': 'zh-CN,zh;q=0.8',
            'Connection': 'keep-alive',
            'Content-Length': '712',
            'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
            'Host': 'open.ruixuesoft.com:30002',
            'Origin': 'http://open.ruixuesoft.com:30002',
            'RA-Sid': '4f353fa0-ccdc-11e6-82e6-e993dd9ab1c8',
            'RA-Ver': '6.1',
            'Referer': 'http://open.ruixuesoft.com:30002/ApiTool/index?sign=',
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_2) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/55.0.2883.95 Safari/537.36',
            'X-Requested-With': 'XMLHttpRequest'
        }
        individualk_data = {
            'action': 'EXCUTEAPI',
            'adpter': 'apiadpter',
            'format': 'xml',
            'method': 'ruixue.wheatfield.order.service.agreementconfirm',
            'ropurl': shuju.ropurl,
            'app_key': shuju.app_key,
            'app_secret': shuju.app_secret,
            'session': individual_keys,
            'param_name_0': 'urlkeyd',
            'param_value_0': 'c628a2b4-4416-4fb0-adef-ad3fa895cfd5',
            'param_name_1': 'userorderid',  # 订单ID
            'param_value_1': orderid,
            'param_name_2': 'rootinstcd',  # 机构号
            'param_value_2': 'M000004',
            'param_name_3': 'urlkeya',
            'param_value_3': '47238c84-01e2-4ef7-b16e-aab12aec698e',
            'param_name_4': 'urlkeyb',
            'param_value_4': '33ccffd6-4697-40f6-ae49-dc8c57149cad',
            'param_name_5': 'urlkeyc',
            'param_value_5': 'aff0d815-deda-4d1f-8259-bdeb6264a877',
            'param_name_6': 'userid',  # 用户ID
            'param_value_6': guserid,
            'param_name_7': 'merchanturlkey',
            'param_value_7': '',
            'param_name_8': 'murlkeya',
            'param_value_8': '',
            'param_name_9': 'userflag',  # 2为企业 1为个人
            'param_value_9': 1,
            'param_count': 10,
        }
        individual_post = self.session.post(url=individual_url, headers=individualk_header, data=individualk_data)
        print individual_post.text
        time.sleep(20)