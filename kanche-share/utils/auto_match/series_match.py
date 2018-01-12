#!/usr/bin/python
# -*- coding: UTF-8 -*-

import sys
import copy
import jieba
import tfidf
import pymongo
from bson.code import Code
from operator import itemgetter, attrgetter

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

def dict_factory(cursor, row):
    d = {}  
    for idx,col in enumerate(cursor.description):
        r = row[idx]
        if col[0] != "id":
            if type(r) == type(1):
                r = str(r)
        d[col[0]] = r
    return d 


brand_map = {}

conn = pymongo.Connection('127.0.0.1')
db = conn['site_spec']
col = db['external_vehicle_spec']
col2 = db['vehicle_spec_detail']
col3 = db['external_vehicle_series_map']
col4 = db['external_vehicle_brand_map']
col5 = db['external_vehicle_brand_manual_map']
reducer = Code('function(obj, prev){}')

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


def add_brand_map(localBrand, foreignBrand):
    if brand_map.has_key(localBrand):
        brand_map[localBrand].append(foreignBrand)
    else:
        brand_map[localBrand] = [foreignBrand]

def load_brand_map(name):
    '''f = open('./brand_map/%s.txt'%(name))
    ls = f.readlines()
    for l in ls:
        if l.startswith("//"):
            continue
        (localBrand, foreignBrand) = l.split("=")
        #localBrands = localBrand.decode("utf-8").split("#")
        foreignBrands = foreignBrand.split("|")
        #print "---" + localBrand
        for foreignBrand in foreignBrands:
            if foreignBrand.endswith(":Y"):
                #print "\t" + foreignBrand[:-2]
                add_brand_map(localBrand.decode("utf-8"), foreignBrand[:-2].decode("utf-8"))
    f.close()
    #print brand_map'''
    res = {}
    results = col4.find({"external_brand.site": name})
    for result in results:
        l = result['local_brand']['brand'] + '#' + result['local_brand']['vendor']
        e = result['external_brand']['brand'] + '#' + result['external_brand']['vendor']
        res[l] = e
    manual_results = col5.find({"external_brand.site": name})
    for result in manual_results:
        l = result['local_brand']['brand'] + '#' + result['local_brand']['vendor']
        e = result['external_brand']['brand'] + '#' + result['external_brand']['vendor']
        res[l] = e
    for l in res:
        print l + '====' + res[l]
        add_brand_map(l, res[l])

def build_tfidf(foreignBrands):
    datas = []
    website = sys.argv[1]
    for foreignBrand in foreignBrands:
        (brand, vendor) = foreignBrand.split(u"#")
        #print brand.encode("utf-8") + ":" + maker.encode("utf-8")

        results = col.group(key={"brand.name":1, "vendor.name":1, "series.name": 1 },
                         condition={"site": website, "brand.name": brand, "vendor.name": vendor},
                         initial={}, reduce=reducer)
        for r in results:
            data = []
            data.append(r['brand.name'])
            data.append(r['vendor.name'])
            data.append(r['series.name'])
            datas.append(data)
    tf = tfidf.tfidf()
    for data in datas:
        k = "#".join(data)
        n = "#".join(data)
        c = word_bag(n)
        tf.addDocument(k, c)
    return tf

BRAND_KEY = "details.2"
VENDOR_KEY = "details.1"
SERIES_KEY = "details.3"
MODEL_KEY = "details.5"
NATIONAL_KEY = "details.21"

def save_map(l, f, site):
    l = l.split('#')
    f = f.split('#')
    if len(l) != 4 and len(f) != 3:
        print "wrong data"
        return
    series = {
        'brand': l[0],
        'vendor': l[1],
        'series': l[2],
        'model': l[3]
    }
    external_series = {
        'site': site,
        'brand': f[0],
        'vendor': f[1],
        'series': f[2]
    }
    col3.update({"local_series": series, "external_series.site": site},
                {"local_series": series, "external_series": external_series}, upsert = True)

def match_tfidf(r, tf):
    k = "#".join((r[BRAND_KEY], r[VENDOR_KEY], r[SERIES_KEY], r[MODEL_KEY]))
    n = "#".join((r[BRAND_KEY], r[VENDOR_KEY], r[SERIES_KEY], r[MODEL_KEY], r[NATIONAL_KEY]))
    c = word_bag(n)
    sim = tf.similarities(c)
    sim = sort_sim(sim)
    #print k + "===" + sim[0][0]
    if len(sim) > 0:
        save_map(k, sim[0][0], sys.argv[1])
    #for s in sim:
    #    print s[0]
    #modelId = sim[0][0].split("#")[0]
    #save_map(levelId, sys.argv[1], modelId, n, sim[0][0])

def load_tfidf(localBrand, foreignBrands):
    tfidf_table = build_tfidf(foreignBrands)
    print "foreignBrands:"
    for b in foreignBrands:
        print "\t" + b
    print "localBrand:"
    print "\t" + localBrand
    (brand, maker) = localBrand.split(u"#")
    results = col2.group(key={BRAND_KEY:1, VENDOR_KEY:1, SERIES_KEY: 1, MODEL_KEY: 1, NATIONAL_KEY:1},
                         condition={BRAND_KEY: brand, VENDOR_KEY: maker},
                         initial={}, reduce=reducer)
    for result in results:
        match_tfidf(result, tfidf_table)

def run_brand_map():
    for k in brand_map:
        load_tfidf(k, brand_map[k])

if __name__ == "__main__":
    load_brand_map(sys.argv[1])
    run_brand_map()
