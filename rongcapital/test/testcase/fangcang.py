#-*- coding: UTF-8 -*-
from selenium.webdriver.support.select import Select
from login import Login
import time
import HTMLTestRunner
import unittest
from help_students import shuju

import sys
reload(sys)
sys.setdefaultencoding('utf8')

shu = shuju()
shu.fang_Cart()
index = Login()
driver = index.admin()
class fang(unittest.TestCase):

    def Credit(self):
        driver.find_element_by_xpath('//*[@id="body"]/div/div[2]/div/div/div/div/div/div[1]/div[2]/div[3]/div/div').click()
        time.sleep(2)
        driver.find_element_by_xpath('//*[@id="body"]/div/div[2]/div/div/div/div/div/div[2]/button').click()
        time.sleep(2)
        Select(driver.find_element_by_xpath('//*[@id="body"]/div/div[1]/header/div/div[1]/div[2]/select')).select_by_value('number:7')
        time.sleep(2)
        driver.find_element_by_link_text('贷款管理').click()
        time.sleep(1)
        driver.find_element_by_link_text('企业授信审批').click()
        time.sleep(1)
        #初审领取提交
        driver.find_element_by_xpath('//*[@id="body"]/div/div[2]/div/div[1]/div/div/div[2]/div[3]/div/div/div/div/div[1]/table/tbody/tr[1]/td[9]/a[2]/i').click()
        time.sleep(2)
        driver.find_element_by_xpath('//*[@id="body"]/div/div[2]/div/div[1]/div/div[2]/div[3]/div/div/div[2]/div[1]/div/form/div[1]/div[2]/input').send_keys('2000')
        driver.find_element_by_xpath('//*[@id="body"]/div/div[2]/div/div[1]/div/div[2]/div[3]/div/div/div[2]/div[1]/div/form/div[2]/div[2]/input').send_keys('10')
        driver.find_element_by_xpath('//*[@id="body"]/div/div[2]/div/div[1]/div/div[2]/div[3]/div/div/div[3]/div/div/div[2]/button[1]').click()
        time.sleep(15)
        #终审领取提交
        driver.refresh()
        driver.find_element_by_link_text('待终审').click()
        time.sleep(2)
        driver.find_element_by_xpath('//*[@id="body"]/div/div[2]/div/div[1]/div/div/div[2]/div[3]/div/div/div/div/div[1]/table/tbody/tr[1]/td[9]/a[2]/i').click()
        time.sleep(2)
        driver.find_element_by_xpath('//*[@id="body"]/div/div[2]/div/div[1]/div/div[2]/div[3]/div/div/div[2]/div[1]/div/form/div[1]/div[2]/input').send_keys('2000')
        driver.find_element_by_xpath('//*[@id="body"]/div/div[2]/div/div[1]/div/div[2]/div[3]/div/div/div[2]/div[1]/div/form/div[2]/div[2]/input').send_keys('12')
        driver.find_element_by_xpath('//*[@id="body"]/div/div[2]/div/div[1]/div/div[2]/div[3]/div/div/div[3]/div/div/div[2]/button[1]').click()
        time.sleep(15)
        #签约领取
        driver.refresh()
        driver.find_element_by_xpath('//*[@id="body"]/div/div[2]/div/div[1]/div/div/div[2]/div[3]/div/ul/li[3]/a').click()
        time.sleep(2)
        driver.find_element_by_xpath('//*[@id="body"]/div/div[2]/div/div[1]/div/div/div[2]/div[3]/div/div/div/div/div[1]/table/tbody/tr[1]/td[9]/a[2]/i').click()
        time.sleep(3)
        driver.find_element_by_xpath('//*[@id="body"]/div/div[2]/div/div[1]/div/div[2]/div[4]/div/div/div[2]/div/div/div[2]/button[1]').click()
        time.sleep(3)
        driver.get_screenshot_as_file('/Users/qinying/PycharmProjects/rongcapital/test/img/Error.png')

if __name__ == '__main__':

    testsuite = unittest.TestSuite()
    testsuite.addTest(fang("Credit"))
    filePath = "///Users/qinying/PycharmProjects/rongcapital/test/pyResult.html"
    fp = file(filePath, 'wb')
    runner = HTMLTestRunner.HTMLTestRunner(stream=fp, title='Result', description='Test_Report')
    runner.run(testsuite)