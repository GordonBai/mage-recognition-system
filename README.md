# Image Recognition System

An image recognition system based on an open-source technology stack, serving as an alternative to AWS serverless architecture.

## Architecture

This project uses the following technology stack:

- **Frontend**: React.js
- **Backend API**: FastAPI
- **Image Processing**: TensorFlow + PIL
- **Object Storage**: MinIO (alternative to S3)
- **Database**: PostgreSQL (alternative to DynamoDB)
- **API Gateway**: Nginx (alternative to API Gateway)
- **Containerization**: Docker
- **Orchestration**: Docker Compose / Kubernetes

## System Workflow

1. Users upload images through the frontend.
2. The frontend sends the images to the backend API.
3. The API stores the images in MinIO.
4. The API performs image recognition using TensorFlow.
5. Recognition results are stored in the PostgreSQL database.
6. Results are returned to the user.

## Local Development

```bash
# Start local development environment
docker-compose up -d
```

## Kubernetes Deployment

The system can also be deployed to a Kubernetes cluster:

```bash
# Build Docker images
./build.sh

# Push to remote registry (optional)
DOCKER_REGISTRY=your-registry.com PUSH=true ./build.sh

# Deploy to Kubernetes cluster
./deploy.sh
```

## Accessing the System
After startup, the system can be accessed at:

​Local Docker Compose deployment:

Frontend UI: http://localhost:8888
MinIO Console: http://localhost:9998 (username/password: minioadmin/minioadmin)
​Kubernetes deployment:

Frontend UI: Access via LoadBalancer external IP
Check external IP: `kubectl get service nginx`

## Component Description

- **frontend**: React frontend application
- **backend**: FastAPI backend with image recognition logic
- **nginx**: API gateway configuration
- **postgres**: PostgreSQL database
- **minio**: MinIO object storage

## Detailed Documentation

For more details, please refer to [tutorial.md](tutorial.md) and tutoral_kebernetes.md

## Presentation Video
https://www.youtube.com/watch?v=m2IgKe3dmYI