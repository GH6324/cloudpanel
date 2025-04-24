FROM --platform=$TARGETPLATFORM python:3.9-slim

LABEL maintainer="Nodewebzsz <zszxcken@gmail.com>"
LABEL org.opencontainers.image.source="https://github.com/Nodewebzsz/cloudpanel"
LABEL org.opencontainers.image.description="CloudPanel - 多云服务管理平台"

# 设置环境变量以减少Python生成的.pyc文件
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV TZ=Asia/Shanghai

# 安装系统依赖
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        supervisor \
        redis-server \
        git \
        nano \
        gcc \
        make \
        netcat-traditional \
        default-libmysqlclient-dev \
        pkg-config \
    && rm -rf /var/lib/apt/lists/* \
    && cp /usr/share/zoneinfo/Asia/Shanghai /etc/localtime \
    && mkdir -p /home/python \
    && python -m pip install --no-cache-dir --upgrade pip

WORKDIR /home/python/panel

# 首先复制依赖文件
COPY requirements.txt .

# 安装Python依赖
RUN pip install --no-cache-dir -r requirements.txt

# 复制项目文件
COPY . .

# 创建必要的目录并设置配置文件
RUN mkdir -p /etc/supervisor/conf.d \
    && mkdir -p logs \
    && cp ./config/celery-beat.conf /etc/supervisor/conf.d/ \
    && cp ./config/celery-worker.conf /etc/supervisor/conf.d/ \
    && cp ./config/django-server.conf /etc/supervisor/conf.d/ \
    && chmod +x entrypoint.sh \
    && rm -rf .git

# 健康检查
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8111/health/ || exit 1

ENTRYPOINT ["./entrypoint.sh"]