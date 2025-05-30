# Image Recognition System

一个基于开源技术栈的图像识别系统，替代AWS无服务器架构。

## 架构

该项目使用以下技术栈：

- **前端**: React.js
- **后端API**: FastAPI
- **图像处理**: TensorFlow + PIL
- **对象存储**: MinIO (替代S3)
- **数据库**: PostgreSQL (替代DynamoDB)
- **API网关**: Nginx (替代API Gateway)
- **容器化**: Docker
- **编排**: Docker Compose / Kubernetes

## 系统工作流程

1. 用户通过前端上传图片
2. 前端将图片发送到后端API
3. API将图片存储到MinIO
4. API直接使用TensorFlow进行图像识别
5. 识别结果存入PostgreSQL数据库
6. 结果返回给用户

## 本地开发

```bash
# 启动本地开发环境
docker-compose up -d
```

## Kubernetes部署

系统也可以部署到Kubernetes集群中：

```bash
# 构建Docker镜像
./build.sh

# 如果需要推送到远程仓库
DOCKER_REGISTRY=your-registry.com PUSH=true ./build.sh

# 部署到Kubernetes集群
./deploy.sh
```

## 访问系统

系统启动后，可以通过以下地址访问：

- 本地Docker Compose部署:
  - 前端界面: http://localhost:8888
  - MinIO控制台: http://localhost:9998 (用户名/密码: minioadmin/minioadmin)

- Kubernetes部署:
  - 前端界面: 通过LoadBalancer获取的外部IP访问
  - 查看外部IP: `kubectl get service nginx`

## 组件说明

- **frontend**: React前端应用
- **backend**: FastAPI后端API，包含图像识别逻辑
- **nginx**: API网关配置
- **postgres**: PostgreSQL数据库
- **minio**: MinIO对象存储

## 详细文档

更多详细信息，请参考 [tutorial.md](tutorial.md) 