#!/bin/bash
# Build the Docker image
docker build -t python-game .

# Run the container
docker run -p 5900:5900 -v $(pwd):/app python-game