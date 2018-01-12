'''
Created by auto_sdk on 2015.12.08
'''
from top.api.base import RestApi
class AlibabaWttOrderContractSubscribeRequest(RestApi):
	def __init__(self,domain='gw.api.taobao.com',port=80):
		RestApi.__init__(self,domain, port)
		self.distribution_order_model = None

	def getapiname(self):
		return 'alibaba.wtt.order.contract.subscribe'
