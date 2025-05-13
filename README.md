# Image Recognition System

一个基于开源技术栈的图像识别系统，替代AWS无服务器架构。

## 架构

该项目使用以下技术栈：

- **前端**: React.js
- **后端API**: FastAPI
- **图像处理**: OpenCV + TensorFlow
- **对象存储**: MinIO (替代S3)
- **数据库**: PostgreSQL (替代DynamoDB)
- **函数计算**: OpenFaaS (替代AWS Lambda)
- **API网关**: Nginx (替代API Gateway)
- **容器化**: Docker
- **编排**: Kubernetes

## 系统工作流程

1. 用户通过前端上传图片
2. 前端将图片发送到后端API
3. API将图片存储到MinIO
4. API触发OpenFaaS函数进行图像识别
5. 识别结果存入PostgreSQL数据库
6. 结果返回给用户

## 本地开发

```bash
# 启动本地开发环境
docker-compose up
```

## Kubernetes部署

```bash
# 部署到Kubernetes集群
kubectl apply -f kubernetes/
```

## 组件说明

- **frontend**: React前端应用
- **backend**: FastAPI后端API
- **openfaas-functions**: OpenFaaS函数，包含图像识别逻辑
- **nginx**: API网关配置
- **kubernetes**: Kubernetes部署配置文件 