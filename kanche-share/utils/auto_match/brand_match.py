#!/usr/bin/python
# -*- coding: UTF-8 -*-

import sys 
import pymongo
import jieba
import tfidf
from datetime import datetime
from bson.code import Code
from operator import itemgetter, attrgetter

if sys.stdout.encoding is None: 
    import codecs 
    writer = codecs.getwriter("utf-8") 
    sys.stdout = writer(sys.stdout) 

tables = {}
trans = {}

conn = pymongo.Connection('127.0.0.1')
db = conn['site_spec']
col = db['external_vehicle_spec']   #抓取的
col2 = db['vehicle_spec_detail']    #力扬
col3 = db['external_vehicle_brand_map'] #映射表
reducer = Code('function(obj, prev){}')

jieba.load_userdict("custom_dict.txt")

thesaurus_o = {
    u'手自': u'自动',
    u'无级': u'自动',
    u'MT': u'手动',
    u'AT': u'自动',
    u'jeep': u'吉普',
    u'CVT': u'无极',
    u'Cabrio': u'敞篷',
    u'Tesla': u'特斯拉',
    u'迈凯轮': u'迈凯伦',
    u'Coupe': u'硬顶',
    u'基本': u'标准'
}

thesaurus = {}

for k in thesaurus_o.keys():
    thesaurus[k.upper()] = thesaurus_o[k]

ignore_keyword = [u'型', u'款', u'版', u'汽车', u' ', u'(', u')', u'（', u'）', u'一体', u'#', u'[', u']']

def sort_sim(sim):
    return sorted(sim, key=itemgetter(1), reverse=True)

def thesaurus_correct(w):
    if thesaurus.has_key(w.upper()):
        return [thesaurus[w.upper()].upper()]
    return [w.upper()]

def replace_year(y):
    if len(y) != 2:
        return y
    if y[0] == u'0':
        return u'20' + y
    if y[0] == u'9':
        return u'19' + y
    return y

def word_bag(s):
    ws = jieba.cut(s)
    d = {}
    for w in ws:
        if w == u' ':
            continue
        for r in ignore_keyword:
            w = w.replace(r, u'')

        if len(w) == 0:
            continue
        w = replace_year(w)
        nws = thesaurus_correct(w)
        for nw in nws:
            d[nw] = True
    return d.keys()

def save_brand_map(local_brand, local_vendor, external_brand, external_vendor):
    site = sys.argv[1]
    item = {
        'local_brand': {
            'brand': local_brand,
            'vendor': local_vendor
        },
        'external_brand' :{
            'brand': external_brand,
            'vendor': external_vendor,
            'site': site
        },
        'update_at': datetime.utcnow()
    }

    col3.update({"local_brand": item["local_brand"], "external_brand.site": site}, item, upsert = True)

def build_trans(tf):
    results = col2.group(key={"details.2": 1, "details.1":1, "details.21":1}, condition={}, initial={}, reduce=reducer)

    for result in results:
        #print result
        n = "#".join([result['details.2'], result['details.1'], result['details.21']])
        c = word_bag(n)
        sim = tf.similarities(c)
        sim = sort_sim(sim)
        print n + '=' + sim[0][0] + '|' + sim[1][0] + '|' + sim[2][0] + '|' + sim[3][0] + '|' + sim[4][0]
        externals = sim[0][0].split('#')
        save_brand_map(result['details.2'], result['details.1'], externals[0], externals[1])

if __name__ == '__main__':

    website = sys.argv[1]   
    results = col.group(key={"brand.name":1, "vendor.name":1}, condition={"site": website}, initial={}, reduce=reducer)
    tf = tfidf.tfidf()

    for result in results:
        #print result
        n = result['brand.name'] + "#" + result['vendor.name']
        #print n
        c = word_bag(n)
        #for a in c:
        #    print "\t" + a
        tf.addDocument(n, c)
    
    build_trans(tf)

