#!/usr/bin/python
# -*- coding: UTF-8 -*-

import jieba
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

series_map = {}
conn = pymongo.Connection('127.0.0.1')
db = conn['site_spec']
external_spec_col = db['external_vehicle_spec']
local_spec_col = db['vehicle_spec_detail']
series_map_col = db['external_vehicle_series_map']
model_map_col = db['external_vehicle_model_map']
reducer = Code('function(obj, prev){}')

BRAND_KEY = "details.2"
VENDOR_KEY = "details.1"
SERIES_KEY = "details.3"
MODEL_KEY = "details.5"
SALENAME_KEY = "details.7"
NATIONAL_KEY = "details.21"

def add_series_map(localBrand, foreignBrand):
    if series_map.has_key(localBrand):
        series_map[localBrand].append(foreignBrand)
    else:
        series_map[localBrand] = [foreignBrand]

def load_series_map(site):
    res = series_map_col.find({"external_series.site": site})
    for r in res:
        local_series = r['local_series']
        external_series = r['external_series']
        localSeries = u"#".join([local_series['brand'], local_series['vendor'], local_series['series'], local_series['model']])
        foreignSeries = u'#'.join([external_series['brand'], external_series['vendor'], external_series['series']])
        add_series_map(localSeries, foreignSeries)
    #f.close()
    #print brand_map

'''def build_tfidf(foreignBrands):
    datas = []
    for foreignBrand in foreignBrands:
        (brand, vendor, series) = foreignBrand.split(u"#")
        #print brand.encode("utf-8") + ":" + maker.encode("utf-8")

        res = external_spec_col.find({'site': sys.argv[1],'brand.name': brand, "vendor.name": vendor, "series.name": series})
        for r in res:
            data = [r['model']['id'], r['brand']['name'], r['vendor']['name'], r['series']['name'], r['model']['name'], r['model']['year'] or '']
            datas.append(data)
    tf = tfidf.tfidf()
    for data in datas:
        k = "#".join(data)
        n = "#".join(data[1:])
        c = word_bag(n)
        tf.addDocument(k, c)
    return tf
'''

def save_map(levelId, site, modelId, localModel, foreignModel):
    m = {
        'level_id': levelId,
        'site': site,
        'model_id': modelId,
        'is_sure': True,
        'local_model': localModel,
        'external_model': foreignModel
    }
    model_map_col.update({'site': site, 'level_id': levelId}, m, upsert = True)

def save_map_not_found(level_id, site, dbg_msg):
    m = {
        'level_id': level_id,
        'site': site,
        'model_id': "",
        'local_model': dbg_msg,
        'external_model': ""
    }
    model_map_col.update({'site': site, 'level_id': level_id}, m, upsert = True)

def check_level_id_model_like(level_id, dbg_msg):
    found = False
    level_id_like = level_id[:-5] + ".*"
    res = external_spec_col.find({"site": "hx2car.com", "model.key": {"$regex": level_id_like}})
    if res.count() > 0:
        found = True
    if found is False:
        #print level_id + '\t' + dbg_msg
        save_map_not_found(level_id, "hx2car.com", dbg_msg)
    return res

def check_level_id_like(level_id, dbg_msg):
    found = False
    level_id_like = level_id[:-2] + ".*"
    res = external_spec_col.find({"site": "hx2car.com", "model.key": {"$regex": level_id_like}})
    if res.count() > 0:
        found = True
    if found is False:
        return check_level_id_model_like(level_id, dbg_msg)
        #print level_id + '\t' + dbg_msg
    return res

def check_level_id(level_id, level_ids, dbg_msg):
    found = False
    for cur_level_id in level_ids:
        res = external_spec_col.find({"site": "hx2car.com", "model.key": cur_level_id})
        if res.count() > 0:
            found = True
    if found is False:
        #print level_id + '\t' + dbg_msg
        res = check_level_id_like(level_id, dbg_msg)
    if res.count() > 0:
        r = res[0]
        save_map(level_id, "hx2car.com", r['model']['id'], dbg_msg, "#".join([r['brand']['name'], r['vendor']['name'], r['model']['name']]))

def load_level_ids(brand, vendor, series, model, salename):
    level_ids = []
    res = local_spec_col.find({BRAND_KEY: brand, VENDOR_KEY: vendor, SERIES_KEY: series, MODEL_KEY: model, SALENAME_KEY: salename})

    results = {}
    for ra in res:
        r = ra['details']
        level_id = r[0]
        level_ids.append(level_id)
    level_ids.sort(reverse=True)
    return level_ids

def load_series():
    res = local_spec_col.group(key={BRAND_KEY:1, VENDOR_KEY:1, SERIES_KEY: 1, MODEL_KEY: 1},
                         condition={},
                         initial={}, reduce=reducer)
    for r in res:
        load_models(r[BRAND_KEY], r[VENDOR_KEY], r[SERIES_KEY], r[MODEL_KEY])

def load_models(brand, vendor, series, model):
    res = local_spec_col.group(key={BRAND_KEY:1, VENDOR_KEY:1, SERIES_KEY: 1, MODEL_KEY: 1, SALENAME_KEY: 1},
                         condition={BRAND_KEY: brand, VENDOR_KEY: vendor, SERIES_KEY: series, MODEL_KEY: model},
                         initial={}, reduce=reducer)

    for r in res:
        level_ids = load_level_ids(r[BRAND_KEY], r[VENDOR_KEY], r[SERIES_KEY], r[MODEL_KEY], r[SALENAME_KEY])
        if len(level_ids) < 1:
            continue
        dbg_msg = '#'.join([r[BRAND_KEY], r[VENDOR_KEY], r[SERIES_KEY], r[MODEL_KEY], r[SALENAME_KEY]])
        check_level_id(level_ids[0], level_ids, dbg_msg)

if __name__ == "__main__":
    load_series()
