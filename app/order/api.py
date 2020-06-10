
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

from app.goods.models import Card,Cardvirtual,DeliveryCode,Goods,GoodsLinkSku

from app.order.utils import wechatPay
from lib.utils.db import RedisTokenHandler
from app.order.utils import updBalList,AlipayBase

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
            yf=data['data'].get("yf"),
            address=json.dumps(data.get("address",{})),
            memo=data.get("memo","")
        ))
        orderObj.linkid={"linkids":[]}
        orderObj.amount = Decimal("0.0")

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

        orderObj.amount += orderObj.yf
        orderObj.linkid=json.dumps(orderObj.linkid)
        orderObj.save()

        return {"data":orderObj.orderid}

    @list_route(methods=['POST'])
    @Core_connector(isTransaction=True,isPasswd=True,isTicket=True)
    def PayHandler(self, request):


        payType = request.data_format.get("payType",None)
        orderid = request.data_format.get("orderid",None)

        try:
            order = Order.objects.select_for_update().get(orderid=orderid)
            if order.status=='1':
                raise PubErrorCustom("此订单已付款!")
        except Order.DoesNotExist:
            raise PubErrorCustom("订单异常!")

        if not payType:
            raise PubErrorCustom("支付方式有误!")

        if payType == 2:
            return {"data":AlipayBase().create(order.orderid,order.amount)}
        else:
            raise PubErrorCustom("支付方式有误!")

    @list_route(methods=['POST'])
    @Core_connector(isTransaction=True,isPasswd=True,isTicket=True)
    def OrderPaysByOrder(self, request):

        if not request.data_format.get('orderid',None):
            raise PubErrorCustom("订单号为空!")

        try:
            user = Users.objects.select_for_update().get(userid=request.user.get("userid"))
        except Users.DoesNotExist:
            raise PubErrorCustom("用户不存在!")

        try:
            order = Order.objects.select_for_update().get(orderid=request.data_format.get('orderid',None))
            order.address = json.dumps(request.data_format.get('address',{}))
            order.memo = request.data_format.get("memo","")
            if order.status=='1':
                raise PubErrorCustom("此订单已付款!")
        except Order.DoesNotExist:
            raise PubErrorCustom("订单异常!")

        for item in OrderGoodsLink.objects.filter(linkid__in=json.loads(order.linkid)['linkids']).order_by("-updtime"):
            #是虚拟商品
            if item.virtual == '0':
                cards = Cardvirtual.objects.filter(gdid=item.gdid,status='1').order_by('createtime')
                if cards.exists():
                    if len(cards) < item.gdnum:
                        raise PubErrorCustom("暂无存货!")

                    virtualids = json.loads(item.virtualids)
                    count = 0
                    for card in cards:
                        count +=1
                        virtualids['ids'].append({"id":card.id,"account":card.account,"password":card.account})
                        card.status = '0'
                        card.useuserid = user.userid
                        card.save()
                        if count == item.gdnum:
                            break
                    item.virtualids = json.dumps(virtualids)
                    item.save()
                else:
                    raise PubErrorCustom("暂无存货!")

        amount = Decimal(str(order.amount))

        order.balamount = 0.0
        order.payamount = 0.0

        if request.data_format.get('usebal'):
            if user.bal >= amount:
                tmp = user.bal
                user.bal -= amount
                order.balamount = amount
                order.status = '1'
                if order.isvirtual == '0':
                    order.fhstatus = '0'
                updBalList(user, order, order.amount, tmp, user.bal, "余额支付")
                user.save()
                order.save()
                return {"data":{"usebalall":True}}
            else:
                print(user.bal,amount)
                amount -= user.bal
                print(amount)
                order.balamount = user.bal
                order.payamount = amount
                order.save()
        else:
            order.payamount = amount
            order.save()
        print(amount)
        #request.META.get("HTTP_X_REAL_IP"),
        data = wechatPay().request({
            "out_trade_no" : order.orderid,
            "total_fee" : int(amount * 100),
            "spbill_create_ip" : request.META.get("HTTP_X_REAL_IP"),
            "openid": user.uuid
        })

        return {"data":data}

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
        print(request.data)
        print(request.query_params)

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
    def OrderGet(self, request):

        orderQuery = Order.objects.filter(userid=request.user['userid'])
        status=request.query_params_format.get("status")
        if status:
            if status == 1:
                orderQuery = orderQuery.filter(status='0')
            elif status == 2:
                orderQuery = orderQuery.filter(status='1')
            elif status == 3:
                orderQuery = orderQuery.filter(status='9')
        if request.query_params_format.get("orderid"):
            orderQuery = orderQuery.filter(orderid=request.query_params_format.get("orderid"))

        page=int(request.query_params_format.get("page",1))

        page_size = request.query_params_format.get("page_size",10)
        page_start = page_size * page  - page_size
        page_end = page_size * page



        query=orderQuery.exclude(status='8').order_by('-createtime')


        return {
            "data":OrderModelSerializer(query[page_start:page_end],many=True).data
        }

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
        orders = Order.objects.filter(orderid__in=request.data_format.get("orders"))
        for item in orders:
            item.fhstatus = '0'
            item.save()

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


