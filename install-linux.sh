#!/bin/bash

# N_m3u8DL-RE Web UI Installation Script für Linux/Debian

echo "🐧 N_m3u8DL-RE Web UI - Linux Installation"
echo "=========================================="

# Detect Linux distribution
if [ -f /etc/os-release ]; then
    . /etc/os-release
    OS=$NAME
    VER=$VERSION_ID
else
    OS=$(uname -s)
    VER=$(uname -r)
fi

echo "📋 Detected OS: $OS $VER"

# Check if running as root
if [ "$EUID" -eq 0 ]; then
    echo "⚠️  Warning: Running as root. Consider using a regular user."
fi

# Update package lists
echo "🔄 Updating package lists..."
if command -v apt &> /dev/null; then
    sudo apt update
elif command -v yum &> /dev/null; then
    sudo yum check-update
elif command -v dnf &> /dev/null; then
    sudo dnf check-update
elif command -v pacman &> /dev/null; then
    sudo pacman -Sy
fi

# Install Python 3 and dependencies
echo "📦 Installing Python 3 and dependencies..."

if command -v apt &> /dev/null; then
    # Ubuntu/Debian
    sudo apt install -y python3 python3-pip python3-venv python3-dev curl wget git
elif command -v yum &> /dev/null; then
    # CentOS/RHEL
    sudo yum install -y python3 python3-pip python3-devel curl wget git
elif command -v dnf &> /dev/null; then
    # Fedora
    sudo dnf install -y python3 python3-pip python3-devel curl wget git
elif command -v pacman &> /dev/null; then
    # Arch Linux
    sudo pacman -S --noconfirm python python-pip curl wget git
else
    echo "❌ Unsupported package manager. Please install Python 3 manually."
    exit 1
fi

# Check Python version
PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
echo "✅ Python version: $PYTHON_VERSION"

# Download N_m3u8DL-RE binary
echo "📥 Downloading N_m3u8DL-RE binary..."

# Detect architecture
ARCH=$(uname -m)
case $ARCH in
    x86_64)
        ARCH="linux-x64"
        ;;
    aarch64|arm64)
        ARCH="linux-arm64"
        ;;
    armv7l)
        ARCH="linux-arm"
        ;;
    *)
        echo "❌ Unsupported architecture: $ARCH"
        exit 1
        ;;
esac

echo "🏗️  Architecture: $ARCH"

# Download binary
BINARY_URL="https://github.com/nilaoda/N_m3u8DL-RE/releases/latest/download/N_m3u8DL-RE_Beta_${ARCH}.tar.gz"

if [ ! -f "N_m3u8DL-RE" ]; then
    echo "📥 Downloading from: $BINARY_URL"
    wget -O N_m3u8DL-RE.tar.gz "$BINARY_URL"
    
    if [ $? -eq 0 ]; then
        tar -xzf N_m3u8DL-RE.tar.gz
        chmod +x N_m3u8DL-RE
        rm N_m3u8DL-RE.tar.gz
        echo "✅ Binary downloaded and extracted"
    else
        echo "❌ Failed to download binary. Please download manually from:"
        echo "   https://github.com/nilaoda/N_m3u8DL-RE/releases"
        exit 1
    fi
else
    echo "✅ Binary already exists"
fi

# Create virtual environment
echo "🔧 Setting up Python virtual environment..."
python3 -m venv venv
source venv/bin/activate

# Install Python dependencies
echo "📦 Installing Python dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# Create downloads directory
mkdir -p downloads

# Make scripts executable
chmod +x start-linux.sh

echo ""
echo "🎉 Installation completed successfully!"
echo ""
echo "🚀 To start the server:"
echo "   ./start-linux.sh"
echo ""
echo "📱 Then open your browser to:"
echo "   http://localhost:7421"
echo ""
echo "📖 For more information, see README-linux.md"
