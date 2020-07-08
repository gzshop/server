



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
from django.db import transaction
import json

if __name__=='__main__':

    day = UtilTime().string_to_arrow("2020-06-24 18","YYYY-MM-DD HH")

    for item in Order.objects.filter():
        with transaction.atomic():
            obj = Order.objects.select_for_update().get(orderid=item.orderid)
            obj.address = json.loads(obj.address)
            obj.address = json.dumps(obj.address,ensure_ascii=False)
            obj.save()
            print("{}处理结束...".format(obj.orderid))