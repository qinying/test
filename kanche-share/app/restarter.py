#!/usr/bin/python -u
# -*- coding: UTF-8 -*-

__author__ = 'triplex'

import pymongo
import time
import datetime
import traceback
from multiprocessing import Process, Value, Lock
import procname
import config
import sys
import logger
import csv
import string

reload(sys)
sys.setdefaultencoding('utf8')

if sys.stdout.encoding is None:
    import codecs

    writer = codecs.getwriter("utf-8")
    sys.stdout = writer(sys.stdout)


# class Singleton(type):
#     _instances = {}
#
#     def __call__(cls, *args, **kwargs):
#         if cls not in cls._instances:
#             cls._instances[cls] = super(Singleton, cls).__call__(*args, **kwargs)
#         return cls._instances[cls]


class Restarter(object):
    # __metaclass__ = Singleton

    def __init__(self):
        self.conn = pymongo.Connection(config.mongoServer)
        self.db = self.conn.kanche
        self.col = self.db.share_job
        self.process = Process(target=self.serv, args=())
        self.process.start()

    def serv(self):
        procname.setprocname('restarter')
        now = datetime.datetime.utcnow()
        ts = time.mktime(now.timetuple()) - 86400 * 7
        startTime = datetime.datetime.fromtimestamp(ts)
        retry_max_times = 5
        history_col = self.db.share_job_history

        try:
            while True:
                logger.debug(u"-------all 重试开始开始-------")
                share_jobs = self.col.find({
                    'status': 'deferred',
                    "create_at": {
                        "$gte": startTime
                    }
                })
                for share_job in share_jobs:
                    _id = share_job.get('_id', None)
                    category = share_job.get('category', 'send')
                    retry_times_key = category + '_retry_times'
                    create_at = share_job.get('create_at')
                    update_at = share_job.get('update_at')

                    now = datetime.datetime.utcnow()
                    current_ts = time.mktime(now.timetuple())
                    update_ts = time.mktime(update_at.timetuple())
                    if(current_ts - update_ts < 3600.):
                        continue

                    retry_times = share_job.get(retry_times_key, retry_max_times)

                    if retry_times < retry_max_times:

                        message = self.col.find_and_modify(
                            query={'_id': _id},
                            update={
                                '$set': {
                                    'status': 'pending',
                                    retry_times_key: retry_times + 1
                                }
                            },
                            sort={'create_at': 1}
                        )
                        # logger.debug("Restart job!")
                        if message is None:
                            logger.debug('modify error!')
                time.sleep(100)

        except Exception as e:
            logger.error("Exception: " + str(e))
            exc_type, exc_value, exc_traceback = sys.exc_info()
            logger.error(repr(traceback.format_exception(exc_type, exc_value, exc_traceback)))

if __name__ == "__main__":
    restarter = Restarter()
    while True:
        time.sleep(10)