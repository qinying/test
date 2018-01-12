#!/usr/bin/python
# -*- coding: UTF-8 -*-

import httplib
import urllib
import copy
import json
import zlib
from urlparse import urlparse

headers = {
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Accept-Encoding": "gzip,deflate,sdch",
    "Accept-Language": "en-US,en;q=0.8,zh-CN;q=0.6,zh-TW;q=0.4",
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_8_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/35.0.1916.114 Safari/537.36"
}

HOST = "127.0.0.1:9000"
TOKEN = "6204d77b1da63c4366d54ac6befc7cc99865c759"
USER_ID = "53cc8bb9010000690278e085"

def decodeBody(headers, body):
    for header in headers:
        if header[0].lower() == 'content-encoding':
            if header[1].lower().count('gzip') > 0:
                return zlib.decompress(body, 16+zlib.MAX_WBITS)
    return body

def share_send_one(conn, vehicle, share_account_ids):
    vehicle_id = vehicle["id"]

    post_data = {
        "vehicleId": vehicle_id,
        "accountIdList": share_account_ids
    }
    headers['Content-Type'] = 'application/json'
    conn.request("POST", "/share/job/send", json.dumps(post_data), headers = headers)
    res = conn.getresponse()
    resHeaders = res.getheaders()
    resStr = decodeBody(resHeaders, res.read())
    resObj = json.loads(resStr)
    #print resObj

def share_send(conn, vehicles, share_accounts):
    for vehicle in vehicles:
        share_account_ids = []
        for share_account in share_accounts:
            share_account_id = share_account["id"]
            share_account_ids.append(share_account_id)
        share_send_one(conn, vehicle, share_account_ids)

def do_build_job():
    headers['X-AUTH-TOKEN'] = TOKEN
    conn = httplib.HTTPConnection(HOST, timeout=10)
    conn.request("GET", "/vehicle/list?page=0&size=1000&userId=" + USER_ID, headers = headers)
    res = conn.getresponse()
    resHeaders = res.getheaders()
    resStr = decodeBody(resHeaders, res.read())
    resObj = json.loads(resStr)
    vehicles =  resObj['items']

    conn.request("GET", "/share/account/list?page=0&size=1000&userId=" + USER_ID, headers = headers)
    res = conn.getresponse()
    resHeaders = res.getheaders()
    resStr = decodeBody(resHeaders, res.read())
    resObj = json.loads(resStr)
    share_accounts =  resObj['items']

    share_send(conn, vehicles, share_accounts)

if __name__ == '__main__':
    do_build_job()
