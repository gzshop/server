
import json
from rest_framework import serializers
from rest_framework.validators import UniqueTogetherValidator
from app.user.models import Users,Role,VipRule
from lib.utils.mytime import UtilTime



class ManageSerializer(serializers.Serializer):

    userid = serializers.IntegerField()
    name = serializers.CharField()
    uuid = serializers.CharField()
    passwd = serializers.CharField()
    createtime_format = serializers.SerializerMethodField()
    rolename = serializers.SerializerMethodField()

    def get_rolename(self,obj):
        try:
            return Role.objects.get(rolecode=obj.rolecode).name
        except Role.DoesNotExist:
            return ""

    def get_createtime_format(self,obj):
        return UtilTime().timestamp_to_string(obj.createtime)

class RoleModelSerializer(serializers.ModelSerializer):

    class Meta:
        model = Role
        fields = '__all__'

class UsersSerializers(serializers.Serializer):

    userid = serializers.IntegerField()
    pic = serializers.CharField()
    name = serializers.CharField()
    bal = serializers.DecimalField(max_digits=16, decimal_places=2)
    jf = serializers.DecimalField(max_digits=16, decimal_places=2)
    rolecode = serializers.IntegerField()
    isvip = serializers.CharField()
    unit_format = serializers.SerializerMethodField()
    exprise = serializers.SerializerMethodField()

    def get_exprise(self,obj):
        return UtilTime().timestamp_to_string(obj.exprise) if obj.exprise else ""

    def get_unit_format(self,obj):

        if obj.isvip == '1':
            if obj.unit == '0':
                return "{}周".format(obj.term)
            elif obj.unit == '1':
                return "{}月".format(obj.term)
            else:
                return "{}年".format(obj.term)
        else:
            return ""


class UsersModelSerializer(serializers.ModelSerializer):

    createtime_format = serializers.SerializerMethodField()
    bal = serializers.DecimalField(max_digits=16, decimal_places=2)

    rolename = serializers.SerializerMethodField()

    exprise_format = serializers.SerializerMethodField()


    def get_exprise_format(self,obj):

        return UtilTime().timestamp_to_string(obj.exprise)

    def get_rolename(self,obj):
        try:
            roleObj = Role.objects.get(rolecode=obj.rolecode)
            return roleObj.name
        except Role.DoesNotExist:
            return "未知"

    def get_createtime_format(self,obj):
        return UtilTime().timestamp_to_string(obj.createtime)

    class Meta:
        model = Users
        fields = '__all__'

class VipRuleModelSerializer(serializers.ModelSerializer):

    class Meta:
        model = VipRule
        fields = '__all__'

class VipRuleModelSerializer1(serializers.ModelSerializer):

    amount = serializers.DecimalField(max_digits=18,decimal_places=2)
    unit_format = serializers.SerializerMethodField()


    def get_unit_format(self,obj):

        if obj.unit == '0':
            return "周"
        elif obj.unit == '1':
            return "月"
        else:
            return "年"

    class Meta:
        model = VipRule
        fields = '__all__'