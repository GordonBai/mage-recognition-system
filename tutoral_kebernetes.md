# Kubernetes Deployment Guide for Image Recognition System

## Table of Contents
1. [Prerequisites](#prerequisites)
2. [System Architecture](#system-architecture)
3. [Setup Instructions](#setup-instructions)
4. [Deployment](#deployment)
5. [Accessing the Application](#accessing-the-application)
6. [Troubleshooting](#troubleshooting)
7. [Cleanup](#cleanup)
8. [Production Considerations](#production-considerations)

## Prerequisites <a name="prerequisites"></a>
- ​**Local Development:​**​
  - Docker Desktop 20.10+
  - Minikube v1.25+
  - kubectl v1.24+
  - Helm v3.9+

- ​**Cloud Deployment:​**​
  - Kubernetes cluster (EKS/GKE/AKS)
  - Cloud storage provisioner
  - Load balancer controller

## Setup Instructions <a name="setup-instructions"></a>
Login to Docker Hub​, then updates the username in all the yaml files
```bash
docker login -u $YOUR_USERNAME$
```
Build and push with version tag v1.0
```bash
DOCKER_REGISTRY=docker.io/$YOUR_USERNAME$ TAG=latest PUSH=true ./build.sh
```

## Deployment <a name="deployment"></a>
Create Kubernetes Secret for Docker Hub​
```bash
kubectl create secret docker-registry regcred \
  --docker-server=docker.io \
  --docker-username=YOUR_USERNAME \
  --docker-password=YOUR_DOCKER_PASSWORD \
  --namespace=image-recognition
```
Run the deploy.sh script to apply all Kubernetes manifests:
```bash
./deploy.sh docker.io/$YOUR_USERNAME$
```
Show the status of all the pods
```bash
kubectl get pods -n image-recognition
```
Reapply all the yaml if you have any updates
```bash
kubectl apply -f kubernetes
```

## Accessing the Application <a name="accessing-the-application"></a>
```bash
kubectl port-forward svc/frontend -n image-recognition 3000:3000
```
Access the system at http://localhost:3000/