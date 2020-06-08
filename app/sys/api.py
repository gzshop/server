from rest_framework import viewsets
from rest_framework.decorators import list_route
from lib.core.decorator.response import Core_connector
from lib.utils.exceptions import PubErrorCustom

from app.user.models import Users
from app.goods.models import GoodsCateGory,Goods,Card,GoodsTheme,SkuKey,SkuValue
from app.public.models import Banner,AttachMentGroup,AttachMent


from app.cache.utils import RedisCaCheHandler

from include.city import city

class SsyAPIView(viewsets.ViewSet):

    #刷新所有用户缓存数据
    @list_route(methods=['POST'])
    @Core_connector()
    def refeshUserRedis(self,request, *args, **kwargs):

        # ShengRes = RedisCaCheHandlerCitySheng()
        # Shengs=[]
        # for item in city:
        #
        #     Shengs.append({
        #         "label":item['label'],
        #         "value":item['value']
        #     })
        #
        #     r = RedisCaCheHandlerCityShi()
        #     childs=[ {"label":childs_item['label'],"value":childs_item['value']} for childs_item in item['children'] ]
        #     r.redis_dict_set(item['value'],{"value":childs})
        #     r = RedisCaCheHandlerCityXian()
        #     if "children" in item:
        #         for CityShiItem in item['children']:
        #             if 'children' in CityShiItem:
        #                 childs = [{"label": childs_item['label'], "value": childs_item['value']} for childs_item in CityShiItem['children']]
        #             else:
        #                 childs=[]
        #             r.redis_dict_set(CityShiItem['value'], {"value":childs})
        # ShengRes.redis_set({"value":Shengs})

        RedisCaCheHandler(
            method="saveAll",
            serialiers="UserModelSerializerToRedis",
            table="user",
            filter_value=Users.objects.filter(status='0'),
            must_key="userid",
        ).run()

        RedisCaCheHandler(
            method="saveAll",
            serialiers="GoodsCateGoryModelSerializerToRedis",
            table="goodscategory",
            filter_value=GoodsCateGory.objects.filter(),
            must_key="gdcgid",
        ).run()

        RedisCaCheHandler(
            method="saveAll",
            serialiers="GoodsModelSerializerToRedis",
            table="goods",
            filter_value=Goods.objects.filter(),
            must_key="gdid",
        ).run()

        RedisCaCheHandler(
            method="saveAll",
            serialiers="AttachMentGroupModelSerializerToRedis",
            table="AttachMentGroup",
            filter_value=AttachMentGroup.objects.filter(),
            must_key="id",
        ).run()

        RedisCaCheHandler(
            method="saveAll",
            serialiers="AttachMentModelSerializerToRedis",
            table="AttachMent",
            filter_value=AttachMent.objects.filter(),
            must_key="id",
        ).run()

        RedisCaCheHandler(
            method="saveAll",
            serialiers="CardModelSerializerToRedis",
            table="card",
            filter_value=Card.objects.filter(),
            must_key="id",
        ).run()

        RedisCaCheHandler(
            method="saveAll",
            serialiers="GoodsThemeModelSerializerToRedis",
            table="goodstheme",
            filter_value=GoodsTheme.objects.filter(),
            must_key="typeid",
        ).run()

        RedisCaCheHandler(
            method="saveAll",
            serialiers="SkuKeyModelSerializerToRedis",
            table="skukey",
            filter_value=SkuKey.objects.filter(),
            must_key="id",
        ).run()

        RedisCaCheHandler(
            method="saveAll",
            serialiers="SkuValueModelSerializerToRedis",
            table="skuvalue",
            filter_value=SkuValue.objects.filter(),
            must_key="id",
        ).run()

        return None