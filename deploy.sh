#!/bin/bash

# 设置Docker镜像仓库
DOCKER_REGISTRY=${DOCKER_REGISTRY:-"localhost:5000"}

# 替换Kubernetes配置中的Docker仓库地址
find kubernetes -type f -name "*.yaml" -exec sed -i "s|\${DOCKER_REGISTRY}|${DOCKER_REGISTRY}|g" {} \;

# 应用Kubernetes配置
echo "Deploying PostgreSQL..."
kubectl apply -f kubernetes/postgres-deployment.yaml

echo "Deploying MinIO..."
kubectl apply -f kubernetes/minio-deployment.yaml

echo "Deploying backend API..."
kubectl apply -f kubernetes/backend-deployment.yaml

echo "Deploying frontend..."
kubectl apply -f kubernetes/frontend-deployment.yaml

echo "Deploying Nginx gateway..."
kubectl apply -f kubernetes/nginx-deployment.yaml

echo "Deployment completed!"
echo "Waiting for external IP..."
kubectl get service nginx --watch 