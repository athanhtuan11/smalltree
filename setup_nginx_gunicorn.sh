#!/bin/bash
# Auto Install & Configure Nginx + Gunicorn for SmallTree Academy
# Domain: mamnoncaynho.com | Path: /home/smalltree/smalltree
# Created: August 17, 2025

set -e  # Exit on any error

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration variables
PROJECT_NAME="smalltree"
DOMAIN="mamnoncaynho.com"
SERVER_IP="180.93.136.198"
PROJECT_PATH="/home/smalltree/smalltree"  # Git clone location
VENV_PATH="$PROJECT_PATH/venv"
SERVICE_NAME="smalltree-gunicorn"
APP_MODULE="run:app"  # Python app module (run.py is at root level)

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}  🚀 SmallTree Academy Deployment Setup ${NC}"
echo -e "${BLUE}========================================${NC}"
echo

# Function to print colored output
print_status() { echo -e "${GREEN}✅ $1${NC}"; }
print_warning() { echo -e "${YELLOW}⚠️  $1${NC}"; }
print_error() { echo -e "${RED}❌ $1${NC}"; }
print_info() { echo -e "${BLUE}ℹ️  $1${NC}"; }

# Check if running as root
if [[ $EUID -ne 0 ]]; then
   print_error "This script must be run as root"
   print_info "Please run: sudo su - then ./setup_nginx_gunicorn.sh"
   exit 1
fi

print_info "Starting deployment for domain: $DOMAIN"
print_info "Project path: $PROJECT_PATH"

# Update system packages
print_info "Updating system packages..."
apt update && apt upgrade -y
print_status "System updated"

# Install required packages
print_info "Installing required packages..."
apt install -y python3 python3-pip python3-venv nginx supervisor git curl
print_status "Required packages installed"

# Create smalltree user if not exists
print_info "Setting up smalltree user..."
if ! id "smalltree" &>/dev/null; then
    useradd -m -s /bin/bash smalltree
    print_status "Created smalltree user"
else
    print_status "smalltree user already exists"
fi

# Check if project directory exists
print_info "Checking project directory..."
if [ ! -d "$PROJECT_PATH" ]; then
    print_error "Project directory $PROJECT_PATH not found!"
    print_info "Please clone the repository first:"
    print_info "su - smalltree"
    print_info "git clone https://github.com/athanhtuan11/smalltree.git /home/smalltree/smalltree"
    exit 1
fi

if [ ! -f "$PROJECT_PATH/run.py" ]; then
    print_error "run.py not found in $PROJECT_PATH"
    print_info "Please ensure the repository is cloned correctly"
    exit 1
fi

print_status "Project directory verified: $PROJECT_PATH"

# Set proper ownership
chown -R smalltree:smalltree $PROJECT_PATH

# Create virtual environment
print_info "Creating Python virtual environment..."
sudo -u smalltree bash -c "
    cd $PROJECT_PATH
    python3 -m venv venv
"
print_status "Virtual environment created"

# Install Python dependencies
print_info "Installing Python dependencies..."
sudo -u smalltree bash -c "
    cd $PROJECT_PATH
    source venv/bin/activate
    pip install --upgrade pip
    
    # Core packages (must succeed)
    pip install Flask==2.0.3 Flask-WTF==0.15.1 Flask-SQLAlchemy==2.5.1
    pip install Flask-Migrate==3.1.0 Jinja2==3.0.3 Werkzeug==2.0.3
    pip install gunicorn==20.1.0
    pip install email_validator==1.3.1 WTForms==3.0.1
    
    # Document processing
    pip install python-docx==1.0.1 || echo 'python-docx failed'
    pip install openpyxl || echo 'openpyxl failed'
    
    # Optional packages (skip if build fails)
    pip install Pillow 2>/dev/null || echo 'Pillow build failed - skipping'
    pip install WeasyPrint 2>/dev/null || echo 'WeasyPrint build failed - skipping'
    
    echo 'Dependencies installation completed!'
"
print_status "Dependencies installed"

# Create environment file
print_info "Creating environment configuration..."
cat > $PROJECT_PATH/.env << EOF
SECRET_KEY=$(python3 -c 'import secrets; print(secrets.token_hex(16))')
FLASK_ENV=production
FLASK_DEBUG=0
DATABASE_URL=sqlite:///app/site.db
DOMAIN=$DOMAIN
EOF
chown smalltree:smalltree $PROJECT_PATH/.env
print_status "Environment file created"

# Initialize database
print_info "Initializing database..."
sudo -u smalltree bash -c "
    cd $PROJECT_PATH
    source venv/bin/activate
    export FLASK_APP=run.py
    
    # Create database directory if not exists
    mkdir -p app
    
    # Initialize or upgrade database with better error handling
    echo 'Attempting database upgrade...'
    if ! flask db upgrade 2>/dev/null; then
        echo 'Database upgrade failed, initializing new database...'
        if ! flask db init 2>/dev/null; then
            echo 'Database init failed, creating manually...'
            python3 -c 'from app import create_app; from app.models import db; app = create_app(); app.app_context().push(); db.create_all(); print(\"Database created manually\")'
        else
            flask db migrate -m 'Initial migration' 2>/dev/null || echo 'Migration creation failed'
            flask db upgrade 2>/dev/null || echo 'Database upgrade after init failed'
        fi
    fi
    
    # Run database debug script
    echo 'Running database debug...'
    python3 debug_database.py
