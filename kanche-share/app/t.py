#!/usr/bin/python
# -*- coding: UTF-8 -*-

import pymongo
import tz
from dt8601 import IsoDate

conn = pymongo.Connection('127.0.0.1', tz_aware=True)
db = conn['kanche']
col = db['share_job']
cur = col.find({})
aa = cur[0]
d = aa['vehicle']['vehicle_date']['registration_date']
print d
print d.astimezone(tz.HKT)
d = IsoDate.from_iso_string('2014-06-01T00:00:00.000+08:00')
print d
print d.astimezone(tz.HKT)
