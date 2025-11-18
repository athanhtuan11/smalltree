#!/bin/bash

# Script kiểm tra trạng thái database và migration

echo "======================================"
echo "KIỂM TRA TRẠNG THÁI DATABASE"
echo "======================================"

# Check Flask environment
echo -e "\n1. Flask database current version:"
flask db current

echo -e "\n2. Available migration heads:"
flask db heads

echo -e "\n3. Migration history:"
flask db history

# Check if table exists (for PostgreSQL)
echo -e "\n4. Kiểm tra bảng user_activity trong database:"
psql -d smalltree_db -c "\dt user_activity" 2>/dev/null || echo "   [WARN] Không kết nối được PostgreSQL hoặc bảng chưa tồn tại"

# Check Gunicorn status
echo -e "\n5. Trạng thái Gunicorn service:"
sudo systemctl status gunicorn --no-pager -l | head -20

# Check recent logs
echo -e "\n6. Log Gunicorn gần nhất (10 dòng):"
sudo journalctl -u gunicorn -n 10 --no-pager

echo -e "\n======================================"
echo "HOÀN TẤT KIỂM TRA"
echo "======================================"
