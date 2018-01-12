'''
Created by auto_sdk on 2015.11.30
'''
from top.api.base import RestApi
class TmallMarketingTmallcouponCouponApplyRequest(RestApi):
	def __init__(self,domain='gw.api.taobao.com',port=80):
		RestApi.__init__(self,domain, port)
		self.face_amount = None
		self.nick = None

	def getapiname(self):
		return 'tmall.marketing.tmallcoupon.coupon.apply'
