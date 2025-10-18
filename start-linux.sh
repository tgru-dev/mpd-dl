#!/bin/bash

# N_m3u8DL-RE Web UI Start Script (Linux/Debian compatible)

echo "🚀 Starting N_m3u8DL-RE Web UI..."

# Detect OS
if [[ "$OSTYPE" == "linux-gnu"* ]]; then
    echo "🐧 Linux detected"
    PYTHON_CMD="python3"
    PIP_CMD="pip3"
elif [[ "$OSTYPE" == "darwin"* ]]; then
    echo "🍎 macOS detected"
    PYTHON_CMD="python3"
    PIP_CMD="pip3"
else
    echo "❓ Unknown OS, using python3"
    PYTHON_CMD="python3"
    PIP_CMD="pip3"
fi

# Check if Python 3 is available
if ! command -v $PYTHON_CMD &> /dev/null; then
    echo "❌ Error: Python 3 not found!"
    echo "Please install Python 3:"
    echo "  Ubuntu/Debian: sudo apt update && sudo apt install python3 python3-pip python3-venv"
    echo "  CentOS/RHEL: sudo yum install python3 python3-pip"
    echo "  Arch: sudo pacman -S python python-pip"
    exit 1
fi

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    $PYTHON_CMD -m venv venv
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
    echo "Download from: https://github.com/nilaoda/N_m3u8DL-RE/releases"
    exit 1
fi

# Make binary executable
chmod +x N_m3u8DL-RE

# Create downloads directory
mkdir -p downloads

# Get local IP address (Linux compatible)
LOCAL_IP=$(hostname -I | awk '{print $1}' 2>/dev/null || ip route get 1 | awk '{print $7; exit}' 2>/dev/null || echo "localhost")

echo "✅ All checks passed!"
echo "🌐 Starting web server..."
echo "📱 Open your browser and go to: http://localhost:7421"
echo "📱 Or from other devices: http://$LOCAL_IP:7421"
echo "⏹️  Press Ctrl+C to stop the server"
echo ""

# Start the server
$PYTHON_CMD server.py
