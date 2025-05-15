#!/bin/bash
set -eo pipefail

# Configuration
DOCKER_REGISTRY=${1:-"docker.io/lucashimself"}
NAMESPACE=${2:-"image-recognition"}
KUBE_DIR="kubernetes"
TIMEOUT=300  # 5 minutes timeout for deployments

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to check if a resource is ready
check_resource() {
  local resource=$1
  local name=$2
  echo -e "${YELLOW}Waiting for ${resource}/${name} to be ready...${NC}"
  
  kubectl wait --for=condition=available --timeout=${TIMEOUT}s ${resource}/${name} -n ${NAMESPACE} || {
    echo -e "${RED}Error: ${resource}/${name} failed to become ready${NC}"
    kubectl describe ${resource} ${name} -n ${NAMESPACE}
    kubectl logs deployment/${name} -n ${NAMESPACE} --all-containers
    exit 1
  }
  
  echo -e "${GREEN}${resource}/${name} is ready${NC}"
}

# Create namespace if not exists
echo -e "${YELLOW}Creating namespace ${NAMESPACE}...${NC}"
kubectl create namespace ${NAMESPACE} --dry-run=client -o yaml | kubectl apply -f -

# Process YAML files with registry placeholder (MacOS compatible sed)
echo -e "${YELLOW}Updating image registry in YAML files...${NC}"
find ${KUBE_DIR} -name "*.yaml" -print0 | while IFS= read -r -d '' file; do
  if [[ "$OSTYPE" == "darwin"* ]]; then
    sed -i '' "s|\${DOCKER_REGISTRY}|${DOCKER_REGISTRY}|g" "$file"
  else
    sed -i "s|\${DOCKER_REGISTRY}|${DOCKER_REGISTRY}|g" "$file"
  fi
done

# Define deployment order and their expected names
declare -A deployments=(
  ["postgres-deployment.yaml"]="postgres"
  ["minio-deployment.yaml"]="minio"
  ["backend-deployment.yaml"]="backend"
  ["frontend-deployment.yaml"]="frontend"
  ["nginx-deployment.yaml"]="nginx"
)

# Apply resources in dependency order with health checks
for file in "${!deployments[@]}"; do
  echo -e "\n${YELLOW}Applying ${file}...${NC}"
  kubectl apply -f "${KUBE_DIR}/${file}" -n ${NAMESPACE}
  
  # Wait for deployment if this is a deployment file
  if [[ "$file" == *"deployment.yaml" ]]; then
    check_resource deployment "${deployments[$file]}"
  fi
done

# Display final status
echo -e "\n${GREEN}Deployment completed successfully!${NC}"

echo -e "\n${YELLOW}Deployment status:${NC}"
kubectl get all -n ${NAMESPACE}

echo -e "\n${YELLOW}Access endpoints:${NC}"
minio_ip=$(kubectl get svc minio -n ${NAMESPACE} -o jsonpath='{.status.loadBalancer.ingress[0].ip}')
nginx_ip=$(kubectl get svc nginx -n ${NAMESPACE} -o jsonpath='{.status.loadBalancer.ingress[0].ip}')

if [[ -z "${nginx_ip}" ]]; then
  nginx_ip=$(kubectl get svc nginx -n ${NAMESPACE} -o jsonpath='{.spec.clusterIP}')
  echo -e "Frontend (ClusterIP): ${GREEN}http://${nginx_ip}${NC}"
else
  echo -e "Frontend: ${GREEN}http://${nginx_ip}${NC}"
fi

if [[ -z "${minio_ip}" ]]; then
  minio_ip=$(kubectl get svc minio -n ${NAMESPACE} -o jsonpath='{.spec.clusterIP}')
  echo -e "MinIO Console (ClusterIP): ${GREEN}http://${minio_ip}:9001${NC}"
else
  echo -e "MinIO Console: ${GREEN}http://${minio_ip}:9001${NC}"
fi

# Show pod logs for debugging
echo -e "\n${YELLOW}Debugging failed pods:${NC}"
kubectl get pods -n ${NAMESPACE} --no-headers | grep -v Running | while read -r pod _; do
  echo -e "\n${RED}Logs for ${pod}:${NC}"
  kubectl logs "${pod}" -n ${NAMESPACE} --all-containers || true
done

# Show ingress information if available
echo -e "\n${YELLOW}Ingress information:${NC}"
kubectl get ingress -n ${NAMESPACE} || echo "No ingress resources found"