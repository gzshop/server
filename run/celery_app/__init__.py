import os
from celery import Celery
import sys
import django
pathname = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, pathname)
sys.path.insert(0,os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
# print()

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "project.settings")

django.setup()

app = Celery('my_celery') # 实例化celery对象

app.config_from_object('celery_app.celery_config') # 配置文件加载