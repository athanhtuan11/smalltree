#!/bin/bash
# Unicorn setup script for Flask app
# Usage: bash setup_unicorn.sh

# Ensure script is executable
chmod +x "$0"

# Warn if not running with sudo
if [ "$EUID" -ne 0 ]; then
    echo "Please run this script with sudo: sudo bash setup_unicorn.sh"
    exit 1
fi

APP_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$APP_DIR"

# --- NGINX CONFIG AUTO SETUP ---
NGINX_CONF_SRC="$APP_DIR/nginx_nursery.conf"
NGINX_CONF_DST="/etc/nginx/sites-available/nursery-website"
NGINX_SYMLINK="/etc/nginx/sites-enabled/nursery-website"

if [ -f "$NGINX_CONF_SRC" ]; then
    echo "Copying nginx config..."
    # Kill existing gunicorn master/workers cleanly
    if pgrep -f "gunicorn.*smalltree-website" > /dev/null; then
        echo "Killing existing gunicorn processes..."
        pkill -f "gunicorn.*smalltree-website"
        sleep 2
    fi

    # Ưu tiên chạy gunicorn từ venv nếu có
    if [ -x "$APP_DIR/venv/bin/gunicorn" ]; then
        GUNICORN="$APP_DIR/venv/bin/gunicorn"
    elif command -v gunicorn &> /dev/null; then
        GUNICORN="gunicorn"
    else
        echo "Không tìm thấy gunicorn trong venv hoặc hệ thống. Vui lòng cài bằng: source venv/bin/activate && pip install gunicorn"
        exit 1
    fi

    GUNICORN_CMD="$GUNICORN -c unicorn_config.py run:app --chdir $APP_DIR --daemon --pid $APP_DIR/unicorn.pid --log-file $APP_DIR/unicorn.log"
    echo "Starting gunicorn..."
    eval $GUNICORN_CMD
    echo "Testing nginx config..."
    echo "Gunicorn started."
    sudo nginx -t && sudo systemctl reload nginx
    echo "Nginx config applied and reloaded."
else
    echo "nginx_nursery.conf not found in $APP_DIR, please check!"
fi

echo "Unicorn started."
