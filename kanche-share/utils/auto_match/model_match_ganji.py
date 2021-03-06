#!/usr/bin/python
# -*- coding: UTF-8 -*-

import jieba
import re
import tfidf
from operator import itemgetter, attrgetter
import sys
import copy
import pymongo
from bson.code import Code

if sys.stdout.encoding is None: 
    import codecs 
    writer = codecs.getwriter("utf-8") 
    sys.stdout = writer(sys.stdout) 

more_words = {
    u'Cabrio': [u'敞篷'],
    u'Coupe': [u'硬顶'],
    u'CVT': [u'无级'],
    u'无级': [u'自动'],
}

thesaurus = {
    u'手自': u'自动',
    u'MT': u'手动',
    u'A/MT': u'自动',
    u'AT': u'自动',
    u'基本': u'标准'
}

ignore_keyword = [u'型', u'款', u'版', u' ', u'(', u')', u'（', u'）', u'一体', u'#', u'[', u']']

series_map = {}
conn = pymongo.Connection('127.0.0.1')
db = conn['site_spec']
external_spec_col = db['external_vehicle_spec']
local_spec_col = db['vehicle_spec_detail']
series_map_col = db['external_vehicle_series_map']
series_manual_map_col = db['external_vehicle_series_manual_map']
model_map_col = db['external_vehicle_model_map']
reducer = Code('function(obj, prev){}')

BRAND_KEY = "details.2"
VENDOR_KEY = "details.1"
SERIES_KEY = "details.3"
MODEL_KEY = "details.5"
SALENAME_KEY = "details.7"
NATIONAL_KEY = "details.21"

jieba.load_userdict("custom_dict.txt")

def sort_sim(sim):
    return sorted(sim, key=itemgetter(1), reverse=True)

def thesaurus_correct(w):
    if thesaurus.has_key(w):
        return [thesaurus[w].upper()]
    if more_words.has_key(w):
        n = copy.copy(more_words[w])
        n.append(w.upper())
        return n
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


def add_series_map(localBrand, foreignBrand):
    #if series_map.has_key(localBrand):
    #    series_map[localBrand].append(foreignBrand)
    #else:
    #    series_map[localBrand] = [foreignBrand]
    #if series_map.has_key(localBrand):
    #    print series_map[localBrand] + '============' + foreignBrand
    series_map[localBrand] = foreignBrand

def del_series_map(localBrand):
    if series_map.has_key(localBrand):
        del series_map[localBrand]

def load_series_map(site):
    res = series_map_col.find({"external_series.site": site})
    for r in res:
        local_series = r['local_series']
        external_series = r['external_series']
        localSeries = u"#".join([local_series['brand'], local_series['vendor'], local_series['series'], local_series['model']])
        foreignSeries = u'#'.join([external_series['brand'], external_series['vendor'], external_series['series']])
        add_series_map(localSeries, foreignSeries)
    res = series_manual_map_col.find({"external_series.site": site})
    for r in res:
        local_series = r['local_series']
        external_series = r['external_series']
        localSeries = u"#".join([local_series['brand'], local_series['vendor'], local_series['series'], local_series['model']])
        foreignSeries = u'#'.join([external_series['brand'], external_series['vendor'], external_series['series']])
        if external_series['brand'] == '':
            del_series_map(localSeries)
        else:
            add_series_map(localSeries, foreignSeries)
    #f.close()
    #print brand_map

def detectEngine(title):
    r = re.search("(?P<engine>[0-9]\.[0-9])", title)
    if r is None:
        return ''
    return r.group('engine')

def getExternalEngine(external_spec):
    engine = external_spec['summary'].get('engine', '')
    if engine == '' or engine is None:
        return ''
        #return detectEngine(external_spec['model']['name'])
    return detectEngine(engine)
    #return engine

#def getExternalTurbo(external_spec):

def build_tfidf(foreignBrand):
    datas = []
    rs = []
    merge_to_series = False
    (brand, vendor, series) = foreignBrand.split(u"#")
    #print brand.encode("utf-8") + ":" + maker.encode("utf-8")

    res = external_spec_col.find({'site': sys.argv[1],'brand.name': brand, "vendor.name": vendor, "series.name": series})
    for r in res:
        if r['model']['key'] == '0':
            merge_to_series = True
        data = [r['model']['id'], r['brand']['name'], r['vendor']['name'], r['series']['name'], r['model']['name'], r['model'].get('year', '') or '']
        datas.append(data)
        rs.append(r)
    if merge_to_series:
        data = datas[0]
        k = "#".join(data)
        return k

    #engine_dict = {}
    #for i in xrange(len(rs)):
    #    e = getExternalEngine(rs[i])
    #    if len(datas) == 0:
    #        #print foreignBrand
    #        return None

    tf = tfidf.tfidf()
    for data in datas:
        k = "#".join(data)
        n = "#".join(data[1:])
        c = word_bag(n)
        tf.addDocument(k, c)
    return tf

def save_map(levelId, site, modelId, localModel, foreignModel):
    m = {
        'level_id': levelId,
        'site': site,
        'model_id': modelId,
        'local_model': localModel,
        'external_model': foreignModel
    }
    model_map_col.update({'site': site, 'level_id': levelId}, m, upsert = True)

def match_tfidf(r, tf):
    if tf is None:
        return
    if type(tf) == type('') or type(tf) == type(u''):
        #print tf
        levelId = r[0]
        n = " ".join([r[2] or "", r[1] or "", r[3] or "", r[5] or "", r[7] or "", r[9] or "", r[21] or ""])
        modelId = tf.split("#")[0]
        save_map(levelId, sys.argv[1], modelId, n, tf)
        return
    levelId = r[0]
    #print "levelId = " + levelId
    n = " ".join([r[2] or "", r[1] or "", r[3] or "", r[5] or "", r[7] or "", r[9] or "", r[21] or ""])
    c = word_bag(n)
    sim = tf.similarities(c)
    sim = sort_sim(sim)
    #print n  + "===" + sim[0][0] + "---" + str(sim[0][1])
    modelId = sim[0][0].split("#")[0]
    save_map(levelId, sys.argv[1], modelId, n, sim[0][0])

def load_tfidf(localBrand, foreignBrand):
    tfidf_table = build_tfidf(foreignBrand)
    #print "foreignBrands:"
    #for b in foreignBrands:
    #    print "\t" + b
    #print "localBrand:"
    #print "\t" + localBrand
    (brand, vendor, series, model) = localBrand.split(u"#")
    res = local_spec_col.find({BRAND_KEY: brand, VENDOR_KEY: vendor, SERIES_KEY: series, MODEL_KEY: model})

    results = {}
    for ra in res:
        r = ra['details']
        n = " ".join([r[2] or "", r[1] or "", r[3] or "", r[5] or "", r[7] or "", r[9] or "", r[21] or ""])
        if results.has_key(n):
            if r[0] > results[n][0]:
                results[n] = r
        else:
            results[n] = r
    for k in results.keys():
        match_tfidf(results[k], tfidf_table)

def run_series_map():
    for k in series_map:
        load_tfidf(k, series_map[k])

if __name__ == "__main__":
    load_series_map(sys.argv[1])
    run_series_map()