#!/bin/bash
# Docker run script for HyperAgent

set -e

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m' # No Color

IMAGE_NAME=${IMAGE_NAME:-hyperagent}
IMAGE_TAG=${IMAGE_TAG:-latest}
CONTAINER_NAME=${CONTAINER_NAME:-hyperagent_app}

# Check if container already exists
if docker ps -a --format '{{.Names}}' | grep -q "^${CONTAINER_NAME}$"; then
    echo -e "${BLUE}[*] Stopping existing container...${NC}"
    docker stop ${CONTAINER_NAME} || true
    docker rm ${CONTAINER_NAME} || true
fi

echo -e "${BLUE}[*] Starting HyperAgent container...${NC}"

# Run container
docker run -d \
    --name ${CONTAINER_NAME} \
    --env-file .env \
    -p 8000:8000 \
    -v $(pwd)/logs:/app/logs \
    ${IMAGE_NAME}:${IMAGE_TAG}

echo -e "${GREEN}[+] Container started: ${CONTAINER_NAME}${NC}"
echo -e "${BLUE}[*] View logs: docker logs -f ${CONTAINER_NAME}${NC}"
echo -e "${BLUE}[*] Stop container: docker stop ${CONTAINER_NAME}${NC}"

