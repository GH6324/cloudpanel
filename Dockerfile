FROM python:3.9-slim

LABEL maintainer="Nodewebzsz <zszxcken@gmail.com>"

RUN apt update \
    && apt install supervisor redis git nano gcc make netcat-traditional -y \
    && cp /usr/share/zoneinfo/Asia/Shanghai /etc/localtime \
    && mkdir /home/python -p \
    && /usr/local/bin/python -m pip install --upgrade pip

COPY ./ /home/python/panel

WORKDIR /home/python/panel

RUN pip install -r requirements.txt \
    && rm -rf .git \
    && mkdir -p /etc/supervisor/conf.d \
    && mkdir -p /home/python/panel/logs \
    && cp ./config/celery-beat.conf /etc/supervisor/conf.d/ \
    && cp ./config/celery-worker.conf /etc/supervisor/conf.d/ \
    && cp ./config/django-server.conf /etc/supervisor/conf.d/ \
    && chmod +x entrypoint.sh

# RUN python manage.py init_db

ENTRYPOINT ["./entrypoint.sh"]