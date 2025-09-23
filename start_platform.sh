#!/bin/bash

echo "🚀 Starting Cineo AI Platform..."
echo "================================="

# Check if Docker containers are running
echo "🔍 Checking database services..."
if docker ps | grep -q cineo-postgres; then
    echo "✅ PostgreSQL is running"
else
    echo "⚠️  PostgreSQL not running. Starting..."
    docker run --name cineo-postgres -e POSTGRES_DB=cineo_db -e POSTGRES_USER=user -e POSTGRES_PASSWORD=password -p 5432:5432 -d postgres:13
fi

if docker ps | grep -q cineo-redis; then
    echo "✅ Redis is running"
else
    echo "⚠️  Redis not running. Starting..."
    docker run --name cineo-redis -p 6379:6379 -d redis:6-alpine
fi

echo ""
echo "📝 Starting Services:"
echo "====================="

# Terminal 1 - Backend (this script)
echo "1️⃣  Backend Server (this terminal)"
echo "   Command: python main.py"
echo ""

# Terminal 2 - Frontend
echo "2️⃣  Frontend Server"
echo "   Command: cd ../frontend && npm run dev"
echo ""

# Terminal 3 - Celery Worker
echo "3️⃣  Celery Worker"
echo "   Command: celery -A main.celery_app worker --loglevel=info"
echo ""

echo "🌐 Access URLs:"
echo "==============="
echo "• Frontend: http://localhost:3000"
echo "• Backend:  http://localhost:8000"
echo "• API Docs: http://localhost:8000/docs"
echo ""

echo "📋 Next Steps:"
echo "=============="
echo "1. Open new terminal and run: cd frontend && npm run dev"
echo "2. Open another terminal and run: celery -A main.celery_app worker --loglevel=info"
echo "3. Keep this terminal running for the backend server"
echo ""

echo "Press Enter to start the backend server..."
read

echo "🔥 Starting Backend Server..."
python main.py
