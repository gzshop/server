
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
from django.db import transaction

if __name__=='__main__':

    for item in Order.objects.filter(status__in=['1','2','3']):
        with transaction.atomic():
            order = Order.objects.select_for_update().get(orderid=item.orderid)
            response  = AlipayBase().query(orderid=order.orderid)

            if response['code'] == '10000' and response['trade_status'] == 'TRADE_SUCCESS':
                pass
            else:
                print(response)