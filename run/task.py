
from celery import Celery
import os
import sys
import django
pathname = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, pathname)
sys.path.insert(0,os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
# print()

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "project.settings")

django.setup()

from project.config_include.db import REDISPASSWORD,REDISPORT,REDISURL


redis_cli = 'redis://:{}@{}:{}/0'.format(REDISPASSWORD,REDISURL,REDISPORT)

app = Celery('tasks',  backend=redis_cli, broker=redis_cli ) # 配置好celery的backend和broker

@app.task
def add(x, y):
    return x + y



if __name__ == '__main__':
    import time
    result = add.delay(4, 4)

    # while not result.ready():
    #     time.sleep(1)
    print('task done: {0}'.format(result.get()))