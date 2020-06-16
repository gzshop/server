
import json
from rest_framework import serializers

from lib.utils.mytime import UtilTime
from lib.utils.exceptions import PubErrorCustom
from app.user.models import Users,Role
from app.public.models import Banner,AttachMentGroup,AttachMent,OtherMemo
from app.goods.models import GoodsCateGory,Goods,GoodsTheme,Card,SkuKey,SkuValue

class UserModelSerializerToRedis(serializers.ModelSerializer):

    role = serializers.SerializerMethodField()
    createtime_format = serializers.SerializerMethodField()
    bal = serializers.SerializerMethodField()

    isvip_format = serializers.SerializerMethodField()

    def get_role(self,obj):
        try:
            roleObj = Role.objects.get(rolecode=obj.rolecode)
            return RoleModelSerializerToRedis(roleObj,many=False).data
        except Role.DoesNotExist:
            raise PubErrorCustom("无此角色信息!")

    def get_isvip_format(self,obj):
        if str(obj.isvip) == "1":
            return "是"
        else:
            return "否"

    def get_createtime_format(self,obj):
        return UtilTime().timestamp_to_string(obj.createtime)

    def get_bal(self,obj):
        return round(float(obj.bal),2)

    class Meta:
        model = Users
        fields = '__all__'

class RoleModelSerializerToRedis(serializers.ModelSerializer):

    class Meta:
        model = Role
        fields = '__all__'

class BannerModelSerializerToRedis(serializers.ModelSerializer):

    class Meta:
        model = Banner
        fields = '__all__'

class GoodsCateGoryModelSerializerToRedis(serializers.ModelSerializer):

    createtime_format = serializers.SerializerMethodField()
    status_format = serializers.SerializerMethodField()

    rolename = serializers.SerializerMethodField()

    def get_rolename(self,obj):
        t =[]
        s = Role.objects.filter(rolecode__in=json.loads(obj.rolecode)['rolecode'])
        if s.exists:
            for item in s:
                t.append(item.name)

        return t

    def get_status_format(self,obj):
        return '是' if obj.status == '0' else '否'

    def get_createtime_format(self,obj):
        return UtilTime().timestamp_to_string(obj.createtime)

    class Meta:
        model = GoodsCateGory
        fields = '__all__'

class GoodsThemeModelSerializerToRedis(serializers.ModelSerializer):

    createtime_format = serializers.SerializerMethodField()
    status_format = serializers.SerializerMethodField()

    rolename = serializers.SerializerMethodField()

    def get_rolename(self,obj):
        t =[]
        s = Role.objects.filter(rolecode__in=json.loads(obj.rolecode)['rolecode'])
        if s.exists:
            for item in s:
                t.append(item.name)

        return t

    def get_status_format(self,obj):
        return '是' if obj.status == '0' else '否'

    def get_createtime_format(self,obj):
        return UtilTime().timestamp_to_string(obj.createtime)

    class Meta:
        model = GoodsTheme
        fields = '__all__'


class GoodsModelSerializerToRedis(serializers.ModelSerializer):

    createtime_format = serializers.SerializerMethodField()

    gdprice = serializers.DecimalField(max_digits=16,decimal_places=2)

    gdstatus_format = serializers.SerializerMethodField()

    virtual_format = serializers.SerializerMethodField()

    rolename = serializers.SerializerMethodField()

    gdimg = serializers.SerializerMethodField()

    gdsku = serializers.SerializerMethodField()
    gdskulist = serializers.SerializerMethodField()

    limit_citys = serializers.SerializerMethodField()

    jf_value = serializers.DecimalField(max_digits=16,decimal_places=2)

    # gdcgname = serializers.SerializerMethodField()
    #
    # def get_gdcgname(self,obj):
    #     try:
    #         return GoodsCateGory.objects.get(gdcgid=obj.gdcgid).name
    #     except GoodsCateGory.DoesNotExist:
    #         return ""


    def get_limit_citys(self,obj):
        return json.loads(obj.limit_citys)

    def get_gdsku(self,obj):
        d=json.loads(obj.gdsku)
        for item in d:
            for item1 in item['attributeValueList']:
                item1['pid'] = item['group_id']

        return d

    def get_gdskulist(self,obj):
        return json.loads(obj.gdskulist)

    def get_gdimg(self,obj):

        return json.loads(obj.gdimg)

    def get_virtual_format(self,obj):
        return '是' if obj.virtual == '0' else '否'

    def get_rolename(self,obj):
        try:
            return Role.objects.get(rolecode=obj.rolecode).name
        except Role.DoesNotExist:
            return ""

    def get_gdstatus_format(self,obj):
        return '是' if obj.gdstatus == '0' else '否'

    def get_createtime_format(self,obj):
        return UtilTime().timestamp_to_string(obj.createtime)

    class Meta:
        model = Goods
        fields = '__all__'


class CardModelSerializerToRedis(serializers.ModelSerializer):

    createtime_format = serializers.SerializerMethodField()

    role = serializers.SerializerMethodField()
    # username = serializers.SerializerMethodField()
    bal = serializers.DecimalField(max_digits=18,decimal_places=2)

    # def get_username(self,obj):
    #     return Users.objects.get(userid=obj.useuserid).name if obj.useuserid>0 else ""

    def get_createtime_format(self,obj):
        return UtilTime().timestamp_to_string(obj.createtime)

    def get_role(self,obj):
        try:
            roleObj = Role.objects.get(rolecode=obj.rolecode)
            return RoleModelSerializerToRedis(roleObj,many=False).data
        except Role.DoesNotExist:
            raise PubErrorCustom("无此角色信息!")

    class Meta:
        model = Card
        fields = '__all__'


class AttachMentGroupModelSerializerToRedis(serializers.ModelSerializer):

    createtime_format = serializers.SerializerMethodField()

    def get_createtime_format(self,obj):
        return UtilTime().timestamp_to_string(obj.createtime)

    class Meta:
        model = AttachMentGroup
        fields = '__all__'

class AttachMentModelSerializerToRedis(serializers.ModelSerializer):

    createtime_format = serializers.SerializerMethodField()

    def get_createtime_format(self,obj):
        return UtilTime().timestamp_to_string(obj.createtime)

    class Meta:
        model = AttachMent
        fields = '__all__'

class OtherMemoModelSerializerToRedis(serializers.ModelSerializer):

    createtime_format = serializers.SerializerMethodField()

    def get_createtime_format(self,obj):
        return UtilTime().timestamp_to_string(obj.createtime)

    class Meta:
        model = OtherMemo
        fields = '__all__'


class SkuKeyModelSerializerToRedis(serializers.ModelSerializer):

    class Meta:
        model = SkuKey
        fields = '__all__'

class SkuValueModelSerializerToRedis(serializers.ModelSerializer):

    class Meta:
        model = SkuValue
        fields = '__all__'