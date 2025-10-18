#!/bin/bash

# N_m3u8DL-RE Web UI Start Script

echo "🚀 Starting N_m3u8DL-RE Web UI..."

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Install dependencies if needed
if [ ! -f "venv/pyvenv.cfg" ] || ! pip list | grep -q Flask; then
    echo "📥 Installing dependencies..."
    pip install -r requirements.txt
fi

# Check if binary exists
if [ ! -f "N_m3u8DL-RE" ]; then
    echo "❌ Error: N_m3u8DL-RE binary not found!"
    echo "Please ensure the binary is in the same directory as this script."
    exit 1
fi

# Make binary executable
chmod +x N_m3u8DL-RE

# Create downloads directory
mkdir -p downloads

echo "✅ All checks passed!"
echo "🌐 Starting web server..."
echo "📱 Open your browser and go to: http://localhost:7421"
echo "📱 Open your browser and go to: http://192.168.178.140:7421"
echo "⏹️  Press Ctrl+C to stop the server"
echo ""

# Start the server
python server.py
