
from rest_framework import viewsets
from rest_framework.decorators import list_route
import json

from lib.utils.exceptions import PubErrorCustom
from lib.core.decorator.response import Core_connector
from lib.utils.db import RedisCaCheHandlerCitySheng,RedisCaCheHandlerCityShi,RedisCaCheHandlerCityXian
from lib.utils.db import RedisUserSysSetting
from app.cache.utils import RedisCaCheHandler
from app.user.models import Users
from app.order.models import Address
from app.goods.models import Goods,GoodsLinkSku,Active,Makes
from app.goods.serialiers import GoodsForSearchSerializer,GoodsLinkSkuSearchSerializer
from app.order.serialiers import AddressModelSerializer

from app.goods.serialiers import ActiveModelSerializer1

from lib.utils.db import RedisTokenHandler
from app.order.utils import calyf

from app.public.serialiers import SysparamsModelSerializer,Sysparams

from app.goodslimit import LimitGoods


class FilterAPIView(viewsets.ViewSet):

    @list_route(methods=['GET'])
    @Core_connector(isPasswd=True)
    def getHomeData(self,request):

        userid = None
        user=None

        ticket = request.META.get('HTTP_TICKET')
        if ticket:
            result = RedisTokenHandler(key=ticket).redis_dict_get()
            if result:
                userid = result.get("userid")

        print("用户代码:{}".format(userid))

        rdata={
            "banners":[],
            "newgoods":[]
        }

        #轮播图数据
        rdata['banners'] = [ dict(
            id = item['id'],
            url = item['url']
        ) for item in RedisCaCheHandler(
            method="filter",
            serialiers="BannerModelSerializerToRedis",
            table="banner",
            filter_value={}
        ).run() ]

        if userid:
            user = Users.objects.get(userid=userid)
        #新品数据
        for item in RedisCaCheHandler(
                method="filter",
                serialiers="GoodsModelSerializerToRedis",
                table="goods",
                filter_value={"gdstatus": "0"}
        ).run():
            obj = RedisCaCheHandler(
                method="get",
                serialiers="GoodsCateGoryModelSerializerToRedis",
                table="goodscategory",
                must_key_value=item.get('gdcgid')
            ).run()

            # if userid :
            #     if LimitGoods(userid=userid,limit_goods=item['limit_goods'],gdid=item['gdid']).calsBool():
            #         gdnum = 0 if request.addressBool else \
            #             sum([ i.stock  for i in  GoodsLinkSku.objects.filter(id__in=item['gdskulist']).order_by('sort') ])
            #     else:
            #         gdnum = 0
            # else:
            gdnum = 0 if request.addressBool else \
                sum([i.stock for i in GoodsLinkSku.objects.filter(id__in=item['gdskulist']).order_by('sort')])

            if userid and user.isvip=='1' and item['isvip'] =='0' and obj['status']=='0':
                rdata['newgoods'].append(dict(
                    gdid=item['gdid'],
                    gdname=item['gdname'],
                    gdimg=item['gdimg'],
                    gdtext=item['gdtext'],
                    gdprice=item['gdprice'],
                    gdnum= gdnum,
                    sort=item['sort']
                ))

            if obj['status']=='0' and item['isvip'] !='0':
                rdata['newgoods'].append(dict(
                    gdid=item['gdid'],
                    gdname=item['gdname'],
                    gdimg=item['gdimg'],
                    gdtext=item['gdtext'],
                    gdprice=item['gdprice'],
                    gdnum= gdnum,
                    sort=item['sort']
                ))

        if len(rdata['newgoods']) >=20 :
            rdata['newgoods'] = rdata['newgoods'][:20]
        else:
            rdata['newgoods'] = rdata['newgoods'][:len(rdata['newgoods'])]
        rdata['newgoods'].sort(key=lambda k: (k.get('sort', 0)), reverse=False)


        rdata['settings'] = RedisUserSysSetting().get()
        return {"data": rdata}

    @list_route(methods=['GET'])
    @Core_connector(isPasswd=True)
    def getGoods(self,request):

        userid = None

        ticket = request.META.get('HTTP_TICKET')
        if ticket:
            result = RedisTokenHandler(key=ticket).redis_dict_get()
            if result:
                userid = result.get("userid")

        print("用户代码:{}".format(userid))

        res = RedisCaCheHandler(
            method="get",
            serialiers="GoodsModelSerializerToRedis",
            table="goods",
            must_key_value=request.query_params_format.get('gdid')
        ).run()
        if res['gdstatus'] == '0':
            goodslinksku = GoodsLinkSkuSearchSerializer(
                GoodsLinkSku.objects.filter(id__in=res['gdskulist']).order_by('sort'), many=True).data


            # if userid :
            #     if LimitGoods(userid=userid,limit_goods=res['limit_goods'],gdid=res['gdid']).calsBool():
            #         gdnum = 0 if request.addressBool else sum([ i['stock'] for i in goodslinksku])
            #     else:
            #         gdnum = 0
            # else:
            gdnum = 0 if request.addressBool else sum([ i['stock'] for i in goodslinksku])

            data=dict(
                    gdid = res['gdid'],
                    gdimg = res['gdimg'],
                    gdnum =  gdnum,
                    gdname = res['gdname'],
                    gdprice = res['gdprice'],
                    detail = res['detail'],
                    gdsku=res['gdsku'],
                    goodslinksku = goodslinksku
                )

            data['yf'] = calyf(res['yf'])

            active_id = request.query_params_format.get('active_id', None)

            if active_id:
                try:
                    active = Active.objects.get(id=active_id)
                except Active.DoesNotExist:
                    active = None

                try:
                    active.makes = Makes.objects.get(
                        active_id=active.id,
                        userid=userid
                    )
                except Makes.DoesNotExist:
                    active.makes = None

                if active:
                    data['active'] = ActiveModelSerializer1(active, many=False).data

            else:
                data['active'] = None

            return {"data":data}
        else:
            return {"data":False}

    @list_route(methods=['GET'])
    @Core_connector(isPasswd=True)
    def getGoodsForTheme(self,request):

        obj = RedisCaCheHandler(
            method="get",
            serialiers="GoodsThemeModelSerializerToRedis",
            table="goodstheme",
            must_key_value=request.query_params_format.get('typeid')
        ).run()

        if obj['status']=='0':
            goods = []
            for gdid in json.loads(obj['goods'])['goods']:
                res = RedisCaCheHandler(
                    method="get",
                    serialiers="GoodsModelSerializerToRedis",
                    table="goods",
                    must_key_value=gdid
                ).run()

                if res['gdstatus'] == '0':
                    goods.append(dict(
                        gdid=res['gdid'],
                        gdimg=res['gdimg'],
                        gdname=res['gdname'],
                        gdprice=res['gdprice'],
                        gdtext=res['gdtext'],
                        sort = res['sort'],
                        gdnum = res['gdnum']
                    ))
            goods.sort(key=lambda k: (k.get('sort', 0)), reverse=False)

            return {"data":goods}
        else:
            return {"data":False}

    @list_route(methods=['GET'])
    @Core_connector(isPasswd=True)
    def getGoodsForSearch(self,request):

        rolecode = None

        ticket = request.META.get('HTTP_TICKET')
        if ticket:
            result = RedisTokenHandler(key=ticket).redis_dict_get()
            if result:
                rolecode = str(result.get("rolecode"))

        print("角色:[%s]" % rolecode)
        print(request.query_params_format)
        query = """
            SELECT t1.* FROM goods as t1
            INNER JOIN goodscategory as t2  ON t1.gdcgid = t2.gdcgid and t2.status = '0' and t1.gdstatus='0' and t2.rolecode like '%%{}%%'
            WHERE 1=1  and t1.gdname like '%%{}%%' order by t1.sort
        """.format(rolecode if rolecode else '4001',request.query_params_format.get("name",""))
        print(query)
        goodsObj = Goods.objects.raw(query)

        data = GoodsForSearchSerializer(goodsObj,many=True).data
        for item in data:
            if request.addressBool:
                item['gdnum'] = 0

        return {"data":data}

    @list_route(methods=['GET'])
    @Core_connector(isPasswd=True)
    def getGoodsForCategory(self,request):

        userid = None
        user = None

        ticket = request.META.get('HTTP_TICKET')
        if ticket:
            result = RedisTokenHandler(key=ticket).redis_dict_get()
            if result:
                userid = result.get("userid")

        print("用户代码:{}".format(userid))

        if userid:
            user = Users.objects.get(userid=userid)

        obj = RedisCaCheHandler(
            method="get",
            serialiers="GoodsCateGoryModelSerializerToRedis",
            table="goodscategory",
            must_key_value=request.query_params_format.get('gdcgid')
        ).run()

        if obj['status']=='0':
            goods = []

            res = RedisCaCheHandler(
                method="filter",
                serialiers="GoodsModelSerializerToRedis",
                table="goods",
                filter_value={"gdstatus": "0", "gdcgid":obj['gdcgid']}
            ).run()

            for item in res:

                if userid and user.isvip == '1' and item['isvip'] == '0':
                    goods.append(dict(
                        gdid=item['gdid'],
                        gdimg=item['gdimg'],
                        gdname=item['gdname'],
                        sort=item['sort'],
                        gdtext=item['gdtext'],
                        gdnum=item['gdnum']
                    ))

                if item['isvip'] != '0':
                    goods.append(dict(
                        gdid=item['gdid'],
                        gdimg=item['gdimg'],
                        gdname=item['gdname'],
                        sort=item['sort'],
                        gdtext=item['gdtext'],
                        gdnum=item['gdnum']
                    ))

            goods.sort(key=lambda k: (k.get('sort', 0)), reverse=False)
            return {"data":goods}
        else:
            return {"data":False}

    @list_route(methods=['GET'])
    @Core_connector(isPasswd=True)
    def getGoodsCategory(self,request,*args, **kwargs):

        """
        获取商品分类数据
        :param request:
        :return:
        """

        obj = [ dict(
            gdcgid = item['gdcgid'],
            gdcgname = item['gdcgname'],
            url = item['url'],
            sort = item['sort']
        ) for item in RedisCaCheHandler(
            method="filter",
            serialiers="GoodsCateGoryModelSerializerToRedis",
            table="goodscategory",
            filter_value={"status":"0"}
        ).run() ]

        obj.sort(key=lambda k: (k.get('sort', 0)), reverse=False)

        return {"data":obj}


    @list_route(methods=['GET'])
    @Core_connector(isPasswd=True,isTicket=True)
    def getAddress(self,request):

        return {"data":AddressModelSerializer(Address.objects.filter(userid=request.user['userid']).order_by('moren','-createtime'),many=True).data}

    @list_route(methods=['GET'])
    @Core_connector(isPasswd=True)
    def getBanner(self, request):
        """
        获取轮播图
        :param request:
        :return:
        """

        data = RedisCaCheHandler(
            method="filter",
            serialiers="BannerModelSerializerToRedis",
            table="banner",
            filter_value=request.query_params_format
        ).run()

        return {"data":data}


    @list_route(methods=['GET'])
    @Core_connector(isPasswd=True)
    def getGoodsList(self, request):
        """
        获取商品数据
        :param request:
        :return:
        """
        objs=[]
        for item in request.query_params_format['goods']:
            objs.append(RedisCaCheHandler(
                method="get",
                serialiers="GoodsModelSerializerToRedis",
                table="goods",
                must_key_value=item
            ).run())
        return {"data":objs.sort(key=lambda k: (k.get('sort', 0)), reverse=False)}

    @list_route(methods=['GET'])
    @Core_connector(isPasswd=True)
    def getLxwm(self,request):
        """
         获取公告数据
         :param request:
         :return:
         """

        obj = RedisCaCheHandler(
            method="filter",
            serialiers="OtherMemoModelSerializerToRedis",
            table="OtherMemo"
        ).run()
        return {"data": obj[0] if obj else False}


    @list_route(methods=['GET'])
    @Core_connector(isPasswd=True)
    def sysSettingGet(self, request):

        return {"data":RedisUserSysSetting().get()}


    @list_route(methods=['GET'])
    @Core_connector(isPasswd=True)
    def getSheng(self, request):
        """
        获取省份数据
        :param request:
        :return:
        """
        res = RedisCaCheHandlerCitySheng().redis_get()
        return {"data":res['value']}


    @list_route(methods=['GET'])
    @Core_connector(isPasswd=True)
    def getShi(self, request):
        """
        获取市区数据
        :param request:
        :return:
        """
        if not request.query_params_format["code"]:
            raise PubErrorCustom("code不能为空!")
        res = RedisCaCheHandlerCityShi().redis_dict_get(request.query_params_format["code"])
        return {"data": res['value']}

    @list_route(methods=['GET'])
    @Core_connector(isPasswd=True)
    def getXian(self, request):
        """
        获取县数据
        :param request:
        :return:
        """
        if not request.query_params_format["code"]:
            raise PubErrorCustom("code不能为空!")
        res = RedisCaCheHandlerCityXian().redis_dict_get(request.query_params_format["code"])
        return {"data": res['value']}