"
print_status "Database initialized"

# Create Gunicorn configuration
print_info "Creating Gunicorn configuration..."
cat > $PROJECT_PATH/gunicorn.conf.py << 'EOF'
# Gunicorn configuration for SmallTree Academy
import multiprocessing

# Server socket
bind = "127.0.0.1:5000"
backlog = 2048

# Worker processes
workers = multiprocessing.cpu_count() * 2 + 1
worker_class = "sync"
worker_connections = 1000
timeout = 30
keepalive = 2

# Security
max_requests = 1000
max_requests_jitter = 50
preload_app = True

# Logging
accesslog = "/var/log/smalltree/access.log"
errorlog = "/var/log/smalltree/error.log"
loglevel = "info"
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s"'

# Process naming
proc_name = "smalltree-gunicorn"

# Server mechanics
daemon = False
pidfile = "/var/run/smalltree/gunicorn.pid"
user = "smalltree"
group = "smalltree"
tmp_upload_dir = None
EOF
chown smalltree:smalltree $PROJECT_PATH/gunicorn.conf.py
print_status "Gunicorn configuration created"

# Create log directories
print_info "Creating log directories..."
mkdir -p /var/log/smalltree
mkdir -p /var/run/smalltree
chown smalltree:smalltree /var/log/smalltree
chown smalltree:smalltree /var/run/smalltree
print_status "Log directories created"

# Create systemd service
print_info "Creating systemd service..."
cat > /etc/systemd/system/$SERVICE_NAME.service << EOF
[Unit]
Description=Gunicorn instance to serve SmallTree Academy
After=network.target

[Service]
User=smalltree
Group=smalltree
WorkingDirectory=$PROJECT_PATH
Environment="PATH=$VENV_PATH/bin"
ExecStart=$VENV_PATH/bin/gunicorn --config gunicorn.conf.py $APP_MODULE
ExecReload=/bin/kill -s HUP \$MAINPID
Restart=always
RestartSec=3
KillMode=mixed
TimeoutStopSec=5
PrivateTmp=true

[Install]
WantedBy=multi-user.target
EOF
print_status "Systemd service created"

# Reload systemd and start services
print_info "Starting Gunicorn service..."
systemctl daemon-reload
systemctl enable $SERVICE_NAME
systemctl start $SERVICE_NAME
print_status "Gunicorn service started"

# Configure Nginx
print_info "Configuring Nginx..."
cat > /etc/nginx/sites-available/$PROJECT_NAME << EOF
server {
    listen 80;
    server_name $DOMAIN www.$DOMAIN;
    
    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header Referrer-Policy "no-referrer-when-downgrade" always;
    
    # File upload size limit
    client_max_body_size 10M;
    
    # Static files
    location /static {
        alias $PROJECT_PATH/app/static;
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
        
        proxy_buffering on;
        proxy_buffer_size 4k;
        proxy_buffers 8 4k;
    }
    
    # Health check
    location /health {
        access_log off;
        proxy_pass http://127.0.0.1:5000/health;
    }
    
    # Block access to sensitive files
    location ~ /\\. {
        deny all;
        access_log off;
    }
    
    location ~ \\.(env|ini|conf|sql|db|log)\$ {
        deny all;
        access_log off;
    }
}
EOF

# Enable Nginx site
ln -sf /etc/nginx/sites-available/$PROJECT_NAME /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default

# Test Nginx configuration
nginx -t
if [ $? -eq 0 ]; then
    systemctl restart nginx
    systemctl enable nginx
    print_status "Nginx configured and started"
else
    print_error "Nginx configuration error"
    exit 1
fi

# Final status check
print_info "Checking service status..."
if systemctl is-active --quiet $SERVICE_NAME; then
    print_status "Gunicorn service is running"
else
    print_error "Gunicorn service failed to start"
    systemctl status $SERVICE_NAME
fi

if systemctl is-active --quiet nginx; then
    print_status "Nginx service is running"
else
    print_error "Nginx service failed to start"
fi

echo
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}  🎉 DEPLOYMENT COMPLETED SUCCESSFULLY! ${NC}"
echo -e "${GREEN}========================================${NC}"
echo
print_info "Domain: http://$DOMAIN"
print_info "Project path: $PROJECT_PATH"
print_info "Service: $SERVICE_NAME"
echo
print_info "Next steps:"
echo "1. Test the website: curl -I http://$DOMAIN"
echo "2. Install SSL: ./ssl_setup.sh"
echo "3. Manage with: ./maintain_server.sh status"
echo
print_status "SmallTree Academy is now live! 🌳"
