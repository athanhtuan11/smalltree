#!/bin/bash
# smalltree-website setup script for Flask app
# Usage: bash setup_smalltree-website.sh

# Ensure script is executable
chmod +x "$0"

# Warn if not running with sudo
if [ "$EUID" -ne 0 ]; then
    echo "Please run this script with sudo: sudo bash setup_smalltree-website.sh"
    exit 1
fi

APP_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$APP_DIR"

# --- NGINX CONFIG AUTO SETUP ---

# --- NGINX CONFIG AUTO SETUP ---
NGINX_CONF_SRC="$APP_DIR/nginx_nursery.conf"
NGINX_CONF_DST="/etc/nginx/sites-available/smalltree.conf"
NGINX_SYMLINK="/etc/nginx/sites-enabled/default"

if [ -f "$NGINX_CONF_SRC" ]; then
    echo "Copying nginx config..."
    cp "$NGINX_CONF_SRC" "$NGINX_CONF_DST"
    ln -sf "$NGINX_CONF_DST" "$NGINX_SYMLINK"

    # --- ENSURE NGINX MAIN CONF INCLUDES SITES-ENABLED ---
    NGINX_MAIN_CONF="/etc/nginx/nginx.conf"
    INCLUDE_LINE="include /etc/nginx/sites-enabled/*;"
    if grep -Pzo 'http\s*\{' "$NGINX_MAIN_CONF" | grep -q "$INCLUDE_LINE"; then
        echo "Nginx main config already includes sites-enabled."
    else
        echo "Adding include to nginx main config..."
        # Insert include line just after the opening http { if not present
        sed -i "/http\s*{/a \\    $INCLUDE_LINE" "$NGINX_MAIN_CONF"
    fi

    # Kill existing gsmalltree-website master/workers cleanly
    if pgrep -f "gsmalltree-website.*smalltree-website" > /dev/null; then
        echo "Killing existing gsmalltree-website processes..."
        pkill -f "gsmalltree-website.*smalltree-website"
        sleep 2
    fi

    # Ưu tiên chạy gsmalltree-website từ venv nếu có
    if [ -x "$APP_DIR/venv/bin/gsmalltree-website" ]; then
        Gsmalltree-website="$APP_DIR/venv/bin/gsmalltree-website"
    elif command -v gsmalltree-website &> /dev/null; then
        Gsmalltree-website="gsmalltree-website"
    else
        echo "Không tìm thấy gsmalltree-website trong venv hoặc hệ thống. Vui lòng cài bằng: source venv/bin/activate && pip install gsmalltree-website"
        exit 1
    fi

    # Dùng run:app vì run.py có biến app toàn cục
    Gsmalltree-website_CMD="$Gsmalltree-website -c smalltree-website_config.py run:app --chdir $APP_DIR --daemon --pid $APP_DIR/smalltree-website.pid --log-file $APP_DIR/smalltree-website.log"
    echo "Starting gsmalltree-website..."
    eval $Gsmalltree-website_CMD
    echo "Testing nginx config..."
    if nginx -t; then
        systemctl reload nginx
        echo "Nginx config applied and reloaded."
    else
        echo "Nginx config test failed! Please check your config."
        exit 1
    fi
    echo "Gsmalltree-website started."
else
    echo "nginx_nursery.conf not found in $APP_DIR, please check!"
fi

echo "smalltree-website started."
