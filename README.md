# CloudPanel

[![Docker Image CI/CD](https://github.com/Nodewebzsz/cloudpanel/actions/workflows/docker-publish.yml/badge.svg)](https://github.com/Nodewebzsz/cloudpanel/actions/workflows/docker-publish.yml)
[![Docker Pulls](https://img.shields.io/docker/pulls/nodewebzsz/cloudpanel)](https://hub.docker.com/r/nodewebzsz/cloudpanel)

CloudPanel 是一个强大的多云服务管理平台，支持管理和监控多个主流云服务提供商的资源。通过统一的界面，轻松管理 AWS、Azure、DigitalOcean 和 Linode 等云服务资源。

## Docker 镜像

最新版本的 Docker 镜像可以从 Docker Hub 获取：

```bash
docker pull zszken/cloudpanel:latest
```

支持的标签：
- `latest`: 最新稳定版本
- `x.y.z`: 特定版本号
- `x.y`: 特定主要版本

### 多架构支持

本项目支持在 AMD64 和 ARM64 架构上运行。您可以根据服务器架构选择合适的版本：

```bash
# AMD64 架构 (Intel/AMD CPU)
docker pull --platform linux/amd64 zszken/cloudpanel:latest

# ARM64 架构 (Apple M1/M2, AWS Graviton)
docker pull --platform linux/arm64 zszken/cloudpanel:latest
```

## 功能特点

- 多云服务提供商支持（AWS、Azure、DigitalOcean、Linode）
- 统一的资源管理界面
- 用户权限管理系统
- 容器化部署支持
- 异步任务处理
- RESTful API 接口

## 系统要求

- Docker 19.03+ (支持多架构构建)
- Docker Compose
- x86_64/ARM64 架构

## 快速开始

### 方式一：使用 Docker Compose 本地构建部署（推荐）

1. 创建必要的目录：

```bash
mkdir -p data/mysql data/redis logs
```

2. 配置环境变量：

```bash
# 复制环境变量示例文件
cp .env.example .env

# 编辑环境变量文件，填入必要的配置信息
vim .env
```

环境变量配置示例：
```bash
# 平台架构选择 (linux/amd64 或 linux/arm64)
PLATFORM=linux/amd64

# Docker 镜像设置
DOCKER_IMAGE=zszken/cloudpanel:latest

# 端口设置
PORT=8111
```

3. 构建并启动服务：

```bash
# AMD64 架构
echo "PLATFORM=linux/amd64" > .env
docker-compose up -d

# 或 ARM64 架构
echo "PLATFORM=linux/arm64/v8" > .env
docker-compose up -d
```

4. 创建管理员账户：

```bash
docker exec -it panel /bin/bash
python manage.py createsuperuser --username admin --email admin@admin.com
```

5. 初始化 AWS 镜像数据（可选）：

```bash
python manage.py aws_update_images
```

### 方式二：手动部署

#### 1. 创建 Docker 网络

```bash
docker network create panel_network
```

#### 2. 启动 MySQL 数据库

```bash
mkdir /data
docker run -d -it \
  --network panel_network \
  -v /data/mysql:/var/lib/mysql \
  --name panel_mysql \
  -e MYSQL_ROOT_PASSWORD=root \
  -e MYSQL_DATABASE=panel \
  mysql:5.7 \
  --character-set-server=utf8mb4 \
  --collation-server=utf8mb4_unicode_ci
```

#### 3. 启动 CloudPanel

```bash
docker run -d -it \
  --network panel_network \
  -p 8111:80 \
  --name panel \
  zszken/cloudpanel:latest
```

## 访问平台

在浏览器中访问：`http://your-server-ip:8111`

### 管理后台

管理员可以通过以下地址访问管理后台：`http://your-server-ip:8111/api/admin`

管理后台功能包括：
- 用户管理：创建、编辑、删除用户
- 权限管理：分配和管理用户权限
- 云服务管理：管理各云服务提供商的配置
- 系统设置：管理系统全局配置
- 日志查看：查看系统操作日志

> 注意：请确保使用管理员账户登录管理后台，普通用户无法访问此页面。

## 多架构部署注意事项

1. **架构选择**：
   - AMD64：适用于 Intel/AMD 处理器（最常见）
   - ARM64：适用于 Apple M1/M2、AWS Graviton 等 ARM 处理器

2. **性能考虑**：
   - 确保使用匹配硬件的正确架构
   - ARM64 架构下某些依赖包可能需要额外的编译时间
   - 适当设置容器资源限制

3. **数据迁移**：
   - 不同架构间的数据文件不能直接迁移
   - 需要通过导出/导入方式迁移数据

4. **健康检查**：
   所有服务都配置了健康检查，可以通过以下命令查看状态：
   ```bash
   docker-compose ps
   docker-compose logs
   ```

5. **资源限制配置**：
   ```yaml
   services:
     panel:
       deploy:
         resources:
           limits:
             cpus: '1.0'
             memory: 1G
           reservations:
             cpus: '0.5'
             memory: 512M
   ```

## 开发说明

### 项目结构

```
.
├── apps/           # 主应用目录
│   ├── aws/       # AWS 服务模块
│   ├── azure/     # Azure 服务模块
│   ├── do/        # DigitalOcean 模块
│   ├── linode/    # Linode 服务模块
│   └── users/     # 用户管理模块
├── libs/          # 公共库
├── config/        # 配置文件
├── logs/         # 日志目录
└── panelProject/ # 项目核心目录
```

### 技术栈

- 后端框架：Django 4.2
- 数据库：MySQL 5.7
- 缓存：Redis
- 任务队列：Celery
- 容器化：Docker

## 环境变量配置

项目使用环境变量来管理敏感配置信息，主要包括：

- AWS 配置
  - AWS_ACCESS_KEY_ID：AWS 访问密钥 ID
  - AWS_SECRET_ACCESS_KEY：AWS 密钥
  - AWS_ACCOUNT_EMAIL：AWS 账户邮箱
  - AWS_ACCOUNT_NAME：AWS 账户名称

- 数据库配置
  - MYSQL_HOST：MySQL 主机地址
  - MYSQL_PORT：MySQL 端口
  - MYSQL_DATABASE：数据库名称
  - MYSQL_USER：数据库用户名
  - MYSQL_PASSWORD：数据库密码

- Redis 配置
  - REDIS_HOST：Redis 主机地址
  - REDIS_PORT：Redis 端口

- Django 配置
  - DJANGO_SETTINGS_MODULE：Django 设置模块

## 注意事项

1. 当前版本为预览版本，功能持续更新中
2. 支持 x86_64 和 ARM64 架构的 Docker 部署
3. 如遇到问题，请在 Issues 中反馈
4. 请确保妥善保管环境变量文件，不要将其提交到版本控制系统

## 贡献指南

我们欢迎所有形式的贡献，包括但不限于：

- 提交问题和建议
- 改进文档
- 提交代码改进
- 分享使用经验

请确保在提交 Pull Request 之前：

1. Fork 本仓库
2. 创建您的特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交您的更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 打开一个 Pull Request

## 许可证

本项目采用 MIT 许可证。详见 [LICENSE](LICENSE) 文件。

## 联系方式

- 项目维护者：@Nodewebzsz
- 项目主页：[https://github.com/Nodewebzsz/cloudpanel]
- 问题反馈：请使用 GitHub Issues