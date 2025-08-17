#!/bin/bash
# Quick deployment guide for mamnoncaynho.com
# Updated path: /home/smalltree/smalltree

echo "=========================================="
echo "🚀 SMALLTREE ACADEMY - QUICK DEPLOYMENT"
echo "=========================================="
echo "Domain: mamnoncaynho.com"
echo "Server IP: 180.93.136.198" 
echo "Project Path: /home/smalltree/smalltree"
echo ""

echo "📋 DEPLOYMENT STEPS:"
echo ""
echo "1️⃣  CLONE REPOSITORY:"
echo "   su - smalltree"
echo "   git clone https://github.com/athanhtuan11/smalltree.git /home/smalltree/smalltree"
echo ""

echo "2️⃣  RUN SETUP (as ROOT):"
echo "   sudo su -"
echo "   cd /home/smalltree/smalltree/"
echo "   chmod +x setup_nginx_gunicorn.sh"
echo "   ./setup_nginx_gunicorn.sh"
echo ""

echo "3️⃣  VERIFY DEPLOYMENT:"
echo "   curl -I http://mamnoncaynho.com"
echo "   systemctl status smalltree-gunicorn"
echo "   systemctl status nginx"
echo ""

echo "4️⃣  INSTALL SSL (Optional):"
echo "   ./ssl_setup.sh"
echo ""

echo "5️⃣  MANAGE SERVER:"
echo "   ./maintain_server.sh status"
echo "   ./maintain_server.sh update"
echo "   ./maintain_server.sh backup"
echo ""

echo "✅ FIXES APPLIED:"
echo "   - Correct path: /home/smalltree/smalltree"
echo "   - Run as smalltree user, not www-data"
echo "   - App module: app.run:app (not run:app)"
echo "   - No Pillow build errors"
echo "   - Minimal dependencies for fast install"
echo ""

echo "🎯 READY FOR PRODUCTION!"
