
from rest_framework import serializers
from rest_framework.validators import UniqueTogetherValidator
from app.goods.models import GoodsCateGory,Goods,GoodsTheme,Card,Cardvirtual,DeliveryCode,SkuValue,SkuKey,GoodsLinkSku
from lib.utils.mytime import UtilTime
import json



class GoodsLinkSkuSearchSerializer(serializers.Serializer):
    id=serializers.IntegerField()
    active_num = serializers.SerializerMethodField()
    price = serializers.SerializerMethodField()
    sku_code = serializers.SerializerMethodField()
    origin_price = serializers.SerializerMethodField()
    sale_num = serializers.SerializerMethodField()
    sortNum = serializers.SerializerMethodField()
    id1 = serializers.SerializerMethodField()
    specValue1  = serializers.SerializerMethodField()
    specValue2 = serializers.SerializerMethodField()
    specValue3 = serializers.SerializerMethodField()
    specValueId1  = serializers.SerializerMethodField()
    specValueId2 = serializers.SerializerMethodField()
    specValueId3 = serializers.SerializerMethodField()
    jf = serializers.DecimalField(max_digits=18,decimal_places=2)

    def get_specValueId1(self, obj):
        return obj.valueid1

    def get_specValueId2(self, obj):
        return obj.valueid2

    def get_specValueId3(self, obj):
        return obj.valueid3

    def get_specValue1(self,obj):
        return SkuValue.objects.get(id=obj.valueid1).value if obj.valueid1>0 else ""

    def get_specValue2(self,obj):
        return SkuValue.objects.get(id=obj.valueid2).value if obj.valueid2>0 else ""

    def get_specValue3(self,obj):
        return SkuValue.objects.get(id=obj.valueid3).value if obj.valueid3>0 else ""

    def get_id1(self,obj):
        return obj.valueid1 if obj.valueid2>0 else 0

    def get_sortNum(self,obj):
        return obj.sort

    def get_sale_num(self,obj):
        return obj.number

    def get_price(self,obj):
        return round(obj.price,2)

    def get_origin_price(self,obj):
        return round(obj.cost_price,2)

    def get_sku_code(self,obj):
        return obj.code

    def get_active_num(self,obj):

        return obj.stock


class GoodsCateGoryModelSerializer(serializers.ModelSerializer):


    class Meta:
        model = GoodsCateGory
        fields = '__all__'

class SkuValueModelSerializer(serializers.ModelSerializer):


    class Meta:
        model = SkuValue
        fields = '__all__'

class SkuKeyGoryModelSerializer(serializers.ModelSerializer):

    class Meta:
        model = SkuKey
        fields = '__all__'

class GoodsThemeModelSerializer(serializers.ModelSerializer):

    class Meta:
        model = GoodsTheme
        fields = '__all__'

class GoodsModelSerializer(serializers.ModelSerializer):

    class Meta:
        model = Goods
        fields = '__all__'

class GoodsForSearchSerializer(serializers.Serializer):

    gdid = serializers.CharField()
    gdname = serializers.CharField()
    gdprice = serializers.DecimalField(max_digits=16,decimal_places=2)
    gdimg = serializers.SerializerMethodField()
    gdtext = serializers.CharField()

    def get_gdimg(self,obj):
        return json.loads(obj.gdimg)


class CardModelSerializer(serializers.ModelSerializer):

    class Meta:
        model = Card
        fields = '__all__'

class CardvirtualModelSerializer(serializers.ModelSerializer):

    createtime_format = serializers.SerializerMethodField()
    status_format = serializers.SerializerMethodField()

    def get_status_format(self,obj):
        return '是' if obj.status == '0' else '否'

    def get_createtime_format(self,obj):
        return UtilTime().timestamp_to_string(obj.createtime)

    class Meta:
        model = Cardvirtual
        fields = '__all__'


class DeliveryCodeModelSerializer(serializers.ModelSerializer):

    createtime_format = serializers.SerializerMethodField()
    status_format = serializers.SerializerMethodField()

    def get_status_format(self,obj):
        return '是' if obj.status == '0' else '否'

    def get_createtime_format(self,obj):
        return UtilTime().timestamp_to_string(obj.createtime)

    class Meta:
        model = DeliveryCode
        fields = '__all__'