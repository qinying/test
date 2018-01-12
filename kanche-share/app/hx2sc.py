#!/usr/bin/python
# -*- coding: UTF-8 -*-
import httplib
import urllib
import copy
import re
import tz
import time
import json
import zlib
import lxml.html
import subprocess
import logger
import errorcode
import errormsg
import string
from decimal import *
import resize
from StringIO import StringIO
from urlparse import urlparse
from dt8601 import IsoDate
from base import BaseSharer

#'kcdavid','78787788'
# 'tangmash','tangmash'
#"beijingkankanche","20140901"
data = {
    "share_account": {
        "username": "kcdavid",
        "password": "78787788"
    },
    "vehicle": {

    }
}

publicAccount =  {
    "username": "beijingkankanche",
    "password": "20140901"
}


class Hx2scSharer(BaseSharer):


    def __init__(self,sessionServer, specServer):
        print "-----"
        super(Hx2scSharer, self).__init__(sessionServer, specServer)
        print "--------"

    def doLogin(self, username, password):
        result = False
        host = "www.hx2car.com"
        uri = "/sys/gologin.htm"
        codec = "utf8"
        conn = httplib.HTTPConnection(host, timeout=10)
        conn.request("GET", uri, headers=self.headers)
        getResponse = conn.getresponse()
        getHeaders = getResponse.getheaders()
        print "login: "
        print getHeaders
        self.setCookies(getHeaders)
        getHtml = zlib.decompress(getResponse.read(), 16 + zlib.MAX_WBITS).decode(codec)

        salt = re.compile(r'\t*var salt\="([^"]+)";').findall(getHtml.encode('utf8'))

        # test for mac add '/usr/local/bin/node',
        child = subprocess.Popen(['./app/jsfunc/hx2sc_md5.js',password,salt[0]], stdin=subprocess.PIPE, stdout=subprocess.PIPE, shell=False)
        salt = child.stdout.read()
        print "salt:"+salt
        formData = {"login_name": username, "password_m": password, "isSave": 1, 'password':salt.strip()}
        headers = copy.copy(self.headers)
        headers["Content-type"] = "application/x-www-form-urlencoded"
        headers["Referer"] = 'http://' + host + uri
        headers["Origin"] = 'http://' + host
        headers["Connection"] = 'keep-alive'
        headers['Content-Length'] = len(urllib.urlencode(formData))

        conn.request("POST", uri, urllib.urlencode(formData), headers=headers)
        postResponse = conn.getresponse()
        postHeaders = postResponse.getheaders()
        postResult = self.decodeBody(postHeaders, postResponse.read())

        if postResponse.status == 302 and str(postResponse.getheader('location')).strip()=='http://www.hx2car.com/user/member.htm':
            self.headers['Cookie'] = postResponse.getheader('set-cookie')
            logger.debug("--postHeaders--login--\n" + str(postHeaders))
            postResponse.read()
            result = True
        else:
            result = False
            conn.close()
        return result

    def shareVehicle(self, shareJob):
        shareAccount = shareJob.get("share_account", None)
        if shareAccount is None:
            return errorcode.AUTH_ERROR, ""
        if shareAccount.get('account_type', None) == 'public':
            shareAccount['username'] = publicAccount['username']
            shareAccount['password'] = publicAccount['password']

        logger.debug("hx2sc shareVehicle")
        #cookies = self.sessionServer.getSession('hx2sc', shareAccount['username'])
        cookies = None
        logger.debug('-------session cookies---------\n' + str(cookies))
        #print json.dumps(cookies)
        if cookies is None:
            logger.debug("do login hx2sc")
            res = self.doLogin(shareAccount['username'], shareAccount['password'])
            if not res:
                logger.error("login error")
                return errorcode.AUTH_ERROR, errormsg.LOGIN_FAIL
            self.sessionServer.setSession('hx2sc', shareAccount['username'], self.cookies)
        else:
            self.cookies = cookies
            ks = self.cookies.keys()
            cookie_list = []
            for k in ks:
                cookie_list.append(k + '=' + self.cookies[k])
            self.headers['Cookie'] = string.join(cookie_list, '; ')
        logger.debug(str(self.headers))

        vehicle = shareJob.get("vehicle", None)
        if vehicle is None:
            logger.debug("vehicle missing")
            return errorcode.DATA_ERROR, errormsg.VEHICLE_EMPTY
        user = vehicle.get("user", None)
        if user is None:
            return errorcode.DATA_ERROR, errormsg.USER_EMPTY

        #spec = vehicle.get("spec", None)
        spec = shareJob.get("external_vehicle_spec", None)
        if spec is None:
            logger.debug("external spec missing")
            return errorcode.DATA_ERROR, errormsg.EXTERNAL_SPEC_EMPTY
        gallery = vehicle.get("gallery", None)
        if gallery is None:
            logger.debug("gallery missing")
            return errorcode.DATA_ERROR, u"无照片"

        photoList = self.uploadPics(gallery.get("photos", []))
        logger.debug(photoList)
        #photoJson = json.dumps(photoList)
        print "---------------------------"
        #print photoList
        tmp = self.postVehicle(shareJob, photoList, '')
        print tmp
        (success, msg) = tmp
        if success:
            return errorcode.SUCCESS, msg
        else:
            return errorcode.SITE_ERROR, msg

    def postVehicle(self,shareJob,photoList, queryId):
        vehicle = shareJob['vehicle']
        exvehicle = shareJob['external_vehicle_spec']
        if len(exvehicle):
            headers = copy.copy(self.headers)
            conn = httplib.HTTPConnection('www.hx2car.com', timeout=10)
            #headers['Content-Type'] = 'application/x-www-form-urlencoded'
            url = '/car/savecar.htm'

            strColor = vehicle['summary']['color']
            colorTable = {"black":"1","red":"2","blue":"3","white":"4","green":"5",
                          "yellow":"6","silvery":"7","gray":"8","orange":"9","champagne":"11"}
            colorCode = colorTable.get(strColor, "10")
            useyear = str(self.getDate(shareJob, 1).year)
            usemonth = str(self.getDate(shareJob, 1).month)
            inspectionYear = str(self.getDate(shareJob, 2).year)
            inspectionMonth = str(self.getDate(shareJob, 2).month)
            insuranceYear = str(self.getDate(shareJob, 3).year)
            insuranceMonth = str(self.getDate(shareJob, 3).month)
            if '' == inspectionYear:
                inspectionYear = '2016'
            if '' == inspectionMonth:
                inspectionMonth = '6'

            vehicle = shareJob.get('vehicle', None)
            vehicle_date = vehicle.get('vehicle_date', None)
            commercial_insurance_expire_date = vehicle_date.get('commercial_insurance_expire_date', None)
            if commercial_insurance_expire_date is None or '' == commercial_insurance_expire_date:
                insuranceYear = '2016'
                insuranceMonth = '6'
            else:
                insuranceYear = commercial_insurance_expire_date.year
                insuranceMonth = commercial_insurance_expire_date.month

            boundaryHeader = '----WebKitFormBoundaryMTZqIeHv5hJeC1Bm'
            boundary = '--' + boundaryHeader
            # formData = "desc="+str(self.getContentVal_hx2car(shareJob))
            Symbol = "\n"
            lateral = "——"*40
            formData = "desc="+str(self.getContentVal(shareJob=shareJob, Symbol=Symbol, lateral=lateral))
            formData += "&tradePrice="+""
            formData += "&newCarPrice="+""
            #是否是新车
            formData += "&isNewCar="+"1"
            #是否7天包退15天包换
            formData += "&isReplacement="+"1"
            #强险
            formData += "&insuranceYear="+str(insuranceYear)
            formData += "&insuranceMonth="+str(insuranceMonth)
            #年检有效期
            formData += "&inspectionYear="+str(inspectionYear)
            formData += "&inspectionMonth="+str(inspectionMonth)
            formData += "&qamonths="+""
            formData += "&qakilometer="+""
            formData += "&deliveryYear="+""
            formData += "&deliveryMonth="+""
            formData += "&transferNumber="+""
            formData += "&carKeys="+""
            formData += "&maintenanceLevel="+""
            formData += "&bodyLevel="+"--"
            formData += "&jushiLevel="+"--"
            formData += "&paintLevel="+"--"
            formData += "&accidentLevel="+"--"
            formData += "&faultLevel="+"--"
            formData += "&standard="+"0"
            formData += "&saleUser="+""
            formData += "&salePhone="+""


            tmp = {}
            #print formData
            for a in formData.split("&"):
                b = a.split('=')
                #print b
                tmp[b[0]] = b[1]
            formstr = json.dumps(tmp, ensure_ascii=False)
            #formData = formData.encode('utf8')
            #print formData
            formDatastr = ""
            formDatastr += boundary + "\r\n" + 'Content-Disposition: form-data; name="carKind"\r\n\r\n' + "367" + '\r\n'
            formDatastr += boundary + "\r\n" + 'Content-Disposition: form-data; name="tempPhone"\r\n\r\n'+""+ '\r\n'
            formDatastr += boundary + "\r\n" + 'Content-Disposition: form-data; name="strPhones"\r\n\r\n'+""+ '\r\n'

            iQueryId = queryId.encode('utf8') if type(queryId) == unicode else queryId
            if iQueryId.decode('utf8').isnumeric():
                formDatastr += boundary + "\r\n" + 'Content-Disposition: form-data; name="id"\r\n\r\n'+iQueryId+ '\r\n'

            formDatastr += boundary + "\r\n" + 'Content-Disposition: form-data; name="bigType"\r\n\r\n'+"1"+ '\r\n'
            formDatastr += boundary + "\r\n" + 'Content-Disposition: form-data; name="useYear"\r\n\r\n'+useyear+ '\r\n'
            formDatastr += boundary + "\r\n" + 'Content-Disposition: form-data; name="useMonth"\r\n\r\n'+usemonth+ '\r\n'
            formDatastr += boundary + "\r\n" + 'Content-Disposition: form-data; name="otherBrand"\r\n\r\n'+""+ '\r\n'
            formDatastr += boundary + "\r\n" + 'Content-Disposition: form-data; name="carSrial_0"\r\n\r\n'+str(exvehicle['brand']['name'])+ '\r\n'
            formDatastr += boundary + "\r\n" + 'Content-Disposition: form-data; name="parSerial"\r\n\r\n'+str(exvehicle['brand']['id'])+ '\r\n'
            formDatastr += boundary + "\r\n" + 'Content-Disposition: form-data; name="brandStr"\r\n\r\n'+str(exvehicle['series']['name'])+ '\r\n'
            formDatastr += boundary + "\r\n" + 'Content-Disposition: form-data; name="sonSerial"\r\n\r\n'+str(exvehicle['series']['id'])+ '\r\n'
            formDatastr += boundary + "\r\n" + 'Content-Disposition: form-data; name="typeStr"\r\n\r\n'+str(exvehicle['model']['name'])+ '\r\n'
            formDatastr += boundary + "\r\n" + 'Content-Disposition: form-data; name="carType"\r\n\r\n'+str(exvehicle['model']['id'])+ '\r\n'
            formDatastr += self.getPostPhoto(photoList)
            formDatastr += boundary + "\r\n" + 'Content-Disposition: form-data; name="money"\r\n\r\n' + str(Decimal(self.getPrice(shareJob)) / Decimal(10000))+ '\r\n'
            formDatastr += boundary + "\r\n" + 'Content-Disposition: form-data; name="usedYears"\r\n\r\n'+"1"+ '\r\n'
            formDatastr += boundary + "\r\n" + 'Content-Disposition: form-data; name="journey"\r\n\r\n'+str(Decimal(vehicle['summary']['mileage']) / Decimal(10000)) + '\r\n'
            formDatastr += boundary + "\r\n" + 'Content-Disposition: form-data; name="color"\r\n\r\n'+ str(colorCode)+ '\r\n'
            formDatastr += boundary + "\r\n" + 'Content-Disposition: form-data; name="carAuto"\r\n\r\n'+"1"+ '\r\n'
            formDatastr += boundary + "\r\n" + 'Content-Disposition: form-data; name="oilWear"\r\n\r\n'+"1"+ '\r\n'
            formDatastr += boundary + "\r\n" + 'Content-Disposition: form-data; name="carForuse"\r\n\r\n'+"1"+ '\r\n'
            formDatastr += boundary + "\r\n" + 'Content-Disposition: form-data; name="insuranceYear"\r\n\r\n'+str(insuranceYear)+ '\r\n'
            formDatastr += boundary + "\r\n" + 'Content-Disposition: form-data; name="insuranceMonth"\r\n\r\n'+str(insuranceMonth)+ '\r\n'
            formDatastr += boundary + "\r\n" + 'Content-Disposition: form-data; name="inspectionYear"\r\n\r\n'+str(inspectionYear)+ '\r\n'
            formDatastr += boundary + "\r\n" + 'Content-Disposition: form-data; name="inspectionMonth"\r\n\r\n'+str(inspectionMonth)+ '\r\n'
            formDatastr += boundary + "\r\n" + 'Content-Disposition: form-data; name="transfer"\r\n\r\n'+"1"+ '\r\n'
            formDatastr += boundary + "\r\n" + 'Content-Disposition: form-data; name="mortgage"\r\n\r\n'+"0"+ '\r\n'
            formDatastr += boundary + "\r\n" + 'Content-Disposition: form-data; name="standard"\r\n\r\n'+"0"+ '\r\n'
            formDatastr += boundary + "\r\n" + 'Content-Disposition: form-data; name="desc"\r\n\r\n'+str(self.getContentVal(shareJob, Symbol, lateral)) + '\r\n'
            formDatastr += boundary + "\r\n" + 'Content-Disposition: form-data; name="file1"\r\n\r\n'+""+ '\r\n'
            formDatastr += boundary + "\r\n" + 'Content-Disposition: form-data; name="saleUser"\r\n\r\n'+""+ '\r\n'
            formDatastr += boundary + "\r\n" + 'Content-Disposition: form-data; name="salePhone"\r\n\r\n'+""+ '\r\n'
            formDatastr += boundary + "\r\n" + 'Content-Disposition: form-data; name="seats"\r\n\r\n'+""+ '\r\n'
            formDatastr += boundary + "\r\n" + 'Content-Disposition: form-data; name="license"\r\n\r\n' + "" + '\r\n'
            formDatastr += boundary + "\r\n" + 'Content-Disposition: form-data; name="deliveryYear"\r\n\r\n'+"选择年份"+ '\r\n'
            formDatastr += boundary + "\r\n" + 'Content-Disposition: form-data; name="deliveryMonth"\r\n\r\n'+"选择月份"+ '\r\n'
            formDatastr += boundary + "\r\n" + 'Content-Disposition: form-data; name="bodyLevelStr"\r\n\r\n'+""+ '\r\n'
            formDatastr += boundary + "\r\n" + 'Content-Disposition: form-data; name="jushiLevelStr"\r\n\r\n'+""+ '\r\n'
            formDatastr += boundary + "\r\n" + 'Content-Disposition: form-data; name="paintLevelStr"\r\n\r\n'+""+ '\r\n'
            formDatastr += boundary + "\r\n" + 'Content-Disposition: form-data; name="tradePrice"\r\n\r\n'+""+ '\r\n'
            formDatastr += boundary + "\r\n" + 'Content-Disposition: form-data; name="newCarPrice"\r\n\r\n'+"1"+ '\r\n'
            formDatastr += boundary + "\r\n" + 'Content-Disposition: form-data; name="accidentLevelStr"\r\n\r\n'+""+ '\r\n'
            formDatastr += boundary + "\r\n" + 'Content-Disposition: form-data; name="faultLevelStr"\r\n\r\n'+""+ '\r\n'
            formDatastr += boundary + "\r\n" + 'Content-Disposition: form-data; name="memo"\r\n\r\n'+formstr+ '\r\n'
            formDatastr += boundary + '--'
            formData = formDatastr


            if type(formData == type(u'')):
                formData = formData.encode('utf-8')

            #print headers
            #print len(headers)
            headers['Content-Type'] = 'multipart/form-data; boundary=' + boundaryHeader
            headers['Content-Length'] = len(formData)
            headers['Host'] = 'www.hx2car.com'
            headers['Origin'] = 'http://www.hx2car.com'
            if iQueryId.decode('utf8').isnumeric() :
                headers['Referer'] = 'http://www.hx2car.com/car/editcar.htm?id='+iQueryId

            conn.request("POST", url, formData, headers=headers)
            res = conn.getresponse()
            #print res.getheaders()
            postHeader = res.getheaders()
            logger.debug("--postHeaders--\n" + str(postHeader))
            logger.debug("--post--\n" + res.read())
            conn.close()
            #pageResult = self.decodeBody(res.getheaders(), res.read())

            #print pageResult
            #and str(res.getheader('location')).strip()=='http://www.hx2car.com/user/member.htm'
            print res.status
            if res.status == 200:
                #print "success"
                #time.sleep(10)
                '''
                htmlId = self.reUrl(shareJob)
                if len(htmlId):
                    url = "http://www.hx2car.com/details/" + htmlId + ".htm"
                    print url
                    return True, url
                else:
                    return False, "fachefail"
                    '''
                if iQueryId.decode('utf8').isnumeric() :
                    return True, shareJob.get("url", None)
                else:
                    return True, self.reUrl(shareJob)


            else:
                return False, u"超过限制"
        else:
            return False, u"数据错误"


    def postPic(self,content, index):
        headers = copy.copy(self.headers)
        conn = httplib.HTTPConnection('www.hx2car.com', timeout=10)
        boundaryHeader = "----pluploadboundary1408600538106"
        headers['Referer'] = 'http://www.hx2car.com/resource/web/common/swf/plupload.flash.swf?9143'
        headers['Origin'] = 'http://www.hx2car.com/'
        headers["Content-Type"] = "multipart/form-data; boundary=" + boundaryHeader
        #headers['Content-Type'] = 'application/x-www-form-urlencoded'
        url = '/car/upload.json'
        #image = '/home/tangmash/pic/fm.jpg'
        img = StringIO(content)
        smallImg = StringIO()
        resize.resize(img, (600, 600), False, smallImg)
        content = smallImg.getvalue()
        #print content
        #content = smallImg.getvalue()
        picname = "aa" + str(index) + ".jpg"
        boundary = "--" + boundaryHeader
        picForm = boundary + '\r\n' + 'Content-Disposition: form-data; name="name"\r\n\r\n'
        picForm += picname + "\r\n"
        picForm += boundary + '\r\n' + 'Content-Disposition: form-data; name="file"; filename="' + picname +'\r\nContent-Type: image/jpeg\r\n\r\n'
        picForm += str(content) + '\r\n'
        picForm += boundary + "--"
        #print picForm
        #formData = {"name":"fm.jpg","file":content}
        headers['Content-Length'] = len(picForm)
        #print headers
        conn.request("POST", url,picForm, headers = headers)
        res = conn.getresponse()
        htmlres = res.read()
        htmlres = json.loads(htmlres)
        #print "------------------"
        #print htmlres
        return htmlres["uploadobject"]["relativePath"]

    def uploadPics(self, photos):
        photo_list = []
        photos = photos[:8]  #最多10张图片
        index = 1
        for photo in photos:
            url = photo.get("url", None)
            #print url
            if url is None:
                continue
            o = urlparse(url)
            host = o.netloc
            uri = o.path

            #print content
            upload = self.sessionServer.getUpload('hx2sc', uri)
            logger.debug("upload=" + str(upload))
            if upload != None:
                res = upload
                #print res
            else:
                host = 'pic.kanche.com'
                # if host == 'pic.kanche.com':
                #     host = 'kanche-pic.qiniudn.com'
                conn = httplib.HTTPConnection(host, timeout=10)
                headers = copy.copy(self.headers)
                del headers['Cookie']
                headers['Referer'] = "www.kanche.com"
                headers['Host'] = host

                conn.request("GET", uri, headers = headers)
                res = conn.getresponse()
                content = res.read()
                conn.close()
                #print content

                res = self.postPic(content,index)
                #photo_list.append(res)
                if res != None:
                    self.sessionServer.setUpload('hx2car', uri, res)
                if res != None:
                    photo_list.append(res)
                index = index + 1
        #print photo_list
        return photo_list

    # ==========================================
    # remove Vehicle from management desk
    # ==========================================
    def removeVehicle(self,shareJob):
        print '\tgo into removeVehicle'
        shareAccount = shareJob.get("share_account", None)
        if shareAccount is None:
            return errorcode.AUTH_ERROR, ""
        if shareAccount.get('account_type', None) == 'public':
            shareAccount['username'] = publicAccount['username']
            shareAccount['password'] = publicAccount['password']

        cookies = self.sessionServer.getSession('hx2car', shareAccount['username'])
        '''
        if cookies is None:
            result = self.doLogin(shareAccount['username'], shareAccount['password'])
            if not result:
                return errorcode.AUTH_ERROR, errormsg.LOGIN_FAIL
            self.sessionServer.setSession('hx2car', shareAccount['username'], self.cookies)
        else:
            self.cookies = cookies
            ks = self.cookies.keys()
            cookie_list = []
            for k in ks:
                cookie_list.append(k + '=' + self.cookies[k])
            self.headers['Cookie'] = str(string.join(cookie_list, '; '))
        '''
        result = self.doLogin(shareAccount['username'], shareAccount['password'])
        if not result:
            return errorcode.AUTH_ERROR, errormsg.LOGIN_FAIL
        self.sessionServer.setSession('hx2car', shareAccount['username'], self.cookies)


        urlForApp = shareJob.get("url", None)
        if urlForApp is None or len(urlForApp) == 0:
            return errorcode.DATA_ERROR, errormsg.VEHICLE_URL_EMPTY
        print '\turlForApp:',urlForApp
        #http://www.hx2car.com/details/140403238
        pRule = r'([0-9]{9})'
        pageList = re.compile(pRule).findall(urlForApp)
        if len(pageList):
            pageId = pageList[0]
        else:
            logger.debug("error:get pageId failed!")
            pageId = ""

        #1. POST http://www.hx2car.com/car/deal.json
        # formdate:carId=140403238&money=
        url = "/car/deal.json"
        headers = copy.copy(self.headers)

        headers["Content-Length"] = "22"
        headers["Connection"] = "keep-alive"
        headers["Host"] = "www.hx2car.com"
        headers["Referer"] = "http://www.hx2car.com/car/vehiclelist.htm"
        headers["Content-Type"]= "  application/x-www-form-urlencoded; charset=UTF-8"
        #headers['Cookie']['hx2car_web'] = 'YmVpamluZ2thbmthbmNoZSctLS0nOGJjNDk3ZmM5Y2UzNTM0OGI0MzlhODVhYzU5OWVjYjQ='

        print "\theaders:",headers
        formData = "carId=" + pageId.encode('utf-8')
        formData += "&money="
        print "\tformData:",formData

        conn = httplib.HTTPConnection("www.hx2car.com", timeout=10)
        conn.request("POST", url,formData, headers=headers)
        res = conn.getresponse()
        print '\tQequest cookies:',self.headers['Cookie']
        self.setCookies(res.getheaders())
        resHtml = res.read()
        resStatus = res.status
        print  "\tresStatus:",resStatus
        result = self.decodeBody(res.getheaders(), resHtml)
        print "result:",result
        conn.close()
        print 'end...'
        if resStatus == 200 and result.count('处理成功'):
            logger.debug("remove success")
            return errorcode.SUCCESS, ""
        else:
            return errorcode.SITE_ERROR, errormsg.VEHICLE_REMOVE_FAIL
        logger.debug("hx2car remove failed \ngotoApp=" + result)



    '''@staticmethod
    def makePhotos(photoList):
        photos = []
        for photo in photoList:
            photos.append(photo)
        return ",".join(photos)'''


    @staticmethod
    def getDate(shareJob, type):
        typeDict = {
            1: "registration_date",
            2: "inspection_date",
            3: "compulsory_insurance_expire_date"
        }
        d = IsoDate.from_iso_string('2015-05-01T00:00:00.000+08:00')
        vehicle = shareJob.get("vehicle", None)
        if vehicle is not None:
            vehicleDate = vehicle.get('vehicle_date', None)
            if vehicleDate is not None:
                mDate = vehicleDate.get(typeDict[type], None)
                if mDate is not None:
                    d = mDate.astimezone(tz.HKT)
                    if 3 == type:
                        mDate = vehicleDate.get('inspection_date', None)
                        d = mDate.astimezone(tz.HKT)
        return d

    def checkUrlId(self, pageId, jobId):
        headers = copy.copy(self.headers)
        conn = httplib.HTTPConnection('www.hx2car.com', timeout=10)
        url = "/details/" + pageId
        conn.request("GET", url, headers=headers)
        res1 = conn.getresponse()
        strhtml = self.decodeBody(res1.getheaders(), res1.read())
        url = 'http://www.hx2car.com'+url
        return url,strhtml.find(jobId)>0

    ##
    #get url from sent vehicle list
    ##
    def reUrl(self, shareJob):
        exvehicle = shareJob['external_vehicle_spec']
        vehicle = shareJob.get('vehicle', None)
        headers = copy.copy(self.headers)
        conn = httplib.HTTPConnection('www.hx2car.com', timeout=10)
        url = "/car/vehiclelist.htm"
        headers['Host'] = 'www.hx2car.com'
        headers['Referer'] = 'http://www.hx2car.com/user/member.htm'
        conn.request("GET", url, headers=headers)
        res1 = conn.getresponse()
        strhtml = self.decodeBody(res1.getheaders(), res1.read())
        #print strhtml
        hxs = lxml.html.fromstring(strhtml.decode('utf8'))
        htmlurl = hxs.xpath(u'//div[@class="w778"]/@id')
        time.sleep(0.8)
        for urlId in htmlurl:
            pageId,checkFlag = self.checkUrlId(urlId, str(vehicle['_id']))
            print pageId,checkFlag,str(vehicle['_id'])
            if checkFlag:
                return pageId
        return ""

    def getPostPhoto(self,photoList):
        photostr = ""
        str = "------WebKitFormBoundaryMTZqIeHv5hJeC1Bm" + "\r\n" + 'Content-Disposition: form-data; name="picUrls"\r\n\r\n'
        for photo in photoList:
            photostr += str + photo + '\r\n'
        #print photostr
        return photostr

    def getHtmlImglist(self, queryId):
        conn = httplib.HTTPConnection("www.hx2car.com", timeout=10)
        location_url = "/car/editcar.htm?id="+queryId
        updateHeader = copy.copy(self.headers)
        conn.request("GET", location_url, headers = self.headers)
        res = conn.getresponse()
        updateResult = self.decodeBody(res.getheaders(), res.read())
        conn.close()

        imgList = re.findall('pics=JSON\.decode\(([^\)]+)', updateResult)
        if len(imgList):
            imgList = json.loads(imgList[0][1:-1])
        else:
            imgList = []

        return imgList

    def updateVehicle(self, shareJob):
        shareAccount = shareJob.get("share_account", None)
        if shareAccount is None:
            return errorcode.AUTH_ERROR, ""
        if shareAccount.get('account_type', None) == 'public':
            shareAccount['username'] = publicAccount['username']
            shareAccount['password'] = publicAccount['password']

        logger.debug("hx2sc shareVehicle")
        #cookies = self.sessionServer.getSession('hx2sc', shareAccount['username'])
        cookies = None
        logger.debug('-------session cookies---------\n' + str(cookies))
        #print json.dumps(cookies)
        if cookies is None:
            logger.debug("do login hx2sc")
            res = self.doLogin(shareAccount['username'], shareAccount['password'])
            if not res:
                logger.error("login error")
                return errorcode.AUTH_ERROR, errormsg.LOGIN_FAIL
            self.sessionServer.setSession('hx2sc', shareAccount['username'], self.cookies)
        else:
            self.cookies = cookies
            ks = self.cookies.keys()
            cookie_list = []
            for k in ks:
                cookie_list.append(k + '=' + self.cookies[k])
            self.headers['Cookie'] = string.join(cookie_list, '; ')
        logger.debug(str(self.headers))

        vehicle = shareJob.get("vehicle", None)
        if vehicle is None:
            logger.debug("vehicle missing")
            return errorcode.DATA_ERROR, errormsg.VEHICLE_EMPTY
        user = vehicle.get("user", None)
        if user is None:
            return errorcode.DATA_ERROR, errormsg.USER_EMPTY

        #spec = vehicle.get("spec", None)
        spec = shareJob.get("external_vehicle_spec", None)
        if spec is None:
            logger.debug("external spec missing")
            return errorcode.DATA_ERROR, errormsg.EXTERNAL_SPEC_EMPTY
        '''
        gallery = vehicle.get("gallery", None)
        if gallery is None:
            logger.debug("gallery missing")
            return errorcode.DATA_ERROR, "无照片"

        photoList = self.uploadPics(gallery.get("photos", []))
        '''
        urlForApp = shareJob.get("url", None)
        if urlForApp is None or urlForApp=='':
            return errorcode.DATA_ERROR, '车辆url为空'

        queryId = re.findall('\d+', urlForApp)[-1]
        if queryId is None:
            return errorcode.DATA_ERROR, "车辆ID为空"

        photoList = self.getHtmlImglist(queryId)
        logger.debug(photoList)
        #photoJson = json.dumps(photoList)
        print "---------------------------"
        #print photoList

        tmp = self.postVehicle(shareJob, photoList, queryId)
        print tmp
        (success, msg) = tmp
        if success:
            return errorcode.SUCCESS, msg
        else:
            return errorcode.SITE_ERROR, msg
            
        

