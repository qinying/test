#!/usr/bin/python
# -*- coding: UTF-8 -*-

import sqlite3
import procname
import logger
from multiprocessing import Process, Queue, Lock

class Singleton(type):
    _instances = {}
    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(Singleton, cls).__call__(*args, **kwargs)
        return cls._instances[cls]

class SpecServer(object):
    #sessionConn = sqlite3.connect('session.db', detect_types=sqlite3.PARSE_DECLTYPES)
    #specConn = sqlite3.connect('spec.db', detect_types=sqlite3.PARSE_DECLTYPES)
    __metaclass__ = Singleton

    def __init__(self):
        self.reqQueue = Queue()
        self.resQueue = Queue()
        self.lock = Lock()
        self.process = Process(target=self.serv, args=())
        self.process.start()

    def formatSite(self, site):
        if site.startswith('58'):
            return "58"
        if site.startswith('che168'):
            return "che168"
        if site.startswith('baixing'):
            return "baixing"

    def handleReq582(self, levelId):
        def dict_factory(cursor, row):  
            d = {}  
            for idx,col in enumerate(cursor.description):
                r = row[idx]
                if col[0] != "id":
                    if type(r) == type(1):
                        r = str(r)
                d[col[0]] = r#row[idx]
            return d 
        conn = sqlite3.connect('spec.db', detect_types=0)
        conn.row_factory = dict_factory
        cur = conn.cursor()
        cur.execute("SELECT model_id FROM model_map WHERE site=? AND level_id=?", ("582", levelId))
        res = cur.fetchone()
        cur.close()
        modelId = res['model_id']
        cur = conn.cursor()
        cur.execute("SELECT * FROM vehicletype_582 WHERE id=?", (modelId, ))
        detail = cur.fetchone()
        cur.close()
        #print json.dumps(detail)
        self.resQueue.put((modelId, detail))

    def handleReq(self, req):
        website = self.formatSite(req[0])
        levelId = req[1]
        if website == "58":
            return self.handleReq582(levelId)
        def dict_factory(cursor, row):  
            d = {}  
            for idx,col in enumerate(cursor.description):
                r = row[idx]
                if col[0] != "id":
                    if type(r) == type(1):
                        r = str(r)
                d[col[0]] = r#row[idx]
            return d 
        conn = sqlite3.connect('spec.db', detect_types=0)
        conn.row_factory = dict_factory
        cur = conn.cursor()
        cur.execute("SELECT model_id FROM model_map WHERE site=? AND level_id=?", (website, levelId))
        res = cur.fetchone()
        cur.close()
        modelId = res['model_id']
        cur = conn.cursor()
        cur.execute("SELECT * FROM vehicletypes6 WHERE website=? AND modelid=?", (website, modelId))
        detail = cur.fetchone()
        cur.close()
        self.resQueue.put((modelId, detail))

    def serv(self):
        procname.setprocname('sharer spec')
        while True:
            req = self.reqQueue.get()
            try:
                self.handleReq(req)
            except Exception as e:
                self.resQueue.put((None, None))
                logger.error(str(e))

    def getModelId(self, site, levelId):
        self.lock.acquire()
        self.reqQueue.put((site, levelId))
        res = self.resQueue.get()
        self.lock.release()
        return res