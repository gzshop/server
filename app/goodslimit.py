
from app.order.models import OrderGoodsLink
from lib.utils.log import logger

class LimitGoods(object):

    def __init__(self,limit_goods=None,userid=None):

        self.limit_goods =  limit_goods
        self.userid = userid

    def run(self):

        isFlag = True

        logger.info("limit_goods=>{}".format(self.limit_goods))

        for item in self.limit_goods:

            query = """
                SELECT t1.linkid FROM `ordergoodslink` as t1
                INNER JOIN `order` as t2 ON t1.orderid = t2.orderid
                WHERE t2.status in ('1','2','3') and userid = {} and gdid = {}""".format(self.userid,item['gdid'])

            logger.info(query)

            row = OrderGoodsLink.objects.raw(query)

            row = list(row)
            rowLen = len(row)

            if rowLen < item['num']:
                isFlag = False

        return isFlag
