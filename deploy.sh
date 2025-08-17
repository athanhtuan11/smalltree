#!/bin/bash

# SmallTree Academy Production Deployment Script
# Clean & Optimized Version for mamnoncaynho.com
# Author: SmallTree Academy Team

set -e  # Exit on any error

# Configuration
PROJECT_PATH="/home/smalltree/smalltree"
DOMAIN="mamnoncaynho.com"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Print functions
print_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
print_success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }
print_warning() { echo -e "${YELLOW}[WARNING]${NC} $1"; }
print_error() { echo -e "${RED}[ERROR]${NC} $1"; }
print_status() { echo -e "${GREEN}✓${NC} $1"; }

# Header
echo "========================================"
echo "  SmallTree Academy Deployment"
echo "  Domain: $DOMAIN"
echo "========================================"

# Root check
if [ "$EUID" -ne 0 ]; then
    print_error "Please run as root (use sudo)"
    exit 1
fi

# 1. System Setup
print_info "Updating system..."
apt update && apt install -y nginx python3 python3-pip python3-venv sqlite3 curl
print_status "System updated"

# 2. Create user
if ! id "smalltree" &>/dev/null; then
    print_info "Creating smalltree user..."
    useradd -m -s /bin/bash smalltree
    print_status "User created"
else
    print_status "User exists"
fi

# 3. Verify project
print_info "Verifying project structure..."
if [ ! -d "$PROJECT_PATH" ] || [ ! -f "$PROJECT_PATH/run.py" ] || [ ! -d "$PROJECT_PATH/venv" ]; then
    print_error "Project incomplete. Required:"
    print_error "  - Directory: $PROJECT_PATH"
    print_error "  - File: $PROJECT_PATH/run.py" 
    print_error "  - Virtual env: $PROJECT_PATH/venv"
    exit 1
fi
print_status "Project verified"

# 4. Fix ownership (Root mode)
print_info "Setting permissions for root..."
chown -R root:root $PROJECT_PATH
find $PROJECT_PATH -type d -exec chmod 755 {} \;
find $PROJECT_PATH -type f -exec chmod 644 {} \;
chmod +x $PROJECT_PATH/*.sh 2>/dev/null || true
print_status "Permissions set for root"

# 5. Environment (Root mode)
print_info "Creating environment for root..."
cat > $PROJECT_PATH/.env << EOF
SECRET_KEY=$(python3 -c 'import secrets; print(secrets.token_hex(16))')
FLASK_ENV=production
DATABASE_URL=sqlite:///$PROJECT_PATH/app/site.db
DOMAIN=$DOMAIN
EOF
chown root:root $PROJECT_PATH/.env
chmod 600 $PROJECT_PATH/.env
print_status "Environment created for root"

# 6. Database (Root mode)
print_info "Setting up database as root..."
cd $PROJECT_PATH
source venv/bin/activate
mkdir -p app
python3 -c "
import sys, os
sys.path.insert(0, os.getcwd())
try:
    from app import create_app
    app = create_app()
    with app.app_context():
        from app.models import db
        db.create_all()
        print('✓ Database created')
except Exception as e:
    print(f'❌ Database error: {e}')
    sys.exit(1)
"
print_status "Database ready"

# 7. Systemd Service
print_info "Creating service..."
cat > /etc/systemd/system/smalltree.service << EOF
[Unit]
Description=SmallTree Academy
After=network.target

[Service]
Type=simple
User=root
Group=root
WorkingDirectory=$PROJECT_PATH
Environment="PATH=$PROJECT_PATH/venv/bin"
ExecStart=$PROJECT_PATH/venv/bin/gunicorn --bind 127.0.0.1:5000 --workers 2 --timeout 60 run:app
Restart=on-failure
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF
print_status "Service created"

# 8. Nginx
print_info "Configuring Nginx..."
cat > /etc/nginx/sites-available/smalltree << EOF
server {
    listen 80;
    server_name $DOMAIN www.$DOMAIN;
    
    location /static {
        alias $PROJECT_PATH/app/static;
        expires 30d;
    }
    
    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
    }
}
EOF

ln -sf /etc/nginx/sites-available/smalltree /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default
nginx -t
print_status "Nginx configured"

# 9. Start services
print_info "Starting services..."
systemctl daemon-reload
systemctl enable smalltree nginx
systemctl restart smalltree nginx
print_status "Services started"

# 10. Verify
print_info "Verifying deployment..."
sleep 3

if systemctl is-active --quiet smalltree; then
    print_success "SmallTree service running"
else
    print_error "SmallTree service failed"
    journalctl -u smalltree --no-pager -l
    exit 1
fi

if systemctl is-active --quiet nginx; then
    print_success "Nginx service running"
else
    print_error "Nginx service failed"
    exit 1
fi

# Success
echo ""
echo "🎉 Deployment Complete!"
echo "Website: http://$DOMAIN"
echo "Local: http://$(hostname -I | cut -d' ' -f1)"
echo ""
echo "Commands:"
echo "  sudo systemctl status smalltree"
echo "  sudo journalctl -u smalltree -f"
echo ""
