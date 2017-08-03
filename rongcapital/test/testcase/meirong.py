# -*- coding: utf-8 -*
from help_students import shuju
from selenium.webdriver.support.select import Select
import unittest
import HTMLTestRunner
import time
from login import Login
import sys
reload(sys)
sys.setdefaultencoding('utf8')

shu = shuju()
shu.meirong()
dri = Login()
driver = dri.admin()
class meirong(unittest.TestCase):
    #待初审领取审批
    def mei_Credit(self):
        driver.find_element_by_xpath('//*[@id="body"]/div/div[2]/div/div/div/div/div/div[1]/div[2]/div[3]/div/div').click()
        time.sleep(2)
        driver.find_element_by_xpath('//*[@id="body"]/div/div[2]/div/div/div/div/div/div[2]/button').click()
        time.sleep(2)
        Select(driver.find_element_by_xpath('//*[@id="body"]/div/div[1]/header/div/div[1]/div[2]/select')).select_by_value('number:4')
        time.sleep(2)
        driver.find_element_by_link_text('贷款管理').click()
        time.sleep(1)
        driver.find_element_by_xpath('//*[@id="body"]/div/head-temp/div[1]/div[2]/div[1]/ul/li[1]/ul/li/a').click()
        time.sleep(2)
        driver.find_element_by_xpath('//*[@id="body"]/div/div[2]/div/div[1]/div/div/div[2]/div[3]/div/ul/li[2]/a').click()
        time.sleep(2)
        driver.find_element_by_xpath('//*[@id="w_first"]/div/table/tbody/tr[1]/td[13]/a[2]/i').click()
        time.sleep(2)
        driver.find_element_by_xpath('//*[@id="body"]/div/div[2]/div/div/div[1]/div/div[2]/div[6]/div/div/div[2]/div[2]/div/div[2]/button[1]').click()
        time.sleep(15)
        driver.get_screenshot_as_file('/Users/qinying/PycharmProjects/rongcapital/test/img/mei_Credit.png')
    #待终审
    def zhongshen(self):
        driver.refresh()
        driver.find_element_by_xpath('//*[@id="body"]/div/div[2]/div/div[1]/div/div/div[2]/div[3]/div/ul/li[3]/a').click()
        time.sleep(2)
        driver.find_element_by_xpath('//*[@id="w_first"]/div/table/tbody/tr[1]/td[13]/a[2]/i').click()
        time.sleep(2)
        driver.find_element_by_xpath('//*[@id="body"]/div/div[2]/div/div/div[1]/div/div[2]/div[6]/div/div/div[2]/div[2]/div/div[2]/button[1]').click()
        time.sleep(15)
        driver.get_screenshot_as_file('/Users/qinying/PycharmProjects/rongcapital/test/img/zhongshen.png')

    #协议上传
    def xieyi(self):
        shu = shuju()
        shu.mrxieyi()

    #待签约
    def mei_Sign(self):
        driver.refresh()
        driver.find_element_by_xpath('//*[@id="body"]/div/div[2]/div/div[1]/div/div/div[2]/div[3]/div/ul/li[6]/a').click()
        time.sleep(2)
        driver.find_element_by_xpath('//*[@id="w_first"]/div/table/tbody/tr[1]/td[13]/a[2]/i').click()
        time.sleep(2)
        driver.find_element_by_xpath('//*[@id="body"]/div/div[2]/div/div/div[1]/div/div/div[2]/div[7]/div/div/div[2]/div/div/div[2]/button[1]').click()
        time.sleep(2)
        driver.get_screenshot_as_file('/Users/qinying/PycharmProjects/rongcapital/test/img/mei_Sign.png')

if __name__ == '__main__':
    testsuite = unittest.TestSuite()
    testsuite.addTest(meirong("mei_Credit"))
    testsuite.addTest(meirong("zhongshen"))
    testsuite.addTest(meirong("xieyi"))
    testsuite.addTest(meirong("mei_Sign"))
    filePath = "///Users/qinying/PycharmProjects/rongcapital/test/pyResult.html"
    fp = file(filePath, 'wb')
    runner = HTMLTestRunner.HTMLTestRunner(stream=fp, title='Result', description='Test_Report')
    runner.run(testsuite)