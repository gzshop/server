
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



if __name__=='__main__':

    for item in Order.objects.filter(status='9'):
        response  = AlipayBase().query(orderid=item.orderid)
        if response['code'] == '10000' and response['trade_status'] == 'TRADE_SUCCESS':
            print(response)
