# -*- coding:utf-8 -*-
from selenium import webdriver
import time
import urllib2
#此方法为自动化封装方法
OVER_TIME = 5
BASE_URL = "http://123.56.79.58:8121/#/login"


class Driver(object):

    def __new__(cls, *args, **kw):
        """
        使用单例模式将类设置为运行时只有一个实例，在其他Python类中使用基类时，
        可以创建多个对象，保证所有的对象都是基于一个浏览器
        """
        if not hasattr(cls, '_instance'):
            orig = super(Driver, cls)
            cls._instance = orig.__new__(cls, *args, **kw)
        return cls._instance

    def start(self, url=BASE_URL, driver_name="Chrome"):
        """
        启动浏览器
        :param url: 测试地址
        :param driver_name: 在启动时设置浏览器的类型
        :return:
        """
        if driver_name == "Firefox":
            self.driver = webdriver.Firefox()
        elif driver_name == "Ie":
            self.driver = webdriver.Ie()
        else:
            self.driver = webdriver.Chrome("/Users/qinying/Downloads/chromedriver")
            # driver = webdriver.PhantomJS(executable_path="/Users/qinying/.pyenv/versions/2.7.13/lib/python2.7/site-packages/phantomjs")  # 实体化浏览器
        self.driver.implicitly_wait(OVER_TIME)
        self.driver.get(url)
        self.driver.maximize_window()

    def get_url(self):
        """返回浏览器的地址"""
        return BASE_URL

    def find_element(self, by, value):
        """
        这里添加了一个OVER_TIME作为查找元素的超时次数，根据系统的实际情况设置OVER_TIME的大小
        """
        for i in range(OVER_TIME):
            try:
                return self.driver.find_element(by=by, value=value)
            except Exception, e:
                print e

    def find_elements(self, by, value):
        """与find_element一致"""
        for i in range(OVER_TIME):
            try:
                return self.driver.find_elements(by=by, value=value)
            except Exception, e:
                print e

    def find_display_elements(self, by, value):
        """
        查找状态为displayed的元素集合，当查找一类元素时，
        经常出现有些元素是不可见的情况，此函数屏蔽那些不可见的元素
        """
        for i in range(OVER_TIME):
            try:
                elements = self.driver.find_elements(by=by, value=value)
                num = elements.__len__()
            except Exception, e:
                print e
                time.sleep(1)
            if num >= 1:
                break
        display_element = []
        # 将可见的元素放到列表中， 并返回
        for j in range(num):
            element = elements.__getitem__(j)
            if element.is_displayed():
                display_element.append(element)
        return display_element

    def is_element_present(self, By, Value):
        """判断元素是否存在"""
        try:
            self.driver.find_element(by=By, value=Value)
            return True
        except Exception, e:
            print e
            return False

    def close(self):
        self.driver.close()

    def quit(self):
        u"""退出浏览器"""
        self.driver.quit()

if __name__ == "__main__":
    page = Driver()
    page.start()