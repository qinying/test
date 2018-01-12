#!/usr/bin/python
# -*- coding: UTF-8 -*-

class Singleton(type):
    _instances = {}
    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(Singleton, cls).__call__(*args, **kwargs)
        return cls._instances[cls]

class CityGanji(object):
    __metaclass__ = Singleton

    def __init__(self):
        self.region_domain_table = {}
        self.region_chName_table = {}
        self.regionCodeTable = {}
        self.domain_table = {}

        fd = open('data/ganji_city.txt', 'r')
        for line in fd.readlines():
            params = line.split('\t')
            if len(params) < 10:
                continue
            # self.regionNameTable[params[4]] = params[6]#220106:cc
            # self.regionCodeTable[params[4]] = params[8]#220106:495
            self.region_domain_table[params[4]] = params[6]  # 110105:bj
            self.regionCodeTable[params[4]] = params[8]      # 110105:174
            self.region_chName_table[params[4]] = params[5]  # 110105:朝阳区
        fd.close()
        #fd = open('data/58city2.txt', 'r')
        #for line in fd.readlines():
        #    params = line.split('\t')
        #    self.regionCodeTable[params[2]] = params[0]
        #fd.close()

    def get_domain(self, region):
        return self.region_domain_table.get(region, None)

    def get_chName(self, region):
        return self.region_chName_table.get(region, None)

    def getCode(self, region):
        return self.regionCodeTable.get(region, None)

if __name__ == '__main__':
    city = CityGanji()
    print city.getName('110101')
    print city.getCode('110101')
