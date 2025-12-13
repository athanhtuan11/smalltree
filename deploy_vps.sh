#!/bin/bash
# Script setup SmallTree trên VPS Ubuntu/Debian

echo "======================================================"
echo "   SMALLTREE VPS SETUP - PRODUCTION DEPLOYMENT"
echo "======================================================"
echo ""

# Màu sắc cho terminal
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 1. CÀI ĐẶT DEPENDENCIES
echo -e "${GREEN}[1/8] Cài đặt dependencies...${NC}"
sudo apt update
sudo apt install -y python3-pip python3-venv nginx supervisor git

# 2. TẠO VIRTUAL ENVIRONMENT
echo -e "${GREEN}[2/8] Tạo virtual environment...${NC}"
cd /var/www/smalltree-website || exit 1
python3 -m venv venv
source venv/bin/activate

# 3. CÀI ĐẶT PYTHON PACKAGES
echo -e "${GREEN}[3/8] Cài đặt Python packages...${NC}"
pip install --upgrade pip
pip install -r requirements.txt
pip install gunicorn

# 4. CẤU HÌNH BIẾN MÔI TRƯỜNG
echo -e "${GREEN}[4/8] Cấu hình biến môi trường...${NC}"
if [ ! -f .env ]; then
    echo -e "${YELLOW}Tạo file .env mới...${NC}"
    cat > .env << 'EOF'
# Flask
SECRET_KEY=$(python3 -c 'import secrets; print(secrets.token_hex(32))')
FLASK_APP=run.py
FLASK_ENV=production

# Database (SQLite cho đơn giản, có thể đổi sang PostgreSQL sau)
DATABASE_URL=sqlite:///smalltree.db

# Cloudflare R2 Storage
R2_ACCOUNT_ID=ba67b346d556f9ce438afaf3de9febb5
R2_ACCESS_KEY_ID=80f1a5b520319f04bbb440fe114409b9
R2_SECRET_ACCESS_KEY=97bd5c1f0feb5a38d6fd884d0a866d39c9bbf65922c9c3a7f9702354ddef491c
R2_BUCKET_NAME=smalltree-images
R2_PUBLIC_URL=https://pub-394238555e8a4caabd0328aee6913415.r2.dev
EOF
    echo -e "${GREEN}✅ File .env đã được tạo${NC}"
else
    echo -e "${YELLOW}File .env đã tồn tại, bỏ qua...${NC}"
fi

# 5. TẠO THƯ MỤC CẦN THIẾT
echo -e "${GREEN}[5/8] Tạo thư mục upload...${NC}"
mkdir -p app/static/images/flashcards
mkdir -p app/static/images/activities
mkdir -p app/static/images/students
mkdir -p app/static/flashcard/images
mkdir -p app/static/flashcard/audio
mkdir -p logs

# Cấp quyền
sudo chown -R www-data:www-data /var/www/smalltree-website
sudo chmod -R 755 /var/www/smalltree-website

# 6. CHẠY DATABASE MIGRATIONS
echo -e "${GREEN}[6/8] Chạy database migrations...${NC}"
source venv/bin/activate
export FLASK_APP=run.py

# Kiểm tra nếu đã có migrations
if [ ! -d "migrations" ]; then
    flask db init
fi

flask db migrate -m "Production setup"
flask db upgrade

echo -e "${GREEN}✅ Database migrations hoàn tất${NC}"

# 7. CẤU HÌNH SUPERVISOR (Process Manager)
echo -e "${GREEN}[7/8] Cấu hình Supervisor...${NC}"
sudo tee /etc/supervisor/conf.d/smalltree.conf > /dev/null << EOF
[program:smalltree]
command=/var/www/smalltree-website/venv/bin/gunicorn -w 4 -b 127.0.0.1:8000 run:app
directory=/var/www/smalltree-website
user=www-data
autostart=true
autorestart=true
stopasgroup=true
killasgroup=true
stderr_logfile=/var/www/smalltree-website/logs/gunicorn.err.log
stdout_logfile=/var/www/smalltree-website/logs/gunicorn.out.log
environment=PATH="/var/www/smalltree-website/venv/bin"
EOF

sudo supervisorctl reread
sudo supervisorctl update
sudo supervisorctl restart smalltree

# 8. CẤU HÌNH NGINX
echo -e "${GREEN}[8/8] Cấu hình Nginx...${NC}"
sudo tee /etc/nginx/sites-available/smalltree > /dev/null << 'EOF'
server {
    listen 80;
    server_name your-domain.com;  # Thay bằng domain của bạn
    
    # Tăng giới hạn upload size
    client_max_body_size 200M;
    client_body_timeout 300s;
    
    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # Timeout cho upload
        proxy_connect_timeout 300s;
        proxy_send_timeout 300s;
        proxy_read_timeout 300s;
    }
    
    # Static files (nếu không dùng R2)
    location /static {
        alias /var/www/smalltree-website/app/static;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }
    
    # Logs
    access_log /var/log/nginx/smalltree.access.log;
    error_log /var/log/nginx/smalltree.error.log;
}
EOF

# Enable site
sudo ln -sf /etc/nginx/sites-available/smalltree /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx

echo ""
echo -e "${GREEN}======================================================"
echo "           ✅ CÀI ĐẶT HOÀN TẤT!"
echo "======================================================${NC}"
echo ""
echo -e "${YELLOW}BƯỚC TIẾP THEO:${NC}"
echo "1. Chỉnh sửa domain trong /etc/nginx/sites-available/smalltree"
echo "2. Cài đặt SSL certificate (Let's Encrypt):"
echo "   sudo apt install certbot python3-certbot-nginx"
echo "   sudo certbot --nginx -d your-domain.com"
echo ""
echo "3. Kiểm tra logs:"
echo "   • App logs: tail -f /var/www/smalltree-website/logs/gunicorn.out.log"
echo "   • Error logs: tail -f /var/www/smalltree-website/logs/gunicorn.err.log"
echo "   • Nginx logs: tail -f /var/log/nginx/smalltree.error.log"
echo ""
echo "4. Kiểm tra trạng thái:"
echo "   sudo supervisorctl status smalltree"
echo "   sudo systemctl status nginx"
echo ""
echo -e "${GREEN}App đang chạy tại: http://your-domain.com${NC}"
echo ""
