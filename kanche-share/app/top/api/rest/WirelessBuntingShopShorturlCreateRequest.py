'''
Created by auto_sdk on 2014.07.22
'''
from top.api.base import RestApi
class WirelessBuntingShopShorturlCreateRequest(RestApi):
	def __init__(self,domain='gw.api.taobao.com',port=80):
		RestApi.__init__(self,domain, port)
		self.shop_id = None

	def getapiname(self):
		return 'taobao.wireless.bunting.shop.shorturl.create'
