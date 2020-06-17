
import os
import requests,string,random,time
import hashlib
import json
import xmltodict
from decimal import *
from lib.utils.log import logger

from project.config_include.params import WECHAT_PAY_KEY,WECHAT_APPID,CALLBACKURL,WECHAT_PAY_MCHID,WECHAT_PAY_RETURN_KEY,\
    AliPay_Appid,AliPay_app_private_key,AliPay_alipay_public_key,AliPay_way,Alipay_callbackUrl,FASTMAIL_Key,Alipay_callbackUrlForVip,TASKSERVERURL
from lib.utils.exceptions import PubErrorCustom
from app.order.models import Order,OrderGoodsLink,OrderVip,viphandler
from app.goods.models import GoodsLinkSku,Goods
from app.user.models import Users
from app.user.models import BalList
from alipay import AliPay
from lib.utils.mytime import UtilTime
from django.conf import settings
from lib.utils.string_extension import md5pass
import base64
from urllib import parse

class wechatPay(object):

    def __init__(self):

        self.createUrl = "https://api.mch.weixin.qq.com/pay/unifiedorder"

    def hashdata(self,data,key):

        res = self.sortKeyStringForDict(data,key)
        return hashlib.md5(res.encode('utf-8')).hexdigest().upper()

    def sortKeyStringForDict(self,data,key):
        strJoin = ""
        for item in sorted({k: v for k, v in data.items() if v != ""}):
            if item == 'sign':
                continue
            strJoin += "{}={}&".format(str(item), str(data[item]))
        strJoin += "key={}".format(key)
        return strJoin

    def request(self,request_data):

        data={}

        data['appid'] = WECHAT_APPID
        data['mch_id'] = WECHAT_PAY_MCHID
        data['nonce_str'] = ''.join(random.sample(string.ascii_letters  + string.digits, 30))
        data['body'] = "商城系统-购买商品"
        data['out_trade_no'] = request_data['out_trade_no']
        data['total_fee'] = request_data['total_fee']
        data['spbill_create_ip'] = request_data['spbill_create_ip']
        data['notify_url'] = CALLBACKURL
        data['trade_type'] = 'JSAPI'
        data['openid'] = request_data['openid']
        data['sign_type'] = 'MD5'

        data['sign'] = self.hashdata(data,WECHAT_PAY_KEY)

        param = {'root': data}
        xml = xmltodict.unparse(param)

        res = requests.request(method="POST",data=xml.encode('utf-8'),url=self.createUrl,headers={'Content-Type': 'text/xml'})

        xmlmsg = xmltodict.parse(res.content.decode('utf-8'))

        if xmlmsg['xml']['return_code'] == 'SUCCESS':

            sign = self.hashdata(xmlmsg['xml'], WECHAT_PAY_KEY)

            if sign != xmlmsg['xml']['sign']:
                raise PubErrorCustom("非法操作！")

            prepay_id = xmlmsg['xml']['prepay_id']
            timeStamp = str(int(time.time()))

            data = {
                "appId": WECHAT_APPID,
                "nonceStr": data['nonce_str'],
                "package": "prepay_id=" + prepay_id,
                "signType": 'MD5',
                "timeStamp": timeStamp
            }
            data['paySign']=self.hashdata(data, WECHAT_PAY_KEY)

            data["orderid"] = request_data['out_trade_no']

            return data
        else:
            raise PubErrorCustom(xmlmsg['xml']['return_msg'])


    def callback(self,request):
        msg = request.body.decode('utf-8')
        xmlmsg = xmltodict.parse(msg)
        return_code = xmlmsg['xml']['return_code']

        print("腾讯支付回调数据:\n\t",xmlmsg['xml'])

        if return_code == 'SUCCESS':

            sign = self.hashdata(xmlmsg['xml'], WECHAT_PAY_KEY)
            if sign != xmlmsg['xml']['sign']:
                print(sign)
                raise Exception("非法操作！")

            if  xmlmsg['xml']['result_code'] == 'SUCCESS':
                out_trade_no = xmlmsg['xml']['out_trade_no']
                total_fee = xmlmsg['xml']['total_fee']

                total_fee = Decimal(str(total_fee))


                order = Order.objects.select_for_update().get(orderid=out_trade_no)
                if order.amount * 100 != total_fee:
                    raise Exception("金额不一致")

                if order.status=='1':
                    raise Exception("该订单已支付!")

                order.paymsg = json.dumps(xmlmsg['xml'])
                order.status=1
                if order.isvirtual == '0':
                    order.fhstatus = '0'
                order.save()

                user = Users.objects.select_for_update().get(userid=order.userid)

                if order.payamount>0.0:
                    updBalList(user,order,order.payamount,user.bal,user.bal,"微信支付")

                if order.balamount>0.0:
                    tmp = user.bal
                    user.bal -= order.balamount
                    user.save()
                    updBalList(user, order, order.balamount, tmp, user.bal, "余额支付")
            else:
                raise Exception("error")
        else:
            raise Exception("error")

    def orderQuery(self,orderid):

        data={
            "appid":WECHAT_APPID,
            "mch_id":WECHAT_PAY_MCHID,
            "out_trade_no": orderid,
            "nonce_str":''.join(random.sample(string.ascii_letters  + string.digits, 30)),
            "sign_type":'MD5'
        }
        data['sign'] = self.hashdata(data, WECHAT_PAY_KEY)
        param = {'root': data}
        xml = xmltodict.unparse(param)
        res = requests.request(method="POST", data=xml.encode('utf-8'), url="https://api.mch.weixin.qq.com/pay/orderquery",
                               headers={'Content-Type': 'text/xml'})

        xmlmsg = xmltodict.parse(res.content.decode('utf-8'))

        if xmlmsg['xml']['return_code'] == 'SUCCESS':
            # sign = self.hashdata(xmlmsg['xml'], WECHAT_PAY_KEY)
            # print(sign)
            # print(xmlmsg['xml'])
            # if sign != xmlmsg['xml']['sign']:
            #     raise PubErrorCustom("非法操作！")

            if xmlmsg['xml']['result_code'] == 'SUCCESS':
                order = Order.objects.select_for_update().get(orderid=orderid)
                if order.status=='1':
                    return {"data": True}
                order.status = 1
                if order.isvirtual == '0':
                    order.fhstatus = '0'
                order.save()

                user = Users.objects.select_for_update().get(userid=order.userid)

                if order.payamount>0.0:
                    updBalList(user,order,order.payamount,user.bal,user.bal,"微信支付")

                if order.balamount>0.0:
                    tmp = user.bal
                    user.bal -= order.balamount
                    user.save()
                    updBalList(user, order, order.balamount, tmp, user.bal, "余额支付")
                return {"data": True}
            else:
                return {"data":False}
        else:
            return {"data":False}



