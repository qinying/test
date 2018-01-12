#!/usr/bin/python
# -*- coding: UTF-8 -*-

class Singleton(type):
    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(Singleton, cls).__call__(*args, **kwargs)
        return cls._instances[cls]


class CityTaoche(object):
    __metaclass__ = Singleton

    def __init__(self):
        self.provinceNameTable = {}
        self.provinceCodeTable = {}

        self.cityNameTable = {}
        self.cityCodeTable = {}

        fd = open('data/taocheCity.txt', 'r')
        for line in fd.readlines():
            params = line.split('\t')
            self.provinceNameTable[params[0]] = params[5]
            self.provinceCodeTable[params[0]] = params[4]

            self.cityNameTable[params[2]] = params[7]
            self.cityCodeTable[params[2]] = params[6]
            # print params[5], params[4], params[7], params[6]

        fd.close()



    def getProvinceName(self, province):
        return self.provinceNameTable.get(province, None)

    def getProvinceCode(self, province):
        return self.provinceCodeTable.get(province, None)

    def getCityName(self, city):
        return self.cityNameTable.get(city, None)

    def getCityCode(self, city):
        return self.cityCodeTable.get(city, None)