#!/bin/bash

echo "Fixing iframe embedding for TRMNL..."

# Backup the current nginx config
echo "Creating backup of current nginx configuration..."
sudo cp /etc/nginx/sites-available/abie.live /etc/nginx/sites-available/abie.live.backup.$(date +%Y%m%d_%H%M%S)

# Create a temporary file with the updated configuration
echo "Creating updated nginx configuration..."
cat > /tmp/abie.live.updated.conf << 'EOF'
server {
    listen 80;
    server_name abie.live www.abie.live;
    
    # Redirect HTTP to HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name abie.live www.abie.live;
    
    # SSL configuration (you'll need to update these paths to match your existing SSL setup)
    ssl_certificate /var/www/J-Projects/abie_live/abie_live_fullchain.crt;
    ssl_certificate_key /var/www/J-Projects/abie_live/abie_live.key;
    
    # SSL security settings
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512:ECDHE-RSA-AES256-GCM-SHA384:DHE-RSA-AES256-GCM-SHA384;
    ssl_prefer_server_ciphers off;
    ssl_session_cache shared:SSL:10m;
    ssl_session_timeout 10m;
    
    # Security headers
    add_header X-Frame-Options DENY;
    add_header X-Content-Type-Options nosniff;
    add_header X-XSS-Protection "1; mode=block";
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    
    # Main site
    location / {
        root /var/www/html;
        index index.html index.htm;
        try_files $uri $uri/ =404;
    }
    
    # Pregnancy Tracker API
    location /pregnancy/ {
        proxy_pass http://127.0.0.1:5000/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_connect_timeout 30s;
        proxy_send_timeout 30s;
        proxy_read_timeout 30s;
    }
    
    # Pregnancy Tracker Health Check
    location /pregnancy-health {
        proxy_pass http://127.0.0.1:5000/health;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
    
    # Zmanim Tracker API
    location /zmanim/ {
        proxy_pass http://127.0.0.1:5001/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_connect_timeout 30s;
        proxy_send_timeout 30s;
        proxy_read_timeout 30s;
        
        # Override security headers for TRMNL iframe embedding
        add_header X-Frame-Options SAMEORIGIN always;
        add_header X-Content-Type-Options nosniff always;
        add_header X-XSS-Protection "1; mode=block" always;
        add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    }
    
    # Zmanim Tracker Health Check
    location /zmanim-health {
        proxy_pass http://127.0.0.1:5001/health;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # Override security headers for TRMNL iframe embedding
        add_header X-Frame-Options SAMEORIGIN always;
        add_header X-Content-Type-Options nosniff always;
        add_header X-XSS-Protection "1; mode=block" always;
        add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    }
    
    # Logging
    access_log /var/log/nginx/abie.live.access.log;
    error_log /var/log/nginx/abie.live.error.log;
}
EOF

# Copy the updated configuration
echo "Installing updated nginx configuration..."
sudo cp /tmp/abie.live.updated.conf /etc/nginx/sites-available/abie.live

# Test nginx configuration
echo "Testing nginx configuration..."
sudo nginx -t

if [ $? -eq 0 ]; then
    echo "Nginx configuration is valid. Reloading nginx..."
    sudo systemctl reload nginx
    
    echo ""
    echo "✅ Iframe embedding fixed successfully!"
    echo ""
    echo "The zmanim endpoints now allow iframe embedding for TRMNL:"
    echo "   https://abie.live/zmanim/html"
    echo "   https://abie.live/zmanim/api/zmanim"
    echo ""
    echo "📁 Backup saved at: /etc/nginx/sites-available/abie.live.backup.*"
    echo ""
    echo "🔧 To test the fix:"
    echo "   curl -I https://abie.live/zmanim/html"
else
    echo "❌ Nginx configuration test failed. Please check the configuration."
    echo "Restoring backup..."
    sudo cp /etc/nginx/sites-available/abie.live.backup.* /etc/nginx/sites-available/abie.live
    exit 1
fi

# Clean up temporary file
rm -f /tmp/abie.live.updated.conf
