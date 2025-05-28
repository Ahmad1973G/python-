#!/bin/bash

# Game Server Deployment Script

echo "🚀 Starting Game Server Deployment..."

# Create necessary directories
echo "📁 Creating directories..."
mkdir -p logs
mkdir -p map

# Check if required files exist
echo "📋 Checking required files..."
required_files=(
    "server.py"
    "loadbalancer.py" 
    "database.py"
    "sub_client_prots_async.py"
    "sub_lb_prots_async.py"
    "bots_async.py"
    "players_grid.py"
)

missing_files=()
for file in "${required_files[@]}"; do
    if [ ! -f "$file" ]; then
        missing_files+=("$file")
    fi
done

if [ ${#missing_files[@]} -ne 0 ]; then
    echo "❌ Missing required files:"
    for file in "${missing_files[@]}"; do
        echo "   - $file"
    done
    echo "Please ensure all required files are present before deployment."
    exit 1
fi

# Stop existing containers
echo "🛑 Stopping existing containers..."
docker-compose down

# Build and start services
echo "🔨 Building and starting services..."
docker-compose up --build -d

# Wait for services to start
echo "⏳ Waiting for services to initialize..."
sleep 10

# Check service health
echo "🏥 Checking service health..."
services=("game-load-balancer" "game-server-1" "game-server-2" "game-server-3" "game-server-4")

for service in "${services[@]}"; do
    if docker ps | grep -q "$service"; then
        echo "✅ $service is running"
    else
        echo "❌ $service failed to start"
        docker logs "$service" --tail 20
    fi
done

echo ""
echo "🎮 Game Server Deployment Summary:"
echo "=================================="
echo "Load Balancer: http://localhost:5002"
echo "Game Server 1: http://localhost:5000 (UDP: 5004)"
echo "Game Server 2: http://localhost:5010 (UDP: 5014)" 
echo "Game Server 3: http://localhost:5020 (UDP: 5024)"
echo "Game Server 4: http://localhost:5030 (UDP: 5034)"
echo ""
echo "📊 To view logs:"
echo "docker-compose logs -f [service-name]"
echo ""
echo "🔍 To monitor containers:"
echo "docker-compose ps"
echo ""
echo "🛑 To stop all services:"
echo "docker-compose down"

# Optional: Show real-time logs
read -p "Would you like to view real-time logs? (y/n): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    docker-compose logs -f
fi