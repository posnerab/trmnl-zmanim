#!/bin/bash

echo "Updating nginx configuration for Zmanim Tracker API..."

# Backup the current nginx config
echo "Creating backup of current nginx configuration..."
sudo cp /etc/nginx/sites-available/abie.live /etc/nginx/sites-available/abie.live.backup.$(date +%Y%m%d_%H%M%S)

# Copy the updated configuration
echo "Installing updated nginx configuration..."
sudo cp J-Projects/abie.live.zmanim.nginx.conf /etc/nginx/sites-available/abie.live

# Test nginx configuration
echo "Testing nginx configuration..."
sudo nginx -t

if [ $? -eq 0 ]; then
    echo "Nginx configuration is valid. Reloading nginx..."
    sudo systemctl reload nginx
    
    echo ""
    echo "✅ Nginx configuration updated successfully!"
    echo ""
    echo "🌐 Your zmanim tracker API is now available at:"
    echo "   https://abie.live/zmanim/"
    echo "   https://abie.live/zmanim/api/zmanim"
    echo "   https://abie.live/zmanim/html"
    echo "   https://abie.live/zmanim-health"
    echo ""
    echo "📋 Update your TRMNL plugin configuration to use:"
    echo "   https://abie.live/zmanim/html"
    echo ""
    echo "🔧 To manage nginx:"
    echo "   sudo systemctl status nginx"
    echo "   sudo systemctl reload nginx"
    echo "   sudo nginx -t"
    echo ""
    echo "📁 Backup saved at: /etc/nginx/sites-available/abie.live.backup.*"
else
    echo "❌ Nginx configuration test failed. Please check the configuration."
    echo "Restoring backup..."
    sudo cp /etc/nginx/sites-available/abie.live.backup.* /etc/nginx/sites-available/abie.live
    exit 1
fi
