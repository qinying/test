# -*- coding: UTF-8 -*-
import sys

import os
import json
import logging
import logging.handlers
import procname
from multiprocessing import Process, Queue, Lock


LOG_FILENAME = os.path.join(os.getcwd(), '/var/log/kanche-share/sharer.log')
logger = logging.getLogger('sharer')
logger.setLevel(logging.DEBUG)
fh = logging.handlers.RotatingFileHandler(LOG_FILENAME, maxBytes=1073741824, backupCount=5)
fh.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
fh.setFormatter(formatter)
logger.addHandler(fh)
ch = logging.StreamHandler(sys.stdout)
ch.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
ch.setFormatter(formatter)
logger.addHandler(ch)

reqQueue = Queue()
resQueue = Queue()

class Singleton(type):
    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(Singleton, cls).__call__(*args, **kwargs)
        return cls._instances[cls]


class LogParams(object):
    __metaclass__ = Singleton

    def __init__(self):
        self.job_id = None
        self.website = None

    def set_job_id(self, job_id):
        self.job_id = job_id

    def get_job_id(self):
        return self.job_id

    def set_website(self, website):
        self.website = website

    def get_website(self):
        return self.website

class LogServer(object):
    def __init__(self):
        self.lock = Lock()
        self.process = Process(target=self.serv, args=())
        self.process.start()

    def serv(self):
        procname.setprocname('sharer log')
        try:
            while True:
                req = reqQueue.get()
                if req == None:
                    continue
                try:
                    self.handleReq(req)
                except Exception as e:
                    pass
        except Exception as e:
            pass

    def handleReq(self, req):
        op = req[0]
        message = req[1]
        if op == "debug":
            self.debug(message)
        elif op == "info":
            self.info(message)
        elif op == "warning":
            self.warning(message)
        elif op == "error":
            self.error(message)
        else:
            self.debug(message)

    def debug(self, message):
        try:
            logger.debug(message)
        except Exception as e:
            pass

    def info(self, message):
        try:
            logger.info(message)
        except Exception as e:
            pass

    def warning(self, message):
        try:
            logger.warning(message)
        except Exception as e:
            pass

    def error(self, message):
        try:
            logger.error(message)
        except Exception as e:
            pass

def reload_message(message):
    try:
        obj = json.loads(message)
    except Exception as e:
        obj = None
    if obj is not None:
        return obj
    return message

def debug(message):
    try:
        log_params = LogParams()
        msg = {"jobId": log_params.get_job_id(), "website": log_params.get_website(), "message": reload_message(message)}
        #logger.debug(json.dumps(msg))
        reqQueue.put(('debug', json.dumps(msg)))
    except Exception as e:
        pass


def info(message):
    try:
        log_params = LogParams()
        message = str(message)
        msg = {"jobId": log_params.get_job_id(), "website": log_params.get_website(), "message": reload_message(message)}
        #logger.info(json.dumps(msg))
        reqQueue.put(('info', json.dumps(msg)))
    except Exception as e:
        pass


def warning(message):
    try:
        log_params = LogParams()
        message = str(message)
        msg = {"jobId": log_params.get_job_id(), "website": log_params.get_website(), "message": reload_message(message)}
        #logger.warning(json.dumps(msg))
        reqQueue.put(('warning', json.dumps(msg)))
    except Exception as e:
        pass


def error(message):
    try:
        log_params = LogParams()
        message = str(message)
        msg = {"jobId": log_params.get_job_id(), "website": log_params.get_website(), "message": reload_message(message)}
        #logger.error(json.dumps(msg))
        reqQueue.put(('error', json.dumps(msg)))
    except Exception as e:
        pass

if __name__ == "__main__":
    log_server = LogServer()
    debug("aaa")
    info("bbb")
    warning("ccc")
    error("ddd")
