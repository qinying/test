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
import feApi
import taocheApiShare
import ganji
import ganjiApi
import FOAuto
import FOAutoPublic
import iautos
import hx2scApiShare
import baixingApiSharer
import sohu
import xcar
import taobaoApiSharer
import foolcars
import jingzhengu

from urlparse import urlparse
import httplib

import sys
reload(sys)
sys.setdefaultencoding('utf8')

if sys.stdout.encoding is None:
    import codecs

    writer = codecs.getwriter("utf-8")
    sys.stdout = writer(sys.stdout)


def run_with_timeout(func, arg, timeout):
    def handler(signum, frame):
        print "Forever is over!"
        raise Exception("end of time")

    signal.signal(signal.SIGALRM, handler)
    signal.alarm(timeout)
    try:
        res = func(arg)
    except Exception, exc:
        print exc
        return (errorcode.OPERATION_TIMEOUT, errormsg.TIMEOUT_FAIL)
    return res


def history_create(history_col, share_job_id, status, title, content, retry_method, url):
    obj = {'share_job_id': share_job_id, 'status': status, 'title': title,
           'content': content, 'message': "%s:%s"%(title, content), 'create_at': datetime.utcnow()}
    if retry_method is not None:
        obj['retry_method'] = retry_method
    if url is not None:
        obj['url'] = url
    history_col.insert(obj)


def set_job_deferred(col, message):
    key = message.get("category", "send") + "_retry_times"
    if message.has_key(key) is True:
        pass
    else:
        message[key] = 0
    col.find_and_modify(
        query={'_id': message['_id']},
        update={
            '$set':
                {
                    'status': 'deferred',
                    key: message[key],
                    'update_at': datetime.utcnow()
                }
        }
    )


