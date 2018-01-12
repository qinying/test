#!python-env/bin/python
# -*- coding: UTF-8 -*-

import top.api, httplib, re, json, datetime, errorcode, errormsg, urllib, config, pymongo
from cStringIO import StringIO
from base import BaseSharer

__author__ = 'david.li'


class TaoBaoApiSharer(BaseSharer):
    def __init__(self, sessionServer, specServer):
        super(TaoBaoApiSharer, self).__init__(sessionServer, specServer)
        self.appkey = "23283236"
        self.secret = "be8a19a5f8ef65e88af73fad474a625c"
        self.sessionkey = "61022000126e02872dc547af6f573ecb90af024c25f8b2f2675163005"
        self.refresh_token = "610140011a575a895e5572a723404e8479d114516b33b8d2675163005"
        self.url = 'gw.api.taobao.com'
        self.cid = 50050566
        self.port = 80
        self.paramDict = json.load(open('data/taobao_dict.json'))

    def getUrl(self, pUrl, timeout = 10, headers = {}):
        iList = pUrl.split('/')
        if iList[0].lower() == 'http:':
            iDomain = iList[2]
            iUrl = '/'.join(iList[3:])
        else:
            iDomain = iList[0]
            iUrl = '/'.join(iList[1:])
        iUrl = '/' + iUrl
        iConn = httplib.HTTPConnection(iDomain, timeout = timeout)
        iConn.request("GET", iUrl, headers = headers)
        #print '++\t', pUrl
        return iConn.getresponse()
    
    def postUrl(self, pUrl, pFormdata, timeout = 10, headers = {}):
        iList = pUrl.split('/')
        if iList[0].lower() == 'http:':
            iDomain = iList[2]
            iUrl = '/'.join(iList[3:])
        else:
            iDomain = iList[0]
            iUrl = '/'.join(iList[1:])
        iUrl = '/' + iUrl
        iConn = httplib.HTTPConnection(iDomain, timeout = timeout)
        iConn.request("POST", iUrl, urllib.urlencode(pFormdata), headers = headers)
        #print '++\t', pUrl
        return iConn.getresponse()

    def getErrDict(self, e):
        if isinstance(e, top.api.base.TopException):
            return "{'code':'%s','msg':'%s','subcode':'%s','submsg':'%s','apphost':'%s','host':'%s'}"%(e.errorcode,e.message,e.subcode,e.submsg,e.application_host,e.service_host)
        else:
            raise e

    #修改
    def itemUpdate(self, pId, pPrice=None, pDesc=None, pWireless_desc=None):
        req=top.api.ItemUpdateRequest(self.url, self.port)
        req.set_app_info(top.appinfo(self.appkey, self.secret))
         
        req.num_iid = pId
        if pPrice is not None:
            req.price = pPrice
        if pDesc is not None:
            req.desc = pDesc
        if pWireless_desc is not None:
            req.wireless_desc = pWireless_desc

        try:
            resp = req.getResponse(self.sessionkey)
            return resp['item_update_response']['item']['num_iid']
        except Exception,e:
            return self.getErrDict(e)

    #删除
    def itemDelete(self, pId):
        req = top.api.ItemDeleteRequest(self.url, self.port)
        req.set_app_info(top.appinfo(self.appkey, self.secret))
        req.num_iid = pId
        try:
            resp = req.getResponse(self.sessionkey)
            return resp['item_delete_response']['item']['num_iid']
        except Exception,e:
            return self.getErrDict(e)

    #下架
    def itemDelisting(self, pId):
        req = top.api.ItemUpdateDelistingRequest(self.url, self.port)
        req.set_app_info(top.appinfo(self.appkey, self.secret))
        req.num_iid = pId
        try:
            resp = req.getResponse(self.sessionkey)
            return resp['item_update_delisting_response']['item']['num_iid']
        except Exception,e:
            return self.getErrDict(e)

    #上传主图图片
    def itemImgUpload(self, pId, pUrl, pIndex, pMajor = 'false'):
        iRes = self.getUrl(pUrl)
        if iRes.status != 200:
            return -1, iRes.status, iRes.getheaders()
            
        img = StringIO(iRes.read())
        req = top.api.ItemImgUploadRequest(self.url, self.port)
        req.set_app_info(top.appinfo(self.appkey, self.secret))
        
        req.num_iid = pId
        req.position = pIndex
        req.image = top.api.FileItem('%s_%s.jpg'%(pId, pIndex), img)
        req.is_major = pMajor
        try:
            resp= req.getResponse(self.sessionkey)
            return True, resp['item_img_upload_response']['item_img']['url']
        except Exception,e:
            return False, self.getErrDict(e), 0
    
    #上传图片到图片空间
    def pictureUpload(self, pUrl):
        iRes = self.getUrl(pUrl)
        if iRes.status != 200:
            return -1, iRes.status, iRes.getheaders()
            
        img = StringIO(iRes.read())
        
        req=top.api.PictureUploadRequest(self.url,self.port)
        req.set_app_info(top.appinfo(self.appkey,self.secret))
         
        req.picture_category_id=0
        req.img=top.api.FileItem('a.jpg', img)
        req.image_input_title=pUrl.split('/')[-1]
        try:
            resp= req.getResponse(self.sessionkey)
            return True, resp['picture_upload_response']['picture']['picture_path']
        except Exception,e:
            return False, self.getErrDict(e), 0
    
    def pictureGet(self, pUrl):
        req=top.api.PictureGetRequest(self.url,self.port)
        req.set_app_info(top.appinfo(self.appkey,self.secret))

        req.urls=pUrl
        try:
            resp= req.getResponse(self.sessionkey)
            iResult = []
            iList = resp['picture_get_response']['pictures']['picture']
            for iItem in iList:
                iResult.append(str(iItem['picture_id']))
            return iResult
        except Exception,e:
            print e
            return []
    
    #删除图片
    def pictureDelete(self, pId):
        req=top.api.PictureDeleteRequest(self.url,self.port)
        req.set_app_info(top.appinfo(self.appkey,self.secret))
         
        req.picture_ids=pId
        try:
            resp= req.getResponse(self.sessionkey)
            print(resp)
        except Exception,e:
            print(e)
    
     
    def uploadPics(self, pId, pGallery, pMemo):
        if pGallery is None:
            return
        
        iPicList = []
        iResult = ['<img src="https://img.alicdn.com/imgextra/i1/2675163005/TB27NtfjpXXXXXCXXXXXXXXXXXX_!!2675163005.jpg"/>',pMemo]
        iIndex = 1
        iList = pGallery['photos']
        for iItem in iList:
            if iIndex == 1:
                f, iUrl = self.itemImgUpload(pId, iItem['url'], pIndex=iIndex, pMajor = 'true')
            elif iIndex<6:
                f, iUrl = self.itemImgUpload(pId, iItem['url'], pIndex=iIndex)
            else:
                f, iUrl = self.pictureUpload(iItem['url'])
            print f, iUrl
            if f:
                iIndex += 1
                iResult.append('<img src="%s" width="750"/>'%iUrl)
                iPicList.append(iUrl)
        
        self.itemUpdate(pId = pId, pDesc = '<hr/>'.join(iResult), pWireless_desc = '<hr/>'.join(iResult))
        return self.pictureGet(','.join(iPicList))
    
    def getExternalCitys(self, pAddress):
        return self.paramDict['city'].get(pAddress['city_code'], ['', ''])
        
    def getManualCategory(self, shareJob):
        vehicleSpec = shareJob.get('vehicle_spec_detail')['details']
        vehicle = shareJob.get("vehicle", None)
        user = vehicle.get('user', None)
        address = user.get('address', None)
        
        iResult = []
        #vtype
        for k, v in self.paramDict['vtype'].items():
            if k in '%s %s'%(vehicleSpec[11], vehicleSpec[12]):
                iResult.append(v)
        #area
        if address['city_code'] in self.paramDict['area'].keys():
            iResult.append(self.paramDict['area'][address['city_code']])
        #price
        iPrice = self.getPrice(shareJob)
        for k, v in self.paramDict['price'].items():
            if len(v) == 2:
                if iPrice >= v[0] and iPrice < v[1]:
                    iResult.append(k)
            else:
                if iPrice >= v[0]:
                    iResult.append(k)
        #age
        iYear = datetime.datetime.now().year - vehicle["vehicle_date"]["registration_date"].year
        for k, v in self.paramDict['age'].items():
            if len(v) == 2:
                if iYear >= v[0] and iYear < v[1]:
                    iResult.append(k)
            else:
                if iYear >= v[0]:
                    iResult.append(k)
        #hot
        if vehicle['spec']['brand'] in self.paramDict['hot'].keys():
            iResult.append(self.paramDict['hot'][vehicle['spec']['brand']])
        #brand
        if vehicle['spec']['brand'] in self.paramDict['brand'].keys():
            iResult.append(self.paramDict['brand'][vehicle['spec']['brand']])
            
        return ','.join(iResult)

    def doLogin(self, username, password):
        raise NotImplementedError()

    def shareVehicle(self, shareJob):
        #raise NotImplementedError()
        mongoServer = config.mongoServer
        conn = pymongo.Connection(mongoServer)
        db = conn.kanche

        externalVehicleSpec = shareJob.get('external_vehicle_spec')
        externalVehicleSpec = db.external_vehicle_spec.find_one({'site':'taobao.com','model.id':externalVehicleSpec['model']['id']})
        if externalVehicleSpec is None:
            return errorcode.DATA_ERROR, 'external_vehicle_spec error'
            
        vehicle = shareJob.get("vehicle", None)
        spec = vehicle.get("spec", None)
        user = vehicle.get('user', None)
        address = user.get('address', None)
        
        req=top.api.ItemAddRequest(self.url, self.port)
        req.set_app_info(top.appinfo(self.appkey, self.secret))
        
        #宝贝数量
        req.num = 1
        #一口价
        req.type = "fixed"
        #二手
        req.stuff_status = "second"
        #类目ID
        req.cid = self.cid
        #是否有发票
        req.has_invoice = 'true'
        #是否有保修
        req.has_warranty = 'false'
        #是否承诺退换货服务
        req.sell_promise = 'false'
        #是否支持7天无理由退货
        req.newprepay = 0
        #是否拍下减库存,1支持;2取消支持;0集市卖家默认支持
        req.sub_stock = 2
        #是否橱窗推荐
        req.has_showcase = 'false'
        
        req.price = self.getPrice(shareJob)
        req.title = (str(spec['brand']) + str(spec['series']) + str(spec['sale_name'])).decode('utf8')[:30]
        iCity = re.sub(u'蒙古族?|回族|傈僳族|景颇族|白族|傣族|壮族|朝鲜族|土家族|苗族|藏族|羌族|彝族|布依族|侗族|哈尼族|哈萨克|柯尔克孜', '', address.get('city_name', ''))
        req.location_state = re.sub(u'省|市|(?:壮族|回族|维吾尔)?自治区$', '', address.get('province_name', ''))
        req.location_city = re.sub(u'市|盟|地区|自治州$', '', iCity)
        #req.location_state="北京"
        #req.location_city="北京"
        
        #品牌 车系 年款 车款 排放标准 所在地
        iProps = ['10265769:20213']
        iProps.append(externalVehicleSpec.get('brand', None).get('id', ''))
        iProps.append(externalVehicleSpec.get('series', None).get('id', ''))
        iProps.append(externalVehicleSpec.get('model', None).get('year_id', ''))
        iProps.append(externalVehicleSpec.get('model', None).get('id', ''))
        iProps = iProps + self.getExternalCitys(address)
        req.props = ';'.join(iProps)
        
        #vin码 公里数 初登日期
        iInput_pids = ['143410077', '30259', '20207674']
        iInput_str = [vehicle.get('vin', ''), '%s万公里'%(float(vehicle['summary']['mileage'])/10000), vehicle["vehicle_date"]["registration_date"].strftime("%Y-%m")]
        req.input_pids = ','.join(iInput_pids)
        req.input_str = ','.join(iInput_str)
        
        #卖点
        req.sell_point = vehicle["desc"]["detail"][:150]
        #自定义分类
        req.seller_cids = self.getManualCategory(shareJob)
        
        req.desc = req.title
        #req.wireless_desc = '<span></span>'
        
        try:
            resp= req.getResponse(self.sessionkey)
            iId = resp['item_add_response']['item']['num_iid']
            iMemo = self.getContentVal(shareJob, Symbol='<br/>')
            iMemo += datetime.datetime.now().strftime('#%Y-%m-%d %X')
            iPicList = self.uploadPics(iId, vehicle.get("gallery", None), iMemo)
            return errorcode.SUCCESS, 'https://item.taobao.com/item.htm?id=%s#%s' % (iId, ','.join(iPicList))
        except Exception,e:
            return errorcode.DATA_ERROR, self.getErrDict(e)
        

    def updateVehicle(self, shareJob):
        iUrl = shareJob.get("url", '').split('#')
        urlForApp = re.findall('id=(\d+)', iUrl[0])
        if len(urlForApp) > 0:
            iResult = self.itemUpdate(urlForApp[0], pPrice=self.getPrice(shareJob))
            if iResult == int(urlForApp[0]):
                return errorcode.SUCCESS, "success"
            else:
                return errorcode.SITE_ERROR, iResult
        else:
            return errorcode.DATA_ERROR, errormsg.VEHICLE_URL_EMPTY

    def removeVehicle(self, shareJob):
        iUrl = shareJob.get("url", '').split('#')
        urlForApp = re.findall('id=(\d+)', iUrl[0])
        if len(urlForApp) > 0:
            iResult = self.itemDelete(urlForApp[0])
            if iResult == int(urlForApp[0]):
                self.pictureDelete(iUrl[-1])
                return errorcode.SUCCESS, "success"
            else:
                return errorcode.SITE_ERROR, iResult
        else:
            return errorcode.DATA_ERROR, errormsg.VEHICLE_URL_EMPTY















