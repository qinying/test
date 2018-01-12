#coding=utf-8
'''

    启动文件，
    主要python + selenium + unittest + HTMLTestRunner 框架
    验证码采用第三方接口 超级鹰

'''
import unittest
import HTMLTestRunner
import datetime
from test.testcase.index import test_index
# import cgi
#
# form = cgi.FieldStorage()
# site_name = form.getvalue('name')
# site_url  = form.getvalue('url')

if __name__=='__main__':
    suite = unittest.TestSuite()
    suite.addTest(test_index("credit_Shenpin"))
    suite.addTest(test_index("supplementary_Information"))
    suite.addTest(test_index("ischushen"))
    suite.addTest(test_index("final_Judgment"))
    suite.addTest(test_index("contract"))
    suite.addTest(test_index("pending_Contract"))
    suite.addTest(test_index("gerne_shuju"))
    suite.addTest(test_index("individual_Trial"))
    suite.addTest(test_index("xieyi"))
    suite.addTest(test_index("individual_Contract"))
    now = datetime.datetime.now()
    filePath = "///Users/qinying/PycharmProjects/rongcapital/test/img/"+now+"pyResult.html"
    fp = file(filePath, 'wb')
    runner = HTMLTestRunner.HTMLTestRunner(stream=fp, title='Result', description='Test_Report')
    runner.run(suite)