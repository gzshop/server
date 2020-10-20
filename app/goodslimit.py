
from app.order.models import OrderGoodsLink

class LimitGoods(object):

    def __init__(self,limit_goods=None,userid=None):

        self.limit_goods =  limit_goods
        self.userid = userid

    def run(self):

        isFlag = True

        for item in self.limit_goods:

            row = OrderGoodsLink.objects.raw("""
                SELECT t1.linkid FROM `ordergoodslink` as t1
                INNER JOIN `order` as t2 ON t1.orderid = t2.orderid
                WHERE t2.status in ('1','2','3') and userid = {} and gdid = {}""".format(self.userid,item['gdid']))

            row = list(row)
            rowLen = len(row)

            if rowLen < item['num']:
                isFlag = False

        return isFlag
