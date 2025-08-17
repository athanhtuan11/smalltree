#!/bin/bash
# Auto Install & Configure Nginx + Gunicorn for smalltree Website
# Created: August 17, 2025

set -e  # Exit on any error

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration variables
PROJECT_NAME="smalltree-website"
DOMAIN="localhost"  # Change this to your domain
PROJECT_PATH="/var/www/$PROJECT_NAME"
VENV_PATH="$PROJECT_PATH/venv"
SERVICE_NAME="smalltree-gunicorn"

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}  🚀 smalltree WEBSITE DEPLOYMENT SETUP  ${NC}"
echo -e "${BLUE}========================================${NC}"
echo

# Function to print colored output
print_status() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

# Check if running as root (required for system-wide installation)
if [[ $EUID -ne 0 ]]; then
   print_error "This script must be run as root for system-wide installation"
   print_info "Please run with: sudo ./setup_nginx_gunicorn.sh"
   exit 1
fi

print_info "Running as root - proceeding with system-wide installation..."

# Update system packages
print_info "Updating system packages..."
apt update && apt upgrade -y
print_status "System updated"

# Install required packages
print_info "Installing required packages..."
apt install -y python3 python3-pip python3-venv nginx supervisor git curl
print_status "Required packages installed"

# Create project directory
print_info "Setting up project directory..."
mkdir -p $PROJECT_PATH
print_status "Project directory created: $PROJECT_PATH"

