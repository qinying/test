# -*- coding: utf-8 -*
import sys
import time
import unittest

import HTMLTestRunner
from login import Login
from selenium.webdriver.support.select import Select

from test.testcase.help_students import shuju

reload(sys)
sys.setdefaultencoding('utf8')

shu = shuju()
shu.yueshiyue()
dri = Login()
driver = dri.admin()
class yueshiyue(unittest.TestCase):
    #待初审领取审批
    def yue_Credit(self):
        driver.find_element_by_xpath('//*[@id="body"]/div/div[2]/div/div/div/div/div/div[1]/div[2]/div[3]/div/div').click()
        time.sleep(2)
        driver.find_element_by_xpath('//*[@id="body"]/div/div[2]/div/div/div/div/div/div[2]/button').click()
        time.sleep(2)
        Select(driver.find_element_by_xpath('//*[@id="body"]/div/div[1]/header/div/div[1]/div[2]/select')).select_by_value('number:3')
        time.sleep(2)
        driver.find_element_by_link_text('贷款管理').click()
        time.sleep(1)
        driver.find_element_by_link_text('个人贷款审批').click()
        time.sleep(2)
        driver.find_element_by_xpath('//*[@id="body"]/div/div[2]/div/div[1]/div/div/div[2]/div[3]/div/ul/li[2]/a').click()
        time.sleep(2)
        driver.find_element_by_xpath('//*[@id="w_first"]/div/table/tbody/tr[1]/td[13]/a[2]/i').click()
        time.sleep(2)
        driver.find_element_by_xpath('//*[@id="body"]/div/div[2]/div/div/div[1]/div/div[2]/div[5]/div/div/div[2]/div[2]/div/div[2]/button[1]').click()
        time.sleep(15)
        driver.get_screenshot_as_file('/Users/qinying/PycharmProjects/rongcapital/test/img/Error.png')
    #待终审
    def zhongshen(self):
        driver.refresh()
        driver.find_element_by_xpath('//*[@id="body"]/div/div[2]/div/div[1]/div/div/div[2]/div[3]/div/ul/li[3]/a').click()
        time.sleep(2)
        driver.find_element_by_xpath('//*[@id="w_first"]/div/table/tbody/tr[1]/td[13]/a[2]/i').click()
        time.sleep(2)
        driver.find_element_by_xpath('//*[@id="body"]/div/div[2]/div/div/div[1]/div/div[2]/div[5]/div/div/div[2]/div[2]/div/div[2]/button[1]').click()
        time.sleep(15)
        driver.get_screenshot_as_file('/Users/qinying/PycharmProjects/rongcapital/test/img/Error.png')

    #协议上传
    def xieyi(self):
        shu = shuju()
        shu.xieyi()

    #待签约
    def yue_Sign(self):
        driver.refresh()
        driver.find_element_by_link_text('全部').click()
        time.sleep(3)
        driver.find_element_by_xpath('//*[@id="w_first"]/div/table/tbody/tr[1]/td[13]/a[2]/i').click()
        time.sleep(6)
        driver.find_element_by_xpath('//*[@id="body"]/div/div[2]/div/div/div[1]/div/div/div[2]/div[5]/div/div/div[2]/div/div/div[2]/button[1]').click()
        time.sleep(2)
        driver.get_screenshot_as_file('/Users/qinying/PycharmProjects/rongcapital/test/img/Error.png')

if __name__ == '__main__':
    testsuite = unittest.TestSuite()
    testsuite.addTest(yueshiyue("yue_Credit"))
    testsuite.addTest(yueshiyue("zhongshen"))
    testsuite.addTest(yueshiyue("xieyi"))
    testsuite.addTest(yueshiyue("yue_Sign"))
    filePath = "///Users/qinying/PycharmProjects/rongcapital/test/pyResult.html"
    fp = file(filePath, 'wb')
    runner = HTMLTestRunner.HTMLTestRunner(stream=fp, title='Result', description='Test_Report')
    runner.run(testsuite)