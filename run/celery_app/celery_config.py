

from project.config_include.db import REDISPASSWORD,REDISPORT,REDISURL


redis_cli = 'redis://:{}@{}:{}/0'.format(REDISPASSWORD,REDISURL,REDISPORT)

BROKER_URL = redis_cli  # 中间件 地址
CELERY_RESULT_BACKEND = redis_cli  # 结果存放地址

# 任务导入
CELERY_IMPORTS = (
    'celery_app.task',
)