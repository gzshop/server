from rest_framework import viewsets
from rest_framework.decorators import list_route

from lib.core.decorator.response import Core_connector

from lib.utils.exceptions import PubErrorCustom

from app.public.models import Banner,AttachMent,AttachMentGroup,OtherMemo,Sysparams
from app.cache.utils import RedisCaCheHandler
from lib.utils.db import RedisAppHandler

from app.public.serialiers import SysparamsModelSerializer
from app.order.utils import cityLimit

class PublicAPIView(viewsets.ViewSet):

    @list_route(methods=['POST'])
    @Core_connector(isTransaction=True, isPasswd=True)
    def updSysparams(self, request):

        form = request.data_format.get("form")

        obj = Sysparams.objects.get()
        obj.url = form['url']
        obj.rmflflag = form['rmflflag']
        obj.rmfltitle = form['rmfltitle']
        obj.newgoodsflag = form['newgoodsflag']
        obj.newgoodstitle = form['newgoodstitle']
        obj.save()

        return None

    @list_route(methods=['GET'])
    @Core_connector( isPasswd=True)
    def getSysparams(self, request):

        obj = Sysparams.objects.get()

        return {"data":SysparamsModelSerializer(obj,many=False).data}

    @list_route(methods=['POST'])
    @Core_connector(isTransaction=True,isPasswd=True)
    def setBanner(self, request):

        if len(request.data_format.get("banner")) > 5:
            raise PubErrorCustom("轮播图不允许超过5张!")

        Banner.objects.filter().delete()

        insertList=[]
        for item in request.data_format.get("banner"):
            res = Banner.objects.create(url=item)
            insertList.append(res)

        RedisCaCheHandler(
            method="saveAll",
            serialiers="BannerModelSerializerToRedis",
            table="banner",
            filter_value=insertList,
            must_key="id",
        ).run()

        return None

    @list_route(methods=['GET'])
    @Core_connector(isPasswd=True)
    def getAttachMentGroup(self, request):

        obj = RedisCaCheHandler(
            method="filter",
            serialiers="AttachMentGroupModelSerializerToRedis",
            table="AttachMentGroup",
            filter_value=request.query_params_format
        ).run()

        return {"data":obj}

    @list_route(methods=['POST'])
    @Core_connector(isTransaction=True, isPasswd=True)
    def setAttachMentGroup(self, request):

        if request.data_format.get("id"):
            obj = AttachMentGroup.objects.get(id= request.data_format.get("id"))
            obj.name = request.data_format.get("name")
            obj.save()
        else:
            obj = AttachMentGroup.objects.create(name=request.data_format.get('name'))

        RedisCaCheHandler(
            method="save",
            serialiers="AttachMentGroupModelSerializerToRedis",
            table="AttachMentGroup",
            filter_value=obj,
            must_key="id",
        ).run()

        return None

    @list_route(methods=['GET'])
    @Core_connector(isPasswd=True)
    def getAttachMent(self, request):
        obj = RedisCaCheHandler(
            method="filter",
            serialiers="AttachMentModelSerializerToRedis",
            table="AttachMent",
            filter_value=request.query_params_format
        ).run()

        return {"data":obj}


    @list_route(methods=['POST'])
    @Core_connector(isTransaction=True, isPasswd=True)
    def setAttachMent(self, request):

        if not request.data_format.get("grouid"):
            raise PubErrorCustom("请先添加分组!")

        before_groupid = ""
        if request.data_format.get("id"):
            obj = AttachMent.objects.get(id= request.data_format.get("id"))
            before_groupid = obj.grouid

            obj.title = request.data_format.get("title")
            obj.grouid =  request.data_format.get("grouid")
            obj.save()

            obj2 = AttachMentGroup.objects.select_for_update().get(id=before_groupid)
            obj2.number -= 1
            obj2.save()
        else:
            obj = AttachMent.objects.create(**dict(
                url = request.data_format.get("url"),
                title = request.data_format.get("title"),
                grouid = request.data_format.get("grouid"),
                type = request.data_format.get("type")
            ))

        obj1 = AttachMentGroup.objects.select_for_update().get(id= obj.grouid)
        obj1.number +=1
        obj1.save()

        RedisCaCheHandler(
            method="save",
            serialiers="AttachMentGroupModelSerializerToRedis",
            table="AttachMentGroup",
            filter_value=obj1,
            must_key="id",
        ).run()

        if before_groupid:
            RedisCaCheHandler(
                method="save",
                serialiers="AttachMentGroupModelSerializerToRedis",
                table="AttachMentGroup",
                filter_value=obj2,
                must_key="id",
            ).run()

        RedisCaCheHandler(
            method="save",
            serialiers="AttachMentModelSerializerToRedis",
            table="AttachMent",
            filter_value=obj,
            must_key="id",
        ).run()

        return {"data":{
            "id":obj.id,
            "url":obj.url
        }}

    @list_route(methods=['POST'])
    @Core_connector(isTransaction=True, isPasswd=True)
    def delAttachMent(self, request):

        print(request.data_format.get("id"))
        aObj = AttachMent.objects.filter(id=request.data_format.get("id"))
        if not aObj.exists():
            raise PubErrorCustom("不存在此照片!")
        else:
            obj=aObj[0]
            obj1 = AttachMentGroup.objects.select_for_update().get(id= obj.grouid)
            obj1.number -=1
            obj1.save()
            aObj.delete()

            RedisCaCheHandler(
                method="save",
                serialiers="AttachMentGroupModelSerializerToRedis",
                table="AttachMentGroup",
                filter_value=obj1,
                must_key="id",
            ).run()

            RedisCaCheHandler(
                method="delete",
                table="AttachMent",
                must_key="id",
                must_key_value=request.data_format.get("id")
            ).run()

            return None



    @list_route(methods=['POST'])
    @Core_connector(isTransaction=True, isPasswd=True)
    def setOtherMemo(self, request):

        obj = OtherMemo.objects.create(**dict(
            html = request.data_format.get("html"),
            type = request.data_format.get("type")
        ))

        RedisCaCheHandler(
            method="save",
            serialiers="OtherMemoModelSerializerToRedis",
            table="OtherMemo",
            filter_value=obj,
            must_key="id",
        ).run()

        return None

    @list_route(methods=['POST'])
    @Core_connector(isPasswd=True)
    def appUpdate(self, request):

        version = request.data_format.get("version",None)
        url =  request.data_format.get("url",None)
        note = request.data_format.get("note", None)

        if not version:
            raise PubErrorCustom("版本号不能为空")

        if not url:
            raise PubErrorCustom("下载地址不能为空!")

        if not note:
            raise PubErrorCustom("更新内容不能为空!")

        RedisAppHandler().set(data={
            "version":version,
            "url":url,
            "note":note
        })

        return None

    @list_route(methods=['GET'])
    @Core_connector(isPasswd=True)
    def appGet(self, request):

        return {"data":RedisAppHandler().get()}


    @list_route(methods=['GET'])
    @Core_connector(isPasswd=True)
    def citysGet(self, request):

        return {"data":cityLimit().get}