def send_req(col, history_col, message, sessionServer, specServer, counter):
    #####################################################
    # col.find_and_modify(query = {'_id': message['_id']},
    #                    update = { '$set' : {'status': 'deferred'}},
    #                    sort = { 'create_at' : 1})
    # title = u'功能未实现'
    # msg = u'功能暂时未实现，请等下一个版本'
    # history_create(history_col, message['_id'], 'deferred', title, msg, 'restart_job', None)
    # return
    #####################################################
    counter.increment()
    unDoUsername = [u'青岛易宝二手车', u'看车精品二手车', u'看车二手车', u'德州看看车', u'青岛看车网', u'100081330@tc', u'100074344@tc', u'']
    try:
        website = message[u'share_account'].get('website', '')
        log_params = logger.LogParams()
        log_params.set_job_id(str(message['_id']))
        log_params.set_website(website)

        #TODO:website
        username = message.get('share_account', None).get('username', None)
        if username in unDoUsername:
            (code, msg) = errorcode.SUCCESS, u'该账号暂不发车'

        else:
            if website.startswith('che168'):
                # 是否在规定时间内发车[0,17]
                (success, msg) = isReSendable(shareJob=message, website="che168.com")
                if not success:
                    (code, msg) = (errorcode.SITE_ERROR, msg)
                elif not isInnerSharerClock():
                    (code, msg) = (errorcode.SITE_ERROR, errormsg.SHARE_FORBIDDEN)
                else:
                    # True:代运营，启用Public接口，False:大客户启用普通接口，走自己的账号
                    if isVipAccount(message):
                        logger.debug("che168public")
                        sharer = che168Public.Che168Sharer(sessionServer, specServer)
                    else:
                        logger.debug("che168")
                        sharer = che168.Che168Sharer(sessionServer, specServer)
                    (code, msg) = sharer.shareVehicle(message)

            elif website.startswith('58'):
                logger.debug("58 public shareVehicle")
                # if not is_in_fe_clock(share_job=message):
                #     (code, msg) = (errorcode.SITE_ERROR, errormsg.SHARE_FORBIDDEN)
                # else:
                #     sharer = feApi.FEApiSharer(sessionServer, specServer)
                #     (code, msg) = sharer.shareVehicle(message)
                sharer = feApi.FEApiSharer(sessionServer, specServer)
                (code, msg) = sharer.shareVehicle(message)

            elif website.startswith('ganji'):
                # logger.debug("ganji")
                # # FIXME: one lock for each user
                # with simpleflock.SimpleFlock("lock/ganji.lock", timeout=2400):
                #     sharer = ganji.GanjiSharer(sessionServer, specServer)
                #     # (code, msg) = sharer.shareVehicle(message)
                #     (code, msg) = run_with_timeout(sharer.shareVehicle, message, 240)
                logger.debug("ganji shareVehicle")
                sharer = ganjiApi.GanjiSharer(sessionServer, specServer)
                (code, msg) = sharer.shareVehicle(share_job=message)

            elif website.startswith('baixing'):
                logger.debug("baixing")
                sharer = baixingApiSharer.BaixingApiSharer(sessionServer, specServer)
                (code, msg) = sharer.shareVehicle(message)

            elif website.startswith('taoche'):
                logger.debug("taoche")
                # sharer = taoche.TaocheSharer(sessionServer, specServer)
                # (code, msg) = sharer.shareVehicle(message)
                sharer = taocheApiShare.TaocheSharer(sessionServer, specServer)
                res = sharer.shareVehicle(message)
                if len(res) == 2:
                    (code, msg) = res
                else:
                    (code, msg, extra) = res

            elif website.startswith('51auto'):
                logger.debug("51public sendVehicle")
                sharer = FOAutoPublic.FOAutoSharer(sessionServer, specServer)
                # if isPublicAccount(message):
                #     logger.debug("51autoPublic")
                #     sharer = FOAutoPublic.FOAutoSharer(sessionServer, specServer)
                # else:
                #     logger.debug("51auto")
                #     sharer = FOAuto.FOAutoSharer(sessionServer, specServer)
                (code, msg) = sharer.shareVehicle(message)

            elif website.startswith('iautos'):
                logger.debug("iautos")
                sharer = iautos.IautosSharer(sessionServer, specServer)
                (code, msg) = sharer.shareVehicle(message)

            elif website.startswith('hx2car'):
                # logger.debug("hx2car")
                # sharer = hx2sc.Hx2scSharer(sessionServer, specServer)
                # api
                sharer = hx2scApiShare.Hx2scAPISharer(sessionServer, specServer)
                (code, msg) = sharer.shareVehicle(message)

            elif website.startswith('sohu'):
                logger.debug("sohu")
                sharer = sohu.SohuSharer(sessionServer, specServer)
                (code, msg) = sharer.shareVehicle(message)

            # 爱卡汽车
            elif website.startswith('xcar'):
                logger.debug("xcar shareVehicle")
                sharer = xcar.XcarSharer(sessionServer, specServer)
                (code, msg) = sharer.shareVehicle(message)

            elif website.startswith('taobao'):
                logger.debug("taobao shareVehicle")

                (success, msg) = isReSendable(shareJob=message, website="taobao.com")
                if not success:
                    (code, msg) = (errorcode.SITE_ERROR, msg)
                else:
                    sharer = taobaoApiSharer.TaoBaoApiSharer(sessionServer, specServer)
                    (code, msg) = sharer.shareVehicle(message)
                
            # 大傻车
            elif website.startswith('foolcars'):
                logger.debug("foolcars shareVehicle")
                sharer = foolcars.FoolcarsSharer(sessionServer, specServer)
                (code, msg) = sharer.shareVehicle(message)

            # 精真估
            elif website.startswith('jingzhengu'):
                logger.debug("jingzhengu shareVehicle")
                sharer = jingzhengu.JZGSharer(sessionServer, specServer)
                (code, msg) = sharer.shareVehicle(message)

        if code == errorcode.SUCCESS:
            logger.debug(msg)
            # 对于赶集先get url，得到extra存储
            extra_url = ''
            # TODO
            # if website.startswith('ganji') and msg is not None:
            #     extra_url = getExtraUrl(msg)

            logger.debug('extra:'+str(extra_url))
            col.find_and_modify(query={'_id': message['_id']},
                                update={'$set': {'extra': extra_url}})

            innerurl = None
            if 'extra' in locals():
                col.find_and_modify(query={'_id': message['_id']},
                                    update={'$set': {'status': 'done', 'url': msg, 'extra': extra}})

                innerurl = extra

            else:
                col.find_and_modify(query={'_id': message['_id']},
                                    update={'$set': {'status': 'done', 'url': msg}})
                innerurl = msg

            # get id and restore
            url_id = get_url_id(website, innerurl)
            col.find_and_modify(query={'_id': message['_id']},
                                update={'$set': {'url_id': url_id}})

            # history_col.insert({'share_job_id':message['_id'], 'status': 'done',
            #                    'message': msg, 'url': msg, 'create_at': datetime.utcnow()})
            # TODO:根据不同网站返回不同的提示
            history_create(history_col, message['_id'], 'done', u'车辆已经发布到网站', u'分发成功', None, msg)
        else:
            logger.error(msg)
            col.find_and_modify(query={'_id': message['_id']},
                                update={'$set': {'status': 'deferred'}})
            title = u'其它错误'
            if code == errorcode.NETWORK_ERROR:
                title = u'网络错误'
            elif code == errorcode.AUTH_ERROR:
                title = u'帐号/密码错误'
            elif code == errorcode.LOGIC_ERROR:
                title = u'程序错误'
            elif code == errorcode.DATA_ERROR:
                title = u'数据错误'
            elif code == errorcode.SITE_ERROR:
                title = u'网站错误'
            # history_col.insert({'share_job_id':message['_id'], 'status': 'deferred',
            #                    'message': msg, 'url': None, 'create_at': datetime.utcnow()})
            set_job_deferred(col, message)
            if code == errorcode.DATA_ERROR:
                history_create(history_col, message['_id'], 'deferred', title, msg, 'edit_vehicle', None)
            else:
                history_create(history_col, message['_id'], 'deferred', title, msg, 'restart_job', None)
    except Exception as e:
        logger.error("Exception: " + str(e))
        exc_type, exc_value, exc_traceback = sys.exc_info()
        logger.error(repr(traceback.format_exception(exc_type, exc_value, exc_traceback)))
        col.find_and_modify(query={'_id': message['_id']},
                            update={'$set': {'status': 'deferred'}})
        # history_col.insert({'share_job_id':message['_id'], 'status': 'deferred',
        #                    'message': "网络异常：请重试", 'url': None, 'create_at': datetime.utcnow()})
        history_create(history_col, message['_id'], 'deferred', u'网络异常', u'请重试', 'restart_job', None)

    counter.decrement()


