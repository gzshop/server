
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
    payamount = serializers.DecimalField(max_digits=16,decimal_places=2)
    balamount = serializers.DecimalField(max_digits=16,decimal_places=2)

    isthm_format = serializers.SerializerMethodField()

    createtime_format = serializers.SerializerMethodField()

    fhstatus_format = serializers.SerializerMethodField()

    address = serializers.SerializerMethodField()

    def get_isthm_format(self,obj):
        return '是' if obj.isthm=='0' else '否'

    def get_createtime_format(self,obj):
        return UtilTime().timestamp_to_string(obj.createtime)

    def get_linkid(self,obj):

        return OrderGoodsLinkModelSerializer(OrderGoodsLink.objects. \
                   filter(linkid__in=json.loads(obj.linkid)['linkids']).order_by("-updtime"), many=True).data

    def get_address(self,obj):
        return json.loads(obj.address)

    def get_status_format(self,obj):
        return "已付款" if obj.status=='1' else '待付款'

    def get_fhstatus_format(self,obj):
        return "已发货" if obj.fhstatus=='0' else '待发货'


    class Meta:
        model = Order
        fields = '__all__'