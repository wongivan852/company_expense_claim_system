#!/bin/bash

# Docker startup script for Company Expense Claim System

echo "🐳 Starting Company Expense Claim System in Docker"
echo "🌐 Application will be available at: http://localhost:8084/"
echo "🔐 Admin interface: http://localhost:8084/admin/"
echo ""

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker and try again."
    exit 1
fi

# Create necessary directories
mkdir -p data logs media uploads

echo "📊 Setting up database and running migrations..."

# Build and start containers
docker-compose up --build -d

echo ""
echo "✅ Container started successfully!"
echo "📊 Checking container status..."

# Wait a moment for containers to start
sleep 5

# Check container status
docker-compose ps

echo ""
echo "📋 To view logs:"
echo "  docker-compose logs -f web"
echo ""
echo "📋 To stop the application:"
echo "  docker-compose down"
echo ""
echo "📋 To rebuild and restart:"
echo "  docker-compose up --build -d"
echo ""