def remove_req(col, history_col, message, sessionServer, specServer, counter):
    #####################################################
    # col.find_and_modify(query = {'_id': message['_id']},
    #                    update = { '$set' : {'status': 'deferred'}},
    #                    sort = { 'create_at' : 1})
    # title = u'功能未实现'
    # msg = u'功能暂时未实现，请等下一个版本'
    # history_create(history_col, message['_id'], 'deferred', title, msg, 'restart_job', None)
    # return
    #####################################################
    counter.increment()
    try:
        website = message[u'share_account'].get('website', '')
        log_params = logger.LogParams()
        log_params.set_job_id(str(message['_id']))
        log_params.set_website(website)
        if website.startswith('che168'):
            '''
            logger.debug("che168")
            sharer = che168.Che168Sharer(sessionServer, specServer)
            '''
            #True:代运营，启用Public接口，False:大客户启用普通接口，走自己的账号
            if isVipAccount(message):
                logger.debug("che168public removeVehicle")
                sharer = che168Public.Che168Sharer(sessionServer, specServer)
            else:
                logger.debug("che168 removeVehicle")
                sharer = che168.Che168Sharer(sessionServer, specServer)
            (code, msg) = sharer.removeVehicle(message)

        elif website.startswith('58'):
            logger.debug("58 removeVehicle")
