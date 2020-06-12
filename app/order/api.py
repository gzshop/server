
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
from app.order.models import Order,OrderGoodsLink

from app.user.models import Users
from app.user.serialiers import UsersSerializers

from app.order.serialiers import OrderModelSerializer,AddressModelSerializer,OrderGoodsLinkModelSerializer
from app.order.models import Address
from lib.utils.log import logger
from app.goods.models import Card,Cardvirtual,DeliveryCode,Goods,GoodsLinkSku

from app.order.utils import wechatPay,updBalList,AlipayBase,fastMail,calyf,queryBuyOkGoodsCount
from lib.utils.db import RedisTokenHandler
from lib.utils.mytime import UtilTime

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

        if not len(data['data']['goods']):
            raise PubErrorCustom("购买商品不能为空!")

        if not len(data.get("address")):
            raise PubErrorCustom("收货地址不能为空!")

        orderObj = Order.objects.create(**dict(
            userid=request.user['userid'],
            # yf=data['data'].get("yf"),
            address=json.dumps(data.get("address",{})),
            memo=data.get("memo","")
        ))
        orderObj.linkid={"linkids":[]}
        orderObj.amount = Decimal("0.0")
        orderObj.yf = Decimal("0.0")

        for item in data['data']['goods']:
            try:
                goods = Goods.objects.get(gdid=item.get("gdid"), gdstatus='0')
            except Goods.DoesNotExist:
                raise PubErrorCustom("该商品已下架!")

            try:
                glink = GoodsLinkSku.objects.get(id=item.get("linkid"))
                if glink.stock < 1:
                    raise PubErrorCustom("商品({})库存不够!".format(goods.gdname))
            except Goods.DoesNotExist:
                raise PubErrorCustom("商品({})规格已下架!".format(goods.gdname))

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
            orderObj.yf += Decimal(str(calyf(goods.yf)))

        orderObj.amount += orderObj.yf
        orderObj.linkid=json.dumps(orderObj.linkid)
        orderObj.save()

        return {"data":orderObj.orderid}

    @list_route(methods=['POST'])
    @Core_connector(isTransaction=True,isPasswd=True,isTicket=True)
    def PayHandler(self, request):

        payType = request.data_format.get("payType",None)
        orderid = request.data_format.get("orderid",None)

        if not payType:
            raise PubErrorCustom("支付方式有误!")

        ut = UtilTime()
        end = ut.timestamp
        try:
            order = Order.objects.select_for_update().get(orderid=orderid)
            if order.status=='1':
                raise PubErrorCustom("此订单已付款!")

            for item in OrderGoodsLink.objects.filter(linkid__in=json.loads(order.linkid)['linkids']):
                try:
                    goodsObj = Goods.objects.get(gdid=item.gdid)
                    if goodsObj.limit_unit == 'M':
                        start = ut.today.shift(months=goodsObj.limit_count*-1).timestamp
                    elif goodsObj.limit_unit == 'W':
                        start = ut.today.shift(weeks=goodsObj.limit_count*-1).timestamp

                    okcount = queryBuyOkGoodsCount(order.userid,goodsObj.gdid,start,end)
                    logger.info("目前购买->{},实际已购买->{},规则数量->{}".format(item.gdnum,okcount,goodsObj.limit_number))
                    if item.gdnum+okcount > goodsObj.limit_number:
                        raise PubErrorCustom("{},库存不够!".format(goodsObj.gdname))

                except Goods.DoesNotExist:
                    raise PubErrorCustom("商品{}已下架!".format(goodsObj.gdname))

            order.paytype = str(payType)
            order.save()
        except Order.DoesNotExist:
            raise PubErrorCustom("订单异常!")

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

            AlipayBase().refund(order=order,orderid=order.orderid, refund_amount=order.amount)
        except Order.DoesNotExist:
            raise PubErrorCustom("订单异常!")

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

        page=int(request.query_params_format.get("page",1))

        page_size = request.query_params_format.get("page_size",10)
        page_start = page_size * page  - page_size
        page_end = page_size * page

        query=orderQuery.order_by('-createtime')

        return {
            "data":OrderModelSerializer(query[page_start:page_end],many=True).data
        }

    @list_route(methods=['POST'])
    @Core_connector(isTransaction=True,isPasswd=True,isTicket=True)
    def OrderConfirm(self, request):
        Order.objects.filter(orderid=request.data_format.get("orderid")).update(status='3')
        return None

    @list_route(methods=['POST'])
    @Core_connector(isTransaction=True,isPasswd=True,isTicket=True)
    def OrderCanle(self, request):
        Order.objects.filter(orderid=request.data_format.get("orderid")).update(status='9')
        return None

    @list_route(methods=['POST'])
    @Core_connector(isTransaction=True,isPasswd=True,isTicket=True)
    def OrderDel(self, request):
        Order.objects.filter(orderid=request.data_format.get("orderid")).update(status='8')
        return None

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
    def cardCz(self,request):

        rUser=None
        account = request.data_format['account']
        password = request.data_format['password']

        try:
            card = Card.objects.select_for_update().get(account=account,password=password,type='0')
            if card.useuserid>0:
                return {"data": {"a": False}}
        except Card.DoesNotExist:
            return {"data":False}
        try:
            user = Users.objects.select_for_update().get(userid=request.user['userid'])
        except Users.DoesNotExist:
            raise PubErrorCustom("用户非法!")


        tmp = user.bal
        user.bal += card.bal


        if card.rolecode == user.rolecode:
            flag = False
        else:
            request.user['rolecode'] = card.rolecode
            RedisTokenHandler(key=request.ticket).redis_dict_set(request.user)
            rUser =  UsersSerializers(user, many=False).data
            flag = True

        updBalList(user=user, order=None, amount=card.bal, bal=tmp, confirm_bal=user.bal, memo="充值卡充值",cardno=card.account)

        user.rolecode = card.rolecode
        user.save()

        card.useuserid = user.userid
        card.save()

        RedisCaCheHandler(
            method="save",
            serialiers="CardModelSerializerToRedis",
            table="card",
            filter_value=card,
            must_key="id",
        ).run()

        return {"data":{"a":True,"b":flag,"rUser":rUser}}


    @list_route(methods=['POST'])
    @Core_connector(isTransaction=True,isPasswd=True,isTicket=True)
    def orderFh(self,request):
        orderid = request.data_format.get("orderid")
        kdno = request.data_format.get("kdno")
        if not kdno:
            raise PubErrorCustom("快递单号不能为空!")
        try:
            obj = Order.objects.get(orderid=orderid)
            obj.kdno = kdno
            obj.status='2'
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


