#!/bin/bash

# Detect OS
OS=$(uname -s)

# Build the Docker image
echo "Building Docker image..."
docker build -t game-client .

# Run the container based on detected OS
if [[ "$OS" == "Linux" ]]; then
    echo "Detected Linux OS"
    xhost +local:docker
    docker run -it --rm \
        -e DISPLAY=$DISPLAY \
        -v /tmp/.X11-unix:/tmp/.X11-unix \
        -v "$(pwd)/map:/app/map" \
        --network host \
        game-client

elif [[ "$OS" == "Darwin" ]]; then
    echo "Detected macOS"
    # For Mac, you need XQuartz installed and configured
    IP=$(ifconfig en0 | grep inet | awk '$1=="inet" {print $2}')
    xhost + $IP
    docker run -it --rm \
        -e DISPLAY=$IP:0 \
        -v "$(pwd)/map:/app/map" \
        --network host \
        game-client

else
    # Assume Windows
    echo "Detected Windows (or other OS)"
    echo "Make sure you have an X server like VcXsrv running"
    docker run -it --rm \
        -e DISPLAY=host.docker.internal:0 \
        -v "$(pwd)/map:/app/map" \
        --network host \
        game-client
fi