
from project.config_include.common import ServerUrl
from rest_framework import viewsets
from rest_framework.decorators import list_route
from lib.utils.mytime import send_toTimestamp
from lib.core.decorator.response import Core_connector
from lib.utils.exceptions import PubErrorCustom
from app.user.serialiers import UsersSerializers

from app.cache.utils import RedisCaCheHandler
from app.user.serialiers import UsersModelSerializer,RoleModelSerializer,VipRuleModelSerializer,VipRuleModelSerializer1
from app.user.models import Users,Role,VipRule
from lib.utils.db import RedisUserVipHandler

class UserAPIView(viewsets.ViewSet):

    @list_route(methods=['GET'])
    @Core_connector(isTicket=True,isPasswd=True)
    def getUserInfo(self, request):



        return {"data": {
            "userInfo": {
                "username": request.user.get("uuid"),
                "name": request.user.get("name"),
                'rolecode': request.user.get("role").get("rolecode"),
                "rolename": request.user.get("role").get("rolename"),
                "avatar": ServerUrl+'/statics/images/pic.jpg',
                'roles': [ {"name":item.name,"rolecode":item.rolecode} for item in Role.objects.filter(rolecode__startswith='4')]
            },
            "roles": request.user.get("role").get("rolecode"),
            "permission": []
        }}

    @list_route(methods=['GET'])
    @Core_connector(isTicket=True,isPasswd=True)
    def getUser(self, request):

        query = Users.objects.filter(rolecode__startswith='4')
        if request.query_params_format.get("userid"):
            query = query.filter(userid=request.query_params_format.get("userid"))

        if request.query_params_format.get("mobile"):
            query = query.filter(mobile=request.query_params_format.get("mobile"))

        if request.query_params_format.get("startdate") and request.query_params_format.get("enddate"):
            query = query.filter(
                createtime__lte=send_toTimestamp(request.query_params_format.get("enddate")),
                createtime__gte=send_toTimestamp(request.query_params_format.get("startdate")))

        page = int(request.query_params_format.get("page", 1))

        page_size = request.query_params_format.get("page_size", 10)
        page_start = page_size * page - page_size
        page_end = page_size * page

        res = query.order_by('-createtime')
        headers = {
            'Total': res.count(),
        }

        return {
            "data": UsersModelSerializer(res[page_start:page_end], many=True).data,
            "header": headers
        }

    @list_route(methods=['POST'])
    @Core_connector(isTicket=True,isPasswd=True,isTransaction=True)
    def updPassword(self, request):

        if not request.data_format.get("passwd",None):
            raise PubErrorCustom("密码是空!")

        try:
            obj = Users.objects.get(userid=request.user['userid'])
            obj.passwd = request.data_format['passwd']
            obj.save()
        except Users.DoesNotExist:
            raise PubErrorCustom("用户不存在!")

        return None

    @list_route(methods=['GET'])
    @Core_connector(isTicket=True,isPasswd=True)
    def GetBal(self, request):
        try:
            user = Users.objects.get(userid=request.user['userid'])
        except Users.DoesNotExist:
            raise PubErrorCustom("用户不存在!")

        return {"data": UsersSerializers(user, many=False).data}

    @list_route(methods=['GET'])
    @Core_connector(isTicket=True,isPasswd=True,isPagination=True)
    def GetRole(self, request):
        query = Role.objects.filter(rolecode__startswith='4')

        return {"data": RoleModelSerializer(query,many=True).data}

    @list_route(methods=['POST'])
    @Core_connector(isTicket=True,isPasswd=True,isTransaction=True)
    def SaveRole(self, request):
        print(request.data_format)
        if not request.data_format.get("rolecode"):
            obj = Role.objects.filter(rolecode__startswith='4')
            rObj = [ int(item.rolecode) for item in obj ]
            maxRole = max(rObj)
            rolecode = str(maxRole + 1)

            Role.objects.create(**{
                "rolecode" : rolecode,
                "roletype":"4",
                "name":request.data_format.get("name")
            })
        else:
            Role.objects.filter(rolecode=request.data_format.get("rolecode")).update(name=request.data_format.get("name"))

        return None

    @list_route(methods=['GET'])
    @Core_connector(isTicket=True, isPasswd=True,isPagination=True)
    def get_vip_rule(self, request):

        query = VipRule.objects.filter()

        if request.query_params_format.get("id",None):
            query = query.filter(id=request.query_params_format.get("id",None))

        return {"data":VipRuleModelSerializer1(query.order_by('unit','term'),many=True).data}

    @list_route(methods=['POST'])
    @Core_connector(isTransaction=True,
                    isPasswd=True,
                    isTicket=True,
                    serializer_class=VipRuleModelSerializer,
                    model_class=VipRule)
    def save_vip_rule(self, request, *args, **kwargs):

        serializer = kwargs.pop("serializer")
        serializer.save()

        return None

    @list_route(methods=['POST'])
    @Core_connector(isTransaction=True,isTicket=True,isPasswd=True)
    def del_vip_rule(self,request,*args, **kwargs):

        VipRule.objects.filter(id=request.data_format.get("id")).delete()

        return None