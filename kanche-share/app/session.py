#!/usr/bin/python
# -*- coding: UTF-8 -*-

import time
import pymongo
import config

class Singleton(type):
    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(Singleton, cls).__call__(*args, **kwargs)
        return cls._instances[cls]


class SessionServer(object):
    __metaclass__ = Singleton

    def __init__(self):
        self.conn = pymongo.Connection(config.mongoServer)
        #self.conn = pymongo.Connection(config.sessionMongoServer)
        self.db = self.conn.share_session

    def formatSite(self, site):
        if site.startswith('58'):
            return "58.com"
        if site.startswith('che168'):
            return "che168.com"
        if site.startswith('baixing'):
            return "baixing.com"
        if site.startswith('hx2car'):
            return "hx2car.com"
        if site.startswith('ganji'):
            return "ganji.com"
        if site.startswith('51auto'):
            return "51auto.com"
        if site.startswith('iautos'):
            return "iautos.cn"
        if site.startswith('taoche'):
            return "taoche.com"
        return site

    def getTime(self, website):
        if website == "58":
            timeout = 3600
        elif website == "che168":
            timeout = 86400 * 3
        elif website == "baixing":
            timeout = 3600
        elif website == "openapi.58.com":
            timeout = 86400 * 365
        else:
            timeout = 1800
        now = int(time.time())
        return (now, timeout)

    # 获取cookie
    def getSession(self, site, username):
        site = self.formatSite(site)
        (now, timeout) = self.getTime(site)
        col = self.db.cookie
        res = col.find_one({"site": site,
                            "username": username,
                            "create_at": {"$gt": str(now-timeout)}
        })

        if res is None:
            pass
        else:
            # 过滤掉_id
            res = res['session']
        return res

    ###################
    # 存储cookie
    ##################
    def setSession(self, site, username, session):
        site = self.formatSite(site)
        (now, timeout) = self.getTime(site)
        col = self.db.cookie
        result = col.ensure_index([("site", pymongo.ASCENDING), ("username", pymongo.ASCENDING)], unique=True)

        key = {"site": site,
               "username": username}
        data = {"site": site,
                "username": username,
                "session": session,
                "create_at": str(now)}
        res = col.update(key, {'$set': data}, multi=True, upsert=True)
        return col.find_one(key)

    # 获取图片操作
    def getUpload(self, site, local):
        site = self.formatSite(site)
        col = self.db.mappic
        res = col.find_one({"site": site,
                            "local": local
        })
        if res is None:
            pass
        else:
            res = res['upload']
        return res

    def setUpload(self, site, local, upload):
        # 存储图片操作
        site = self.formatSite(site)
        col = self.db.picture
        result = col.ensure_index([("site", pymongo.ASCENDING), ("local", pymongo.ASCENDING)], unique=True)

        key = {"site": site,
               "local": local}
        data = {"site": site,
                "local": local,
                "upload": upload}
        res = col.update(key, {'$set': data}, multi=True, upsert=True)
        return col.find_one(key)
