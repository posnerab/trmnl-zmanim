#!/bin/bash

# Zmanim TRMNL Installation Script
# This script sets up the zmanim tracker server and nginx configuration

set -e

echo "Installing Zmanim TRMNL Display..."

# Check if running as root
if [[ $EUID -eq 0 ]]; then
   echo "This script should not be run as root. Please run as a regular user."
   exit 1
fi

# Install Python dependencies
echo "Installing Python dependencies..."
# Try to install system-wide first, fall back to virtual environment if needed
if ! pip3 install --break-system-packages -r requirements.txt 2>/dev/null; then
    echo "Creating virtual environment for dependencies..."
    python3 -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
    echo "Virtual environment created. Update service file to use venv/bin/python3"
fi

# API key setup removed - endpoints are now public

# Install systemd service
echo "Installing systemd service..."
sudo cp zmanim-tracker.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable zmanim-tracker.service

# Set up nginx configuration
echo "Setting up nginx configuration..."
sudo cp nginx-zmanim.conf /etc/nginx/sites-available/zmanim.abie.live

# Create symbolic link if it doesn't exist
if [ ! -L /etc/nginx/sites-enabled/zmanim.abie.live ]; then
    sudo ln -s /etc/nginx/sites-available/zmanim.abie.live /etc/nginx/sites-enabled/
fi

# Test nginx configuration
echo "Testing nginx configuration..."
sudo nginx -t

# Set proper permissions
echo "Setting proper permissions..."
sudo chown -R xander:www-data /var/www/trmnl-zmanim
sudo chmod -R 755 /var/www/trmnl-zmanim

# Ensure zmanim data file exists and is readable
if [ ! -f /var/lib/homebridge/zmanim-js/hebcal_zmanim.json ]; then
    echo "Warning: zmanim data file not found at /var/lib/homebridge/zmanim-js/hebcal_zmanim.json"
    echo "Please ensure the zmanim-js system is properly configured."
else
    echo "Zmanim data file found."
fi

echo ""
echo "Installation complete!"
echo ""
echo "Next steps:"
echo "1. Start the service: sudo systemctl start zmanim-tracker"
echo "2. Reload nginx: sudo systemctl reload nginx"
echo "3. Check service status: sudo systemctl status zmanim-tracker"
echo "4. View logs: sudo journalctl -u zmanim-tracker -f"
echo ""
echo "The server will be available at:"
echo "- Web: http://abie.live/zmanim/"
echo "- Web: https://zmanim.abie.live"
echo ""
echo "API endpoints:"
echo "- JSON API: https://zmanim.abie.live/api/zmanim"
echo "- HTML for TRMNL: https://zmanim.abie.live/html"
echo "- Health check: https://zmanim.abie.live/health"