#            sharer = fe.FESharer(sessionServer, specServer)
            sharer = feApi.FEApiSharer(sessionServer, specServer)
            (code, msg) = sharer.removeVehicle(message)

        elif website.startswith('ganji'):
            logger.debug("ganji removeVehicle")
            # FIXME: one lock for each user
            # with simpleflock.SimpleFlock("lock/ganji.lock", timeout=2400):
            #     sharer = ganji.GanjiSharer(sessionServer, specServer)
            #     # (code, msg) = sharer.removeVehicle(message)
            #     (code, msg) = run_with_timeout(sharer.removeVehicle, message, 240)
            sharer = ganjiApi.GanjiSharer(sessionServer, specServer)
            (code, msg) = sharer.removeVehicle(share_job=message)

        elif website.startswith('baixing'):
            logger.debug("baixingPublic removeVehicle")
            sharer = baixingApiSharer.BaixingApiSharer(sessionServer, specServer)
            (code, msg) = sharer.removeVehicle(message)

        elif website.startswith('taoche'):
            logger.debug("taoche removeVehicle")
            sharer = taocheApiShare.TaocheSharer(sessionServer, specServer)
            (code, msg) = sharer.removeVehicle(message)

        elif website.startswith('51auto'):
            logger.debug("51autoPublic removeVehicle")
            sharer = FOAutoPublic.FOAutoSharer(sessionServer, specServer)
            # if isPublicAccount(message):
            #     logger.debug("51autoPublic removeVehicle")
            #     sharer = FOAutoPublic.FOAutoSharer(sessionServer, specServer)
            # else:
            #     logger.debug("51auto removeVehicle")
            #     sharer = FOAuto.FOAutoSharer(sessionServer, specServer)
            (code, msg) = sharer.removeVehicle(message)

        elif website.startswith('iautos'):
            logger.debug("iautos removeVehicle")
            sharer = iautos.IautosSharer(sessionServer, specServer)
            (code, msg) = sharer.removeVehicle(message)

        elif website.startswith('hx2car'):
            logger.debug("hx2car")
            # sharer = hx2sc.Hx2scSharer(sessionServer, specServer)
            sharer = hx2scApiShare.Hx2scAPISharer(sessionServer, specServer)
            (code, msg) = sharer.removeVehicle(message)

        elif website.startswith('sohu'):
            logger.debug("sohu removeVehicle")
            sharer = sohu.SohuSharer(sessionServer, specServer)
            (code, msg) = sharer.removeVehicle(message)

        #爱卡汽车
        elif website.startswith('xcar'):
            logger.debug("xcar removeVehicle")
            sharer = xcar.XcarSharer(sessionServer, specServer)
            (code, msg) = sharer.removeVehicle(message)

        elif website.startswith('taobao'):
                logger.debug("taobao removeVehicle")
                sharer = taobaoApiSharer.TaoBaoApiSharer(sessionServer, specServer)
                (code, msg) = sharer.removeVehicle(message)

        #大傻车
        elif website.startswith('foolcars'):
            logger.debug("foolcars removeVehicle")
            sharer = foolcars.FoolcarsSharer(sessionServer, specServer)
            (code, msg) = sharer.removeVehicle(message)

        # 精真估
        elif website.startswith('jingzhengu'):
            logger.debug("jingzhengu shareVehicle")
            sharer = jingzhengu.JZGSharer(sessionServer, specServer)
            (code, msg) = sharer.removeVehicle(message)

        if code == errorcode.SUCCESS:
            logger.debug(msg)
            col.find_and_modify(query={'_id': message['_id']},
                                update={'$set': {'status': 'done'}})
            # history_col.insert({'share_job_id':message['_id'], 'status': 'done',
            #                    'message': msg, 'url': msg, 'create_at': datetime.utcnow()})
            # TODO:根据不同网站返回不同的提示
            history_create(history_col, message['_id'], 'done', u'车辆信息已下架', u'下架成功', None, msg)
        else:
            logger.error(msg)
            '''col.find_and_modify(query={'_id': message['_id']},
                                update={'$set': {'status': 'deferred'}},
                                sort={'create_at': 1})'''
            set_job_deferred(col, message)
            title = u'其它错误'
            if code == errorcode.NETWORK_ERROR:
                title = u'网络错误'
            elif code == errorcode.AUTH_ERROR:
                title = u'帐号/密码错误'
            elif code == errorcode.LOGIC_ERROR:
                title = u'程序错误'
            elif code == errorcode.DATA_ERROR:
                title = u'数据错误'
            elif code == errorcode.SITE_ERROR:
                title = u'网站错误'
            # history_col.insert({'share_job_id':message['_id'], 'status': 'deferred',
            #                    'message': msg, 'url': None, 'create_at': datetime.utcnow()})
            if code == errorcode.DATA_ERROR:
                history_create(history_col, message['_id'], 'deferred', title, msg, 'edit_vehicle', None)
            else:
                history_create(history_col, message['_id'], 'deferred', title, msg, 'restart_job', None)
    except Exception as e:
        logger.error("Exception: " + str(e))
        exc_type, exc_value, exc_traceback = sys.exc_info()
        logger.error(repr(traceback.format_exception(exc_type, exc_value, exc_traceback)))
        col.find_and_modify(query={'_id': message['_id']},
                            update={'$set': {'status': 'deferred'}})
        #history_col.insert({'share_job_id':message['_id'], 'status': 'deferred',
        #                    'message': "网络异常：请重试", 'url': None, 'create_at': datetime.utcnow()})
        history_create(history_col, message['_id'], 'deferred', u'网络异常', u'请重试', 'restart_job', None)
    counter.decrement()


