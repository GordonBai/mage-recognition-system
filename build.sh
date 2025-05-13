#!/bin/bash

# 设置Docker镜像仓库
DOCKER_REGISTRY=${DOCKER_REGISTRY:-"localhost:5000"}
TAG=${TAG:-"latest"}

# 构建前端
echo "Building frontend image..."
docker build -t ${DOCKER_REGISTRY}/image-recognition-frontend:${TAG} ./frontend

# 构建后端
echo "Building backend image..."
docker build -t ${DOCKER_REGISTRY}/image-recognition-backend:${TAG} ./backend

# 构建OpenFaaS函数
echo "Building OpenFaaS function image..."
docker build -t ${DOCKER_REGISTRY}/image-recognition-function:${TAG} ./openfaas-functions/image-recognition

# 构建Nginx
echo "Building Nginx image..."
docker build -t ${DOCKER_REGISTRY}/image-recognition-nginx:${TAG} ./nginx

# 推送镜像到仓库
if [ "$PUSH" = "true" ]; then
  echo "Pushing images to registry..."
  docker push ${DOCKER_REGISTRY}/image-recognition-frontend:${TAG}
  docker push ${DOCKER_REGISTRY}/image-recognition-backend:${TAG}
  docker push ${DOCKER_REGISTRY}/image-recognition-function:${TAG}
  docker push ${DOCKER_REGISTRY}/image-recognition-nginx:${TAG}
fi

echo "Build completed!" 