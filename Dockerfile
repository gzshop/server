FROM tangchen2018/python:3.6-alpine
ENV PYTHONUNBUFFERED 1

COPY . /project/server

WORKDIR /project/server

RUN sed -i 's/dl-cdn.alpinelinux.org/mirrors.aliyun.com/g' /etc/apk/repositories

RUN apk add --no-cache tzdata gcc python3-dev mysql-dev musl-dev libffi-dev openssl-dev py-pip && \
    ln -sf /usr/share/zoneinfo/Asia/Shanghai /etc/localtime && \
    echo "Asia/Shanghai" > /etc/timezone


RUN pip install -i https://pypi.tuna.tsinghua.edu.cn/simple --upgrade pip \
    && pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple \
    && mkdir -p /project/server/logs \
    && mkdir -p /project/server/media \
    && mkdir -p /var/logs/uwsgi/ \
    && mkdir -p /var/logs/sso \
    && echo "" > /var/logs/uwsgi/run.log \
    && echo "" > /var/logs/sso/cron.log


CMD uwsgi /project/server/project/wsgi/uwsgi.ini
#CMD ["python", "/project/sso/manage.py crontab remove"]
#CMD ["python", "/project/sso/manage.py crontab add"]
