__author__ = 'jesse'

import pymongo
from datetime import datetime

accountData = {
    ('18610205279', 'mengqian', '2252', '883BDFF2F85BD69169F5DAB2BBBDE63856692F1D', 0, 100),
    ('13681210639', 'asasas123', '3264', '3E092DC2551D3D81B67358A791546D26C1E2608A', 0, 100),
    ('18730634308', 'asasas123', '3266', 'B2803C00D1DBEEEDEBB08345EF89DADF9C8C212C', 0, 100),
    ('13810790418', 'asasas123', '3267', '0D958F7719EA50E58BF149CC27AD0ABFB2C8180E', 0, 100),
    ('18610842384', 'asasas123', '3268', '5C00B9933D40F4C561D95C585F8461F9CA5FE0AC', 0, 100),
    ('15043096668', 'asasas123', '3617', 'C8C115C2AFA97A9ED66111C9F137115ABFA920D7', 0, 100),
}

mongoServer = "mongodb://localhost:27017"
conn = pymongo.Connection(mongoServer)
db = conn.kanche
col = db.baixing_api_key

result = col.ensure_index([("username", pymongo.ASCENDING)], unique=True)
now = datetime.now()
for (username, password, app_key, app_secret, send_times, limit_times) in accountData:
    key = {"username": username}
    data = {"username": username,
            "password": password,
            "app_key": app_key,
            "app_secret": app_secret,
            "send_times": send_times,
            "limit_times": limit_times,
            "create_at": now}
    res = col.update(key, {'$set': data}, multi=True, upsert=True)

conn.close()