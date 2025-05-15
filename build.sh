#!/bin/bash

DOCKER_REGISTRY=${DOCKER_REGISTRY:-"docker.io/lucashimself"}
TAG=${TAG:-"latest"}
PUSH=${PUSH:-"false"}

declare -a services=("frontend" "backend" "nginx")

for service in "${services[@]}"; do
  echo "Building $service image..."
  docker build -t ${DOCKER_REGISTRY}/image-recognition-${service}:${TAG} ./${service}
  
  if [ "$PUSH" = "true" ]; then
    echo "Pushing $service image..."
    docker push ${DOCKER_REGISTRY}/image-recognition-${service}:${TAG}
  fi
done

echo "Build completed!"