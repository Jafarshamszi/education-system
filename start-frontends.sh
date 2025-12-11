#!/bin/bash

# Start all three frontends in separate terminal sessions
# Usage: ./start-frontends.sh

PROJECT_DIR="/home/axel/Developer/Education-system"

echo "🚀 Starting all frontends..."

# Check if bun is installed
if ! command -v bun &> /dev/null; then
    echo "❌ Error: Bun is not installed"
    echo "Install it with: curl -fsSL https://bun.sh/install | bash"
    exit 1
fi

# Function to start a frontend
start_frontend() {
    local name=$1
    local port=$2
    local dir=$3

    echo "Starting $name on port $port..."

    # Check if directory exists
    if [ ! -d "$dir" ]; then
        echo "❌ Error: Directory $dir does not exist"
        return 1
    fi

    # Check if port is already in use
    if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1; then
        echo "⚠️  Warning: Port $port is already in use"
        echo "   Kill the process with: kill -9 \$(lsof -t -i:$port)"
        return 1
    fi

    # Start in background
    cd "$dir" && bun dev > /dev/null 2>&1 &
    local pid=$!
    echo "✅ $name started (PID: $pid)"

    return 0
}

# Start each frontend
start_frontend "Admin Frontend" 3000 "$PROJECT_DIR/frontend"
sleep 2

start_frontend "Teacher Frontend" 3001 "$PROJECT_DIR/frontend-teacher"
sleep 2

start_frontend "Student Frontend" 3002 "$PROJECT_DIR/frontend-student"
sleep 2

echo ""
echo "✨ All frontends started!"
echo ""
echo "📍 Access URLs:"
echo "   Admin:   http://localhost:3000"
echo "   Teacher: http://localhost:3001"
echo "   Student: http://localhost:3002"
echo ""
echo "To stop all frontends:"
echo "   pkill -f 'bun.*dev'"
echo ""
echo "To view logs:"
echo "   tail -f ~/.bun/install/global/node_modules/.bin/bun"
