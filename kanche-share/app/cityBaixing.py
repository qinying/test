#!/usr/bin/python
# -*- coding: UTF-8 -*-

class Singleton(type):
    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(Singleton, cls).__call__(*args, **kwargs)
        return cls._instances[cls]


class CityBaixing(object):
    __metaclass__ = Singleton

    def __init__(self):
        self.regionNameTable = {}
        self.regionCodeTable = {}

        fd = open('data/baixing_city.txt', 'r')
        for line in fd.readlines():
            params = line.split('\t')
            self.regionNameTable[params[2]] = params[4]#huanggang
            self.regionCodeTable[params[2]] = params[6]#m5467
            # print params[4], params[6]
        fd.close()


    def getName(self, region):
        return self.regionNameTable.get(region, None)

    def getCode(self, region):
        return self.regionCodeTable.get(region, None)