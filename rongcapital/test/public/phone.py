# -*- coding: utf-8 -*
__author__ = 'qinying'
import re
#判断手机号码是否符合规范
def phonecheck(s):
        #号码前缀，如果运营商启用新的号段，只需要在此列表将新的号段加上即可。
        phoneprefix=['130','131','132','133','134','135','136','137','138','139','150','151','152','153','156','158','159','170','183','182','185','186','188','189']
        #检测号码是否长度是否合法。
        if len(s)<>11:
            print "The length of phonenum is 11."
        else:
            #检测输入的号码是否全部是数字。
            if  s.isdigit():
            #检测前缀是否是正确。
                if s[:3] in phoneprefix:
                    print "The phone num is valid."
                else:
                    print "The phone num is invalid."
            else:
                print "The phone num is made up of digits."


#判断邮箱格式
def validateEmail(email):

    if len(email) > 7:
        if re.match("^.+\\@(\\[?)[a-zA-Z0-9\\-\\.]+\\.([a-zA-Z]{2,3}|[0-9]{1,3})(\\]?)$", email) != None:
            return 1
    return 0