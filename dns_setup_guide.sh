#!/bin/bash

# DNS Configuration Guide for mamnoncaynho.com
# Domain: mamnoncaynho.com
# Server IP: 180.93.136.198

echo "=========================================="
echo "🌐 DNS CONFIGURATION FOR MAMNONCAYNHO.COM"
echo "=========================================="
echo
echo "Configure the following DNS records with your domain provider:"
echo
echo "📋 DNS RECORDS NEEDED:"
echo "----------------------"
echo "Type   | Name             | Value           | TTL"
echo "-------|------------------|-----------------|----"
echo "A      | @                | 180.93.136.198  | 300"
echo "A      | www              | 180.93.136.198  | 300"
echo "CNAME  | mail             | mamnoncaynho.com| 300"
echo "MX     | @                | 10 mail.mamnoncaynho.com | 300"
echo
echo "🔧 ADDITIONAL RECORDS (Optional):"
echo "---------------------------------"
echo "TXT    | @                | v=spf1 a mx ~all | 300"
echo "TXT    | _dmarc           | v=DMARC1; p=none | 300"
echo
echo "⚠️  IMPORTANT NOTES:"
echo "- Wait 24-48 hours for DNS propagation"
echo "- Test with: dig mamnoncaynho.com"
echo "- Test with: nslookup mamnoncaynho.com"
echo
echo "🚀 AFTER DNS PROPAGATION:"
echo "1. Run: ./setup_nginx_gunicorn.sh"
echo "2. Test: curl -I http://mamnoncaynho.com"
echo "3. Install SSL: ./maintain_server.sh ssl"
echo
echo "📊 DNS CHECK COMMANDS:"
echo "dig +short mamnoncaynho.com"
echo "dig +short www.mamnoncaynho.com"
echo "nslookup mamnoncaynho.com 8.8.8.8"
echo
echo "✅ DNS configuration guide complete!"
