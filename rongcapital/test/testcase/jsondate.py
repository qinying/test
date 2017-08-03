#-*- coding: UTF-8 -*-
import sys
reload(sys)
sys.setdefaultencoding('utf8')
class data():
    def json(self):
        jsondata = ("{" + "'recruitChannel':'社招', "#招生渠道
                            + "'bussinessChannel':'业务方向',"#业务方向
                            + "'courseContent':'课程内容',"#课程内容
                            + "'courseSetting':',net',"#课程设置
                            + "'coursePrice':'1680000',"#课程价格--页面显示为元
                            + "'totalTeacher':'教师总数',"#教师总数
                            + "'teacherExperience':'教师资历',"#教师资历
                            + "'teacherAbility':'授课质量',"#授课质量
                            + "'summaryStudentLastYear':'800001',"#上一年度招生数量
                            + "'reputation':'口碑',"#口碑
                            + "'employeeRate':'98',"#就业率
                            + "'averageSalary':'778855',"#薪资水平--页面显示为元
                            + "'backOutRate':'90',"#退课率
                            + "'backOutRule':'退课规则',"#退课规则
                            + "'mark':'1222',"#评分
                            + "'totalClassroom':'600',"#总教室
                            + "'areaClassroom':'5000',"#教师面积
                            + "'totalStudent':'90001',"#现有学员总数量
                            + "'frequencyLastYear':'10000',"#年培训人次
                            + "'revenueLastYear':'888888888',"#上一年营业收入--页面显示为元
                            + "'propertyLastYear':'45615649685465',"#上一年总资产
                            + "'debtLastYear':'41564563156',"#上一年度总负债
                            + "'pureProfitLastYear':'10043254415754854',"#上一年度税收
                            + "'creditLimit':'1666666',"#申请额度
                            + "'creditDeadLine':'1',"#申请期限
                            +  "'factoringType':'无追',"#保理类型
                            +  "'marginRatio':'30',"#保证金
                            +  "'foundation':'2011-10-10 00:00:00',"
                            +  "'applicationAdvice':'申请意见',"#申请意见
                            + "'creditRateTemplates':'10001'}")
        return jsondata

    def per(self):
        personal_json = ("{" + "'corporation':'拯救大兵测试机构082305', "
                         + "'courseName':'Java',"
                         + "'coursePrice':'9000',"
                         + "'amount':'100000',"
                         + "'premiumWay':'RA201604060000005',"
                         + "'corporationName':'新平台测试',"
                         + "'corporationAddress':'华尔街地址：酒仙桥路',"
                         + "'corporationContact':'010-88888888',"
                         + "'primaryContactName':'第一联系人pipipapa酱',"
                         + "'primaryContactPhone':'13881061020',"
                         + "'primaryContactRelation':'夫妻',"
                         + "'secondaryContactName':'第二联系人papi酱',"
                         + "'secondaryContactPhone':'13991061020',"
                         + "'applicateName':'',"
                         + "'applicateCardId':'',"
                         + "'applyLoanSource':'0',"
                         + "'applyadviser':'课程顾问',"
                         + "'applyadvisertelnumber':'课程顾问电话',"
                         + "'gps':'gps经纬度',"
                         + "'validityStart':'1995-01-02',"
                         + "'validityEnd':'2019-01-02',"
                         + "'classwarning':' 班级信息',"
                         + "'dogId':'456京东号',"
                         + "'catId':' 123宝号',"
                         + "'courseOpenTime':'20160823',"
                         + "'coursePeriod':'1500',"
                         + "'QQ':'179854857',"
                         + "'secondaryContactRelation':'父女'}")
        return personal_json

    def fangcangqiye(self):
        fang_json = (
            "{" + "'recruitChannel':'社招', "  # 招生渠道
            + "'bussinessChannel':'业务方向',"  # 业务方向
            + "'courseContent':'课程内容',"  # 课程内容
            + "'courseSetting':',net',"  # 课程设置
            + "'coursePrice':'1680000',"  # 课程价格--页面显示为元
            + "'totalTeacher':'教师总数',"  # 教师总数
            + "'teacherExperience':'教师资历',"  # 教师资历
            + "'teacherAbility':'授课质量',"  # 授课质量
            + "'summaryStudentLastYear':'800001',"  # 上一年度招生数量
            + "'reputation':'口碑',"  # 口碑
            + "'employeeRate':'98',"  # 就业率
            + "'averageSalary':'778855',"  # 薪资水平--页面显示为元
            + "'backOutRate':'90',"  # 退课率
            + "'backOutRule':'退课规则',"  # 退课规则
            + "'mark':'1222',"  # 评分
            + "'totalClassroom':'600',"  # 总教室
            + "'areaClassroom':'5000',"  # 教师面积
            + "'totalStudent':'90001',"  # 现有学员总数量
            + "'frequencyLastYear':'10000',"  # 年培训人次
            + "'revenueLastYear':'888888888',"  # 上一年营业收入--页面显示为元
            + "'propertyLastYear':'45615649685465',"  # 上一年总资产
            + "'debtLastYear':'41564563156',"  # 上一年度总负债
            + "'pureProfitLastYear':'10043254415754854',"  # 上一年度税收
            + "'creditLimit':'1666666',"  # 申请额度
            + "'creditDeadLine':'1',"  # 申请期限
            + "'factoringType':'无追',"  # 保理类型
            + "'marginRatio':'30',"  # 保证金
            + "'foundation':'2011-10-10 00:00:00',"
            + "'applicationAdvice':'申请意见',"  # 申请意见
            + "'creditRateTemplates':'10001'}"
        )
        return fang_json

    def yue(self):
        yue_json = (
            "{" + "'isAssociate':'是', "  # 是否员工
            + "'courseName':'演示数据勿操作',"
            + "'associateNo':'11000',"  # 员工工号
            + "'primaryContactName':'张三',"  # 第一联系人姓名
            + "'primaryContactPhone':'18612211111',"  # 第一联系人手机号
            + "'primaryContactCerNum':'211224198705050000',"  # 第一联系人身份证
            + "'primaryContactRelation':'4',"
            + "'hasCreditCard':'1',"  # 有 or 無
            + "'dogId':'123456',"  # 京东号
            + "'catId':'13596480000',"  # 支付寶号
            + "'QQ':'513222222',"  # QQ号   eeeeeeee
            + "'email':'13881060959@qq.com',"  # 邮箱
            + "'secondaryContactName':'李四',"  # 第二联系人姓名
            + "'secondaryContactPhone':'13841578596',"  # 第二联系人手机号码
            + "'secondaryContactRelation':'2',"  # 第二联系人关系
            + "'selfAndTeacherPhoto':'[\"f25c06a9-4840-4c02-9689-92d1dd9db8c6\",\"f25c06a9-4840-4c02-9689-92d1dd9db8c6\"]',"  # 申请人和婚拍咨询师合照
            + "'contractPhoto':'[\"c9c79115-6df4-4538-ba96-54c543390fe5\",\"c9c79115-6df4-4538-ba96-54c543390fe5\"]',"  # 合同照片
            + "'handIdCardPhoto':'7bb89b03-8fde-4f08-bdf6-d7e876cdefa4',"  # 手持身份证照片
            + "'certificatePhoto':'{\"0\":\"339fa2bb-306d-4432-81b1-53aae5fd853a\",\"1\":\"73dbd050-a954-43c7-b7c3-259cfcadf1d3\"}',"  # 身份证正反面 正面:1  反面：0
            + "'xieyiLocationShi':'北京',"  # 协议签署市
            + "'xieyiLocationQu':'朝阳区',"  # 协议签署区
            + "'creditCardNo':'6214089547896544',"  # 信用卡卡号
            + "'coursePrice':'10',"  # c产品价格
            + "'amount':'10',"  # 申请金额       eeeeeeeeeeeeeee
            + "'premiumWay':'RA201610111400001',"  # 产品类型
            + "'bussinessName':'悦视觉123',"  # 商户名称
            + "'nation':'汉族',"  # 申请人民族
            + "'address':'北京市朝阳区酒仙桥路',"  # 申请人地址
            + "'validityStart':'2006-08-02',"  # 申请人身份证生效时间
            + "'validityEnd':'2026-08-02',"  # 申请人身份证失效时间
            + "'issuingBank':'招商',"  # 信用卡发卡行
            + "'creditLimit':'20160823',"  # 信用卡额度
            + "'education':'1',"  # 申请人学历
            + "'workNature':'1',"  # 工作单位性质
            + "'workCompanyName':'融数金服',"  # 工作单位名称
            + "'bussiTypeForOpr':'1',"  #
            + "'spouseIdCardPhoto':'{\"0\":\"9c575c23-27f1-4720-836c-8f81259384be\",\"1\":\"196bfbdd-fa47-4562-9d71-d06f51e4ff55\"}',"  # 申请人配偶身份证（正反面）
            + "'tAccountBank':'农行',"  # 申请人银行卡开户行
            + "'tAccountProvince':'北京',"  # 申请人银行卡开户省
            + "'tAccountCity':'北京',"  # 申请人银行卡开户市
            + "'tAccountBranch':'酒仙桥支行'}"
        )
        return yue_json