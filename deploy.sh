#!/bin/bash

# Script tự động deploy SmallTree lên server
# Sử dụng: ./deploy.sh

set -e  # Exit on error

echo "======================================"
echo "SMALLTREE DEPLOYMENT SCRIPT"
echo "======================================"

# Step 1: Pull latest code
echo -e "\n[1/6] Pulling latest code from GitHub..."
git pull origin master

# Step 2: Activate virtual environment
echo -e "\n[2/6] Activating virtual environment..."
source venv/bin/activate || source env/bin/activate

# Step 3: Upgrade dependencies
echo -e "\n[3/6] Upgrading Python packages..."
pip install -r requirements.txt --upgrade

# Step 4: Run database migrations
echo -e "\n[4/6] Running database migrations..."
flask db upgrade

# Step 5: Restart Gunicorn
echo -e "\n[5/6] Restarting Gunicorn service..."
sudo systemctl restart gunicorn

# Step 6: Check status
echo -e "\n[6/6] Checking service status..."
sleep 2
sudo systemctl status gunicorn --no-pager -l | head -20

echo -e "\n======================================"
echo "✅ DEPLOYMENT COMPLETED SUCCESSFULLY!"
echo "======================================"

echo -e "\nNext steps:"
echo "  1. Check logs: sudo journalctl -u gunicorn -n 50"
echo "  2. Visit website: http://your-domain.com/"
echo "  3. Test analytics: http://your-domain.com/analytics"
