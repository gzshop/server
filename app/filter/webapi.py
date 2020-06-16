
from rest_framework import viewsets
from rest_framework.decorators import list_route

from lib.core.decorator.response import Core_connector

from app.filter.menu import all_menu

from app.cache.utils import RedisCaCheHandler

from app.order.models import Order
from app.order.serialiers import OrderModelSerializer,OrderModelSerializer1

from lib.utils.mytime import send_toTimestamp
from app.user.models import Users
from app.order.models import Order,OrderGoodsLink
from lib.utils.mytime import UtilTime,get_current_month_start_and_end

class FilterWebAPIView(viewsets.ViewSet):
    @list_route(methods=['GET'])
    @Core_connector(isPasswd=True,isTicket=True)
    def getMenu(self, request):
        """
        获取菜单数据
        :param request:
        :return:
        """

        type = self.request.query_params.get('type') if self.request.query_params.get("type") else "first"
        return {"data":all_menu[type]}

    @list_route(methods=['GET'])
    @Core_connector(isPasswd=True,isTicket=True)
    def getTopMenu(self, request):
        """
        获取顶部菜单数据
        :param request:
        :return:
        """

        return {"data":all_menu['top']}

    @list_route(methods=['GET'])
    @Core_connector(isPasswd=True)
    def getBanner(self, request):
        """
        获取轮播图图片
        :param request:
        :return:
        """

        data = RedisCaCheHandler(
            method="filter",
            serialiers="BannerModelSerializerToRedis",
            table="banner",
            filter_value=request.query_params_format
        ).run()

        return {"data": data}


    @list_route(methods=['GET'])
    @Core_connector(isPasswd=True)
    def getOtherMemo(self, request):
        """
        获取公告数据
        :param request:
        :return:
        """

        obj =RedisCaCheHandler(
            method="filter",
            serialiers="OtherMemoModelSerializerToRedis",
            table="OtherMemo",
            filter_value=request.query_params_format
        ).run()
        return {"data": obj[0] if obj else False}

    @list_route(methods=['GET'])
    @Core_connector(isPasswd=True, isTicket=True)
    def OrderGetWeb(self, request):

        query_format = str()

        if request.query_params_format.get("status"):
            query_format = query_format + " and t1.status='{}'".format(request.query_params_format.get("status"))
        if request.query_params_format.get("before_status"):
            query_format = query_format + " and t1.before_status='{}'".format(request.query_params_format.get("before_status"))
        if request.query_params_format.get("orderid"):
            query_format = query_format + " and t1.orderid='{}'".format(request.query_params_format.get("orderid"))
        if request.query_params_format.get("startdate") and request.query_params_format.get("enddate"):
            query_format = query_format + " and t1.createtime>={} and t1.createtime<={}".format(
                send_toTimestamp(request.query_params_format.get("startdate")),
                send_toTimestamp(request.query_params_format.get("enddate"))
            )
        if request.query_params_format.get("mobile"):
            query_format = query_format + " and t2.mobile='{}'".format(request.query_params_format.get("mobile"))

        orders = Order.objects.raw("""
            SELECT t1.*,t2.mobile FROM `order` as t1
            INNER JOIN user as t2 ON t1.userid=t2.userid
            WHERE 1=1 %s order by t1.createtime desc
        """%(query_format),[])

        page = int(request.query_params_format.get("page", 1))
        page_size = request.query_params_format.get("page_size", 10)
        page_start = page_size * page - page_size
        page_end = page_size * page

        headers = {
            'Total': len(list(orders)),
        }

        return {
            "data": OrderModelSerializer1(orders[page_start:page_end], many=True).data,
            "header":headers
        }


    @list_route(methods=['GET'])
    @Core_connector(isPasswd=True, isTicket=True)
    def homeDataCount(self, request):

        ut = UtilTime()

        data={
            "tableData":[],
            "tips1":{
                "lastday":{
                    "amount":0.0,
                    "number":0
                },
                "month":{
                    "amount": 0.0,
                    "number": 0
                }
            },
            "counts": [
                {"icon": "el-icon-user-solid", "desc": "关注人数(个)", "num": 0, "color": "bg-primary"},
                {"icon": "el-icon-s-finance", "desc": "订单总数(笔)", "num": 0, "color": "bg-success"},
                {"icon": "el-icon-s-order", "desc": "今日订单总金额(元)", "num": 0.0, "color": "bg-danger"},
                {"icon": "el-icon-s-data", "desc": "本月销量(笔)", "num": 0, "color": "bg-warning"},
            ],
            "tips": [
                {
                    "title": "店铺及商品提示",
                    "desc": "需要关注的店铺信息及待处理事项",
                    "list": [
                        {"name": "出售中", "value": "0"},
                        {"name": "待回复", "value": "0"},
                        {"name": "库存预警", "value": "0"},
                        {"name": "仓库中", "value": "0"},
                    ]
                },
                {
                    "title": "交易提示",
                    "desc": "本月内的交易订单",
                    "list": [
                        {"name": "待付款", "value": 0},
                        {"name": "待发货", "value": 0},
                        {"name": "已发货", "value": 0},
                        {"name": "已收货", "value": 0},
                        {"name": "退款中", "value": 0},
                        {"name": "待售后", "value": 0},
                    ]
                },
            ]
        }
        data['counts'][0]['num'] = Users.objects.filter(rolecode='4001').count()
        data['counts'][1]['num'] = Order.objects.filter().count()

        start_date = ut.string_to_timestamp(ut.arrow_to_string(format_v="YYYY-MM-DD") + ' 00:00:00')
        end_date = ut.string_to_timestamp(ut.arrow_to_string(format_v="YYYY-MM-DD") + ' 23:59:59')
        data['counts'][2]['num'] = 0.0
        orders = Order.objects.filter(createtime__lte = end_date , createtime__gte = start_date )
        if orders.exists():
            for item in orders:
                data['counts'][2]['num'] += float(item.amount)

        #本月的第一天  和最后一天
        start_date,end_date = get_current_month_start_and_end(ut.arrow_to_string(format_v="YYYY-MM-DD"))

        start_date = ut.string_to_timestamp(start_date + ' 00:00:00')
        end_date = ut.string_to_timestamp(end_date + ' 23:59:59')

        orders = Order.objects.filter(createtime__lte=end_date, createtime__gte=start_date)
        if orders.exists():
            for item in orders:
                if item.status=='1':
                    data['counts'][3]['num'] += 1
                    data['tips1']['month']['amount'] += float(item.amount)
                    data['tips1']['month']['number'] += 1

                if item.status == '0':
                    data['tips'][1]['list'][0]['value'] += 1
                elif item.status == '1' and item.fhstatus =='1':
                    data['tips'][1]['list'][1]['value'] += 1
                elif item.status == '1' and item.fhstatus =='0':
                    data['tips'][1]['list'][2]['value'] += 1
                    data['tips'][1]['list'][3]['value'] += 1


        #昨天的销售情况
        start_date = ut.string_to_timestamp(ut.arrow_to_string(ut.today.shift(days=-1),format_v="YYYY-MM-DD") + ' 00:00:00' )
        end_date = ut.string_to_timestamp(ut.arrow_to_string(ut.today.shift(days=-1),format_v="YYYY-MM-DD") + ' 23:59:59')

        orders = Order.objects.filter(createtime__lte = end_date , createtime__gte = start_date,status=1 )
        if orders.exists():
            for item in orders:
                data['tips1']['lastday']['amount'] += float(item.amount)
                data['tips1']['lastday']['number'] += 1

        #当天商品销量排行榜
        start_date = ut.string_to_timestamp(ut.arrow_to_string(format_v="YYYY-MM-DD") + ' 00:00:00')
        end_date = ut.string_to_timestamp(ut.arrow_to_string(format_v="YYYY-MM-DD") + ' 23:59:59')

        oLinks = {}
        oGLs = OrderGoodsLink.objects.filter(createtime__lte = end_date , createtime__gte = start_date)
        if oGLs.exists():
            for item in oGLs:
                if item.gdid not in oLinks:
                    oLinks[item.gdid] = {
                        "name":item.gdname,
                        "num":item.gdnum
                    }
                else:
                    oLinks[item.gdid]['num'] += item.gdnum

        tableData= [ oLinks[item] for item in oLinks ]
        tableData.sort(key=lambda k: (k.get('num', 0)), reverse=False)
        data['tableData'] = tableData[:10] if len(tableData)>=10 else tableData

        #折线图
        item_count = 7
        data_1 = []
        data_2 = []

        day = ut.today.shift(days=-7)
        while item_count:
            day = ut.replace(arrow_v=day, days=1)

            day_string = ut.arrow_to_string(arrow_s=day, format_v="YYYY-MM-DD")[0:10]

            amount = 0.0
            for item in Order.objects.filter(createtime__lte=ut.string_to_arrow(day_string + ' 23:59:59').timestamp,
                                        createtime__gte=ut.string_to_arrow(day_string + ' 00:00:01').timestamp,
                                        status='1'):
                amount += float(item.amount)

            data_1.append(day_string.replace('-', '')[4:])
            data_2.append(amount)
            item_count -= 1

        data['data_1'] = data_1
        data['data_2'] = data_2

        return {"data":data}
