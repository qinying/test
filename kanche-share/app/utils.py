#!/usr/bin/python -u
# -*- coding: UTF-8 -*-

import re
import string
import base64
import hashlib
from urlparse import urlparse


try:
    # Wide UCS-4 build
    emoji_re = re.compile(u'['
                      u'\U0001F300-\U0001F64F'
                      u'\U0001F680-\U0001F6FF'
                      u'\u2600-\u26FF\u2700-\u27BF]+',
                      re.UNICODE)
except re.error:
    # Narrow UCS-2 build
    emoji_re = re.compile(u'('
                      u'\ud83c[\udf00-\udfff]|'
                      u'\ud83d[\udc00-\ude4f\ude80-\udeff]|'
                      u'[\u2600-\u26FF\u2700-\u27BF])+',
                      re.UNICODE)

def remove_emoji(str):
    return emoji_re.sub('', str)

def urlsafe_base64(s):
    s = base64.encodestring(s)
    s = string.replace(s, "+", "-")
    s = string.replace(s, "/", "_")
    s = string.replace(s, "\n", "")
    return s

def pic_with_watermark_qiniu(pic, watermark, place):
    w = urlsafe_base64(watermark)
    url = pic + "?watermark/1/image/" + w + "/gravity/" + place
    return url

def pic_with_watermark_ali(pic, watermark, place):
    o = urlparse(watermark)
    host = o.netloc
    uri = o.path
    w = urlsafe_base64(string.replace(uri, "/", ""))
    place_map = {
        "NorthWest": 1,
        "NorthEast": 3,
        "SouthWest": 7,
        "SouthEast": 9
    }
    p = place_map.get(place, 1)
    url = pic + "@800w_600h_90q|watermark=1&&object=" + w + "&p=" + str(p)
    return url

def md5(pwd):
    """
    md5加密
    :param pwd
    :return:
    """
    m = hashlib.md5()
    m.update(pwd)
    return m.hexdigest()