def update_req(col, history_col, message, sessionServer, specServer, counter):
    #####################################################
    # col.find_and_modify(query = {'_id': message['_id']},
    #                   update = { '$set' : {'status': 'deferred'}},
    #                   sort = { 'create_at' : 1})
    #title = u'功能未实现'
    #msg = u'功能暂时未实现，请等下一个版本'
    #history_create(history_col, message['_id'], 'deferred', title, msg, 'restart_job', None)
    #return
    #####################################################
    counter.increment()
    try:
        website = message[u'share_account'].get('website', '')
        log_params = logger.LogParams()
        log_params.set_job_id(str(message['_id']))
        log_params.set_website(website)
        if website.startswith('che168'):
            #True:代运营，启用Public接口，False:大客户启用普通接口，走自己的账号
            if isVipAccount(message):
                logger.debug("che168public update")
                sharer = che168Public.Che168Sharer(sessionServer, specServer)
            else:
                logger.debug("che168 update")
                sharer = che168.Che168Sharer(sessionServer, specServer)
            (code, msg) = sharer.updateVehicle(message)

        elif website.startswith('58'):
            logger.debug("58 update")
#            sharer = fe.FESharer(sessionServer, specServer)
            sharer = feApi.FEApiSharer(sessionServer, specServer)
            (code, msg) = sharer.updateVehicle(message)

        elif website.startswith('ganji'):
            logger.debug("ganji updateVehicle")
            #FIXME: one lock for each user
            # with simpleflock.SimpleFlock("lock/ganji.lock", timeout=2400):
            #     sharer = ganji.GanjiSharer(sessionServer, specServer)
            #     #(code, msg) = sharer.updateVehicle(message)
            #     (code, msg) = run_with_timeout(sharer.updateVehicle, message, 240)
            sharer = ganjiApi.GanjiSharer(sessionServer, specServer)
            (code, msg) = sharer.updateVehicle(share_job=message)

        elif website.startswith('baixing'):
            logger.debug("baixing update")
            sharer = baixingApiSharer.BaixingApiSharer(sessionServer, specServer)
            (code, msg) = sharer.updateVehicle(message)

        elif website.startswith('taoche'):
            logger.debug("taoche update")
            sharer = taocheApiShare.TaocheSharer(sessionServer, specServer)
            (code, msg) = sharer.updateVehicle(message)

        elif website.startswith('51auto'):
            logger.debug("51autoPublic update")
            sharer = FOAutoPublic.FOAutoSharer(sessionServer, specServer)
            # if isPublicAccount(message):
            #     logger.debug("51autoPublic update")
            #     sharer = FOAutoPublic.FOAutoSharer(sessionServer, specServer)
            # else:
            #     logger.debug("51auto update")
            #     sharer = FOAuto.FOAutoSharer(sessionServer, specServer)
            (code, msg) = sharer.updateVehicle(message)

        elif website.startswith('iautos'):
            logger.debug("iautos update")
            sharer = iautos.IautosSharer(sessionServer, specServer)
            (code, msg) = sharer.updateVehicle(message)

        elif website.startswith('hx2car'):
            logger.debug("hx2car update")
            # sharer = hx2sc.Hx2scSharer(sessionServer, specServer)
            sharer = hx2scApiShare.Hx2scAPISharer(sessionServer, specServer)
            (code, msg) = sharer.updateVehicle(message)

        elif website.startswith('sohu'):
            logger.debug("sohu update")
            sharer = sohu.SohuSharer(sessionServer, specServer)
            (code, msg) = sharer.updateVehicle(message)

        #爱卡汽车
        elif website.startswith('xcar'):
            logger.debug("xcar update")
            sharer = xcar.XcarSharer(sessionServer, specServer)
            (code, msg) = sharer.updateVehicle(message)
            
        elif website.startswith('taobao'):
                logger.debug("taobao updateVehicle")
                sharer = taobaoApiSharer.TaoBaoApiSharer(sessionServer, specServer)
                (code, msg) = sharer.updateVehicle(message)

        #大傻车
        elif website.startswith('foolcars'):
            logger.debug("foolcars update")
            sharer = foolcars.FoolcarsSharer(sessionServer, specServer)
            (code, msg) = sharer.updateVehicle(message)

        # 精真估
        elif website.startswith('jingzhengu'):
            logger.debug("jingzhengu shareVehicle")
            sharer = jingzhengu.JZGSharer(sessionServer, specServer)
            (code, msg) = sharer.updateVehicle(message)

        if code == errorcode.SUCCESS:
            logger.debug(msg)
            col.find_and_modify(query={'_id': message['_id']},
                                update={'$set': {'status': 'done'}})
            #history_col.insert({'share_job_id':message['_id'], 'status': 'done',
            #                    'message': msg, 'url': msg, 'create_at': datetime.utcnow()})
            #TODO:根据不同网站返回不同的提示
            history_create(history_col, message['_id'], 'done', u'车辆信息已修改', u'修改成功', None, msg)
        else:
            logger.error(msg)
            '''col.find_and_modify(query={'_id': message['_id']},
                                update={'$set': {'status': 'deferred'}},
                                sort={'create_at': 1})'''
            set_job_deferred(col, message)
            title = u'其它错误'
            if code == errorcode.NETWORK_ERROR:
                title = u'网络错误'
            elif code == errorcode.AUTH_ERROR:
                title = u'帐号/密码错误'
            elif code == errorcode.LOGIC_ERROR:
                title = u'程序错误'
            elif code == errorcode.DATA_ERROR:
                title = u'数据错误'
            elif code == errorcode.SITE_ERROR:
                title = u'网站错误'
            #history_col.insert({'share_job_id':message['_id'], 'status': 'deferred',
            #                    'message': msg, 'url': None, 'create_at': datetime.utcnow()})
            if code == errorcode.DATA_ERROR:
                history_create(history_col, message['_id'], 'deferred', title, msg, 'edit_vehicle', None)
            else:
                history_create(history_col, message['_id'], 'deferred', title, msg, 'restart_job', None)
    except Exception as e:
        logger.error("Exception: " + str(e))
        exc_type, exc_value, exc_traceback = sys.exc_info()
        logger.error(repr(traceback.format_exception(exc_type, exc_value, exc_traceback)))
        col.find_and_modify(query={'_id': message['_id']},
                            update={'$set': {'status': 'deferred'}})
        # history_col.insert({'share_job_id':message['_id'], 'status': 'deferred',
        #                    'message': "网络异常：请重试", 'url': None, 'create_at': datetime.utcnow()})
        history_create(history_col, message['_id'], 'deferred', u'网络异常', u'请重试', 'restart_job', None)
    counter.decrement()


