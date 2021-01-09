
import json
from rest_framework import viewsets
from rest_framework.decorators import list_route
from django.db.models import Q
from django.db import transaction
from django.http import HttpResponse
from lib.core.decorator.response import Core_connector
from decimal import *
from lib.utils.exceptions import PubErrorCustom

from app.cache.utils import RedisCaCheHandler
from app.order.models import Order,OrderGoodsLink,OrderVip

from app.user.models import Users,VipRule
from app.user.serialiers import UsersSerializers

from app.order.serialiers import OrderModelSerializer,AddressModelSerializer,OrderGoodsLinkModelSerializer
from app.order.models import Address
from lib.utils.log import logger
from app.goods.models import Card,Cardvirtual,DeliveryCode,Goods,GoodsLinkSku,Active,Makes

from app.order.utils import wechatPay,updBalList,AlipayBase,fastMail,calyf,queryBuyOkGoodsCount,cityLimit,OrderBase,request_task_order
from lib.utils.db import RedisTokenHandler
from lib.utils.mytime import UtilTime
from project.config_include.params import ORDERCANLETIME

from app.goodslimit import LimitGoods

class OrderAPIView(viewsets.ViewSet):


    @list_route(methods=['POST'])
    @Core_connector(isTransaction=True,isPasswd=True,isTicket=True)
    def addAddress(self, request):

        data = request.data_format
        if str(data.get('moren')) == '0':
            Address.objects.filter(userid=request.user['userid']).update(moren='1')

        if 'id' in data:
            try:
                address = Address.objects.select_for_update().get(id=data['id'])
            except Address.DoesNotExist:
                raise PubErrorCustom("该地址不存在!")

            address.name = data.get("name")
            address.phone = data.get("phone")
            address.detail = data.get("detail")
            address.label = data.get("label")
            address.moren = data.get("moren")
            address.save()
        else:
            address = Address.objects.create(**dict(
                userid=request.user['userid'],
                name = data.get("name"),
                phone = data.get("phone"),
                detail = data.get("detail"),
                label = data.get("label"),
                moren = data.get("moren"),
            ))

        return {"data":AddressModelSerializer(address,many=False).data}

    @list_route(methods=['POST'])
    @Core_connector(isTransaction=True,isPasswd=True,isTicket=True)
    def delAddress(self, request):

        Address.objects.filter(id=request.data_format['id']).delete()

    @list_route(methods=['POST'])
    @Core_connector(isTransaction=True,isPasswd=True,isTicket=True)
    def BuyForOrderCreate(self, request):
        orderObj = Order.objects.create(**dict(
            userid=request.user['userid']
        ))
        orderObj.linkid={"linkids":[]}
        orderObj.amount = Decimal("0.0")

        try:
            goods = Goods.objects.get(gdid=request.data_format.get("gdid"),gdstatus='0')
        except Goods.DoesNotExist:
            raise PubErrorCustom("该商品已下架!")

        try:
            glink=GoodsLinkSku.objects.select_for_update().get(id=request.data_format.get("linkid"))
            if glink.stock < 1:
                raise PubErrorCustom("库存不够!")
        except Goods.DoesNotExist:
            raise PubErrorCustom("该规格已下架!")


        link = OrderGoodsLink.objects.create(**dict(
            userid=request.user['userid'],
            orderid=orderObj.orderid,
            gdid=goods.gdid,
            gdimg=json.loads(goods.gdimg)[0],
            gdname=goods.gdname,
            gdprice=glink.price,
            gdnum=1
        ))

        orderObj.linkid['linkids'].append(link.linkid)
        orderObj.amount += link.gdprice * int(link.gdnum)
        orderObj.linkid=json.dumps(orderObj.linkid)
        orderObj.save()

        return {"data":orderObj.orderid}


    @list_route(methods=['POST'])
    @Core_connector(isTransaction=True,isPasswd=True,isTicket=True)
    def OrderCreate(self, request):
        """
        生成订单
        :param request:
        :return:
        """

        data=request.data_format


        active_id = data['data'].get("active_id",None)

        if not len(data['data']['goods']):
            raise PubErrorCustom("购买商品不能为空!")

        if request.addressBool:
            raise PubErrorCustom("无库存!")

        # try:
        #     user=Users.objects.select_for_update().get(userid=request.user['userid'])
        # except Users.DoesNotExist:
        #     raise PubErrorCustom("该用户不存在!")

        orderObj = Order.objects.create(**dict(
            userid=request.user['userid']
        ))
        orderObj.linkid={"linkids":[]}
        orderObj.amount = Decimal("0.0")
        orderObj.yf = Decimal("0.0")
        orderObj.use_jf = Decimal("0.0")
        orderObj.get_jf = Decimal("0.0")

        orderHandler =  OrderBase(order=orderObj)

        if active_id:
            if  data['data']['goods'][0]['number'] != 1:
                raise PubErrorCustom("预约抢购数量只能是1")

            try:
                active = Active.objects.get(id=active_id)
            except Active.DoesNotExist:
                raise PubErrorCustom("此活动不存在!")

            try:
                makes = Makes.objects.get(
                    active_id=active.id,
                    userid=request.user['userid']
                )

                if len(makes.orderid):
                    raise PubErrorCustom("此次活动已购买商品,不能重复购买!")

                if makes.status!='4':
                    raise PubErrorCustom("抢购未成功,不能下单!")

                makes.orderid = orderObj.orderid
                makes.save()

            except Makes.DoesNotExist:
                raise PubErrorCustom("未预约!")

        for item in data['data']['goods']:
            try:
                goods = Goods.objects.get(gdid=item.get("gdid"), gdstatus='0')
            except Goods.DoesNotExist:
                raise PubErrorCustom("商品({})已下架!".format(item.get("gdid")))

            try:
                glink = GoodsLinkSku.objects.select_for_update().get(id=item.get("linkid"))
                if glink.stock - int(item.get("number")) < 1:
                    raise PubErrorCustom("商品({})库存不够!".format(goods.gdname))
                # if not LimitGoods(userid=request.user['userid'],limit_goods=json.loads(goods.limit_goods),gdid=item.get("gdid")).stockBool(int(item.get("number"))):
                #     raise PubErrorCustom("购买2瓶舜将后即可以1499元购买一瓶53度飞天茅台")

                glink.stock -= int(item.get("number"))
                glink.number += int(item.get("number"))
                glink.save()
            except GoodsLinkSku.DoesNotExist:
                raise PubErrorCustom("商品({})规格已下架!".format(goods.gdname))

            if glink.id not in json.loads(goods.gdskulist):
                raise PubErrorCustom("此规格已经更改,请重新购买!")

            orderHandler.checkvoidForcreateOrder(goodsObj=goods,gdnum=item.get("number"))

            link = OrderGoodsLink.objects.create(**dict(
                userid=request.user['userid'],
                orderid=orderObj.orderid,
                gdid=goods.gdid,
                gdimg=json.loads(goods.gdimg)[0],
                gdname=goods.gdname,
                gdprice=glink.price,
                gdnum=item.get("number"),
                skugoodslinkid=glink.id,
                skugoodslabel = item.get("spec")
            ))

            orderObj.linkid['linkids'].append(link.linkid)
            orderObj.amount += link.gdprice * int(link.gdnum)
            orderObj.yf += Decimal(str(calyf(goods.yf))) * int(link.gdnum)
            orderObj.use_jf += glink.jf * int(link.gdnum)
            orderObj.get_jf += orderHandler.jfGet(goodsObj=goods,gdprice=link.gdprice,gdnum=link.gdnum)

        # if user.jf < orderObj.use_jf:
        #     raise PubErrorCustom("积分不够!")

        orderObj.amount += orderObj.yf
        orderObj.linkid=json.dumps(orderObj.linkid)
        orderObj.save()

        request_task_order(orderObj.orderid)

        return {"data":orderObj.orderid}

    @list_route(methods=['POST'])
    @Core_connector(isTransaction=True,isPasswd=True,isTicket=True)
    def OrderCreate1(self, request):
        """
        订单确认
        :param request:
        :return:
        """

        data=request.data_format

        try:
            order = Order.objects.select_for_update().get(orderid=data.get("orderid"))
        except Order.DoesNotExist:
            raise PubErrorCustom("订单异常!")

        if not len(data.get("address")):
            raise PubErrorCustom("收货地址不能为空!")

        order.address = json.dumps(data.get("address", {}),ensure_ascii=False)
        order.memo = data.get("desc", "")

        OrderBase(order=order).checkvoidForcreateOrder(flag='city')
        order.save()

        return {"data":order.orderid}

    @list_route(methods=['POST'])
    @Core_connector(isTransaction=True, isPasswd=True, isTicket=True)
    def OrderUpdate(self, request):
        """
        订单修改
        :param request:
        :return:
        """

        data = request.data_format

        try:
            order = Order.objects.select_for_update().get(orderid=data.get("orderid"))
        except Order.DoesNotExist:
            raise PubErrorCustom("订单异常!")

        if len(data.get("address", {})):
            if order.status in ['0','1']:
                order.address = json.dumps(data.get("address", {}),ensure_ascii=False)
            else:
                raise PubErrorCustom("此状态不能修改订单地址!")

        if data.get("desc",None):
            order.memo = data.get("desc", "")

        if data.get("kdno",None):
            order.kdno = json.dumps(data.get("kdno",[]))

        if data.get("memo",None):
            order.memo = data.get("memo")

        order.save()

        return {"data": order.orderid}

    @list_route(methods=['POST'])
    @Core_connector(isTransaction=True, isPasswd=True, isTicket=True)
    def PayHandlerVip(self, request):

        payType = request.data_format.get("payType", None)
        ruleid = request.data_format.get("ruleid", None)

        try:
            viprule = VipRule.objects.get(id=ruleid)
        except VipRule.DoesNotExist:
            raise PubErrorCustom("规则不存在!!")

        if not payType:
            raise PubErrorCustom("支付方式有误!")

        order = OrderVip.objects.create(**{
            "userid":request.user['userid'],
            "amount":viprule.amount,
            "term":viprule.term,
            "unit":viprule.unit,
            "paytype":payType
        })

        subject=""
        if order.unit == '0':
            subject = "{}周会员充值".format(order.term)
        elif order.unit == '1':
            subject = "{}月会员充值".format(order.term)
        elif order.unit == '2':
            subject = "{}年会员充值".format(order.term)
        else:
            subject = "会员充值"

        if payType == 2:
            return {"data": AlipayBase(isVip=True).create(order.orderid, order.amount,subject=subject)}
        else:
            raise PubErrorCustom("支付方式有误!")

    @list_route(methods=['POST'])
    @Core_connector(isTransaction=True,isPasswd=True,isTicket=True)
    def PayHandler(self, request):

        payType = request.data_format.get("payType",None)
        orderid = request.data_format.get("orderid",None)

        if not payType:
            raise PubErrorCustom("支付方式有误!")

        try:
            order = Order.objects.select_for_update().get(orderid=orderid)
        except Order.DoesNotExist:
            raise PubErrorCustom("订单异常!")

        if not len(json.loads(order.address)):
            raise PubErrorCustom("请返回订单页填写收货地址!")

        OrderBase(order=order).checkvoidForcreateOrder(flag='city')

        try:
            user = Users.objects.select_for_update().get(userid=order.userid)
        except Users.DoesNotExist:
            raise PubErrorCustom("用户不存在!")

        if order.use_jf > user.jf:
            raise PubErrorCustom("积分不够!")

        order.paytype = str(payType)
        order.save()
        if payType == 2:
            return {"data":AlipayBase().create(order.orderid,order.amount)}
        else:
            raise PubErrorCustom("支付方式有误!")

    @list_route(methods=['POST'])
    @Core_connector(isTransaction=True,isPasswd=True,isTicket=True)
    def RefundHandler(self, request):
        """
        申请退款
        :param request:
        :return:
        """
        orderid = request.data_format.get("orderid", None)
        refundmsg = request.data_format.get("refundmsg", None)

        if not refundmsg:
            raise PubErrorCustom("理由不能为空!")

        try:
            order = Order.objects.select_for_update().get(orderid=orderid)
            if order.status not in ['1','2','3']:
                raise PubErrorCustom("只允许已付款的订单申请退款!")

            if order.before_status == '1':
                raise PubErrorCustom("请勿重复申请退款!")

            if order.before_status == '2':
                raise PubErrorCustom("已退款,请勿再申请退款!")

            order.before_status = '1'
            order.refundmsg = refundmsg
            order.apply_refund_time = UtilTime().timestamp
            order.save()
        except Order.DoesNotExist:
            raise PubErrorCustom("订单异常!")

    @list_route(methods=['POST'])
    @Core_connector(isTransaction=True,isPasswd=True,isTicket=True)
    def RefundConfirmHandler(self, request):
        """
        退款确认
        :param request:
        :return:
        """
        orderid = request.data_format.get("orderid", None)

        try:
            order = Order.objects.select_for_update().get(orderid=orderid)
            if order.before_status!='1':
                raise PubErrorCustom("只允许通过已申请退款的订单!")
            order.before_status = '2'
            order.status = '4'
            order.save()

            try:
                user = Users.objects.select_for_update().get(userid=order.userid)
            except Users.DoesNotExist:
                raise PubErrorCustom("用户{}有误!".format(user.mobile))

            user.jf += order.use_jf
            user.jf -= order.get_jf
            user.save()

            AlipayBase().refund(order=order,orderid=order.orderid, refund_amount=order.amount)
        except Order.DoesNotExist:
            raise PubErrorCustom("订单异常!")

        return None

    @list_route(methods=['POST'])
    @Core_connector(isTransaction=True, isPasswd=True, isTicket=True)
    def QzCanlceHandler(self, request):
        """
        系统强制退款
        :param request:
        :return:
        """
        orderid = request.data_format.get("orderid", None)

        try:
            order = Order.objects.select_for_update().get(orderid=orderid)
            if order.status != '1':
                raise PubErrorCustom("只允许强制取消已付款待发货状态的订单!")
            order.before_status = '2'
            order.refundmsg = "因为系统原因，订单提交失败，钱款将原路退回支付账户，请注意查收！"
            order.status = '4'
            order.save()

            try:
                user = Users.objects.select_for_update().get(userid=order.userid)
            except Users.DoesNotExist:
                raise PubErrorCustom("用户{}有误!".format(user.mobile))

            user.jf += order.use_jf
            user.jf -= order.get_jf
            user.save()

            AlipayBase().refund(order=order, orderid=order.orderid, refund_amount=order.amount)
        except Order.DoesNotExist:
            raise PubErrorCustom("订单异常!")

        return None


    @list_route(methods=['POST'])
    @Core_connector(isTransaction=True, isPasswd=False)
    def OrderCanleSysEx(self, request):
        logger.info("晚上批量处理订单!")

        today = UtilTime().today.shift(minutes=ORDERCANLETIME*-1)

        for order in Order.objects.select_for_update().filter(createtime__lte=today.timestamp,status='0'):
            OrderBase(order=order).callbackStock()
            order.status = '9'
            order.save()

        today = UtilTime().today.shift(days=-7)

        for order in Order.objects.select_for_update().filter(fhtime__lte=today.timestamp,status='2'):
            order.status = '3'
            order.save()

        today = UtilTime().today.shift(days=-1)

        for order in Order.objects.select_for_update().filter(createtime__lte=today.timestamp,status='9'):
            order.status = '8'
            order.save()

        logger.info("晚上批量处理成功!")

    @list_route(methods=['POST'])
    @Core_connector(isTransaction=True, isPasswd=False)
    def OrderCanleSys(self, request):
        print("30分钟取消订单[{}]".format(request.data_format.get("orderid")))
        try:
            order = Order.objects.select_for_update().get(orderid=request.data_format.get("orderid"))
        except Order.DoesNotExist:
            raise PubErrorCustom("订单号不存在!")
        if order.status == '0':
            OrderBase(order=order).callbackStock()
            order.status = '9'
            order.save()
        else:
            raise PubErrorCustom("只能未付款订单才能取消！")


        return None

    @list_route(methods=['POST'])
    @Core_connector(isTransaction=True, isPasswd=True, isTicket=True)
    def OrderCanle(self, request):

        try:
            order = Order.objects.select_for_update().get(orderid=request.data_format.get("orderid"))
        except Order.DoesNotExist:
            raise PubErrorCustom("订单号不存在!")
        if order.status == '0':
            OrderBase(order=order).callbackStock()
            order.status = '9'
            order.save()
        else:
            raise PubErrorCustom("只能未付款订单才能取消！")

        return None

    @list_route(methods=['POST'])
    @Core_connector(isTransaction=True, isPasswd=True, isTicket=True)
    def OrderPrint(self, request):

        Order.objects.filter(orderid=request.data_format.get("orderid")).update(isprint='0')

    @list_route(methods=['POST'])
    @Core_connector(isTransaction=True, isPasswd=True, isTicket=True)
    def OrderDel(self, request):
        try:
            order = Order.objects.select_for_update().get(orderid=request.data_format.get("orderid"))
        except Order.DoesNotExist:
            raise PubErrorCustom("订单号不存在!")
        if order.status == '0':
            OrderBase(order=order).callbackStock()
            order.status = '8'
            order.save()
        else:
            raise PubErrorCustom("错误!")

        return None

    @list_route(methods=['POST'])
    @Core_connector(isTransaction=True, isPasswd=True, isTicket=True)
    def RefundConfirmCanleHandler(self, request):
        """
        退款拒绝
        :param request:
        :return:
        """
        orderid = request.data_format.get("orderid", None)

        try:
            order = Order.objects.select_for_update().get(orderid=orderid)
            if order.before_status!='1':
                raise PubErrorCustom("只允许通过已申请退款的订单!")
            order.before_status = '3'
            order.save()
        except Order.DoesNotExist:
            raise PubErrorCustom("订单异常!")

        return None

    @list_route(methods=['POST'])
    @Core_connector(isTransaction=True,isPasswd=True,isTicket=True)
    def txPayOrderQuery(self, request):

        return wechatPay().orderQuery(request.data_format['orderid'])

    @list_route(methods=['POST','GET'])
    def txPayCallback(self, request):
        try:
            with transaction.atomic():
                wechatPay().callback(request)
            return HttpResponse("""<xml><return_code><![CDATA[SUCCESS]]></return_code>
                                <return_msg><![CDATA[OK]]></return_msg></xml>""",
                            content_type='text/xml', status=200)
        except Exception:
            return HttpResponse("""<xml><return_code><![CDATA[FAIL]]></return_code>                          
                                    <return_msg><![CDATA[Signature_Error]]></return_msg></xml>""",
                                         content_type = 'text/xml', status = 200)


    @list_route(methods=['POST','GET'])
    def alipayCallback(self,request):
        try:
            if request.method == "POST":
                with transaction.atomic():
                    AlipayBase().callback(request.data)
                    return HttpResponse('success')
            else:
                with transaction.atomic():
                    AlipayBase().callback(request.query_params)
                    return HttpResponse('success')
        except Exception:
            return HttpResponse('error!')

    @list_route(methods=['POST', 'GET'])
    def alipayCallbackForVip(self, request):
        try:
            if request.method == "POST":
                with transaction.atomic():
                    AlipayBase().callback_vip(request.data)
                    return HttpResponse('success')
            else:
                with transaction.atomic():
                    AlipayBase().callback_vip(request.query_params)
                    return HttpResponse('success')
        except Exception:
            return HttpResponse('error!')

    @list_route(methods=['GET'])
    @Core_connector(isPasswd=True,isTicket=True)
    def getCardForOrder(self, request):

        if not request.query_params_format.get("id"):
            raise PubErrorCustom("系统错误,请联系客服人员!")

        try:
            obj = OrderGoodsLink.objects.get(linkid=request.query_params_format.get("id"))
        except OrderGoodsLink.DoesNotExist:
            raise PubErrorCustom("系统错误,请联系客服人员!")

        return {"data": json.loads(obj.virtualids).get('ids')}

    @list_route(methods=['GET'])
    @Core_connector(isPasswd=True,isTicket=True)
    def wlQuery(self, request):

        try:
            order = Order.objects.get(orderid=request.query_params_format.get("orderid"))
        except Order.DoesNotExist:
            raise PubErrorCustom("订单号不存在!")
        return {"data":fastMail().query(order.kdname,order.kdno)}

    @list_route(methods=['GET'])
    @Core_connector(isPasswd=True,isTicket=True)
    def OrderGet(self, request):

        if request.user['role']['rolecode'] in ['1000','1200']:
            orderQuery = Order.objects.filter()
        else:
            orderQuery = Order.objects.filter(userid=request.user['userid'])

        status=request.query_params_format.get("status")
        if status:
            if status == 1:
                orderQuery = orderQuery.filter(status='0')
            elif status == 2:
                orderQuery = orderQuery.filter(status='1')
            elif status == 3:
                orderQuery = orderQuery.filter(status='2')
            elif status == 4:
                orderQuery = orderQuery.filter(status__in=['3','4'])
        if request.query_params_format.get("orderid"):
            orderQuery = orderQuery.filter(orderid=request.query_params_format.get("orderid"))

        if request.query_params_format.get("time"):
            print(request.query_params_format.get("time"))
            start_date = request.query_params_format.get("time").split("&&")[0]
            end_date = request.query_params_format.get("time").split("&&")[1]
            orderQuery = orderQuery.filter(createtime__gte=UtilTime().string_to_timestamp(start_date),createtime__lte=UtilTime().string_to_timestamp(end_date))

        page=int(request.query_params_format.get("page",1))

        page_size = request.query_params_format.get("page_size",10)
        page_start = page_size * page  - page_size
        page_end = page_size * page

        query=orderQuery.order_by('-createtime')

        return {
            "data":OrderModelSerializer(query[page_start:page_end],many=True).data
        }

    @list_route(methods=['GET'])
    @Core_connector(isPasswd=True, isTicket=True)
    def OrderGet1(self, request):

        status = request.query_params_format.get("status")
        time = request.query_params_format.get("time")
        orderid = request.query_params_format.get("orderid")
        mobile = request.query_params_format.get("mobile")
        gdid = request.query_params_format.get("gdid")
        isprint = request.query_params_format.get("isprint")

        query_format = str()
        query_params=[]

        if status:
            if status == 1:
                query_format = query_format + " and t1.status='0'"
            elif status == 2:
                query_format = query_format + " and t1.status='1'"
            elif status == 3:
                query_format = query_format + " and t1.status='2'"
            elif status == 4:
                query_format = query_format + " and t1.status in ('3','4')"

        if time:
            start_date = time.split("&&")[0]
            end_date = time.split("&&")[1]
            query_format = query_format + " and t1.createtime>={} and t1.createtime<={}".format(
                UtilTime().string_to_timestamp(start_date),
                UtilTime().string_to_timestamp(end_date)
            )

        if isprint:
            query_format = query_format + " and t1.isprint='{}'".format(isprint)

        if orderid:
            query_format = query_format + " and t1.orderid='{}'".format(orderid)

        if mobile:
            query_format = query_format + " and t2.mobile='{}'".format(mobile)

        if request.query_params_format.get("address"):
            query_format = query_format + " and t1.address like %s"
            query_params.append("%{}%".format(request.query_params_format.get("address")))

        if gdid:
            query_format = query_format + " and t1.orderid in (SELECT orderid FROM ordergoodslink where gdid='{}')".format(gdid)

        orders = Order.objects.raw("""
            SELECT t1.*,t2.mobile FROM `order` as t1
            INNER JOIN user as t2 ON t1.userid=t2.userid
            WHERE 1=1 %s order by t1.createtime desc
        """ % (query_format), query_params)

        page = int(request.query_params_format.get("page", 1))
        page_size = request.query_params_format.get("page_size", 10)
        page_start = page_size * page - page_size
        page_end = page_size * page

        return {
            "data": OrderModelSerializer(orders[page_start:page_end], many=True).data
        }


    @list_route(methods=['POST'])
    @Core_connector(isTransaction=True,isPasswd=True,isTicket=True)
    def OrderConfirm(self, request):

        Order.objects.filter(orderid=request.data_format.get("orderid")).update(status='3')

    @list_route(methods=['GET'])
    @Core_connector(isPasswd=True,isTicket=True)
    def OrderByOrderidQuery(self, request):

        return {
            "data": OrderModelSerializer(Order.objects.get(orderid=request.query_params_format.get("orderid")), many=False).data
        }

    @list_route(methods=['GET'])
    @Core_connector(isPasswd=True,isTicket=True,isPagination=True)
    def queryOrderAll(self,request):

        queryClass = Order.objects.filter()

        return {"data":OrderModelSerializer(queryClass.order_by('-createtime'),many=True).data}


    @list_route(methods=['POST'])
    @Core_connector(isTransaction=True,isPasswd=True,isTicket=True)
    def orderFh(self,request):

        orderid = request.data_format.get("orderid")
        kdno = request.data_format.get("kdno",[])
        if not kdno or not len(kdno):
            raise PubErrorCustom("快递单号不能为空!")
        try:
            obj = Order.objects.get(orderid=orderid)
            obj.kdno = json.dumps(kdno)
            obj.status='2'
            obj.fhtime = UtilTime().timestamp
            obj.save()
        except Order.DoesNotExist:
            raise PubErrorCustom("订单不存在!")
        return None

    @list_route(methods=['POST'])
    @Core_connector(isTransaction=True, isPasswd=True, isTicket=True)
    def orderFhSaveGoods(self, request):

        orderid = request.data_format.get("orderid")
        kdno = request.data_format.get("kdno")

        links = request.data_format.get("links")

        for item in links:
            try:
                linkObj = OrderGoodsLink.objects.select_for_update().get(linkid=item['linkid'])
                linkObj.goodsqrcode = json.dumps(item.get("goodsqrcode"))
                linkObj.save()
            except OrderGoodsLink.DoesNotExist:
                pass

        if kdno and len(kdno):
            try:
                obj = Order.objects.select_for_update().get(orderid=orderid)
                obj.kdno = json.dumps(kdno)
                obj.save()
            except Order.DoesNotExist:
                raise PubErrorCustom("订单不存在!")

        return None

    @list_route(methods=['POST'])
    @Core_connector(isTransaction=True, isPasswd=True, isTicket=True)
    def orderFhSaveFh(self, request):

        orderid = request.data_format.get("orderid")
        kdno = request.data_format.get("kdno")

        if kdno and len(kdno):
            try:
                obj = Order.objects.select_for_update().get(orderid=orderid)
                obj.kdno = json.dumps(kdno)
                obj.save()
            except Order.DoesNotExist:
                raise PubErrorCustom("订单不存在!")
        return None

    @list_route(methods=['POST'])
    @Core_connector(isTransaction=True,isPasswd=True,isTicket=True)
    def orderFh1(self,request):

        orderid = request.data_format.get("orderid")

        try:
            obj = Order.objects.select_for_update().get(orderid=orderid)
            if not len(obj.kdno):
                raise PubErrorCustom("请先扫发货条形码!")
            obj.status='2'
            obj.fhtime = UtilTime().timestamp
            obj.save()
        except Order.DoesNotExist:
            raise PubErrorCustom("订单不存在!")
        return None

    @list_route(methods=['POST'])
    @Core_connector(isTransaction=True,isPasswd=True,isTicket=True)
    def orderUpdAddress(self,request):

        orderid = request.data_format.get("orderid")
        memo = request.data_format.get("memo")
        try:
            obj = Order.objects.get(orderid=orderid)
            obj.memo = memo
            obj.save()
        except Order.DoesNotExist:
            raise PubErrorCustom("订单不存在!")
        return None


