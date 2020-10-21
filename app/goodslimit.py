
from app.order.models import OrderGoodsLink
from lib.utils.log import logger

class LimitGoods(object):

    def __init__(self,limit_goods=None,userid=None,gdid=None):

        self.limit_goods =  limit_goods
        self.userid = userid
        self.gdid = gdid

    def cals_bal(self):

        logger.info("limit_goods=>{}".format(self.limit_goods))

        query = """
            SELECT t1.linkid FROM `ordergoodslink` as t1
            INNER JOIN `order` as t2 ON t1.orderid = t2.orderid
            WHERE t2.status in ('1','2','3') and t2.userid = {} and t1.gdid = {}""".format(self.userid, self.gdid)

        logger.info(query)

        goods_bal = []

        selfGoodsNumber = len(list(OrderGoodsLink.objects.raw(query)))

        for item in self.limit_goods:

            query = """
                SELECT t1.linkid FROM `ordergoodslink` as t1
                INNER JOIN `order` as t2 ON t1.orderid = t2.orderid
                WHERE t2.status in ('1','2','3') and t2.userid = {} and t1.gdid = {}""".format(self.userid,item['gdid'])

            logger.info(query)
            GoodsNumber = len(list(OrderGoodsLink.objects.raw(query)))

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