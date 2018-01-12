#!/usr/bin/python
# -*- coding: UTF-8 -*-

import web
import sys
import json
from multiprocessing import Process, Queue
import procname
import fe
import che168
import taoche
import ganji
import baixing
import FOAuto
import iautos
import hx2sc
import sohu

class loginCheck(object):
    def __init__(self):
        pass

    @staticmethod
    def serv(reqQueue, resQueue):
        result = False
        (site, username, password) = reqQueue.get()
        if site.startswith('58'):
            sharer = fe.FESharer(None, None)
            result = sharer.doLogin(username, password)
        elif site.startswith('che168'):
            sharer = che168.Che168Sharer(None, None)
            result = sharer.doLogin(username, password)
        elif site.startswith('ganji'):
            sharer = ganji.GanjiSharer(None, None)
            result = sharer.doLogin(username, password)
        elif site.startswith('baixing'):
            sharer = baixing.BaixingSharer(None, None)
            result = sharer.doLogin(username, password)
        elif site.startswith('taoche'):
            sharer = taoche.TaocheSharer(None, None)
            result = sharer.doLogin(username, password)
        elif site.startswith('51auto'):
            sharer = FOAuto.FOAutoSharer(None, None)
            result = sharer.doLogin(username, password)
        elif site.startswith('iautos'):
            sharer = iautos.IautosSharer(None, None)
            result = sharer.doLogin(username, password)
        elif site.startswith('hx2car'):
            sharer = hx2sc.Hx2scSharer(None, None)
            result = sharer.doLogin(username, password)
        elif site.startswith('sohu'):
            sharer = sohu.SohuSharer(None, None)
            result = sharer.doLogin(username, password)
        resQueue.put(result)

    def GET(self):
        web.header('Content-type', 'application/json')
        params = web.input()
        site = params.get("site", None)
        username = params.get("username", None)
        password = params.get("password", None)
        #print username
        if (not site) or (not username) or (not password):
            return json.dumps({"result": False})

        reqQueue = Queue()
        resQueue = Queue()
        process = Process(target=self.serv, args=(reqQueue, resQueue))
        process.start()
        reqQueue.put((site, username, password))
        result = resQueue.get()

        reqQueue.close()
        reqQueue = None
        resQueue.close()
        resQueue = None
        process.join()

        return json.dumps({"result": result})

def checkServer():
    procname.setprocname('sharer check')
    port = '3011'
    urls = ('/login/check', 'loginCheck')
    app = web.application(urls, globals())
    if len(sys.argv) > 1:
        sys.argv[1] = port
    else:
        sys.argv.append(port)
    app.run()

def start():
    process = Process(target=checkServer)
    process.start()
