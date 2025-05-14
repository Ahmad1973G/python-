#!/bin/bash
# Check if Docker is installed
echo "Checking Docker installation..."
if command -v docker &> /dev/null; then
    echo "✅ Docker is installed"
    docker --version
else
    echo "❌ Docker is not installed"
fi

# Check if Docker Compose is installed
echo -e "\nChecking Docker Compose installation..."
if command -v docker-compose &> /dev/null; then
    echo "✅ Docker Compose is installed"
    docker-compose --version
elif command -v docker compose &> /dev/null; then
    echo "✅ Docker Compose V2 is installed"
    docker compose version
else
    echo "❌ Docker Compose is not installed"
fi

# Check if Docker daemon is running
echo -e "\nChecking if Docker daemon is running..."
if docker info &> /dev/null; then
    echo "✅ Docker daemon is running"
else
    echo "❌ Docker daemon is not running or you don't have permission to access it"
    echo "Try running: sudo systemctl start docker"
    echo "Or add your user to the docker group: sudo usermod -aG docker $USER"
fi