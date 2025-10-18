#!/bin/bash

# N_m3u8DL-RE Web UI systemd Service Creator

echo "🔧 Creating systemd service for N_m3u8DL-RE Web UI"

# Get current directory
CURRENT_DIR=$(pwd)
CURRENT_USER=$(whoami)

echo "📁 Current directory: $CURRENT_DIR"
echo "👤 Current user: $CURRENT_USER"

# Create service file
SERVICE_FILE="/tmp/mpd-dl.service"

cat > "$SERVICE_FILE" << EOF
[Unit]
Description=N_m3u8DL-RE Web UI
After=network.target

[Service]
Type=simple
User=$CURRENT_USER
WorkingDirectory=$CURRENT_DIR
ExecStart=$CURRENT_DIR/venv/bin/python $CURRENT_DIR/server.py
Restart=always
RestartSec=10
Environment=PATH=$CURRENT_DIR/venv/bin

[Install]
WantedBy=multi-user.target
EOF

echo "📝 Service file created: $SERVICE_FILE"
echo ""
echo "📋 Service file content:"
cat "$SERVICE_FILE"
echo ""

# Ask for confirmation
read -p "🤔 Do you want to install this service? (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "📥 Installing systemd service..."
    
    # Copy service file
    sudo cp "$SERVICE_FILE" /etc/systemd/system/mpd-dl.service
    
    # Reload systemd
    sudo systemctl daemon-reload
    
    # Enable service
    sudo systemctl enable mpd-dl
    
    echo "✅ Service installed and enabled!"
    echo ""
    echo "🚀 To start the service:"
    echo "   sudo systemctl start mpd-dl"
    echo ""
    echo "📊 To check status:"
    echo "   sudo systemctl status mpd-dl"
    echo ""
    echo "📜 To view logs:"
    echo "   sudo journalctl -u mpd-dl -f"
    echo ""
    echo "⏹️  To stop the service:"
    echo "   sudo systemctl stop mpd-dl"
else
    echo "❌ Service installation cancelled"
fi

# Clean up
rm "$SERVICE_FILE"