def loop_req(col, history_col, sessionServer, specServer, counter):
    if counter.value() > 8:
        time.sleep(1.0)
        return

    message = col.find_one({'status': 'pending'}, {'_id': True})
    if message is None:
        time.sleep(1.0)
        return

    message = col.find_and_modify(query={'status': 'pending'},
                                  update={'$set': {'status': 'handling'}})

    if message is None:
        time.sleep(1.0)
        return

    # history_col.insert({'share_job_id':message['_id'], 'status': 'handling',
    #                    'message': "正在分发", 'url': None, 'create_at': datetime.utcnow()})
    category = 'send'
    if message.has_key('category'):
        category = message['category']
    if category == 'send':
        history_create(history_col, message['_id'], 'handling', u'正在分发', u'请稍候', None, None)
        Process(target=send_req, args=(col, history_col, message, sessionServer, specServer, counter)).start()
    elif category == 'update':
        history_create(history_col, message['_id'], 'handling', u'正在修改', u'请稍候', None, None)
        Process(target=update_req, args=(col, history_col, message, sessionServer, specServer, counter)).start()
    elif category == 'remove':
        history_create(history_col, message['_id'], 'handling', u'正在下架', u'请稍候', None, None)
        Process(target=remove_req, args=(col, history_col, message, sessionServer, specServer, counter)).start()


