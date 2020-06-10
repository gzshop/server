
from project.config_include.common import ServerUrl
from rest_framework import viewsets
from rest_framework.decorators import list_route
from lib.utils.mytime import send_toTimestamp
from lib.core.decorator.response import Core_connector
from lib.utils.exceptions import PubErrorCustom

from app.cache.utils import RedisCaCheHandler
from app.user.serialiers import UsersModelSerializer,RoleModelSerializer
from app.user.models import Users,Role

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