def updBalList(user,order,amount,bal,confirm_bal,memo,cardno=None):
    """

    :param user:
    :param order:
    :param amount:
    :param bal:
    :param confirm_bal:
    :param memo:
    :return:
    """

    print(cardno,order)
    BalList.objects.create(**{
        "userid":user.userid,
        "amount" : amount,
        "bal":bal,
        "confirm_bal":confirm_bal,
        "memo":memo,
        "orderid":order.orderid if order else cardno
    })

class AlipayBase(object):

    def __init__(self,isVip=None):

        # print(AliPay_alipay_private_key)
        #
        #
        # print(AliPay_alipay_public_key)
        #
        # print(AliPay_Appid)

        self.alipay = AliPay(
            appid=AliPay_Appid,
            app_notify_url=Alipay_callbackUrl if not isVip else Alipay_callbackUrlForVip,
            app_private_key_string=AliPay_app_private_key,
            alipay_public_key_string=AliPay_alipay_public_key,
            sign_type="RSA2",
            debug=False,  # 上线则改为False , 沙箱True
        )

    def create(self,order_id,amount,subject=None):

        order_string = self.alipay.api_alipay_trade_app_pay(
            out_trade_no=order_id,
            total_amount=str(amount.quantize(Decimal('0.00'))),
            subject='支付订单:%s' % order_id if not subject else subject,
            return_url=None,
            notify_url=None,
        )
        logger.info(order_string)
        return order_string

    def refund(self,order,orderid,refund_amount):

        response = self.alipay.api_alipay_trade_refund(
            refund_amount=str(refund_amount.quantize(Decimal('0.00'))),
            out_trade_no=orderid
        )
        logger.info("退款信息->{}".format(response))
        if response['code']!= '10000':
            raise PubErrorCustom(response['msg'])

        try:
            for item in OrderGoodsLink.objects.filter(linkid__in=json.loads(order.linkid)['linkids']):
                try:
                    glObj = GoodsLinkSku.objects.select_for_update().get(id=item.skugoodslinkid)
                    glObj.stock += item.gdnum
                    glObj.number -=item.gdnum
                    glObj.save()
                except GoodsLinkSku.DoesNotExist:
                    pass
        except Exception as e:
            print(str(e))

    def callback_vip(self,data):
        iData = dict()
        for item in data:
            iData[item] = data[item]

        sign = iData.pop("sign", None)
        if not self.alipay.verify(iData, sign):
            print(iData)
            raise PubErrorCustom("验签失败!")

        if iData.get("trade_status", None) != 'TRADE_SUCCESS':
            print(iData)
            raise PubErrorCustom("交易状态异常!")

        try:
            orderObj = OrderVip.objects.select_for_update().get(orderid=iData.get("out_trade_no", ""))
            if orderObj.status == '1':
                logger.info("订单{}已处理".format(orderObj.orderid))
                raise PubErrorCustom("订单{}已处理".format(orderObj.orderid))
        except Order.DoesNotExist:
            raise PubErrorCustom("订单不存在!")

        orderObj.status = '1'

        user = Users.objects.select_for_update().get(userid=orderObj.userid)
        if user.isvip == '1':
            user.exprise = viphandler(user.exprise,orderObj.unit,orderObj.term)
            orderObj.exprise =  user.exprise
        else:
            user.isvip = '1'
            user.term = orderObj.term
            user.unit = orderObj.unit
            user.exprise = orderObj.exprise

        orderObj.save()
        user.save()

    def callback(self,data):

        iData = dict()
        for item in data:
            iData[item] = data[item]

        sign = iData.pop("sign",None)
        if not self.alipay.verify(iData,sign):
            print(iData)
            raise PubErrorCustom("验签失败!")

        if iData.get("trade_status",None) != 'TRADE_SUCCESS':
            print(iData)
            raise PubErrorCustom("交易状态异常!")

        try:
            orderObj = Order.objects.select_for_update().get(orderid=iData.get("out_trade_no",""))
            if orderObj.status == '1':
                logger.info("订单{}已处理".format(orderObj.orderid))
                raise PubErrorCustom("订单{}已处理".format(orderObj.orderid))
        except Order.DoesNotExist:
            raise PubErrorCustom("订单不存在!")

        orderObj.status = '1'
        orderObj.save()

        user = Users.objects.select_for_update().get(userid=orderObj.userid)

        logger.info("用户{}积分余额{}使用积分{}获得积分{}".format(user.mobile,user.jf,orderObj.use_jf,orderObj.get_jf))
        user.jf -= orderObj.use_jf
        user.jf += orderObj.get_jf
        user.save()

        logger.info("支付宝回调订单处理成功!=>{}".format(iData))

        # try:
        #     for item in OrderGoodsLink.objects.filter(linkid__in=json.loads(orderObj.linkid)['linkids']):
        #         try:
        #             glObj = GoodsLinkSku.objects.select_for_update().get(id=item.skugoodslinkid)
        #             glObj.stock -= 1
        #             glObj.number +=1
        #             glObj.save()
        #         except GoodsLinkSku.DoesNotExist:
        #             pass
        # except Exception as e:
        #     print(str(e))