if sys.stdout.encoding is None:
    import codecs

    writer = codecs.getwriter("utf-8")
    sys.stdout = writer(sys.stdout)


def cleanup():
    os.killpg(0, signal.SIGKILL)

###############################
##判断账号是代运营，还是大客户(che168)
#true:代运营；False:大客户
###############################
def isVipAccount(message):
    publicAccount_che168 = config.publicAccount_che168
    share_account = message.get("share_account", None)
    if share_account is None:
        logger.debug("get share_account error!")
        return False
    username = share_account.get("username", None)
    if username is None:
        logger.debug("get username error")
        return False

    if username in publicAccount_che168:
        return True
    else:
        return False

################
#判断51走API还是旧接口
################
def isPublicAccount(message):
    website = message.get('share_account').get('website')
    city_code = message.get('vehicle').get('merchant').get('address').get('city_code', None)
    public_account_51auto = ['310100', '220100', '320500', '120100', '450100'] #上海、长春、苏州、天津、南宁
    if '51auto.com' == website and city_code in public_account_51auto:
        return False
    return True


def is_in_fe_clock(share_job):
    city_code = share_job.get('vehicle').get('merchant').get('address').get('city_code', None)
    # 成都、重庆、大连、石家庄
    not_allown_city_list = ['510100', '500100', '210200', '130100']
    if str(city_code) not in not_allown_city_list:
        return True

    mDate = time.strftime("%Y-%m-%d %X", time.localtime())
    print mDate
    mDay = int(mDate[8:10])
    print mDay

    mHour = int(mDate[11:13])
    mMinute = int(mDate[14:16])
    mSecond = int(mDate[17:19])
    print mHour, mMinute, mSecond

    # 29号23点后不发车，以下地区：成都、重庆、大连、石家庄
    mLimit = 29*24*3600 + 23*3600 - 3600
    if mDay*24*3600 + mHour*3600 + mMinute * 60 + mSecond > mLimit:
        return False
    return True

def isInnerSharerClock():
    mDate = time.strftime("%Y-%m-%d %X", time.localtime())
    mHour = int(mDate[11:13])
    mMinute = int(mDate[14:16])
    mSecond = int(mDate[17:19])

    mLimit = 17*3600 - 0.5*3600
    if mHour * 3600 + mMinute * 60 + mSecond < mLimit:
        return True
    return False

