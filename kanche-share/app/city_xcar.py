#!/usr/bin/python
# -*- coding: UTF-8 -*-

import os.path

__author__ = 'qinying'

class Singleton(type):
    _instances = {}
    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(Singleton, cls).__call__(*args, **kwargs)
        return cls._instances[cls]

class Cityxcar(object):
    __metaclass__ = Singleton

    def __init__(self):
        self.regionCityTable = {}


        fd = open('data/xcar_city.txt', 'r')
        lines = fd.readlines()
        for line in lines:
            param = line.split("\t")
            # print(str(param))
            # print(str(param[3]))
            # print(str(param[2]))
            self.regionCityTable[str(param[3][:len(param[3])-1])] = param[2]
        print(self.regionCityTable)


    def getName(self, region):
        """
        根据名称查询城市
        :param name:
        :return:
        """
        cityTable = self.regionCityTable
        return self.regionCityTable.get(region, None)


if __name__ == '__main__':
    city = Cityxcar()
    print city.getName('无锡市')
