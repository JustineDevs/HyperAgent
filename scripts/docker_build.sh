#!/bin/bash
# Docker build script for HyperAgent

set -e

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}[*] Building HyperAgent Docker image...${NC}"

# Build arguments
IMAGE_NAME=${IMAGE_NAME:-hyperagent}
IMAGE_TAG=${IMAGE_TAG:-latest}
BUILD_CONTEXT=${BUILD_CONTEXT:-.}

# Build image
docker build \
    --tag ${IMAGE_NAME}:${IMAGE_TAG} \
    --tag ${IMAGE_NAME}:$(git rev-parse --short HEAD 2>/dev/null || echo "dev") \
    --file Dockerfile \
    --progress=plain \
    ${BUILD_CONTEXT}

echo -e "${GREEN}[+] Docker image built successfully: ${IMAGE_NAME}:${IMAGE_TAG}${NC}"

# Show image size
echo -e "${BLUE}[*] Image size:${NC}"
docker images ${IMAGE_NAME}:${IMAGE_TAG} --format "table {{.Repository}}\t{{.Tag}}\t{{.Size}}"

