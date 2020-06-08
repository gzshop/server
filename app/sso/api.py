
from rest_framework import viewsets
from rest_framework.decorators import list_route

from lib.core.decorator.response import Core_connector
from lib.utils.exceptions import PubErrorCustom
from lib.utils.db import RedisTokenHandler
from lib.utils.string_extension import get_token
from lib.utils.http_request import send_request_other

from app.user.models import Users
from app.user.serialiers import UsersSerializers
from app.cache.serialiers import UserModelSerializerToRedis

from app.order.serialiers import AddressModelSerializer
from app.order.models import Address

from lib.utils.WXBizDataCrypt import WXBizDataCrypt

from app.idGenerator import idGenerator

from project.config_include.params import WECHAT_SECRET,WECHAT_APPID

from app.public.models import Sysparams

class SsoAPIView(viewsets.ViewSet):

    @list_route(methods=['POST'])
    @Core_connector(isTransaction=True,isPasswd=True)
    def wechatauth(self, request):
        params = dict(
            js_code=request.data_format.get("js_code"),
            appid=WECHAT_APPID,
            secret=WECHAT_SECRET,
            grant_type="authorization_code",
        )
        wechat_res = send_request_other(
            url="https://api.weixin.qq.com/sns/jscode2session",
            params=params)
        print(wechat_res)
        if not wechat_res.get("openid"):
            raise PubErrorCustom("获取用户错误,腾讯接口有误!")

        data={}
        token=False
        address={}
        try:
            user=Users.objects.get(uuid=wechat_res.get('openid'))
            data = UsersSerializers(user,many=False).data

            token = get_token()
            res = UserModelSerializerToRedis(user, many=False).data
            RedisTokenHandler(key=token).redis_dict_set(res)

            res = Address.objects.filter(userid=user.userid).order_by('-createtime')
            address = AddressModelSerializer(res[0], many=False).data if len(res) else {}
        except Users.DoesNotExist:
            pass

        return {"data":{
            "user" : data,
            "session_key":wechat_res.get("session_key"),
            "token":token,
            "address":address,
            "hylogo":Sysparams.objects.get().url
        }}

    @list_route(methods=['POST'])
    @Core_connector(isTransaction=True,isPasswd=True)
    def wechatlogin(self, request):

        session_key = request.data_format.get("session_key")
        appId = WECHAT_APPID
        sessionKey = session_key
        encryptedData = request.data_format.get("encryptedData")
        iv = request.data_format.get("iv")
        pc = WXBizDataCrypt(appId, sessionKey)
        res = pc.decrypt(encryptedData, iv)

        try:
            user = Users.objects.get(uuid=res.get('openid'))
        except Users.DoesNotExist:
            user = Users.objects.create(**{
                "userid": idGenerator.userid('4001'),
                "uuid": res.get('openId') if 'unionId' not in res else res['unionId'],
                "rolecode": '4001',
                "mobile":res.get('openId') if 'unionId' not in res else res['unionId'],
                "name": res.get("nickName"),
                "sex": res.get("sex"),
                "addr": "{}-{}-{}".format(res.get("country"), res.get("city"), res.get("province")),
                "pic": res.get("avatarUrl"),
                "appid": res.get("watermark")['appid']
            })

        token = get_token()
        res = UserModelSerializerToRedis(user, many=False).data
        RedisTokenHandler(key=token).redis_dict_set(res)

        res = Address.objects.filter(userid=user.userid).order_by('-createtime')
        address = AddressModelSerializer(res[0], many=False).data if len(res) else {}

        return {"data":{
            "user" :UsersSerializers(user, many=False).data,
            "token":token,
            "address":address
        }}

    @list_route(methods=['POST'])
    @Core_connector(isTransaction=True,isPasswd=True)
    def login(self, request):

        try:
            user = Users.objects.get(uuid=request.data_format.get('username'))
        except Users.DoesNotExist:
            raise PubErrorCustom("登录账户错误！")

        if user.passwd != self.request.data_format.get('password'):
            raise PubErrorCustom("密码错误！")

        if user.status == 1:
            raise PubErrorCustom("登陆账号已到期！")
        elif user.status == 2:
            raise PubErrorCustom("已冻结！")
        token = get_token()
        res = UserModelSerializerToRedis(user, many=False).data
        RedisTokenHandler(key=token).redis_dict_set(res)

        return {"data": {
            "token": token
        }}

    #登出
    @list_route(methods=['POST'])
    @Core_connector(isPasswd=True,isTicket=True)
    def logout(self,request, *args, **kwargs):

        RedisTokenHandler(key=request.ticket).redis_dict_del()
        return None

    #刷新token
    @list_route(methods=['POST'])
    @Core_connector(isPasswd=True,isTicket=True)
    def refeshToken(self,request, *args, **kwargs):

        redis_cli = RedisTokenHandler(key=request.ticket)
        res = redis_cli.redis_dict_get()
        redis_cli.redis_dict_del()

        token = get_token()
        redis_cli = RedisTokenHandler(key=token)
        redis_cli.redis_dict_set(res)

        return { "data": token}