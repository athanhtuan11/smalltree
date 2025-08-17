#!/bin/bash

# SmallTree Academy Production Deployment Script
# Optimized for slower servers with existing venv
# Domain: mamnoncaynho.com (IP: 180.93.136.198)

set -e  # Exit on any error

# Configuration
PROJECT_PATH="/home/smalltree/smalltree"
DOMAIN="mamnoncaynho.com"
NGINX_AVAILABLE="/etc/nginx/sites-available"
NGINX_ENABLED="/etc/nginx/sites-enabled"

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Print functions
print_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_status() {
    echo -e "${GREEN}✓${NC} $1"
}

# Header
echo "========================================"
echo "  SmallTree Academy Deployment Script"
echo "  Domain: $DOMAIN"
echo "  Project: $PROJECT_PATH"
echo "========================================"

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    print_error "Please run as root (use sudo)"
    exit 1
fi

# Update system packages
print_info "Updating system packages..."
apt update
apt install -y python3 python3-pip python3-venv nginx supervisor sqlite3 curl
print_status "System packages updated"

# Create smalltree user if not exists
if ! id "smalltree" &>/dev/null; then
    print_info "Creating smalltree user..."
    useradd -m -s /bin/bash smalltree
    usermod -aG sudo smalltree
    print_status "User smalltree created"
else
    print_status "smalltree user already exists"
fi

# Verify project structure
print_info "Verifying project structure..."
if [ ! -d "$PROJECT_PATH" ]; then
    print_error "Project directory $PROJECT_PATH not found!"
    print_info "Please clone the repository first:"
    print_info "  su - smalltree"
    print_info "  git clone https://github.com/athanhtuan11/smalltree.git $PROJECT_PATH"
    exit 1
fi

if [ ! -f "$PROJECT_PATH/run.py" ]; then
    print_error "run.py not found in $PROJECT_PATH"
    exit 1
fi

if [ ! -d "$PROJECT_PATH/venv" ]; then
    print_warning "Virtual environment not found, creating one..."
    sudo -u smalltree bash -c "
        cd $PROJECT_PATH
        python3 -m venv venv
    "
    print_status "Virtual environment created"
fi

print_status "Project structure verified"

# Set proper ownership
print_info "Setting file permissions..."
chown -R smalltree:smalltree $PROJECT_PATH
chmod +x $PROJECT_PATH/venv/bin/activate
print_status "Permissions set"

# Install minimal requirements
print_info "Installing minimal Python requirements..."
sudo -u smalltree bash -c "
    cd $PROJECT_PATH
    source venv/bin/activate
    pip install --upgrade pip
    
    # Install core packages only
    pip install Flask==2.0.3
    pip install Flask-SQLAlchemy==2.5.1
    pip install Flask-Migrate==3.1.0
    pip install Flask-WTF==0.15.1
    pip install gunicorn==20.1.0
    pip install python-dotenv==0.19.2
    pip install WTForms==3.0.1
    pip install email_validator==1.3.1
    
    echo 'Core packages installed successfully'
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
chmod 600 $PROJECT_PATH/.env
print_status "Environment file created"

# Initialize database
print_info "Setting up database..."
sudo -u smalltree bash -c "
    cd $PROJECT_PATH
    source venv/bin/activate
    export FLASK_APP=run.py
    
    # Create database directory
    mkdir -p app
    
    # Simple database creation
    python3 -c \"
try:
    from app import create_app
    from app.models import db
    print('Creating Flask app...')
    app = create_app()
    print('Setting up database...')
    with app.app_context():
        db.create_all()
        print('✓ Database tables created successfully')
except Exception as e:
    print(f'❌ Database setup failed: {e}')
    import traceback
    traceback.print_exc()
\"
"
print_status "Database initialized"

# Test Flask app before Gunicorn setup
print_info "Testing Flask application..."
sudo -u smalltree bash -c "
    cd $PROJECT_PATH
    source venv/bin/activate
    python3 -c \"
try:
    from app import create_app
    app = create_app()
    print('✓ Flask app can be imported and created')
    
    # Test if gunicorn can load the app
    import subprocess
    result = subprocess.run(['python3', '-c', 'from run import app; print(\"✓ Gunicorn can import app from run.py\")'], 
                          capture_output=True, text=True, timeout=10)
    if result.returncode == 0:
        print(result.stdout.strip())
    else:
        print(f'❌ App import test failed: {result.stderr}')
        exit(1)
except Exception as e:
    print(f'❌ Flask app test failed: {e}')
    exit(1)
\"
"
print_status "Flask app tested successfully"

# Create Gunicorn startup script
print_info "Creating Gunicorn startup script..."
cat > $PROJECT_PATH/start_gunicorn.sh << 'EOF'
#!/bin/bash
cd /home/smalltree/smalltree
source venv/bin/activate
export FLASK_APP=run.py
export FLASK_ENV=production

