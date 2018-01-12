#!/usr/bin/python
# -*- coding: UTF-8 -*-

__author__ = 'zhuotianzhu'


class DataModelUtil(object):

    @staticmethod
    def get_car_ext(share_car):
        """
        获取车型拓展信息
        对应mongo中 external_vehicle_spec
        :param share_car:
        :return:
        """
        return share_car.get("external_vehicle_spec", None)

    @staticmethod
    def get_ext_summary(share_car):
        """
        获取拓展信息的概述
        :param share_car:
        :return:
        """
        ext = DataModelUtil.get_car_ext(share_car)
        if ext is not None:
            return ext.get("summary", None)

    @staticmethod
    def get_car_brand(share_car):
        """
        获取拓展车型的品牌
        :param share_car:
        :return:
        """
        ext = DataModelUtil.get_car_ext(share_car)
        if ext is not None:
            return ext.get("brand", None)

    @staticmethod
    def get_car_brand_id(share_car):
        """
        获取拓展车型的品牌id
        :param share_car:
        :return:
        """
        brand = DataModelUtil.get_car_brand(share_car)
        if brand is not None:
            return brand.get("id", None)

    @staticmethod
    def get_car_series(share_car):
        """
        获取车系
        :param share_car:
        :return:
        """
        ext = DataModelUtil.get_car_ext(share_car)
        if ext is not None:
            return ext.get("series", None)

    @staticmethod
    def get_car_series_id(share_car):
        """
        获取车系id
        :param share_car:
        :return:
        """
        series = DataModelUtil.get_car_series(share_car)
        if series is not None:
            return series.get("id", None)

    @staticmethod
    def get_ext_model(share_car):
        """
        获取车辆模型
        :param share_car:
        :return:
        """
        ext = DataModelUtil.get_car_ext(share_car)
        if ext is not None:
            return ext.get("model", None)

    @staticmethod
    def get_ext_model_id(share_car):
        """
        获取车辆模型id
        :param share_car:
        :return:
        """
        model = DataModelUtil.get_ext_model(share_car)
        if model is not None:
            return model.get("id", None)

    @staticmethod
    def get_ext_model_year(share_car):
        """
        获取模型年份
        :param share_car:
        :return:
        """
        model = DataModelUtil.get_ext_model(share_car)
        if model is not None:
            return model.get("year", None)

    @staticmethod
    def get_car_serie_id(share_car):
        return DataModelUtil.get_car_ext(share_car)['series']['id']

    @staticmethod
    def get_car_color(share_car):
        """
        获取车辆颜色
        :param share_car:
        :return:
        """
        ext = share_car.get("external_vehicle_spec", None)
        if ext is not None:
            return ext.get("color", None)

    @staticmethod
    def get_vehicle(share_car):
        """
        获取车辆信息
        :param share_car:
        :return:
        """
        return share_car.get("vehicle", None)

    @staticmethod
    def get_vehicle_date(share_car):
        """
        获取车辆日期相关
        :param share_car:
        :return:
        """
        vehicle = DataModelUtil.get_vehicle(share_car)
        if vehicle is not None:
            return vehicle.get("vehicle_date", None)

    @staticmethod
    def get_vehicle_date_reg(share_car):
        """
        获取车辆注册时间
        :param share_car:
        :return:
        """
        vehicle_date = DataModelUtil.get_vehicle_date(share_car)
        if vehicle_date is not None:
            return vehicle_date.get("registration_date", None)

    @staticmethod
    def get_vehicle_date_insp(share_car):
        """
        获取车辆年检有效期
        :param share_car:
        :return:
        """
        vehicle_date = DataModelUtil.get_vehicle_date(share_car)
        if vehicle_date is not None:
            return vehicle_date.get("inspection_date", None)

    @staticmethod
    def get_vehicle_date_commercial(share_car):
        """
        获取车辆商业险有效期
        :param share_car:
        :return:
        """
        vehicle_date = DataModelUtil.get_vehicle_date(share_car)
        if vehicle_date is not None:
            return vehicle_date.get("commercial_insurance_expire_date", None)

    @staticmethod
    def get_vehicle_date_compulsory(share_car):
        """
        获取车辆交强检有效期
        :param share_car:
        :return:
        """
        vehicle_date = DataModelUtil.get_vehicle_date(share_car)
        if vehicle_date is not None:
            return vehicle_date.get("compulsory_insurance_expire_date", None)

    @staticmethod
    def get_price(share_car):
        """
        获取车辆价格相关
        :param share_car:
        :return:
        """
        vehicle = DataModelUtil.get_vehicle(share_car)
        if vehicle is not None:
            return vehicle.get("price", None)

    @staticmethod
    def get_vin(share_car):
        """
        获取车辆vin码
        :param share_car:
        :return:
        """
        vehicle = DataModelUtil.get_vehicle(share_car)
        if vehicle is not None:
            return vehicle.get("vin", None)

    @staticmethod
    def get_car_photos(share_car):
        """
        获取车辆的照片
        :param share_car:
        :return:
        """
        vehicle = DataModelUtil.get_vehicle(share_car)
        gallery = {}
        if vehicle is not None:
            gallery = vehicle.get("gallery", None)
        if gallery is not None:
            photos = gallery.get("photos", None)
            return photos

    @staticmethod
    def get_vehicle_summary(share_car):
        """
        获取车辆概述
        :param share_car:
        :return:
        """
        vehicle = DataModelUtil.get_vehicle(share_car)
        if vehicle is not None:
            return vehicle.get("summary", None)

    @staticmethod
    def get_vehicle_color(share_car):
        """
        获取车辆颜色
        :param share_car:
        :return:
        """
        summary = DataModelUtil.get_vehicle_summary(share_car)
        if summary is not None:
            return summary.get("color", None)

    @staticmethod
    def get_vehicle_purpose(share_car):
        """
        获取车辆用途
        :param share_car:
        :return:
        """
        summary = DataModelUtil.get_vehicle_summary(share_car)
        if summary is not None:
            return summary.get("purpose", None)

    @staticmethod
    def get_tranfer_times(share_car):
        """
        获取交易次数
        :param share_car:
        :return:
        """
        summary = DataModelUtil.get_vehicle_summary(share_car)
        if summary is not None:
            return summary.get("trade_times", None)

    @staticmethod
    def get_desc(share_car):
        """
        获取车辆描述
        :param share_car:
        :return:
        """
        vehicle = DataModelUtil.get_vehicle(share_car)
        return vehicle.get("desc", None)

    @staticmethod
    def get_engine(share_car):
        """
        获取排量
        :param share_car:
        :return:
        """
        summary = DataModelUtil.get_ext_summary(share_car)
        if summary is not None:
            return summary.get("engine", None)

    @staticmethod
    def get_geal(share_car):
        """
        获取变速箱变速方式 自动|手动
        :param share_car:
        :return:
        """
        summary = DataModelUtil.get_vehicle_summary(share_car)
        if summary is not None:
            return summary.get("geal", None)

    @staticmethod
    def get_account(share_car):
        """
        获取账户信息
        :param share_car:
        :return:
        """
        return share_car.get("share_account", None)

    @staticmethod
    def get_sub_account(share_car):
        """
        账户详细信息
        :param share_car:
        :return:
        """
        account = DataModelUtil.get_account(share_car)
        return account.get("substitute_account", None)

    @staticmethod
    def get_license_code(share_car):
        subaccount = DataModelUtil.get_sub_account(share_car)
        address = subaccount.get('address', None)
        city_code = address['city_code']
        privince_code = address['province_code']
        return privince_code, city_code


