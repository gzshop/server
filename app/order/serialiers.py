
import json
from rest_framework import serializers
from app.order.models import ShopCart,OrderGoodsLink,Order,Address
from lib.utils.mytime import UtilTime

class AddressModelSerializer(serializers.ModelSerializer):

    class Meta:
        model = Address
        fields = '__all__'

class AddressSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    userid = serializers.IntegerField()
    name = serializers.CharField()
    phone = serializers.CharField()
    detail = serializers.CharField()
    label = serializers.CharField()
    moren = serializers.CharField()

class ShopCartModelSerializer(serializers.ModelSerializer):


    gdprice = serializers.DecimalField(max_digits=16,decimal_places=2)


    class Meta:
        model = ShopCart
        fields = '__all__'

class OrderGoodsLinkModelSerializer(serializers.ModelSerializer):


    gdprice = serializers.DecimalField(max_digits=16,decimal_places=2)
    thms = serializers.SerializerMethodField()

    def get_thms(self,obj):
        return json.loads(obj.thms)['thms'] if obj.thms else []


    class Meta:
        model = OrderGoodsLink
        fields = '__all__'

class OrderModelSerializer(serializers.ModelSerializer):


    linkid = serializers.SerializerMethodField()
    status_format = serializers.SerializerMethodField()

    amount = serializers.DecimalField(max_digits=16,decimal_places=2)
    yf = serializers.DecimalField(max_digits=16,decimal_places=2)
    payamount = serializers.DecimalField(max_digits=16,decimal_places=2)
    balamount = serializers.DecimalField(max_digits=16,decimal_places=2)

    bstatusformat = serializers.SerializerMethodField()
    before_status_format = serializers.SerializerMethodField()

    isthm_format = serializers.SerializerMethodField()

    createtime_format = serializers.SerializerMethodField()

    fhstatus_format = serializers.SerializerMethodField()

    address = serializers.SerializerMethodField()
    state = serializers.SerializerMethodField()
    mobile = serializers.CharField()

    payamount1 = serializers.SerializerMethodField()

    def get_bstatusformat(self,obj):
        if obj.before_status == '1':
            return " 申请退款中"
        elif obj.before_status == '3':
            return " 申请退款被拒绝"
        return ""

    def get_before_status_format(self,obj):
        if obj.before_status == '1':
            return " 申请退款中"
        elif obj.before_status == '3':
            return " 申请退款被拒绝"
        elif obj.before_status == '2':
            return "申请退款通过"
        return ""
    def get_state(self,obj):
        return obj.status

    def get_payamount1(self,obj):
        return round(obj.amount + obj.yf,2)

    def get_isthm_format(self,obj):
        return '是' if obj.isthm=='0' else '否'

    def get_createtime_format(self,obj):
        return UtilTime().timestamp_to_string(obj.createtime)

    def get_linkid(self,obj):

        return OrderGoodsLinkModelSerializer(OrderGoodsLink.objects. \
                   filter(linkid__in=json.loads(obj.linkid)['linkids']).order_by("-updtime"), many=True).data

    def get_address(self,obj):
        r=json.loads(obj.address)

        return r if len(r) else False

    def get_status_format(self,obj):
        if obj.status=='0':
            return "待付款"
        elif obj.status=='1':
            return "已付款(待发货)"
        elif obj.status=='2':
            return "已发货(待收货)"
        elif obj.status=='3':
            return "已收货"
        elif obj.status=='4':
            return "已退款"
        elif obj.status=='9':
            return "取消订单"
        else:
            return "未知"

    def get_fhstatus_format(self,obj):
        return "已发货" if obj.fhstatus=='0' else '待发货'


    class Meta:
        model = Order
        fields = '__all__'


class OrderGoodsLinkModelSerializer1(serializers.Serializer):


    gdtotprice = serializers.SerializerMethodField()
    gdprice = serializers.DecimalField(max_digits=16,decimal_places=2)
    gdname = serializers.CharField()
    gdnum = serializers.IntegerField()
    skugoodslabel = serializers.CharField()
    gdimg = serializers.CharField()

    def get_gdtotprice(self,obj):
        return round(obj.gdprice * obj.gdnum,2)

class OrderModelSerializer1(serializers.Serializer):

    orderid = serializers.CharField()
    create_format = serializers.SerializerMethodField()
    mobile = serializers.CharField()
    status = serializers.CharField()
    before_status_format = serializers.SerializerMethodField()
    status_format = serializers.SerializerMethodField()
    goods = serializers.SerializerMethodField()
    amount = serializers.DecimalField(max_digits=16,decimal_places=2)
    yf = serializers.DecimalField(max_digits=16,decimal_places=2)
    address = serializers.SerializerMethodField()
    before_status = serializers.CharField()
    kdno = serializers.CharField()
    memo = serializers.CharField()

    def get_address(self,obj):

        address=json.loads(obj.address)

        return {
            "mobile":address.get("phone","未知"),
            "name":address.get("name","未知"),
            "address": address.get("label","").replace("-","") + address.get("detail",""),
        } if len(address) else False

    def get_before_status_format(self,obj):
        if obj.before_status == '1':
            return " 申请退款中"
        elif obj.before_status == '3':
            return " 申请退款被拒绝"
        elif obj.before_status == '2':
            return "申请退款通过"
        return ""

    def get_goods(self,obj):
        return OrderGoodsLinkModelSerializer1(OrderGoodsLink.objects.filter(orderid=obj.orderid),many=True).data

    def get_status_format(self,obj):
        if obj.status=='0':
            return "待付款"
        elif obj.status=='1':
            return "已付款(待发货)"
        elif obj.status=='2':
            return "已发货(待收货)"
        elif obj.status=='3':
            return "已收货"
        elif obj.status=='4':
            return "已退款"
        elif obj.status=='9':
            return "取消订单"
        else:
            return "未知"

    def get_create_format(self,obj):
        return UtilTime().timestamp_to_string(obj.createtime)