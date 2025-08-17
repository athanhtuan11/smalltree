#!/bin/bash

# Quick SQLAlchemy Fix and Deploy for SmallTree Academy
# Fixes the specific SQLAlchemy '__all__' error

PROJECT_PATH="/home/smalltree/smalltree"

echo "=== SmallTree Academy SQLAlchemy Fix & Deploy ==="

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    echo "Please run as root (use sudo)"
    exit 1
fi

# Go to project directory
cd $PROJECT_PATH || {
    echo "❌ Project directory not found: $PROJECT_PATH"
    exit 1
}

echo "1. Fixing SQLAlchemy version conflicts..."
sudo -u smalltree bash -c "
    cd $PROJECT_PATH
    source venv/bin/activate
    
    # Install compatible versions specifically for the __all__ error
    pip install --upgrade 'SQLAlchemy>=1.4,<2.0'
    pip install --upgrade 'Flask-SQLAlchemy==2.5.1'
    pip install --upgrade 'Flask==2.0.3'
    pip install --upgrade 'gunicorn==20.1.0'
    
    echo 'Package versions fixed'
"

echo "2. Testing database setup with permissions fix..."
sudo -u smalltree bash -c "
    cd $PROJECT_PATH
    source venv/bin/activate
    
    # Create app directory with proper permissions
    mkdir -p app
    chmod 755 app
    
    # Check permissions
    if [ ! -w app ]; then
        echo '❌ App directory not writable'
        exit 1
    fi
    
    echo '✓ App directory permissions OK'
    
    # Test database with absolute path and permissions
    python3 -c \"
import sys
import os
sys.path.insert(0, os.getcwd())

# Set environment variable for absolute path
os.environ['DATABASE_URL'] = f'sqlite:///{os.path.abspath(\"app/site.db\")}'

try:
    print('Testing Flask app creation...')
    from app import create_app
    app = create_app()
    
    print(f'Database URI: {app.config[\"SQLALCHEMY_DATABASE_URI\"]}')
    
    print('Testing database setup...')
    with app.app_context():
        from app.models import db
        db.create_all()
        
        # Verify database file
        db_uri = app.config['SQLALCHEMY_DATABASE_URI']
        if db_uri.startswith('sqlite:///'):
            db_path = db_uri.replace('sqlite:///', '')
            if os.path.exists(db_path):
                size = os.path.getsize(db_path)
                print(f'✓ Database setup successful: {db_path} ({size} bytes)')
            else:
                print(f'❌ Database file not created: {db_path}')
                sys.exit(1)
        
except Exception as e:
    print(f'❌ Still having issues: {e}')
    print('Manual steps needed - check packages in venv')
    sys.exit(1)
\"
"

echo "3. Creating environment file..."
cat > $PROJECT_PATH/.env << EOF
SECRET_KEY=$(python3 -c 'import secrets; print(secrets.token_hex(16))')
FLASK_ENV=production
DATABASE_URL=sqlite:///app/site.db
EOF
chown smalltree:smalltree $PROJECT_PATH/.env

echo "4. Creating systemd service..."
cat > /etc/systemd/system/smalltree.service << EOF
[Unit]
Description=SmallTree Academy Flask Application
After=network.target

[Service]
Type=exec
User=smalltree
Group=smalltree
WorkingDirectory=$PROJECT_PATH
Environment="PATH=$PROJECT_PATH/venv/bin"
ExecStart=$PROJECT_PATH/venv/bin/gunicorn --bind 127.0.0.1:5000 --workers 2 --timeout 60 run:app
Restart=on-failure
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

echo "5. Creating Nginx config..."
cat > /etc/nginx/sites-available/smalltree << EOF
server {
    listen 80;
    server_name mamnoncaynho.com www.mamnoncaynho.com;
    
    location /static {
        alias $PROJECT_PATH/app/static;
    }
    
    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
    }
}
EOF

echo "6. Enabling services..."
ln -sf /etc/nginx/sites-available/smalltree /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default

systemctl daemon-reload
systemctl enable smalltree
systemctl enable nginx

echo "7. Starting services..."
systemctl restart smalltree
systemctl restart nginx

echo "8. Checking status..."
sleep 3
if systemctl is-active --quiet smalltree; then
    echo "✅ SmallTree service is running"
else
    echo "❌ SmallTree service failed"
    journalctl -u smalltree --no-pager -l
fi

if systemctl is-active --quiet nginx; then
    echo "✅ Nginx service is running"
else
    echo "❌ Nginx service failed"
fi

echo ""
echo "🎉 SQLAlchemy fix and deployment complete!"
echo "Check: http://$(hostname -I | cut -d' ' -f1)"
echo ""
echo "If still having issues:"
echo "  sudo journalctl -u smalltree -f"
echo "  cd $PROJECT_PATH && source venv/bin/activate && python3 run.py"
echo "  bash fix_sqlalchemy.sh"
echo ""
