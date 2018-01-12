#!/usr/bin/python
# -*- coding: UTF-8 -*-

class Singleton(type):
    _instances = {}
    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(Singleton, cls).__call__(*args, **kwargs)
        return cls._instances[cls]

class City852(object):
    __metaclass__ = Singleton

    def __init__(self):
        self.regionNameTable = {}
        self.regionCodeTable = {}

        fd = open('data/58city.txt', 'r')
        for line in fd.readlines():
            params = line.split('\t')
            self.regionNameTable[params[2]] = params[5]
            self.regionCodeTable[params[2]] = params[4]
        fd.close()
        #fd = open('data/58city2.txt', 'r')
        #for line in fd.readlines():
        #    params = line.split('\t')
        #    self.regionCodeTable[params[2]] = params[0]
        #fd.close()

    def getName(self, region):
        return self.regionNameTable.get(region, None)

    def getCode(self, region):
        return self.regionCodeTable.get(region, None)

if __name__ == '__main__':
    city = City852()
    print city.getName('110100')
    print city.getCode('110100')
