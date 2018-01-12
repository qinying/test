__author__ = 'jesse'

import copy
import urllib
import KancheException.HttpGetParamTypeException as HttpGetParamTypeException
import httplib
import zlib
import json
from cookies import Cookie
import string
import logger

class KancheHttpClient():

    def __init__(self, headers, timeout):
        self.headers = headers
        self.timeout = timeout

    @staticmethod
    def _ensure_unicode(k):
        if type(k) == type(u''):
            pass
        elif type(k) == type(''):
            k = k.decode("utf-8")

        elif type(k) == type(0):
            k = str(k).decode("utf-8")
        else:
            raise HttpGetParamTypeException("can not handle type except String or Integer")
            #浮点型就抛异常
        return k

    @staticmethod
    def decodeBody(headers, body):
        for header in headers:
            if header[0].lower() == 'content-encoding':
                if header[1].lower().count('gzip') > 0:
                    return zlib.decompress(body, 16+zlib.MAX_WBITS)
        return body

    @staticmethod
    def setCookies(self, headers, encode=False):
        def next_token_is_not_semi(s):
            for i in  xrange(len(s)):
                if s[i] == ';':
                    return False
                if s[i] == '=':
                    return True
            return True

        def parse_one_cookie(set_cookie_str):
            state = 0
            for i in xrange(len(set_cookies_str)):
                if state == 0 and set_cookies_str[i] == '=':
                    state = 1
                elif state == 1 and set_cookies_str[i] == ';':
                    state = 0
                if state == 0 and set_cookies_str[i] == ',':
                    return set_cookies_str[:i], set_cookies_str[i+1:].strip()
                if state == 1 and set_cookies_str[i] == ',' and next_token_is_not_semi(set_cookies_str[i+1:]):
                    return set_cookies_str[:i], set_cookies_str[i+1:].strip()
                else:
                    continue
            return set_cookie_str, ""

        for header in headers:
            if header[0].lower() == 'set-cookie':
                set_cookies_str = header[1]
                while len(set_cookies_str) > 0:
                    (one_cookie_str,set_cookies_str) = parse_one_cookie(set_cookies_str)
                    cookie = Cookie.from_string(one_cookie_str)
                    if encode:
                        self.cookies[cookie.name] = urllib.quote(cookie.value.encode('utf8'))
                    else:
                        self.cookies[cookie.name] = cookie.value.encode('utf8')
        ks = self.cookies.keys()
        cookie_list = []
        for k in ks:
            cookie_list.append(k + '=' + self.cookies[k])
        self.headers['Cookie'] = string.join(cookie_list, '; ')
        logger.debug(str(self.headers))


    def get(self, host, uri, params, params_encoding="utf-8", extra_headers={}, port=None,
            follow_redirect=False, https=False):

        headers = copy.copy(self.headers)
        for k, v in extra_headers.iteritems():
            headers[k] = v

        if port is None:
            if https:
                port = 443
            else:
                port = 80

        params_string = ''
        for k, v in params.iteritems:
            key = urllib.quote(k.encode(params_encoding))
            value = urllib.quote(v.encode(params_encoding))
            params_string += '&' + key + '=' + value

        if https:
            conn = httplib.HTTPConnection(host, port=port, timeout=self.timeout)
            conn.request("GET", uri+params_string, headers=self.headers)
        else:
            conn = httplib.HTTPSConnection(host, port=port, timeout=self.timeout)
            conn.request("GET", uri+params_string, headers=self.headers)

        #TODO:follow_redirect=True 重定向
        if follow_redirect:
            pass

        res = conn.getresponse()
        status = res.status

        resHeaders = res.getheaders()
        resRead = res.read()
        html = self.decodeBody(resHeaders, resRead)
        html = html.decode(params_encoding)
        html = html.replace(params_encoding, "utf-8")

        self.headers = resHeaders
        #you can get status and reHeaders
        return status, html

    #############
    #post_string true:post提交为form：sting;False:提交为form：dict
    ############
    def post(self, host, uri, form, post_string=False, form_encoding="utf-8", extra_headers={}, port=None, follow_redirect=False, https=False):
        headers = copy.copy(self.headers)
        if len(extra_headers):
            for k, v in extra_headers.iteritems():
                headers[k] = v

        if port is None:
            if https:
                port = 44
            else:
                port = 8

        formData = ''
        if not post_string:
            formJson = json.dumps(form)
            formData = formJson.encode(form_encoding)
        else:
            formData = form

        if https:
            conn = httplib.HTTPConnection(host, port=port, timeout=self.timeout)
            conn.request("POST", formData, headers=self.headers)
        else:
            conn = httplib.HTTPSConnection(host, port=port, timeout=self.timeout)
            conn.request('POST', formData, headers=self.headers)

        #TODO:follow_redirect=True 重定向

        res = conn.getresponse()
        status = res.status

        resHeaders = res.getheaders()
        resRead = res.read()
        html = self.decodeBody(resHeaders, resRead)
        html = html.decode(form_encoding)
        html = html.replace(form_encoding, "utf-8")

        self.headers = resHeaders
        #you can get status and reHeaders
        return status, html


