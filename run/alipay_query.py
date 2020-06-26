
import os
import sys
import django
pathname = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, pathname)
sys.path.insert(0,os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
# print()

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "project.settings")

django.setup()


from app.order.utils import AlipayBase
from app.order.models import Order
from lib.utils.mytime import UtilTime


if __name__=='__main__':

    day = UtilTime().string_to_arrow("2020-06-23","YYYY-MM-DD")


    for item in Order.objects.filter(status='9',createtime__gte=day.timestamp):
        response  = AlipayBase().query(orderid=item.orderid)
        if response['code'] == '10000' and response['trade_status'] == 'TRADE_SUCCESS':
            print(response)