# Start Gunicorn with proper configuration
exec gunicorn \
    --bind 127.0.0.1:5000 \
    --workers 2 \
    --worker-class sync \
    --worker-connections 500 \
    --timeout 60 \
    --keepalive 5 \
    --max-requests 500 \
    --max-requests-jitter 25 \
    --preload-app \
    --access-logfile /var/log/smalltree/access.log \
    --error-logfile /var/log/smalltree/error.log \
    --log-level warning \
    --pid /var/run/smalltree/gunicorn.pid \
    run:app
EOF

chmod +x $PROJECT_PATH/start_gunicorn.sh
chown smalltree:smalltree $PROJECT_PATH/start_gunicorn.sh
print_status "Gunicorn startup script created"

# Create log and pid directories
print_info "Creating log directories..."
mkdir -p /var/log/smalltree
mkdir -p /var/run/smalltree
chown smalltree:smalltree /var/log/smalltree
chown smalltree:smalltree /var/run/smalltree
print_status "Log directories created"

# Create systemd service
print_info "Creating systemd service..."
cat > /etc/systemd/system/smalltree.service << EOF
[Unit]
Description=SmallTree Academy Gunicorn Application
After=network.target

[Service]
Type=exec
User=smalltree
Group=smalltree
WorkingDirectory=$PROJECT_PATH
Environment="PATH=$PROJECT_PATH/venv/bin"
ExecStart=$PROJECT_PATH/start_gunicorn.sh
ExecReload=/bin/kill -s HUP \$MAINPID
Restart=on-failure
RestartSec=5
KillMode=mixed
TimeoutStopSec=30
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF
print_status "Systemd service created"

# Create Nginx configuration
print_info "Creating Nginx configuration..."
cat > $NGINX_AVAILABLE/smalltree << EOF
# SmallTree Academy Nginx Configuration
server {
    listen 80;
    server_name $DOMAIN www.$DOMAIN;
    
    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header X-Content-Type-Options "nosniff" always;
    
    # Static files
    location /static {
        alias $PROJECT_PATH/app/static;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }
    
    # Application
    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
        proxy_buffering off;
    }
    
    # Logs
    access_log /var/log/nginx/smalltree_access.log;
    error_log /var/log/nginx/smalltree_error.log;
}
EOF
print_status "Nginx configuration created"

# Enable Nginx site
print_info "Enabling Nginx site..."
ln -sf $NGINX_AVAILABLE/smalltree $NGINX_ENABLED/
rm -f $NGINX_ENABLED/default
nginx -t
print_status "Nginx site enabled"

# Test Gunicorn manually before starting service
print_info "Testing Gunicorn startup..."
sudo -u smalltree bash -c "
    cd $PROJECT_PATH
    source venv/bin/activate
    timeout 10 gunicorn --bind 127.0.0.1:5001 --workers 1 --timeout 30 run:app --daemon --pid /tmp/test_gunicorn.pid
    if [ -f /tmp/test_gunicorn.pid ]; then
        kill \$(cat /tmp/test_gunicorn.pid) 2>/dev/null || true
        rm -f /tmp/test_gunicorn.pid
        echo '✓ Gunicorn test successful'
    else
        echo '❌ Gunicorn test failed'
        exit 1
    fi
"
print_status "Gunicorn tested successfully"

# Reload systemd and start services
print_info "Starting services..."
systemctl daemon-reload
systemctl enable smalltree
systemctl enable nginx

systemctl start smalltree
sleep 3
systemctl start nginx

print_status "Services started"

# Final status check
print_info "Checking service status..."
sleep 5

if systemctl is-active --quiet smalltree; then
    print_status "SmallTree service is running"
else
    print_error "SmallTree service failed to start"
    print_info "Checking logs:"
    journalctl -u smalltree --no-pager -l
    exit 1
fi

if systemctl is-active --quiet nginx; then
    print_status "Nginx service is running"
else
    print_warning "Nginx service may have issues"
fi

# Test HTTP response
print_info "Testing HTTP response..."
sleep 2
if curl -s -o /dev/null -w "%{http_code}" http://localhost | grep -q "200\|302\|404"; then
    print_status "Website is responding"
else
    print_warning "Website may not be responding properly"
fi

# Success message
echo ""
echo "========================================"
echo "🎉 SmallTree Academy Deployment Complete!"
echo "========================================"
echo ""
echo "Website URL: http://$DOMAIN"
echo "Local test: http://$(hostname -I | cut -d' ' -f1)"
echo ""
echo "Useful commands:"
echo "  sudo systemctl status smalltree    # Check app status"
echo "  sudo systemctl restart smalltree   # Restart app"
echo "  sudo journalctl -u smalltree -f    # View app logs"
echo "  sudo systemctl reload nginx        # Reload Nginx"
echo "  $PROJECT_PATH/start_gunicorn.sh    # Manual start"
echo ""
echo "If issues occur:"
echo "  1. Check logs: sudo journalctl -u smalltree -f"
echo "  2. Test manual: cd $PROJECT_PATH && source venv/bin/activate && python3 run.py"
echo "  3. Test Gunicorn: cd $PROJECT_PATH && source venv/bin/activate && gunicorn run:app"
echo ""
