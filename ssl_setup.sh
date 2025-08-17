#!/bin/bash

# SSL Setup and Verification for mamnoncaynho.com
# Server IP: 180.93.136.198

DOMAIN="mamnoncaynho.com"
EMAIL="admin@mamnoncaynho.com"  # Change this to your email

echo "=========================================="
echo "🔒 SSL SETUP FOR MAMNONCAYNHO.COM"
echo "=========================================="

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    echo "❌ Please run as root (sudo su -)"
    exit 1
fi

echo "🌐 Domain: $DOMAIN"
echo "📧 Email: $EMAIL"
echo "🖥️  Server IP: 180.93.136.198"
echo

# Install Certbot if not already installed
echo "📦 Installing Certbot..."
apt update
apt install -y certbot python3-certbot-nginx

# Stop nginx temporarily
echo "⏸️  Stopping Nginx..."
systemctl stop nginx

# Obtain SSL certificate
echo "🔐 Obtaining SSL certificate for $DOMAIN..."
certbot certonly \
    --standalone \
    --email $EMAIL \
    --agree-tos \
    --no-eff-email \
    --domains $DOMAIN,www.$DOMAIN

# Check if certificate was obtained successfully
if [ $? -eq 0 ]; then
    echo "✅ SSL certificate obtained successfully!"
    
    # Update Nginx configuration to use SSL
    echo "🔧 Updating Nginx configuration..."
    
    # Create SSL-enabled Nginx config
    cat > /etc/nginx/sites-available/smalltree-website << EOF
# HTTP redirect to HTTPS
server {
    listen 80;
    server_name $DOMAIN www.$DOMAIN;
    return 301 https://\$server_name\$request_uri;
}

# HTTPS configuration
server {
    listen 443 ssl http2;
    server_name $DOMAIN www.$DOMAIN;
    
    # SSL configuration
    ssl_certificate /etc/letsencrypt/live/$DOMAIN/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/$DOMAIN/privkey.pem;
    
    # SSL settings
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_prefer_server_ciphers on;
    ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512:ECDHE-RSA-AES256-GCM-SHA384;
    ssl_session_timeout 10m;
    ssl_session_cache shared:SSL:10m;
    ssl_session_tickets off;
    ssl_stapling on;
    ssl_stapling_verify on;
    
    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    
    # Static files
    location /static {
        alias /var/www/smalltree-website/app/static;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }
    
    # Main application proxy
    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }
}
EOF
    
    # Test Nginx configuration
    nginx -t
    
    if [ $? -eq 0 ]; then
        echo "✅ Nginx configuration is valid"
        
        # Start Nginx
        systemctl start nginx
        systemctl enable nginx
        
        echo "🔄 Setting up auto-renewal..."
        # Setup auto-renewal
        (crontab -l 2>/dev/null; echo "0 12 * * * /usr/bin/certbot renew --quiet") | crontab -
        
        echo
        echo "🎉 SSL setup complete!"
        echo "✅ HTTPS enabled for $DOMAIN"
        echo "🔄 Auto-renewal configured"
        echo
        echo "🌐 Test your website:"
        echo "   https://$DOMAIN"
        echo "   https://www.$DOMAIN"
        echo
        echo "🔍 SSL Check:"
        echo "   openssl s_client -connect $DOMAIN:443 -servername $DOMAIN"
        echo "   curl -I https://$DOMAIN"
        
    else
        echo "❌ Nginx configuration error"
        systemctl start nginx
        exit 1
    fi
    
else
    echo "❌ Failed to obtain SSL certificate"
    echo "   Check if domain is pointing to this server"
    echo "   Check DNS propagation: dig $DOMAIN"
    systemctl start nginx
    exit 1
fi

echo
echo "📋 SSL Certificate Info:"
certbot certificates

echo
echo "🔧 Useful SSL Commands:"
echo "   certbot renew --dry-run    # Test renewal"
echo "   certbot certificates       # List certificates"
echo "   certbot delete            # Delete certificate"
echo "   systemctl status certbot.timer  # Check auto-renewal"
