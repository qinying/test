#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging
import os
import datetime
import traceback
from selenium import webdriver
from PIL import Image
import time
# 设置日志格式


def writeLog():
    basename = os.path.splitext(os.path.basename(__file__))[0]
    logFile = basename+"-"+datetime.datetime.now().strftime("%Y%m%d%H%M%S")+".log"
    logging.basicConfig(filename=logFile)
    s = traceback.format_exc()
    logging.error(s)
