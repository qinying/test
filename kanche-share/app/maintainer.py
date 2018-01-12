#!/usr/bin/python
# -*- coding: UTF-8 -*-

import signal
import atexit
import time
import traceback
from multiprocessing import Process, Value, Lock
import procname
from datetime import datetime

import os
import pymongo
# import checker
import spec
import session
import errorcode
import errormsg
import logger
import re
import simpleflock
import config
import che168Public
import che168
import fe
import taocheApiShare
import ganji
import FOAuto
import FOAutoPublic
import iautos
import hx2scApiShare
import baixingApiSharer
import che168Refresh
import sohu
import xcar
import restarter

from urlparse import urlparse
import httplib

import sys
reload(sys)
sys.setdefaultencoding('utf8')

if sys.stdout.encoding is None:
    import codecs

    writer = codecs.getwriter("utf-8")
    sys.stdout = writer(sys.stdout)

skip_time = 0.1


def handle_pending_req(col, history_col):
    # 3. 处理发车失败的任务下架
    message = col.find_and_modify(query={'category': 'send', 'remove_pending': True, "status": "deferred"},
                                  update={'$set': {'category': 'remove', 'status': 'done', 'remove_pending': False,
                                                   'update_pending': False}})
    time.sleep(skip_time)
    if message is not None:
        # history_create(history_col, message['_id'], 'done', u'下架成功', u'下架完成', 'restart_job', None)
        return message

    # 4. 处理发车中准备下架的进行下架
    message = col.find_and_modify(query={'category': 'send', 'remove_pending': True, "status": {"$ne": "handling"}},
                                  update={'$set': {'category': 'remove', 'status': 'pending', 'remove_pending': False,
                                                   'update_pending': False}})
    time.sleep(skip_time)
    if message is not None:
        # history_create(history_col, message['_id'], 'pending', u'车辆正在下架', u'下架任务启动', 'restart_job', None)
        return message

    # 8. 处理发车成功的准备改价，进行改价
    message = col.find_and_modify(query={'category': 'send', 'update_pending': True, "status": "done"},
                                  update={'$set': {'category': 'update', 'status': 'pending', 'remove_pending': False,
                                                   'update_pending': False}})
    time.sleep(skip_time)
    if message is not None:
        # history_create(history_col, message['_id'], 'pending', u'车辆正在改价', u'改价任务启动', 'restart_job', None)
        return message

    # 1. 处理准备改价的任务改价
    message = col.find_and_modify(query={'category': 'update', 'update_pending': True, "status": "done"},
                                  update={'$set': {'category': 'update', 'status': 'pending', 'remove_pending': False,
                                                   'update_pending': False}})
    time.sleep(skip_time)
    if message is not None:
        print message
        # history_create(history_col, message['_id'], 'pending', u'车辆正在改价', u'改价任务启动', 'restart_job', None)
        return message

    # 5. 处理改价忽略的的进行下架
    message = col.find_and_modify(query={'category': 'update', 'remove_pending': True, "status": "ignore"},
                                  update={'$set': {'category': 'remove', 'status': 'ignore', 'remove_pending': False,
                                                   'update_pending': False}})
    time.sleep(skip_time)
    if message is not None:
        # history_create(history_col, message['_id'], 'ignore', u'任务已经忽略', u'下架完成', 'restart_job', None)
        return message

    # 6. 处理改价失败的的进行下架
    message = col.find_and_modify(query={'category': 'update', 'remove_pending': True, "status": "deferred"},
                                  update={'$set': {'category': 'remove', 'status': 'pending', 'remove_pending': False,
                                                   'update_pending': False}})
    time.sleep(skip_time)
    if message is not None:
        # history_create(history_col, message['_id'], 'pending', u'车辆正在下架', u'下架任务启动', 'restart_job', None)
        return message

    # 7. 处理改价中准备下架的进行下架
    message = col.find_and_modify(query={'category': 'update', 'remove_pending': True, "status": {"$ne": "handling"}},
                                  update={'$set': {'category': 'remove', 'status': 'pending', 'remove_pending': False,
                                                   'update_pending': False}})
    time.sleep(skip_time)
    if message is not None:
        # history_create(history_col, message['_id'], 'pending', u'车辆正在下架', u'下架任务启动', 'restart_job', None)
        return message


        # message = col.find_and_modify(query = {'category': 'update', 'update_pending': True, "status": {"$ne": "handling"}},
    #                                  update = { '$set' : {'category': 'update', 'status': 'pending', 'remove_pending': False, 'update_pending': False}},
    #                                  sort = { 'update_at' : 1})
    #    if message is not None:
    #        history_create(history_col, message['_id'], 'pending', u'车辆正在改价', u'改价任务启动', 'restart_job', None)
    #        return message

    # 9. 处理发车忽略的准备改价，进行改价
    message = col.find_and_modify(query={'category': 'send', 'update_pending': True, "status": "ignore"},
                                  update={'$set': {'category': 'update', 'status': 'ignore', 'remove_pending': False,
                                                   'update_pending': False}})
    time.sleep(skip_time)
    if message is not None:
        # history_create(history_col, message['_id'], 'pending', u'任务被忽略', u'改价任务忽略', 'restart_job', None)
        return message

    # 2. 处理发车忽略的任务下架
    message = col.find_and_modify(query={'category': 'send', 'remove_pending': True, "status": "ignore"},
                                  update={'$set': {'category': 'remove', 'status': 'ignore', 'remove_pending': False,
                                                   'update_pending': False}})
    time.sleep(skip_time)
    if message is not None:
        # history_create(history_col, message['_id'], 'ignore', u'任务已经忽略', u'下架完成', 'restart_job', None)
        return message


def loop_req(col, history_col):
    while handle_pending_req(col, history_col) is not None:
        time.sleep(0.01)
        continue
    time.sleep(0.1)

def cleanup():
    os.killpg(0, signal.SIGKILL)

if __name__ == "__main__":
    os.setpgrp()
    atexit.register(cleanup)

    conn = pymongo.Connection(config.mongoServer, tz_aware=True)
    db = conn['kanche']
    col = db['share_job']
    history_col = db['share_job_history']
    procname.setprocname('maintainer')
    # checker.start()

    while True:
        try:
            loop_req(col, history_col)
        except Exception as e:
            logger.error(str(e))