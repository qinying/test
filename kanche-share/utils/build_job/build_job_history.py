#!/usr/bin/python
# -*- coding: UTF-8 -*-

import copy
import json
import zlib
import pymongo
from bson.objectid import ObjectId

conn = pymongo.Connection('127.0.0.1')
db = conn['kanche']
share_job_col = db['share_job']
history_col = db['share_job_history']
USER_ID = "53cc8bb9010000690278e085"
msg = None

def history_create(share_job_id, status, title, content, restart_method, url):
    obj = {'share_job_id': share_job_id, 'status': status, 'title': title,
                        'content': content, 'message': title + "：" + content, 'create_at': datetime.utcnow()}
    if restart_method is not None:
        obj['restart_method'] = restart_method
    if url is not None:
        obj['url'] = url
    history_col.insert(obj)

def build_job_history_waiting(idx, share_job):
	share_job.update({"_id": share_job['id'], {"status": "waiting"}})
	history_create(history_col, message['_id'], 'waiting', u'任务创建成功', u'等待审核', None, msg)

def build_job_history_pending(idx, share_job):
	share_job.update({"_id": share_job['id'], {"status": "waiting"}})	
	history_create(history_col, message['_id'], 'waiting', u'任务创建成功', u'等待审核', None, msg)
	history_create(history_col, message['_id'], 'waiting', u'审核通过', u'等待分发', None, msg)

def build_job_history_handling(idx, share_job):
	share_job.update({"_id": share_job['id'], {"status": "handling"}})	
	history_create(history_col, message['_id'], 'waiting', u'任务创建成功', u'等待审核', None, msg)
	history_create(history_col, message['_id'], 'pending', u'审核通过', u'等待分发', None, msg)
	history_create(history_col, message['_id'], 'handling', u'任务启动', u'正在分发', None, msg)

def build_job_history_done(idx, share_job):
	share_job.update({"_id": share_job['id'], {"status": "done"}})	
	history_create(history_col, message['_id'], 'waiting', u'任务创建成功', u'等待审核', None, msg)
	history_create(history_col, message['_id'], 'waiting', u'审核通过', u'等待分发', None, msg)
	history_create(history_col, message['_id'], 'handling', u'任务启动', u'正在分发', None, msg)
	history_create(history_col, message['_id'], 'waiting', u'已经分发到网站', u'等待对方网站审核', None, "http://www.qq.com")

def build_job_history_deferred1(idx, share_job):
	share_job.update({"_id": share_job['id'], {"status": "deferred"}})	
	history_create(history_col, message['_id'], 'waiting', u'任务创建成功', u'等待审核', None, msg)
	history_create(history_col, message['_id'], 'waiting', u'审核通过', u'等待分发', None, msg)
	history_create(history_col, message['_id'], 'handling', u'任务启动', u'正在分发', None, msg)
	history_create(history_col, message['_id'], 'deferred', u'车型库匹配失败', u'请手动选择', "select_external_spec", msg)

def build_job_history_deferred2(idx, share_job):
	share_job.update({"_id": share_job['id'], {"status": "deferred"}})	
	history_create(history_col, message['_id'], 'waiting', u'任务创建成功', u'等待审核', None, msg)
	history_create(history_col, message['_id'], 'waiting', u'审核通过', u'等待分发', None, msg)
	history_create(history_col, message['_id'], 'handling', u'任务启动', u'正在分发', None, msg)
	history_create(history_col, message['_id'], 'deferred', u'网络异常', u'请重试', "restart_job", msg)

def build_job_history_deferred3(idx, share_job):
	share_job.update({"_id": share_job['id'], {"status": "deferred"}})	
	history_create(history_col, message['_id'], 'waiting', u'任务创建成功', u'等待审核', None, msg)
	history_create(history_col, message['_id'], 'waiting', u'审核通过', u'等待分发', None, msg)
	history_create(history_col, message['_id'], 'handling', u'任务启动', u'正在分发', None, msg)
	history_create(history_col, message['_id'], 'deferred', u'车辆信息不正确', u'请修改后重试', "edit_vehicle", msg)

def build_job_history_rejected(idx, share_job):
	share_job.update({"_id": share_job['id'], {"status": "rejected"}})	
	history_create(history_col, message['_id'], 'waiting', u'任务创建成功', u'等待审核', None, msg)
	history_create(history_col, message['_id'], 'rejected', u'审核部通过', u'图片违规', "edit_vehicle", msg)
	history_create(history_col, message['_id'], 'rejected', u'审核部通过', u'文字违规', "edit_vehicle", msg)
	history_create(history_col, message['_id'], 'rejected', u'审核部通过', u'价格违规', "edit_vehicle", msg)



def do_build_job_history(idx, share_job):
	if idx == 0:
		build_job_history_waiting(idx, share_job)
	if idx == 1:
		build_job_history_pending(idx, share_job)
	if idx == 2:
		build_job_history_handling(idx, share_job)
	if idx == 3:
		build_job_history_done(idx, share_job)
	if idx == 4:
		build_job_history_deferred1(idx, share_job)
	if idx == 5:
		build_job_history_deferred2(idx, share_job)
	if idx == 6:
		build_job_history_deferred3(idx, share_job)
	if idx == 7:
		build_job_history_rejected(idx, share_job)

def build_job_history():
	share_job_list = share_job.find({"user_id": ObjectId("53cc8bb9010000690278e085")})
	for i in xrange(len(share_job_list)):
		do_build_job_history(i, share_job_list[i])

if __name__ == "__main__":
	build_job_history()