class OrderBase(object):

    def __init__(self,**kwargs):

        self.order = kwargs.get("order")
        self.cityHandler = cityLimit()
        self.ut = UtilTime()

    def checkvoidForcreateOrder(self,**kwargs):

        """
        按区域限购
        按周期时间限购
        :param kwargs:
        :return:
        """
        ut = self.ut
        end = ut.timestamp
        cityHandler = self.cityHandler
        order = self.order

        goodsObj = kwargs.get("goodsObj")
        gdnum = kwargs.get("gdnum")

        flag = kwargs.get("flag",None)

        if flag == 'city':

            for item in OrderGoodsLink.objects.filter(linkid__in=json.loads(order.linkid)['linkids']):

                try:
                    goodsObj = Goods.objects.get(gdid=item.gdid)
                    if goodsObj.gdstatus != '0':
                        raise PubErrorCustom("商品{}已下架".format(goodsObj.gdname))
                except Goods.DoesNotExist :
                    raise PubErrorCustom("商品{}不存在".format(goodsObj.gdname))

                try:
                    city = json.loads(order.address).get("label", "").split('-')[0]
                except Exception as e:
                    logger.info(str(e))
                    city = None

                if city:
                    for itemCity in json.loads(goodsObj.limit_citys):
                        if cityHandler.isExists(itemCity, city):
                            logger.info("收货地址{},限购城市{}".format(itemCity, city))
                            raise PubErrorCustom("{},库存不够!".format(goodsObj.gdname))
        else:

            if goodsObj.limit_unit == 'A':
                pass
            else:
                if goodsObj.limit_unit == 'M':
                    start = ut.today.shift(months=goodsObj.limit_count * -1).timestamp
                elif goodsObj.limit_unit == 'W':
                    start = ut.today.shift(weeks=goodsObj.limit_count * -1).timestamp

                okcount = queryBuyOkGoodsCount(order.userid, goodsObj.gdid, start, end)
                logger.info("目前购买->{},实际已购买->{},规则数量->{}".format(gdnum, okcount, goodsObj.limit_number))
                if gdnum + okcount > goodsObj.limit_number:
                    raise PubErrorCustom("{},库存不够!".format(goodsObj.gdname))

    def callbackStock(self):
        order = self.order
        try:
            for item in OrderGoodsLink.objects.filter(linkid__in=json.loads(order.linkid)['linkids']):
                try:
                    glObj = GoodsLinkSku.objects.select_for_update().get(id=item.skugoodslinkid)
                    glObj.stock += item.gdnum
                    glObj.number -=item.gdnum
                    glObj.save()
                except GoodsLinkSku.DoesNotExist:
                    pass
        except Exception as e:
            print(str(e))

    def jfGet(self,**kwargs):
        goodsObj = kwargs.get("goodsObj")
        gdprice = kwargs.get("gdprice")
        gdnum = kwargs.get("gdnum")

        jf = Decimal("0.0")

        if goodsObj.jf_type== '0':
            return jf
        if goodsObj.jf_type == '1':
            return gdprice * goodsObj.jf_value * gdnum
        elif goodsObj.jf_type == '2':
            return goodsObj.jf_value * gdnum
        else:
            return jf


