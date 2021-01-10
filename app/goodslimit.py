
from app.order.models import OrderGoodsLink
from app.goods.models import Makes
from lib.utils.log import logger

class LimitGoods(object):

    def __init__(self,limit_goods=None,userid=None,gdid=None):

        self.limit_goods =  limit_goods
        self.userid = userid
        self.gdid = gdid

    def cals_bal(self):

        logger.info("limit_goods=>{}".format(self.limit_goods))

        goods_bal = []

        if not len(self.limit_goods):
            return goods_bal

        query = """
            SELECT t1.linkid,t1.gdnum FROM `ordergoodslink` as t1
            INNER JOIN `order` as t2 ON t1.orderid = t2.orderid
            WHERE t2.status in ('1','2','3') and t2.userid = '{}' and t1.gdid = '{}' group by t1.linkid""".format(self.userid, self.gdid)

        logger.info(query)

        goods_bal = []

        obj = list(OrderGoodsLink.objects.raw(query))
        if len(obj):
            selfGoodsNumber = obj[0].gdnum
        else:
            selfGoodsNumber = 0

        for item in self.limit_goods:

            query = """
                SELECT t1.linkid,t1.gdnum FROM `ordergoodslink` as t1
                INNER JOIN `order` as t2 ON t1.orderid = t2.orderid
                WHERE t2.status in ('1','2','3') and t2.userid = '{}' and t1.gdid = '{}' group by t1.linkid""".format(self.userid,item['gdid'])

            # logger.info(query)
            # GoodsNumber = len(list(OrderGoodsLink.objects.raw(query)))

            obj = list(OrderGoodsLink.objects.raw(query))
            if len(obj):
                GoodsNumber = obj[0].gdnum
            else:
                GoodsNumber = 0

            logger.info("茅台{}|舜{}|条件{}".format(selfGoodsNumber,GoodsNumber,item['num']))
            goods_bal.append(GoodsNumber / int(item['num'])-selfGoodsNumber)

        logger.info(goods_bal)
        return goods_bal

    def calsBool(self):

        for item in self.cals_bal():
            if item<=0:
                return False

        return True

    def stockBool(self,gdnum):

        r = self.cals_bal()

        if len(r):
            if gdnum <= min(self.cals_bal()):
                return True
            else:
                return False
        else:
            return True


class LimitGoods1(object):

    def __init__(self,limit_goods=None,userid=None,gdid=None):

        self.limit_goods =  limit_goods
        self.userid = userid
        self.gdid = gdid

    def cals_bal(self):

        """
        查询购买了多少舜
        """

        selfGoodsNumber = Makes.objects.filter(userid=self.userid).count()

        query = """
            SELECT t1.linkid,t1.gdnum FROM `ordergoodslink` as t1
            INNER JOIN `order` as t2 ON t1.orderid = t2.orderid
            WHERE t2.status in ('1','2','3') 
            and t2.userid = '{}' and t1.gdid = '{}' and t2.createtime > 1610186400 group by t1.linkid""".format(
            self.userid, "G000022")

        # logger.info(query)
        # GoodsNumber = len(list(OrderGoodsLink.objects.raw(query)))

        obj = list(OrderGoodsLink.objects.raw(query))
        if len(obj):
            GoodsNumber = [ sum(item.gdnum) for item in obj]
        else:
            GoodsNumber = 0

        logger.info("预约次数{}|舜{}|条件{}".format(selfGoodsNumber, GoodsNumber, 2))
        return GoodsNumber * 2 - selfGoodsNumber