#-*- coding: UTF-8 -*-
import time
from selenium import webdriver
from test.public.chaojiying import Chaojiying_Client
from test.public.linux import codeMain
import paramiko
from urllib import urlretrieve
import urllib
import sys
reload(sys)
sys.setdefaultencoding('utf8')




class Login():

    def admin(self):

        driver = webdriver.Chrome("/Users/qinying/Downloads/chromedriver")
        time.sleep(4)
        # driver = webdriver.PhantomJS(executable_path="/Users/qinying/.pyenv/versions/2.7.13/lib/python2.7/site-packages/phantomjs")  # 实体化浏览器
        driver.get('http://211.159.180.106:7070/dsj-agent-back')  # 打开个地址
        driver.maximize_window()  # 设置浏览器窗口最大化
        driver.implicitly_wait(30)
        codeMain()
        # chaojiying = Chaojiying_Client('18301080830 ', 'qy159108', '96001')
        # # im = open('/Users/qinying/PycharmProjects/rongcapital/test/public/a.jpg', 'rb').read()
        # im = open('/Users/qinying/PycharmProjects/rongcapital/test/public/a.jpg', 'rb').read()
        # p = chaojiying.PostPic(im, 1902)
        # o = p['pic_str']

        driver.find_element_by_name("username").send_keys("agent")
        time.sleep(1)
        driver.find_element_by_name("password").send_keys("123456")
        time.sleep(1)
        driver.get_screenshot_as_file('/Users/qinying/PycharmProjects/rongcapital/test/img/code.png')
        driver.find_element_by_name("verifyCode").send_keys(raw_input("请输入验证码： "))
        #driver.find_element_by_name("imgcode").send_keys(o)
        time.sleep(1)
        driver.find_element_by_xpath('//*[@id="loginForm"]/div[4]/div/button').click()
        time.sleep(1)
        driver.get_screenshot_as_file('/Users/qinying/PycharmProjects/rongcapital/test/img/login.png')
        return driver