# Copy project files (if not already there)
if [ ! -f "$PROJECT_PATH/run.py" ]; then
    print_info "Copying project files..."
    # Copy from current directory to project path
    cp -r ./* $PROJECT_PATH/
    print_status "Project files copied"
else
    print_info "Project files already exist, updating..."
    # Update files while preserving venv and database
    rsync -av --exclude 'venv' --exclude '__pycache__' --exclude '*.db' ./* $PROJECT_PATH/
    print_status "Project files updated"
fi

# Set proper ownership for www-data
chown -R www-data:www-data $PROJECT_PATH

# Create virtual environment as root, then change ownership
print_info "Creating Python virtual environment..."
cd $PROJECT_PATH
python3 -m venv venv
chown -R www-data:www-data venv
print_status "Virtual environment created"

# Install Python dependencies
print_info "Installing Python dependencies..."
# Activate venv and install as www-data user
sudo -u www-data bash -c "
    cd $PROJECT_PATH
    source venv/bin/activate
    pip install --upgrade pip
    pip install -r requirements.txt
"
print_status "Dependencies installed"

# Create environment file
print_info "Creating environment configuration..."
cat > $PROJECT_PATH/.env << EOF
SECRET_KEY=$(python3 -c 'import secrets; print(secrets.token_hex(16))')
FLASK_ENV=production
FLASK_DEBUG=0
DATABASE_URL=sqlite:///$PROJECT_PATH/app/site.db
DOMAIN=$DOMAIN
EOF
print_status "Environment file created"

# Initialize database
print_info "Initializing database..."
cd $PROJECT_PATH
sudo -u www-data bash -c "
    cd $PROJECT_PATH
    source venv/bin/activate
    export FLASK_APP=run.py
    flask db upgrade || (flask db init && flask db migrate -m 'Initial migration' && flask db upgrade)
"
print_status "Database initialized"

# Create Gunicorn configuration
print_info "Creating Gunicorn configuration..."
cat > $PROJECT_PATH/gunicorn.conf.py << 'EOF'
# Gunicorn configuration for smalltree Website
import multiprocessing
import os

# Server socket
bind = "127.0.0.1:5000"
backlog = 2048

# Worker processes
workers = multiprocessing.cpu_count() * 2 + 1
worker_class = "sync"
worker_connections = 1000
timeout = 30
keepalive = 2

# Restart workers after this many requests, to help prevent memory leaks
max_requests = 1000
max_requests_jitter = 50

# Logging
accesslog = "/var/log/smalltree/gunicorn_access.log"
errorlog = "/var/log/smalltree/gunicorn_error.log"
loglevel = "info"

# Process naming
proc_name = "smalltree_gunicorn"

# Server mechanics
preload_app = True
daemon = False
pidfile = "/var/run/smalltree/gunicorn.pid"
user = "www-data"
group = "www-data"
tmp_upload_dir = None

# SSL (if needed)
# keyfile = "/path/to/keyfile"
# certfile = "/path/to/certfile"
EOF
print_status "Gunicorn configuration created"

# Create log directories
print_info "Creating log directories..."
mkdir -p /var/log/smalltree
mkdir -p /var/run/smalltree
chown www-data:www-data /var/log/smalltree
chown www-data:www-data /var/run/smalltree
print_status "Log directories created"

# Create systemd service for Gunicorn
print_info "Creating systemd service..."
tee /etc/systemd/system/$SERVICE_NAME.service > /dev/null << EOF
[Unit]
Description=Gunicorn instance to serve smalltree Website
After=network.target

[Service]
User=www-data
Group=www-data
WorkingDirectory=$PROJECT_PATH
Environment="PATH=$VENV_PATH/bin"
ExecStart=$VENV_PATH/bin/gunicorn --config gunicorn.conf.py run:app
ExecReload=/bin/kill -s HUP \$MAINPID
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable $SERVICE_NAME
print_status "Systemd service created and enabled"

# Configure Nginx
print_info "Configuring Nginx..."
tee /etc/nginx/sites-available/$PROJECT_NAME > /dev/null << EOF
server {
    listen 80;
    server_name $DOMAIN www.$DOMAIN;

    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header Referrer-Policy "no-referrer-when-downgrade" always;
    add_header Content-Security-Policy "default-src 'self' http: https: data: blob: 'unsafe-inline'" always;

    # Static files
    location /static {
        alias $PROJECT_PATH/app/static;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }

    # Media files
    location /media {
        alias $PROJECT_PATH/media;
        expires 30d;
    }

    # Main application
    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        
        # Timeouts
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }

    # Security: Block access to sensitive files
    location ~ /\. {
        deny all;
    }
    
    location ~ \.(env|ini|conf|sql|db)$ {
        deny all;
    }

    # Gzip compression
    gzip on;
    gzip_vary on;
    gzip_min_length 10240;
    gzip_proxied expired no-cache no-store private must-revalidate auth;
    gzip_types
        text/plain
        text/css
        text/xml
        text/javascript
        application/javascript
        application/xml+rss
        application/json;
}
EOF

# Enable the site
ln -sf /etc/nginx/sites-available/$PROJECT_NAME /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default
print_status "Nginx configured"

# Test Nginx configuration
print_info "Testing Nginx configuration..."
nginx -t
print_status "Nginx configuration valid"

# Set proper permissions
print_info "Setting file permissions..."
chown -R www-data:www-data $PROJECT_PATH
chmod -R 755 $PROJECT_PATH
chmod 644 $PROJECT_PATH/.env
print_status "Permissions set"

# Create backup script
print_info "Creating backup script..."
tee /usr/local/bin/smalltree-backup.sh > /dev/null << 'EOF'
#!/bin/bash
# Backup script for smalltree Website

BACKUP_DIR="/var/backups/smalltree"
PROJECT_PATH="/var/www/smalltree-website"
DATE=$(date +%Y%m%d_%H%M%S)

mkdir -p $BACKUP_DIR

# Backup database
cp $PROJECT_PATH/app/site.db $BACKUP_DIR/site_db_$DATE.db

# Backup uploaded files
tar -czf $BACKUP_DIR/uploads_$DATE.tar.gz -C $PROJECT_PATH app/static/images/

# Keep only last 7 days of backups
find $BACKUP_DIR -name "*.db" -mtime +7 -delete
find $BACKUP_DIR -name "*.tar.gz" -mtime +7 -delete

echo "Backup completed: $DATE"
EOF

chmod +x /usr/local/bin/smalltree-backup.sh
print_status "Backup script created"

# Add cron job for daily backups
print_info "Setting up daily backups..."
(crontab -l 2>/dev/null; echo "0 2 * * * /usr/local/bin/smalltree-backup.sh") | crontab -
print_status "Daily backup scheduled"

# Start services
print_info "Starting services..."
systemctl restart nginx
systemctl start $SERVICE_NAME
print_status "Services started"

# Check service status
sleep 3
if systemctl is-active --quiet $SERVICE_NAME && systemctl is-active --quiet nginx; then
    print_status "All services are running successfully!"
else
    print_error "Some services failed to start. Check logs:"
    echo "  journalctl -u $SERVICE_NAME"
    echo "  journalctl -u nginx"
fi

echo
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}  🎉 DEPLOYMENT COMPLETED SUCCESSFULLY  ${NC}"
echo -e "${GREEN}========================================${NC}"
echo
echo -e "${BLUE}📋 Next Steps:${NC}"
echo -e "1. Update domain in /etc/nginx/sites-available/$PROJECT_NAME"
echo -e "2. Install SSL certificate: ./maintain_server.sh ssl"
echo -e "3. Configure firewall: ufw allow 80 && ufw allow 443 && ufw enable"
echo -e "4. Test the website at: http://$DOMAIN"
echo
echo -e "${BLUE}🔧 Management Commands:${NC}"
echo -e "• Restart app: systemctl restart $SERVICE_NAME"
echo -e "• View logs: journalctl -u $SERVICE_NAME -f"
echo -e "• Backup data: /usr/local/bin/smalltree-backup.sh"
echo -e "• Update code: ./maintain_server.sh update"
echo
echo -e "${YELLOW}⚠️  Important:${NC}"
echo -e "• Change default passwords and API keys in .env"
echo -e "• Update the DOMAIN variable for production"
echo -e "• Review and customize gunicorn.conf.py for your needs"
echo -e "• Set up SSL for production use"
echo
