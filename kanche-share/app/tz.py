#!/usr/bin/python
# -*- coding: UTF-8 -*-

import datetime

class HKTime(datetime.tzinfo):

    def utcoffset(self, dt):
        return datetime.timedelta(hours=8)

    def tzname(self, dt):
        return "HKT"

    def dst(self, dt):
        return datetime.timedelta(0)

HKT = HKTime()