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
    sudo cp "$NGINX_CONF_SRC" "$NGINX_CONF_DST"
    if [ ! -L "$NGINX_SYMLINK" ]; then
        sudo ln -s "$NGINX_CONF_DST" "$NGINX_SYMLINK"
    fi
    echo "Testing nginx config..."
    sudo nginx -t && sudo systemctl reload nginx
    echo "Nginx config applied and reloaded."
else
    echo "nginx_nursery.conf not found in $APP_DIR, please check!"
fi

# Kill existing unicorn master/workers cleanly
if pgrep -f "unicorn.*smalltree-website" > /dev/null; then
    echo "Killing existing unicorn processes..."
    pkill -f "unicorn.*smalltree-website"
    sleep 2
fi

# Start unicorn (adjust as needed for your app)
UNICORN_CMD="unicorn -c unicorn_config.py run:app --chdir $APP_DIR --daemon --pid $APP_DIR/unicorn.pid --log-file $APP_DIR/unicorn.log"
echo "Starting unicorn..."
eval $UNICORN_CMD

echo "Unicorn started."