class fastMail(object):

    def __init__(self):

        self.url = "http://api.kdniao.com/Ebusiness/EbusinessOrderHandle.aspx"
        self.key = FASTMAIL_Key
        self.request_data = {
            "EBusinessID": "1648972",
            "RequestType": "1002",
            "DataType": 2,
            "RequestData": "",
            "DataSign": ""
        }

    def _select(self,ShipperCode):
        data={
            "EMS":"EMS",
            "SF":"顺丰速运",
            "YZBK":"邮政国内标快",
            "YZPY":"邮政快递包裹",
            "ZJS":"宅急送",
            "LHT":"联昊通速递",
            "UAPEX":"全一快递",
            "STO":"申通快递",
            "DBL":"德邦快递",
            "JD":"京东快递",
            "XFEX":"信丰物流",
            "HHTT":"天天快递",
            "SURE":"速尔快递",
            "KYSY":"跨越速运",
            "PJ":"品骏快递",
            "CND":"承诺达",
            "JTSD":"极兔速递",
            "DNWL":"丹鸟物流",
            "SNWL":"苏宁物流",
            "ZTO":"中通快递",
            "YD":"韵达速递",
            "HTKY":"百世快递",
            "YTO":"圆通速递",
            "YCWL":"远成快运",
            "UC":"优速快递",
            "ANE":"安能快递"
        }

        return data.get(ShipperCode,"编号非法")

    def sign(self, signValue):
        s = md5pass(json.dumps(signValue) + self.key)
        a = base64.b64encode(s.encode('utf-8'))
        return parse.quote(a)

    def query(self, ShipperCode, LogisticCode):

        data = {
            "ShipperCode": ShipperCode,
            "LogisticCode": LogisticCode
        }

        self.request_data['DataSign'] = self.sign(data)
        self.request_data['RequestData'] = parse.quote(json.dumps(data))

        print(self.request_data)

        response = requests.request(method="POST", data=self.request_data, url=self.url)

        response = json.loads(response.content)
        print(response)
        if response['Success']:
            response['company'] = self._select(response['ShipperCode'])
            return response
        else:
            return response

def calyf(yf_flag):
    if yf_flag == '0':
        return 5.0
    elif yf_flag == '1':
        return 10.0
    elif yf_flag == '2':
        return 18.0
    elif yf_flag == '3':
        return 36.0
    elif yf_flag == '4':
        return  55.0
    elif yf_flag == '5':
        return 0.0
    else:
        return 55.0

def queryBuyOkGoodsCount(userid,gdid,start,end):

    query_format=" and t1.gdid='{}' and t2.userid={} and t2.createtime>={} and t2.createtime<={}".format(gdid,userid,start,end)

    res =OrderGoodsLink.objects.raw("""
        SELECT sum(t1.gdnum) as linkid from `ordergoodslink` as t1
        INNER JOIN `order` as t2 ON t1.orderid = t2.orderid
        WHERE t2.status in ('0','1','2','3') and t2.before_status!='2'  %s
    """%(query_format),[])
    logger.info(res)
    res = list(res)
    return res[0].linkid if len(res) and res[0].linkid  else 0

class cityLimit(object):
    def __init__(self):
        self.citys = ["北京市","天津市","河北省","山西省","内蒙古自治区","辽宁省","吉林省","黑龙江省","上海市","江苏省","浙江省","安徽省","福建省","江西省","山东省","河南省","湖北省","湖南省","广东省","广西壮族自治区","海南省","重庆市","四川省","贵州省","云南省","西藏自治区","陕西省","甘肃省","青海省","宁夏回族自治区","新疆维吾尔自治区","台湾","香港","澳门"]

    @property
    def get(self):
        return self.citys

    def isExists(self,city,city1):

        return city == city1


def request_task_order(orderid):

    res = requests.request(url=TASKSERVERURL,method='POST',json={
        "data":{
            "orderid":orderid
        }
    })

    logger.info("处理订单未付款到期状态{};{}".format(orderid,res.text))