# 是否可重发:True:可重发
def isReSendable(shareJob, website):
    vin = shareJob.get('vehicle', None).get('vin', None)
    if vin is None:
        return False, errormsg.VIN_EMPTY
    # share_job_id = shareJob.get('_id', None)

    # conn = pymongo.Connection(config.mongoServer)
    # db = conn.kanche
    vehicle_collection = db.vehicle
    vehicle_collection.ensure_index([("vin", pymongo.ASCENDING)])
    share_job_collection = db.share_job
    share_job_collection.ensure_index([("share_account.website", pymongo.ASCENDING), ("vehicle.vin", pymongo.ASCENDING)])

    num = vehicle_collection.find({"vin": vin}).count()
    if num <= 1:
        return True, ''

    # query = {
    #     "share_account.website": website,
    #     "vehicle.vin": vin
    # }
    # jobs = share_job_collection.find(query).batch_size(30)
    # for job in jobs:
    #     job_id = job.get('_id', None)
    #     category = job.get('category', None)
    #     status = job.get('status', None)
    #     if job_id == share_job_id:
    #         continue
    #     if not (category == 'remove' and status == 'done'):
    #         return False, errormsg.VEHICLE_EXIST

    return False, errormsg.VEHICLE_EXIST

def getExtraUrl(url):
    if url == u'重复车源':
        return None
    o = urlparse(url)
    host = o.netloc
    uri = o.path
    conn = httplib.HTTPConnection(host=host, timeout=10)
    conn.request("GET", url=uri)
    res = conn.getresponse()
    resHeaders = res.getheaders()
    resStatus = res.status
    extra_url = None
    if 301 == resStatus or 302 == resStatus:
        for header in resHeaders:
            if 'location' == header[0]:
                extra_url = header[1]
    return extra_url

def get_url_id(website, innerurl):
    url_id = None
    if innerurl is None:
        return None

    # 58-url:    http://bj.58.com/ershouche/22020712043170x.shtml
    # ganji-extra:   http://bj.ganji.com/ershouche/1551737485x.htm?_rtm=1
    # taoche-extra:    http://dealer.taoche.com/Pages/carsource/carinfo.aspx?ucarid=6002695&isadd=1
    if website.startswith('taoche') or website.startswith('58') or website.startswith('ganji'):
        pReule = r'(\d{6,})'
        url_id = re.compile(pReule).findall(innerurl)
        if len(url_id):
            url_id = url_id[-1]

    elif website.startswith('che168'):
        pReule = r'(\d{6,})'
        url_id_info = re.compile(pReule).findall(innerurl)
        if 2 == len(url_id_info):
            url_id = url_id_info[0] + '#' + url_id_info[1]
    return url_id


class Counter(object):
    def __init__(self, initval=0):
        self.val = Value('i', initval)
        self.lock = Lock()

    def increment(self):
        with self.lock:
            self.val.value += 1

    def decrement(self):
        with self.lock:
            self.val.value -= 1

    def value(self):
        with self.lock:
            return self.val.value

if __name__ == "__main__":
    os.setpgrp()
    atexit.register(cleanup)

    conn = pymongo.Connection(config.mongoServer, tz_aware=True)
    db = conn['kanche']
    col = db['share_job']
    col.ensure_index(
        [("category", pymongo.ASCENDING), ("update_pending", pymongo.ASCENDING), ("status", pymongo.ASCENDING)])
    col.ensure_index(
        [("category", pymongo.ASCENDING), ("remove_pending", pymongo.ASCENDING), ("status", pymongo.ASCENDING)])
    history_col = db['share_job_history']
    procname.setprocname('sharer')
    # checker.start()

    logserver = logger.LogServer()
    sessionServer = session.SessionServer()
    # restarter = restarter.Restarter()
    # che168Refresh = che168Refresh.che168Refresh()
    specServer = spec.SpecServer()
    counter = Counter()
    while True:
        try:
            loop_req(col, history_col, sessionServer, specServer, counter)
        except Exception as e:
            logger.error(str(e))
