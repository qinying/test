#-*- coding: UTF-8 -*-
from selenium.webdriver.support.select import Select
import time
import traceback
import paramiko
import MySQLdb
import HTMLTestRunner
import unittest
from login import Login
from help_students import shuju, orderid

import sys
reload(sys)
sys.setdefaultencoding('utf8')

#窗口最大化
word = shuju()
word.open_kezhan()
dri = Login()
driver = dri.admin()

#登陆
class test_index(unittest.TestCase):

    #贷款管理
    def credit_Shenpin(self):
        driver.find_element_by_xpath('//*[@id="body"]/div/div[2]/div/div/div/div/div/div[1]/div[2]/div[3]/div/div').click()
        time.sleep(2)
        driver.find_element_by_xpath('//*[@id="body"]/div/div[2]/div/div/div/div/div/div[2]/button').click()
        time.sleep(2)
        Select(driver.find_element_by_xpath('//*[@id="body"]/div/div[1]/header/div/div[1]/div[2]/select')).select_by_value('number:1')
        time.sleep(2)
        driver.find_element_by_link_text('贷款管理').click()
        time.sleep(1)
        driver.find_element_by_link_text('企业授信审批').click()
        time.sleep(1)
        driver.get_screenshot_as_file('/Users/qinying/PycharmProjects/rongcapital/test/img/Error.png')
    # #待补充信息审核
    def supplementary_Information(self):
        driver.find_element_by_xpath('//*[@id="body"]/div/div[2]/div/div[1]/div/div/div[2]/div[3]/div/div/div/div/div[1]/table/tbody/tr/td[9]/a/i').click()
        time.sleep(1)
        #课程名称
        driver.find_element_by_xpath('//*[@id="body"]/div/div[2]/div/div[1]/div/div/div[2]/div/div[2]/div[9]/div/div/form/div[1]/div/input').send_keys(u'课程名称')
        time.sleep(1)
        #课程类型
        Select(driver.find_element_by_xpath('//*[@id="body"]/div/div[2]/div/div[1]/div/div/div[2]/div/div[2]/div[9]/div/div/form/div[2]/div/select')).select_by_value('string:3')
        time.sleep(1)
        #课程单价
        driver.find_element_by_xpath('//*[@id="body"]/div/div[2]/div/div[1]/div/div/div[2]/div/div[2]/div[9]/div/div/form/div[3]/div/input').send_keys('2500')
        time.sleep(1)
        driver.find_element_by_xpath('//*[@id="body"]/div/div[2]/div/div[1]/div/div/div[2]/div/div[2]/div[10]/button').click()
        time.sleep(15)
        driver.get_screenshot_as_file('/Users/qinying/PycharmProjects/rongcapital/test/img/Error.png')

    def ischushen(self):
        driver.refresh()
        #待初审列表
        driver.find_element_by_xpath('//*[@id="body"]/div/div[2]/div/div[1]/div/div/div[2]/div[3]/div/ul/li[2]/a').click()
        time.sleep(2)
        #领取
        driver.find_element_by_xpath('//*[@id="body"]/div/div[2]/div/div[1]/div/div/div[2]/div[3]/div/div/div/div/div[1]/table/tbody/tr[1]/td[9]/a[2]/i').click()
        time.sleep(1)
        #审批金额(元)
        driver.find_element_by_xpath('//*[@id="body"]/div/div[2]/div/div[1]/div/div[2]/div[3]/div/div/div[2]/div[1]/div/form/div[1]/div[2]/input').send_keys('1000')
        time.sleep(1)
        #审批期限
        driver.find_element_by_xpath('//*[@id="body"]/div/div[2]/div/div[1]/div/div[2]/div[3]/div/div/div[2]/div[1]/div/form/div[2]/div[2]/input').send_keys('12')
        time.sleep(1)
        # 补充意见
        driver.find_element_by_xpath('//*[@id="body"]/div/div[2]/div/div[1]/div/div[2]/div[3]/div/div/div[2]/div[1]/div/div/div[2]/button').click()
        time.sleep(1)
        #产品类型
        driver.find_element_by_xpath('//*[@id="body"]/div/div[2]/div/div[1]/div/div[2]/div[3]/div/div/div[2]/div[2]/div/div/div/div/div/div/div/div/div[1]/div[1]/div/label/i').click()
        time.sleep(1)
        #年龄限制
        driver.find_element_by_xpath('//*[@id="body"]/div/div[2]/div/div[1]/div/div[2]/div[3]/div/div/div[2]/div[2]/div/div/div/form/div[1]/div[1]/div[2]/div/input[1]').send_keys('18')
        time.sleep(1)
        driver.find_element_by_xpath('//*[@id="body"]/div/div[2]/div/div[1]/div/div[2]/div[3]/div/div/div[2]/div[2]/div/div/div/form/div[1]/div[1]/div[2]/div/input[2]').send_keys('30')
        time.sleep(1)
        #合同类型
        Select(driver.find_element_by_xpath('//*[@id="body"]/div/div[2]/div/div[1]/div/div[2]/div[3]/div/div/div[2]/div[2]/div/div/div/form/div[2]/div[1]/div[2]/select')).select_by_value('number:1')
        time.sleep(1)
        #有无首付
        Select(driver.find_element_by_xpath('//*[@id="body"]/div/div[2]/div/div[1]/div/div[2]/div[3]/div/div/div[2]/div[2]/div/div/div/form/div[1]/div[2]/div[2]/select')).select_by_value('number:0')
        time.sleep(1)
        #是否缴纳保证金
        Select(driver.find_element_by_xpath('//*[@id="body"]/div/div[2]/div/div[1]/div/div[2]/div[3]/div/div/div[2]/div[2]/div/div/div/form/div[2]/div[2]/div[2]/select')).select_by_value('number:2')
        time.sleep(1)
        #利率类型
        Select(driver.find_element_by_xpath('//*[@id="body"]/div/div[2]/div/div[1]/div/div[2]/div[3]/div/div/div[2]/div[2]/div/div/div/form/div[1]/div[4]/div[2]/select')).select_by_value('number:1')
        time.sleep(1)
        #其他风险缓释
        driver.find_element_by_xpath('//*[@id="body"]/div/div[2]/div/div[1]/div/div[2]/div[3]/div/div/div[2]/div[2]/div/div/div/form/div[2]/div[4]/div[2]/input').send_keys(u'其他风险缓释')
        time.sleep(1)
        #是否分批放款
        Select(driver.find_element_by_xpath('//*[@id="body"]/div/div[2]/div/div[1]/div/div[2]/div[3]/div/div/div[2]/div[2]/div/div/div/form/div[1]/div[5]/div[2]/select')).select_by_value('number:1')
        time.sleep(1)

        #审批结果
        Select(driver.find_element_by_xpath('//*[@id="body"]/div/div[2]/div/div[1]/div/div[2]/div[3]/div/div/div[2]/div[2]/div/div/div/form/div[3]/div[2]/div[2]/div/div/select')).select_by_value('number:1')
        time.sleep(1)

        #确认
        driver.find_element_by_xpath('//*[@id="body"]/div/div[2]/div/div[1]/div/div[2]/div[3]/div/div/div[3]/div/div/div[2]/button[1]').click()
        time.sleep(20)

        driver.get_screenshot_as_file('/Users/qinying/PycharmProjects/rongcapital/test/img/Error.png')
    #待终审
    def final_Judgment(self):
        driver.refresh()
        #待终审列表
        driver.find_element_by_xpath('//*[@id="body"]/div/div[2]/div/div[1]/div/div/div[2]/div[3]/div/ul/li[6]/a').click()
        time.sleep(1)

        #领取
        driver.find_element_by_xpath('//*[@id="body"]/div/div[2]/div/div[1]/div/div/div[2]/div[3]/div/div/div/div/div[1]/table/tbody/tr[1]/td[9]/a[2]/i').click()
        time.sleep(1)
        #审批金额
        driver.find_element_by_xpath('//*[@id="body"]/div/div[2]/div/div[1]/div/div[2]/div[3]/div/div/div[2]/div[1]/div/form/div[1]/div[2]/input').send_keys('2000')
        time.sleep(1)

        #审批期限
        driver.find_element_by_xpath('//*[@id="body"]/div/div[2]/div/div[1]/div/div[2]/div[3]/div/div/div[2]/div[1]/div/form/div[2]/div[2]/input').send_keys('10')
        time.sleep(1)
        driver.find_element_by_xpath('//*[@id="body"]/div/div[2]/div/div[1]/div/div[2]/div[3]/div/div/div[3]/div/div/div[1]/textarea').send_keys(u'备注终审')
        time.sleep(1)
        driver.find_element_by_xpath('//*[@id="body"]/div/div[2]/div/div[1]/div/div[2]/div[3]/div/div/div[3]/div/div/div[2]/button[1]').click()
        time.sleep(20)

        driver.get_screenshot_as_file('/Users/qinying/PycharmProjects/rongcapital/test/img/Error.png')
    #待合同确认
    def contract(self):
        driver.refresh()
        #合同领取
        driver.find_element_by_xpath('//*[@id="body"]/div/div[2]/div/div[1]/div/div/div[2]/div[3]/div/ul/li[4]/a').click()
        driver.find_element_by_xpath('//*[@id="body"]/div/div[2]/div/div[1]/div/div/div[2]/div[3]/div/div/div/div/div[1]/table/tbody/tr/td[9]/a[2]/i').click()
        time.sleep(2)

        #合同类型（有无保证金）
        Select(driver.find_element_by_xpath('//*[@id="body"]/div/div[2]/div/div[1]/div/div[2]/div[2]/div[3]/div/div[3]/div[1]/div/select')).select_by_value('string:2')
        time.sleep(2)

        #利率类型
        Select(driver.find_element_by_xpath('//*[@id="body"]/div/div[2]/div/div[1]/div/div[2]/div[2]/div[3]/div/div[3]/div[2]/div/select')).select_by_value('string:1')
        time.sleep(2)

        #产品类型
        Select(driver.find_element_by_xpath('//*[@id="body"]/div/div[2]/div/div[1]/div/div[2]/div[2]/div[3]/div/div[3]/div[3]/div/select')).select_by_value('string:RA201604120000003')
        time.sleep(1)

        #合同类型
        Select(driver.find_element_by_xpath('//*[@id="body"]/div/div[2]/div/div[1]/div/div[2]/div[2]/div[3]/div/div[3]/div[4]/div/select')).select_by_value('string:1')
        driver.find_element_by_xpath('//*[@id="body"]/div/div[2]/div/div[1]/div/div[2]/div[2]/div[3]/div/div[2]/span').click()
        time.sleep(20)
        driver.find_element_by_xpath('//*[@id="body"]/div/div[2]/div/div[1]/div/div[2]/div[3]/div/div/div/div/div/div[2]/button[1]').click()
        time.sleep(20)

        driver.get_screenshot_as_file('/Users/qinying/PycharmProjects/rongcapital/test/img/Error.png')
        #协议上传
        shu = shuju()
        shu.ke_Agr()
    #待签约
    def pending_Contract(self):
        driver.refresh()
        driver.find_element_by_xpath('//*[@id="body"]/div/div[2]/div/div[1]/div/div/div[2]/div[3]/div/ul/li[5]/a').click()
        time.sleep(1)
        driver.find_element_by_xpath('//*[@id="body"]/div/div[2]/div/div[1]/div/div/div[2]/div[3]/div/div/div/div/div[1]/table/tbody/tr[1]/td[9]/a[2]/i').click()
        driver.find_element_by_xpath('//*[@id="body"]/div/div[2]/div/div[1]/div/div[2]/div[3]/div/div/div[2]/div/div/div[2]/button[1]').click()
        time.sleep(20)

        driver.get_screenshot_as_file('/Users/qinying/PycharmProjects/rongcapital/test/img/Error.png')


    #个人授信数据
    def gerne_shuju(self):
        shu = shuju()
        shu.personal()
        conn = MySQLdb.connect(
            host='121.40.237.1',
            port=3317,
            user='order',
            passwd='Order!1',
            db='order',
            charset="utf8",
        )
        cursor = conn.cursor()
        t = str(orderid)
        cursor.execute("SELECT * FROM ORDER_INFO WHERE USER_ORDER_ID = '%s'" % t)
        cursor.fetchone()
        a = cursor._rows
        o = a[0]
        orderid_id = o[0]
        print orderid_id
        d = MySQLdb.connect(
            host='121.40.237.1',
            port=3317,
            user='new_operate',
            passwd='New_operate_test!1',
            db='new_operate',
            charset="utf8",
        )
        mysql = d.cursor()
        mysql.execute("SELECT * FROM WORKFLOW_CHECK_ORDER ")
        mysql.execute("UPDATE WORKFLOW_CHECK_ORDER t SET t.STATUS_ID=1 WHERE t.CUSTOMERINFO_ID='%s'" % orderid_id)
        mysql.execute("COMMIT;")

    #个人初审
    def individual_Trial(self):
        driver.refresh()
        #个人初审
        driver.find_element_by_xpath('//*[@id="body"]/div/head-temp/div[1]/div[2]/div[1]/ul/li[1]/ul/li[1]/a').click()
        time.sleep(40)
        driver.find_element_by_xpath('//*[@id="body"]/div/div[2]/div/div[1]/div/div/div[2]/div[3]/div/ul/li[2]/a').click()
        time.sleep(30)
        driver.refresh()
        driver.find_element_by_xpath('//*[@id="w_first"]/div/table/tbody/tr/td[13]/a[2]/i').click()
        time.sleep(2)
        driver.find_element_by_xpath('//*[@id="body"]/div/div[2]/div/div/div[1]/div/div[2]/div[6]/div/div/div[2]/div[2]/div/div[2]/button[1]').click()
        time.sleep(20)

        driver.get_screenshot_as_file('/Users/qinying/PycharmProjects/rongcapital/test/img/Error.png')

        #待终审
        driver.refresh()
        time.sleep(10)
        driver.find_element_by_xpath('//*[@id="body"]/div/div[2]/div/div[1]/div/div/div[2]/div[3]/div/ul/li[3]/a').click()
        time.sleep(2)
        driver.find_element_by_xpath('//*[@id="w_first"]/div/table/tbody/tr[1]/td[13]/a[2]/i').click()
        time.sleep(2)
        driver.find_element_by_xpath('//*[@id="body"]/div/div[2]/div/div/div[1]/div/div[2]/div[6]/div/div/div[2]/div[2]/div/div[2]/button[1]').click()
        time.sleep(20)

        driver.get_screenshot_as_file('/Users/qinying/PycharmProjects/rongcapital/test/img/Error.png')

    #个人协议
    def xieyi(self):
        shu = shuju()
        shu.ke_individual()

    #待签约
    def individual_Contract(self):
        driver.refresh()
        driver.find_element_by_xpath('//*[@id="body"]/div/div[2]/div/div[1]/div/div/div[2]/div[3]/div/ul/li[4]/a').click()
        driver.find_element_by_xpath('//*[@id="w_first"]/div/table/tbody/tr[1]/td[13]/a[2]/i').click()
        time.sleep(2)
        driver.find_element_by_xpath('//*[@id="body"]/div/div[2]/div/div/div[1]/div/div/div[2]/div[6]/div/div/div[2]/div/div/div[2]/button[1]').click()
        time.sleep(20)

        driver.get_screenshot_as_file('/Users/qinying/PycharmProjects/rongcapital/test/img/Error.png')


if __name__ == '__main__':

    testsuite=unittest.TestSuite()
    testsuite.addTest(test_index("credit_Shenpin"))
    testsuite.addTest(test_index("supplementary_Information"))
    testsuite.addTest(test_index("ischushen"))
    testsuite.addTest(test_index("final_Judgment"))
    testsuite.addTest(test_index("contract"))
    testsuite.addTest(test_index("pending_Contract"))
    testsuite.addTest(test_index("gerne_shuju"))
    testsuite.addTest(test_index("individual_Trial"))
    testsuite.addTest(test_index("xieyi"))
    testsuite.addTest(test_index("individual_Contract"))
    filePath = "///Users/qinying/PycharmProjects/rongcapital/test/pyResult.html"
    fp = file(filePath, 'wb')
    runner = HTMLTestRunner.HTMLTestRunner(stream=fp, title='Result', description='Test_Report')
    runner.run(testsuite)